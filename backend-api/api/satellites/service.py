from datetime import datetime, date, timedelta
from uuid import UUID
from typing import Protocol, Literal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, aliased
from sqlalchemy import select, func

from api import db
from api import domain


class SatelliteServiceError(Exception):
    ...


class SatelliteNotFound(SatelliteServiceError):

    def __init__(
        self,
        satellite_ids: list[int],
    ):
        self.satellite_ids = satellite_ids


class SatelliteOrbitNotFound(SatelliteServiceError):

    def __init__(
        self,
        satellite_ids: list[int],
    ):
        self.satellite_ids = satellite_ids


class SatelliteDimensionsType(Protocol):
    mass: float | None
    length: float | None
    diameter: float | None
    span: float | None


class SatelliteType(Protocol):
    id: int | None
    norad_id: int | None
    intl_designator: str | None
    name: str | None
    description: str | None
    tags: list[str]
    decay_date: date | None
    launch_date: date | None
    dimensions: SatelliteDimensionsType | None


class OrbitType(Protocol):
    id: UUID | None
    satellite_id: int
    epoch: datetime
    perigee: float | None
    apogee: float | None
    inclination: float | None
    tle: str | None
    created_at: datetime | None
    updated_at: datetime | None
    downloaded_at: datetime | None
    originator_created_at: datetime | None
    originator: str | None
    ref_frame: str | None
    time_system: str | None
    mean_element_theory: str | None
    mean_motion: float | None
    eccentricity: float
    ra_of_asc_node: float
    arg_of_pericenter: float
    mean_anomaly: float
    gm: float | None
    ephemeris_type: Literal[0, "SGP", "SGP4", "SDP4", "SGP8", "SDP8"] | None
    element_set_no: int | None
    rev_at_epoch: int | None
    bstar: float | None
    mean_motion_dot: float | None
    mean_motion_ddot: float | None
    satellite: SatelliteType | None


class SatelliteQueryParam(Protocol):
    norad_ids: list[int]
    intl_designators: list[str]
    page_size: int
    cursor: str
    q: str | None


async def insert_satellite(
    db_session: AsyncSession,
    satellite: SatelliteType,
) -> domain.Satellite:
    sat_model = _build_satellite_db_model(satellite)
    db_session.add(sat_model)
    await db_session.flush()
    await db_session.refresh(sat_model)
    return _build_satellite_domain_model(sat_model)


async def batch_insert_satellites(
    db_session: AsyncSession,
    satellites: list[SatelliteType],
) -> list[domain.Satellite]:
    sat_models = [
        _build_satellite_db_model(satellite)
        for satellite in satellites
    ]
    db_session.add(sat_models)
    await db_session.flush()
    await db_session.refresh(sat_models)
    satellites = [
        _build_satellite_domain_model(sat_model)
        for sat_model in sat_models
    ]
    return satellites

async def get_satellite_id_from_norad_id(
    db_session: AsyncSession,
    norad_id: int,
) -> int:
    stmt = select(db.Satellite.id).where(db.Satellite.norad_id == norad_id)
    satellite_id = await db_session.scalar(stmt)
    if satellite_id is None:
        raise SatelliteNotFound
    return satellite_id


async def get_satellite(
    db_session: AsyncSession,
    satellite_id: int,
    include_latest_orbit: bool = False,
) -> domain.Satellite:
    if include_latest_orbit:
        subq = (
            select(
                db.Orbit.id.label("orbit_id"),
                func.max(db.Orbit.epoch),
            )
            .where(db.Orbit.satellite_id == satellite_id)
            .group_by(db.Orbit.satellite_id)
            .subquery()
        )
        stmt = (select(db.Satellite, db.Orbit)
            .where(db.Satellite.id == satellite_id)
            .join(db.Orbit.id == subq.c.orbit_id)
        )
        sat_model, orbit_model = (await db_session.scalars(stmt)).first()
        if sat_model is None:
            raise SatelliteNotFound
        satellite = _build_satellite_domain_model(sat_model)
        orbit = _build_orbit_domain_model(orbit_model)
        satellite.orbits = [orbit]
    else:
        sat_model = await db_session.get(db.Satellite, satellite_id)
        if sat_model is None:
            raise SatelliteNotFound
        satellite = _build_satellite_domain_model(sat_model)
    return satellite


async def query_satellites(
    db_session: AsyncSession,
    satellite_ids: list[int] | None = None,
    norad_ids: list[int] | None = None,
    intl_designators: list[str] | None = None,
    page_size: int | None = None,
    cursor: str | None = None,
    q: str | None = None,
) -> list[domain.Satellite]:
    if satellite_ids:
        stmt = (select(db.Satellite)
            .where(db.Satellite.id.in_(norad_ids))
        )
    elif norad_ids:
        # Only use norad_ids for query
        stmt = (select(db.Satellite)
            .where(db.Satellite.norad_id.in_(norad_ids))
        )
    else:
        stmt = select()


async def query_latest_satellite_orbit(
    db_session: AsyncSession,
    norad_ids: list[int],
    originators: list[str] | None = None,
) -> list[domain.Satellite]:
    """Query latest orbits for satellites and embed satellite details"""
    orbit_a = aliased(db.Orbit)
    stmt = (
        select(
            orbit_a.id.label("orbit_id"),
            func.max(orbit_a.epoch),
        )
        .group_by(orbit_a.satellite_id)
        .join(orbit_a.satellite)
        .where(db.Satellite.norad_id.in_(norad_ids))
    )
    if originators:
        stmt = stmt.where(orbit_a.originator.in_(originators))
    subq = stmt.subquery()
    stmt = (
        select(db.Orbit)
        .join(subq, db.Orbit.id == subq.c.orbit_id)
        .options(selectinload(db.Orbit.satellite))
    )
    results = await db_session.scalars(stmt)
    # Remap database orbit models to satellite domain objects
    satellites = [
        _build_satellite_domain_model(orbit.satellite, [orbit])
        for orbit in results
    ]
    # Raise error if satellites or orbits are missing
    # # Confirm we get all satellites back
    # norad_ids_found = set(sat.norad_id for sat in satellites)
    # norad_ids_missing = params.norad_ids - norad_ids_found
    # if norad_ids_missing:
    #     raise HTTPException(status_code=404, detail=f"Norad IDs {norad_ids_missing} not found")
    # # Confirm that all satellites have at least one orbit in time range
    # for satellite in satellites:
    #     if not satellite.orbits:
    #         raise HTTPException(status_code=404, detail=f"No orbits found for satellite {satellite.name}, Norad ID {satellite.norad_id} in time range")


    return satellites





async def query_satellite_orbit_time_range(
    db_session: AsyncSession,
    satellite_ids: list[int],
    start: datetime,
    end: datetime,
    originators: list[str] | None = None,
) -> list[domain.Satellite]:
    """Query satellites and embed orbits with epochs within time range"""
    satellite_stmt = select(db.Satellite).where(db.Satellite.id.in_(satellite_ids))
    orbit_stmt = select(db.Orbit).where(db.Orbit.satellite_id.in_(satellite_ids))

    if originators:
        orbit_stmt = orbit_stmt.where(db.Orbit.originator.in_(originators))
    orbit_stmt = (orbit_stmt
        .where(db.Orbit.epoch >= start - timedelta(days=3))
        .where(db.Orbit.epoch <= end)
        .order_by(db.Orbit.epoch.desc())
    )
    res = await db_session.scalars(satellite_stmt)
    satellite_models = res.all()
    res = await db_session.scalars(orbit_stmt)
    orbits = res.all()
    satellite_map = {
        satellite_model.id: _build_satellite_domain_model(satellite_model)
        for satellite_model in sorted(satellite_models, key=lambda x: x.id)
    }
    for orbit in orbits:
        satellite_map[orbit.satellite_id].orbits.append(orbit)
    requested_satellite_ids = set(satellite_ids)
    found_satellite_ids = set(satellite_map.keys())
    if missing_satellite_ids := (requested_satellite_ids - found_satellite_ids):
        raise SatelliteNotFound(satellite_ids=list(missing_satellite_ids))
    for satellite_id, satellite_orbits in satellite_map.items():
        if not satellite_orbits:
            raise SatelliteOrbitNotFound(satellite_id=[satellite_id])
    return list(satellite_map.values())


def _build_satellite_db_model(satellite: SatelliteType) -> db.Satellite:
    sat_db_model = db.Satellite(
        id=satellite.norad_id,
        cospar_id=satellite.intl_designator,
        name=satellite.name,
        description=satellite.description,
        decayed_date=satellite.decay_date,
        launch_date=satellite.launch_date,
    )
    return sat_db_model


def _build_satellite_domain_model(
    sat_model: db.Satellite,
    orbit_models: list[db.Orbit] = [],
) -> domain.Satellite:
    orbits = [
        _build_orbit_domain_model(orbit_model)
        for orbit_model in orbit_models
    ]
    satellite = domain.Satellite(
        id=sat_model.id,
        norad_id=sat_model.norad_id,
        intl_designator=sat_model.intl_designator,
        name=sat_model.name,
        description=sat_model.description,
        tags=[],   # TODO: Add Satellite model tags
        decay_date=sat_model.decay_date,
        launch_date=sat_model.launch_date,
        dimensions=domain.SatelliteDimensions(
            mass=sat_model.mass,
            length=sat_model.length,
            diameter=sat_model.diameter,
            span=sat_model.span,
        ),
        orbits=orbits,
    )
    return satellite


def _build_orbit_domain_model(orbit_model: db.Orbit, satellite_model: db.Satellite = None) -> domain.Orbit:
    satellite = _build_satellite_domain_model(satellite_model) if satellite_model else None
    orbit = domain.Orbit(
        id=orbit_model.id,
        epoch=orbit_model.epoch,
        satellite_id=orbit_model.satellite_id,
        originator=orbit_model.originator,
        originator_created_at=orbit_model.originator_created_at,
        downloaded_at=orbit_model.downloaded_at,
        ref_frame=orbit_model.ref_frame,
        time_system=orbit_model.time_system,
        mean_element_theory=orbit_model.mean_element_theory,
        eccentricity=orbit_model.eccentricity,
        ra_of_asc_node=orbit_model.ra_of_asc_node,
        arg_of_pericenter=orbit_model.arg_of_pericenter,
        mean_anomaly=orbit_model.mean_anomaly,
        ephemeris_type=orbit_model.ephemeris_type,
        element_set_no=orbit_model.element_set_no,
        rev_at_epoch=orbit_model.rev_at_epoch,
        bstar=orbit_model.bstar,
        mean_motion=orbit_model.mean_motion,
        mean_motion_dot=orbit_model.mean_motion_dot,
        mean_motion_ddot=orbit_model.mean_motion_ddot,
        perigee=orbit_model.perigee,
        apogee=orbit_model.apogee,
        inclination=orbit_model.inclination,
        tle=orbit_model.tle,
        satellite=satellite,
    )
    return orbit
