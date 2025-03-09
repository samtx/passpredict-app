from collections.abc import Iterator
from datetime import datetime, date, UTC
from uuid import UUID
import logging
from typing import Literal, cast, Any, Annotated

from hatchet_sdk import Context
from sqlalchemy import create_engine
from sqlalchemy.orm import selectinload, Session
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy import select, UniqueConstraint
from pydantic import BaseModel, ConfigDict, AfterValidator, BeforeValidator

from api import db
from ..client import hatchet


__all__ = [
    "InsertOrbitBatch",
]


logger = logging.getLogger(__name__)


def spacetrack_unknown_tba_is_null(value: Any) -> Any:
    if isinstance(value, str) and value in ("UNKNOWN", "TBA - TO BE ASSIGNED"):
        return None
    return value


class Satellite(BaseModel):
    norad_id: int
    intl_designator: Annotated[str | None, BeforeValidator(spacetrack_unknown_tba_is_null)] = None
    name: Annotated[str | None, BeforeValidator(spacetrack_unknown_tba_is_null)] = None
    launch_date: date | None = None

    model_config = ConfigDict(extra="ignore")


def ensure_tz_aware(value: datetime | None) -> datetime | None:
    """Ref: https://docs.python.org/3/library/datetime.html#determining-if-an-object-is-aware-or-naive"""
    if value is None:
        return value
    if (value.tzinfo is None) or (value.tzinfo.utcoffset(value) == None):
        value = value.replace(tzinfo=UTC)
    return value


class Orbit(BaseModel):
    epoch: Annotated[datetime, AfterValidator(ensure_tz_aware)]
    inclination: float
    eccentricity: float
    ra_of_asc_node: float
    arg_of_pericenter: float
    mean_anomaly: float
    bstar: float
    mean_motion: float
    mean_motion_dot: float
    mean_motion_ddot: float
    rev_at_epoch: int | None = None
    originator: str | None = None
    originator_created_at: Annotated[datetime | None, AfterValidator(ensure_tz_aware)] = None
    downloaded_at: Annotated[datetime | None, AfterValidator(ensure_tz_aware)] = None
    created_at: Annotated[datetime | None, AfterValidator(ensure_tz_aware)] = None
    updated_at: Annotated[datetime | None, AfterValidator(ensure_tz_aware)] = None
    perigee: float | None = None
    apogee: float | None = None
    time_system: str | None = None
    ref_frame: str | None = None
    mean_element_theory: str | None = None
    element_set_no: int | None = None
    ephemeris_type: Literal["0", "SGP", "SGP4", "SDP4", "SGP8", "SDP8"] | None = None
    tle: str | None = None
    satellite: Satellite = None

    model_config = ConfigDict(extra="ignore")


class InsertOrbitBatchInput(BaseModel):
    orbits: list[Orbit]


class NewOrbit(BaseModel):
    orbit_id: UUID
    satellite_id: int
    norad_id: int
    epoch: datetime
    originator: str
    name: str | None = None


class InsertOrbitBatchOutput(BaseModel):
    new_orbits: list[NewOrbit]


@hatchet.workflow(
    input_validator=InsertOrbitBatchInput,
)
class InsertOrbitBatch:

    def __init__(
        self,
        db_url: str,
    ):
        self.db_url = db_url

    @hatchet.step()
    def insert_orbits(self, context: Context) -> InsertOrbitBatchOutput:
        input_ = cast(InsertOrbitBatchInput, context.workflow_input())
        sync_url = self.db_url.replace("+aiosqlite", "")
        engine = create_engine(sync_url)
        with Session(bind=engine, expire_on_commit=False) as db_session:
            with db_session.begin():
                new_orbits = batch_insert_orbits(db_session, input_.orbits)

        return InsertOrbitBatchOutput(new_orbits=new_orbits)


def batch_insert_orbits(
    db_session: Session,
    orbits: list[Orbit],
) -> list[NewOrbit]:
    """
    Use two statements:
        1. Create satellite records which don't exist yet for the orbits
        2. Insert orbit rows from values if they don't exist

    TODO: Rewrite this SQL query to do the inserts at the same time
    """
    def gen_satellite_data(orbits: list[Orbit]) -> Iterator[tuple[dict[str, Any], int]]:
        updated_at = datetime.now(UTC)
        for orbit in orbits:
            data = {
                "norad_id": orbit.satellite.norad_id,
                "intl_designator": orbit.satellite.intl_designator,
                "name": orbit.satellite.name,
                "updated_at": updated_at,
            }
            if launch_date := orbit.satellite.launch_date:
                data["launch_date"] = launch_date
            yield data, int(orbit.satellite.norad_id)

    orbit_satellite_data, orbit_norad_ids = zip(*gen_satellite_data(orbits))

    stmt = insert(db.Satellite).on_conflict_do_nothing(index_elements=["norad_id"])
    db_session.execute(stmt, orbit_satellite_data)

    stmt = (
        select(
            db.Satellite.norad_id,
            db.Satellite.id.label("satellite_id"),
        )
        .where(db.Satellite.norad_id.in_(orbit_norad_ids))
    )
    res = db_session.execute(stmt)
    rows = res.all()
    norad_id_to_satellite_id = {r[0]: r[1] for r in rows}
    # Update orbit records with corresponding satellite_id
    def gen_orbit_data(orbits: list[Orbit]) -> Iterator[dict[str, Any]]:
        for orbit in orbits:
            data = orbit.model_dump()
            data["satellite_id"] = norad_id_to_satellite_id[orbit.satellite.norad_id]
            yield data

    orbit_data = list(gen_orbit_data(orbits))
    insert_orbits_stmt = (insert(db.Orbit)
        .on_conflict_do_nothing(index_elements=["satellite_id", "epoch", "originator"])
        .returning(db.Orbit)
        .options(selectinload(db.Orbit.satellite))
    )
    res = db_session.scalars(insert_orbits_stmt, orbit_data)
    inserted_orbits = cast(list[db.Orbit], res.all())
    db_session.flush()
    new_orbits = [
        NewOrbit(
            orbit_id=orbit.id,
            satellite_id=orbit.satellite_id,
            norad_id=orbit.satellite.norad_id,
            name=orbit.satellite.name,
            epoch=orbit.epoch,
            originator=orbit.originator,
        )
        for orbit in inserted_orbits
    ]
    return new_orbits
