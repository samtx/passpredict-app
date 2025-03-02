from datetime import datetime, UTC
import logging
from itertools import batched
from typing import cast, TypedDict
import json
import tempfile
import gzip

import httpx
from hatchet_sdk import Context
from hatchet_sdk.rate_limit import RateLimit
from pydantic import BaseModel, SecretStr, computed_field

from api.settings import config
from ..client import hatchet
from .insert_orbits import Orbit, Satellite, InsertOrbitBatchOutput, NewOrbit


__all__ = [
    "FetchSpacetrackOrbits",
]


logger = logging.getLogger(__name__)

SPACETRACK_BASE_URL = "https://www.space-track.org"
SPACETRACK_AUTH_ENDPOINT = "/ajaxauth/login"
SPACETRACK_TIMEOUT = 30
SPACETRACK_EPOCH_DAYS_SINCE = 0.5


class SpacetrackJson(TypedDict):
    CCSDS_OMM_VERS: str
    COMMENT: str
    CREATION_DATE: str
    ORIGINATOR: str
    OBJECT_NAME: str
    OBJECT_ID: str
    CENTER_NAME: str
    REF_FRAME: str
    TIME_SYSTEM: str
    MEAN_ELEMENT_THEORY: str
    EPOCH: str
    MEAN_MOTION: float
    ECCENTRICITY: float
    INCLINATION: float
    RA_OF_ASC_NODE: float
    ARG_OF_PERICENTER: float
    MEAN_ANOMALY: float
    EPHEMERIS_TYPE: str
    CLASSIFICATION_TYPE: str
    NORAD_CAT_ID: int
    ELEMENT_SET_NO: int
    REV_AT_EPOCH: int
    BSTAR: float
    MEAN_MOTION_DOT: float
    MEAN_MOTION_DDOT: float
    SEMIMAJOR_AXIS: float
    PERIOD: float
    APOAPSIS: float
    PERIAPSIS: float
    OBJECT_TYPE: str
    RCS_SIZE: str
    COUNTRY_CODE: str
    LAUNCH_DATE: str
    SITE: str
    DECAY_DATE: str | None
    FILE: int | None
    GP_ID: int
    TLE_LINE0: str
    TLE_LINE1: str
    TLE_LINE2: str


class FetchSpacetrackOrbitOptions(BaseModel):
    base_url: str = SPACETRACK_BASE_URL
    auth_endpoint: str = SPACETRACK_AUTH_ENDPOINT
    epoch_days_since: float = SPACETRACK_EPOCH_DAYS_SINCE
    timeout: float = SPACETRACK_TIMEOUT
    # include_unknown: bool = False


class DownloadStepOutput(BaseModel):
    request_url: str
    status_code: int
    fname: str
    queried_at: datetime


class NewOrbitOutput(BaseModel):
    new_orbits: list[NewOrbit]

    @computed_field
    @property
    def count(self) -> int:
        return len(self.new_orbits)


@hatchet.workflow(
    on_events=["fetch-orbits:spacetrack"],
    on_crons=["17 4,12,20 * * *"],
    input_validator=FetchSpacetrackOrbitOptions,
)
class FetchSpacetrackOrbits:

    def __init__(
        self,
        username: str,
        password: str | SecretStr,
    ):
        self.username = username
        if hasattr(password, "get_secret_value"):
            self.password = password.get_secret_value()
        else:
            self.password = password

    @hatchet.step(
        # rate_limits=[RateLimit(key="spacetrack-tle-request", units=1)],
        retries=3,
        backoff_factor=4,
    )
    async def download_orbit_data(self, context: Context) -> DownloadStepOutput:
        """Download orbit data from spacetrack"""
        options = cast(FetchSpacetrackOrbitOptions, context.workflow_input())
        headers = {'user-agent': 'api.passpredict.com'}
        endpoint = f"/basicspacedata/query/class/gp/decay_date/null-val/epoch/>now-{options.epoch_days_since:f}/orderby/norad_cat_id/format/json"
        async with httpx.AsyncClient(
            base_url=options.base_url,
            headers=headers,
            follow_redirects=True,
            timeout=options.timeout,
        ) as client:
            # Login first to get authentication cookies
            credentials = {"identity": self.username, "password": self.password}
            try:
                login_response = await client.post(SPACETRACK_AUTH_ENDPOINT, data=credentials)
                context.log("Logged in to spacetrack")
                response = await client.get(endpoint)
            except httpx.RequestError as exc:
                context.log(
                    (
                        f"HTTP request error downloading orbits from spacetrack, "
                        f"URL: {exc.request.url}, {repr(exc)}"
                    )
                )
                raise
        queried_at = datetime.now(UTC)
        # Save response content to temporary file
        with tempfile.NamedTemporaryFile(
            prefix=context.workflow_run_id(),
            suffix=".gz",
            mode="wb",
            delete=False,
            delete_on_close=False,
        ) as f:
            with gzip.GzipFile(fileobj=f, mode="wb") as gz:
                gz.write(response.content)
                fname = f.name
        return DownloadStepOutput(
            request_url=str(response.request.url),
            status_code=response.status_code,
            fname=fname,
            queried_at=queried_at,
        )

    @hatchet.step(parents=["download_orbit_data"])
    def parse_and_insert_orbits_to_database(self, context: Context) -> NewOrbitOutput:
        download_output = context.step_output("download_orbit_data")
        if isinstance(download_output, dict):
            download_output = DownloadStepOutput.model_validate(download_output)
        with gzip.GzipFile(download_output.fname, mode="rb") as gz:
            spacetrack_data = json.load(gz)
        parsed_orbits_gen = (
            _spacetrack_data_to_orbit(data, downloaded_at=download_output.queried_at)
            for data in spacetrack_data
        )
        # batch orbit updates and insert synchronously
        new_orbits = []
        for orbits in batched(parsed_orbits_gen, config.orbit_insert_batch):
            orbit_data = [orbit.model_dump(mode="json") for orbit in orbits]
            insert_workflow = context.spawn_workflow(
                "InsertOrbitBatch",
                {"orbits": orbit_data},
            )
            result_data = insert_workflow.sync_result()["insert_orbits"]
            new_orbits.extend(NewOrbit.model_validate(data) for data in result_data["new_orbits"])
        return NewOrbitOutput(new_orbits=new_orbits)


def _spacetrack_data_to_orbit(
    data: SpacetrackJson,
    *,
    downloaded_at: datetime = None,
) -> Orbit:
    """ Parse JSON response from spacetrack and return Orbit model """
    try:
        tle = "\n".join((data["TLE_LINE1"], data["TLE_LINE2"]))
    except KeyError:
        tle = None
    sat_intl_designator = data.get("OBJECT_ID")
    if sat_intl_designator == "UNKNOWN":
        sat_intl_designator = None
    sat_name = data.get("OBJECT_NAME")
    if sat_name == "TBA - TO BE ASSIGNED":
        sat_name = None
    return Orbit(
        epoch=data["EPOCH"],
        inclination=data["INCLINATION"],
        eccentricity=data["ECCENTRICITY"],
        ra_of_asc_node=data["RA_OF_ASC_NODE"],
        arg_of_pericenter=data['ARG_OF_PERICENTER'],
        mean_anomaly=data["MEAN_ANOMALY"],
        bstar=data["BSTAR"],
        mean_motion=data["MEAN_MOTION"],
        mean_motion_dot=data["MEAN_MOTION_DOT"],
        mean_motion_ddot=data["MEAN_MOTION_DDOT"],
        rev_at_epoch=data["REV_AT_EPOCH"],
        originator=data["ORIGINATOR"],
        originator_created_at=data["CREATION_DATE"],
        downloaded_at=downloaded_at,
        perigee=data["PERIAPSIS"],
        apogee=data["APOAPSIS"],
        time_system=data["TIME_SYSTEM"],
        ref_frame=data["REF_FRAME"],
        mean_element_theory=data["MEAN_ELEMENT_THEORY"],
        ephemeris_type=data.get("EPHEMERIS_TYPE"),
        tle=tle,
        satellite=Satellite(
            norad_id=data["NORAD_CAT_ID"],
            intl_designator=sat_intl_designator,
            name=sat_name,
            launch_date=data["LAUNCH_DATE"],
        ),
    )
