from collections.abc import Sequence
from datetime import date, datetime
from typing import Literal
from uuid import UUID
from dataclasses import dataclass, field
from enum import Enum


@dataclass(frozen=True)
class SatelliteDimensions:
    mass: float | None = None
    length: float | None = None
    diameter: float | None = None
    span: float | None = None


@dataclass(frozen=True)
class Orbit:
    satellite_id: int
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
    id: UUID | None = None
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
    satellite: 'Satellite | None' = None


@dataclass
class Satellite:
    norad_id: int
    intl_designator: str
    name: str
    id: int | None = None
    description: str | None = None
    tags: list[str] = field(default_factory=list)
    decay_date: date | None = None
    launch_date: date | None = None
    dimensions: SatelliteDimensions | None = None
    orbits: list[Orbit] = field(default_factory=list)


class PassType(str, Enum):
    daylight = 'daylight'
    unlit = 'unlit'
    visible = 'visible'


# class Coordinate(NamedTuple):
#     = namedtuple('Coordinate', 'lat lon h', defaults=(0.0,))


@dataclass(frozen=True)
class Location:
    latitude: float
    longitude: float
    height: float = 0
    name: str | None = None


@dataclass(frozen=True)
class Point:
    datetime: datetime
    azimuth: float
    elevation: float
    range: float
    brightness: float | None = None

    def __repr__(self):
        dtstr = self.datetime.strftime("%b %d %Y, %H:%M:%S")
        s = "{}UTC el={:.1f}d, az={:.1f}d, rng={:.1f}km".format(
            dtstr, self.elevation, self.azimuth, self.range)
        return s


@dataclass(frozen=True)
class Overpass:
    aos: Point
    tca: Point
    los: Point
    norad_id: int
    dt_razel: list[Sequence[datetime, float, float, float]] = field(default_factory=list)
    type: PassType | None = None
    brightness: float | None = None
    vis_begin: Point | None = None
    vis_end: Point | None = None
    vis_tca: Point | None = None

    @property
    def duration(self) -> float:
        return (self.los.datetime - self.aos.datetime).total_seconds()

    @property
    def max_elevation(self) -> float:
        return self.tca.elevation

