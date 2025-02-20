from datetime import datetime
from dataclasses import dataclass
from enum import Enum


class PassType(str, Enum):
    daylight = 'daylight'
    unlit = 'unlit'
    visible = 'visible'


@dataclass(frozen=True)
class Location:
    latitude: float
    longitude: float
    height: float = 0
    name: str | None = None


@dataclass
class Point(frozen=True):
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

@dataclass
class Overpass:
    aos: Point
    tca: Point
    los: Point
    duration: float
    max_elevation: float
    norad_id: int
    type: PassType | None = None
    brightness: float | None = None
    vis_begin: Point | None = None
    vis_end: Point | None = None