import asyncio
from datetime import datetime, UTC, date
import logging
from itertools import chain, batched
from typing import cast, Awaitable, Any, TypedDict
from json import JSONDecodeError

import httpx
from hatchet_sdk import Context, RateLimitDuration
from hatchet_sdk.rate_limit import RateLimit
from sqlalchemy.ext.asyncio import async_sessionmaker

from api.settings import config
from api.satellites.domain import Orbit, Satellite
from ..client import hatchet


__all__ = [
    "FetchSpacetrackOrbits",
    "SpaceTrackTLERequest",
]


logger = logging.getLogger(__name__)

SPACETRACK_BASE_URL = "https://www.space-track.org"
SPACETRACK_AUTH_ENDPOINT = "/ajaxauth/login"
SPACETRACK_TIMEOUT = 30
SPACETRACK_EPOCH_DAYS_SINCE = 3



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


def parse_datetime(s: str) -> datetime:
    """Parse datetime string and make tz-aware"""
    d = datetime.fromisoformat(s)
    if not d.tzinfo:
        d = d.replace(tzinfo=UTC)
    return d


@hatchet.workflow(
    on_events=["fetch-orbits:spacetrack"],
    on_crons=["17 4,12,20 * * *"],
)
class FetchSpacetrackOrbits:

    @hatchet.step()
    async def download_orbit_data(self, context: Context):
        """Download orbit data from spacetrack"""
        input_ = context.workflow_input()
        base_url = input_.get("base_url", SPACETRACK_BASE_URL)
        timeout = input_.get("timeout", SPACETRACK_TIMEOUT)
        epoch_days_since= input_.get("epoch_days_since", SPACETRACK_EPOCH_DAYS_SINCE)
        request_workflow = await context.aio.spawn_workflow(
            "CelestrakOrbitRequest",
            {
                "base_url": base_url,
                "endpoint": f"/basicspacedata/query/class/gp/decay_date/null-val/epoch/>now-{epoch_days_since:f}/orderby/norad_cat_id/format/json",
                "timeout": timeout,
            },
        )
        workflow_result = await request_workflow.result()
        orbit_data = workflow_result["orbit_data"]
        queried_at = datetime.now(UTC)
        return {
            "orbit_data": orbit_data,
            "queried_at": queried_at.isoformat(),
        }

    @hatchet.step(parents=["download_orbit_data"])
    def parse_orbit_data(self, context: Context):
        prev_output = context.step_output("download_orbit_data")
        orbit_data = cast(list[SpacetrackJson], prev_output["orbit_data"])
        queried_at = parse_datetime(prev_output["queried_at"])
        parsed_orbits = [
            self._spacetrack_json_to_orbit(data, downloaded_at=queried_at)
            for data in orbit_data
        ]
        return {"parsed_orbits": parsed_orbits}

    @staticmethod
    def _spacetrack_json_to_orbit(
        data: SpacetrackJson,
        *,
        downloaded_at: datetime = None,
    ) -> Orbit:
        """ Parse JSON response from spacetrack and return Orbit model """
        norad_id = int(data["NORAD_CAT_ID"])
        try:
            tle = "\n".join((data["TLE_LINE1"], data["TLE_LINE2"]))
        except KeyError:
            tle = None
        satellite = Satellite(
            norad_id=norad_id,
            intl_designator=data.get("OBJECT_ID"),
            name=data["OBJECT_NAME"],
            launch_date=date.fromisoformat(data["LAUNCH_DATE"]),
        )
        return Orbit(
            norad_id=norad_id,
            epoch=parse_datetime(data["EPOCH"]),
            inclination=float(data["INCLINATION"]),
            eccentricity=float(data["ECCENTRICITY"]),
            ra_of_asc_node=float(data["RA_OF_ASC_NODE"]),
            arg_of_pericenter=float(data['ARG_OF_PERICENTER']),
            mean_anomaly=float(data["MEAN_ANOMALY"]),
            bstar=float(data["BSTAR"]),
            mean_motion=float(data["MEAN_MOTION"]),
            mean_motion_dot=float(data["MEAN_MOTION_DOT"]),
            mean_motion_ddot=float(data["MEAN_MOTION_DDOT"]),
            rev_at_epoch=int(data["REV_AT_EPOCH"]),
            originator=data["ORIGINATOR"],
            originator_created_at=parse_datetime(data["CREATION_DATE"]),
            downloaded_at=downloaded_at,
            perigee=float(data["PERIAPSIS"]),
            apogee=float(data["APOAPSIS"]),
            time_system=data["TIME_SYSTEM"],
            ref_frame=data["REF_FRAME"],
            mean_element_theory=data["MEAN_ELEMENT_THEORY"],
            ephemeris_type=data.get("EPHEMERIS_TYPE"),
            tle=tle,
            satellite=satellite,
        )

    @hatchet.step(parents=["download_orbit_data", "parse_orbit_data"])
    async def insert_orbits_to_database(self, context: Context):
        unique_orbit_data = context.step_output("parse_orbit_data")["unique_orbit_data"]
        queried_at = context.step_output("download_orbit_data")["queried_at"]
        # batch orbit updates and insert synchronously
        results = {"new_orbits": []}
        for orbits in batched(unique_orbit_data, config.orbit_insert_batch):
            insert_workflow = await context.aio.spawn_workflow(
                "InsertOrbitBatch",
                {
                    "orbits": orbits,
                    "queried_at": queried_at,
                },
            )
            workflow_result = await insert_workflow.result()
            results["new_orbits"].extend(workflow_result["new_orbits"])
        return results


@hatchet.workflow()
class SpaceTrackTLERequest:

    def __init__(
        self,
        username: str,
        password: str,
    ):
        self.username = username
        self.password = password

    @hatchet.step(
        rate_limits=[RateLimit(key="spacetrack-tle-request", units=1)],
        retries=3,
        backoff_factor=4,
    )
    async def request(self, context: Context) -> dict[str, Any]:
        input_ = context.workflow_input()
        base_url = input_["base_url"]
        params = input_["params"]
        endpoint = input_["endpoint"]
        timeout = input_["timeout"]
        headers = {'user-agent': 'api.passpredict.com'}
        output = {"orbit_data": []}
        async with httpx.AsyncClient(
            base_url=base_url,
            headers=headers,
            follow_redirects=True,
            timeout=timeout,
        ) as client:
            # Login first to get authentication cookies
            credentials = {"username": self.username, "password": self.password}
            try:
                response = await client.post(SPACETRACK_AUTH_ENDPOINT, data=credentials)
            except httpx.RequestError as exc:
                context.log(
                    f"HTTP request error logging in to spacetrack, {repr(exc)}"
                )
                raise
            if response.status_code >= 400:
                context.log(
                    f"Bad login response from spacetrack, {response.text}"
                )
                return output
            context.log("Logged in to spacetrack")

            try:
                response = await client.get(endpoint, params=params)
            except httpx.RequestError as exc:
                context.log(
                    f"HTTP request error downloading orbits from spacetrack, {repr(exc)}"
                )
                raise
        if response.status_code >= 400:
            context.log(
                f"Bad HTTP response downloading orbits from spacetrack, {response.text}"
            )
            return output
        try:
            data = response.json()
        except JSONDecodeError as exc:
            # Log exception and continue
            context.log(
                f"Error parsing orbit response from spacetrack, {str(exc)}, text: {response.text}"
            )
            return output
        output["orbit_data"] = data
        return output


