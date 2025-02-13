from datetime import datetime, date
from uuid import UUID
from typing import Protocol, Literal, Any
from collections.abc import Iterator
from dataclasses import asdict

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, AsyncConnection
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy import (
    Connection,
    cte,
)

from api import db
from .domain import Satellite, SatelliteDimensions, Orbit


class SatelliteServiceError(Exception):
    ...


class SatelliteNotFound(SatelliteServiceError):
    ...


class SatelliteOrbitNotFound(SatelliteServiceError):
    ...


class SatelliteDimensionsProtocol(Protocol):
    mass: float | None
    length: float | None
    diameter: float | None
    span: float | None


class SatelliteProtocol(Protocol):
    norad_id: int
    intl_designator: str
    name: str
    description: str | None
    tags: list[str]
    decayed_date: date | None
    launch_date: date | None
    dimensions: SatelliteDimensionsProtocol | None


class OrbitProtocol(Protocol):
    id: UUID | None
    norad_id: int
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


class SatelliteQueryParamProtocol(Protocol):
    norad_ids: list[int]
    intl_designators: list[str]
    page_size: int
    cursor: str
    q: str | None


class SatelliteService:

    def __init__(
        self,
        Session: async_sessionmaker,
    ):
        self.Session = Session

    async def insert_satellite(
        self,
        satellite: SatelliteProtocol,
    ) -> Satellite:
        sat_model = self._build_satellite_db_model(satellite)
        async with self.Session.begin() as session:
            session.add(sat_model)
            await session.flush()
            await session.refresh(sat_model)
        return self._build_satellite_domain_model(sat_model)

    async def batch_insert_satellites(
        self,
        satellites: list[SatelliteProtocol],
    ) -> list[Satellite]:
        sat_models = [
            self._build_satellite_db_model(satellite)
            for satellite in satellites
        ]
        async with self.Session.begin() as session:
            session.add(sat_models)
            await session.flush()
            await session.refresh(sat_models)
        satellites = [
            self._build_satellite_domain_model(sat_model)
            for sat_model in sat_models
        ]
        return satellites

    async def get_satellite(
        self,
        norad_id: int,
    ) -> Satellite:
        ...

    async def query_satellites(
        self,
        params: SatelliteQueryParamProtocol,
    ) -> list[Satellite]:
        ...

    async def update_satellite(
        self,
        satellite: SatelliteProtocol,
    ) -> Satellite:
        ...

    async def delete_satellite(
        self,
        norad_id: int,
    ) -> None:
        ...

    async def insert_orbit(
        self,
        orbit: OrbitProtocol,
    ) -> Orbit:
        ...

    # async def batch_insert_orbits(
    #     self,
    #     orbits: list[OrbitProtocol],
    # ) -> list[Orbit]:


    async def batch_insert_orbits(
        self,
        orbits: list[OrbitProtocol],
    ) -> list[Orbit]:
        """
        Use two statements:
            1. Create satellite records which don't exist yet for the orbits
            2. Upsert orbit rows from values
        """
        norad_ids = {
            orbit.norad_id
            for orbit in orbits
        }

        orbit_value_gen = (
            self._build_orbit_db_model_data(orbit)
            for orbit in orbits
        )

        async with self.Session.begin() as session:
            create_sats_stmt = (insert(db.Satellite)
                .values({"id": norad_id for norad_id in norad_ids})
                .on_conflict_do_nothing(index_elements=["id"])
            )
            insert_orbits_stmt = (insert(db.Orbit)
                .values(list(orbit_value_gen))
                .on_conflict_do_nothing(index_elements=["id", "epoch", "originator"])
            )
            await session.execute(create_sats_stmt)
            await session.execute(insert_orbits_stmt)
            await session.commit()

    async def update_orbit(
        self,
        orbit: OrbitProtocol,
    ) -> Orbit:
        ...

    async def delete_orbit(
        self,
        orbit_id: UUID,
    ) -> None:
        ...

    async def query_orbits(
        self,
        params,
    ) -> list[Orbit]:
        ...

    async def get_orbit(
        self,
        orbit_id: UUID,
    ) -> Orbit:
        ...



    @staticmethod
    def _build_satellite_db_model(satellite: SatelliteProtocol) -> db.Satellite:
        sat_db_model = db.Satellite(
            id=satellite.norad_id,
            cospar_id=satellite.intl_designator,
            name=satellite.name,
            description=satellite.description,
            decayed_date=satellite.decayed_date,
            launch_date=satellite.launch_date,
        )
        return sat_db_model

    @staticmethod
    def _build_satellite_domain_model(sat_model: db.Satellite) -> Satellite:
        satellite = Satellite(
            norad_id=sat_model.id,
            intl_designator=sat_model.cospar_id,
            name=sat_model.name,
            description=sat_model.description,
            tags=[],   # TODO: Add Satellite model tags
            decayed_date=sat_model.decayed_date,
            launch_date=sat_model.launch_date,
            dimensions=SatelliteDimensions(
                mass=sat_model.mass,
                length=sat_model.length,
                diameter=sat_model.diameter,
                span=sat_model.span,
            )
        )
        return satellite

    @staticmethod
    def _build_orbit_db_model_data(orbit: OrbitProtocol) -> dict[str, Any]:
        orbit_id = orbit.id if orbit.id else Orbit.new_id()
        orbit_obj = Orbit(
            id=orbit_id,
            epoch=orbit.epoch,
            satellite_id=orbit.norad_id,
            originator=orbit.originator,
            originator_created_at=orbit.originator_created_at,
            downloaded_at=orbit.downloaded_at,
            ref_frame=orbit.ref_frame,
            time_system=orbit.time_system,
            mean_element_theory=orbit.mean_element_theory,
            eccentricity=orbit.eccentricity,
            ra_of_asc_node=orbit.ra_of_asc_node,
            arg_of_pericenter=orbit.arg_of_pericenter,
            mean_anomaly=orbit.mean_anomaly,
            gm=orbit.gm,
            ephemeris_type=orbit.ephemeris_type,
            element_set_no=orbit.element_set_no,
            rev_at_epoch=orbit.rev_at_epoch,
            bstar=orbit.bstar,
            mean_motion=orbit.mean_motion,
            mean_motion_dot=orbit.mean_motion_dot,
            mean_motion_ddot=orbit.mean_motion_ddot,
            perigee=orbit.perigee,
            apogee=orbit.apogee,
            inclination=orbit.inclination,
            tle=orbit.tle,
        )
        return asdict(orbit_obj)

    @staticmethod
    def _build_orbit_domain_model(orbit_model: db.Orbit) -> Orbit:
        orbit = Orbit(
            id=orbit_model.id,
            epoch=orbit_model.epoch,
            norad_id=orbit_model.satellite_id,
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
            gm=orbit_model.gm,
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
        )
        return orbit
