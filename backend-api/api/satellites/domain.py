from datetime import date, datetime
from typing import Literal
from uuid import UUID, uuid4
from dataclasses import dataclass, field


@dataclass(frozen=True)
class SatelliteDimensions:
    mass: float | None = None
    length: float | None = None
    diameter: float | None = None
    span: float | None = None


@dataclass(frozen=True)
class Orbit:
    norad_id: int
    epoch: datetime
    inclination: float
    eccentricity: float
    ra_of_asc_node: float
    arg_of_pericenter: float
    mean_anomaly: float
    bstar: float
    mean_motion: float
    mean_motion_dot: float
    mean_motion_ddot: float
    id: UUID = field(default_factory=uuid4)
    gm: float | None =  None
    rev_at_epoch: int | None = None
    originator: str | None = None
    originator_created_at: datetime | None = None
    downloaded_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    perigee: float | None = None
    apogee: float | None = None
    time_system: str | None = None
    ref_frame: str | None = None
    mean_element_theory: str | None = None
    element_set_no: int | None = None
    ephemeris_type: Literal[0, "SGP", "SGP4", "SDP4", "SGP8", "SDP8"] | None = None
    tle: str | None = None
    satellite: "Satellite" | None = None

    @staticmethod
    def new_id() -> UUID:
        return uuid4()


@dataclass
class Satellite:
    norad_id: int
    intl_designator: str
    name: str
    description: str | None = None
    tags: list[str] = field(default_factory=list)
    decay_date: date | None = None
    launch_date: date | None = None
    dimensions: SatelliteDimensions | None = None
    orbits: list[Orbit] = field(default_factory=list)