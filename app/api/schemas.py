import datetime as dt
from enum import Enum
from math import floor
from typing import List, Sequence, Tuple, Optional

from pydantic import BaseModel, Field


COORDINATES = ['N','NNE','NE','ENE','E','ESE','SE','SSE','S','SSW','SW','WSW','W','WNW','NW','NNW','N']


class Satellite(BaseModel):
    id: int   # NORAD ID
    cospar_id: str = None
    name: str = None
    description: str = None
    decayed: bool = None
    launch_date: dt.date = None
    launch_year: int = None
    # orbit_type: int = None
    # constellation: int = None
    mass: float = None
    length: float = None
    diameter: float = None
    span: float = None
    #shape: int = None
    perigee: float = None
    apogee: float = None
    inclination: float = None


class Point(BaseModel):
    # __slots__ = ['datetime', 'azimuth', 'elevation', 'range', 'declination', 'right_ascension']
    datetime: dt.datetime
    timestamp: float = Field(..., title='Unix timestamp in seconds since Jan 1 1970')
    azimuth: float
    elevation: float
    range: float
    declination: float = None
    right_ascension: float = None

    def direction_from_azimuth(self):
        ''' Return direction from azimuth degree '''
        azm = self.azimuth % 360
        mod = 360/16. # number of degrees per coordinate heading
        start = 0 - mod/2
        n = floor((azm-start)/mod)
        direction = COORDINATES[n]
        return direction

    def __repr__(self):
        dtstr = self.datetime.strftime("%b %d %Y, %H:%M:%S")
        s = "{}UTC el={:.1f}d, az={:.1f}d, rng={:.1f}km".format(
            dtstr, self.elevation, self.azimuth, self.range)
        return s


# class SatelliteDetails(BaseModel):
#     id = int   # NORAD ID
#     name: str = None
#     cospar_id: str = None
#     radio_downlink: float = None  # MHz
#     intrinsic_brightness: float = None  # magnitude
#     maximum_brightness: float = None    # magnitude
#     category: str = None
#     description: str = None
#     country: str = None
#     launch_date: datetime.date = None
#     launch_site: str = None
#     mass: float = None   # kg


class PassType(str, Enum):
    daylight = 'daylight'
    unlit = 'unlit'
    visible = 'visible'


# class Overpass(BaseModel):
#     start_pt: Point
#     max_pt: Point
#     end_pt: Point
#     satellite_id: int = None
#     type: PassType = None
#     vis_start_pt: Point = None
#     vis_end_pt: Point = None
#     brightness: float = None


class Overpass(BaseModel):
    aos_dt: dt.datetime
    max_dt: dt.datetime
    los_dt: dt.datetime
    duration: float
    max_elevation: float
    satellite_id: int = None
    type: PassType = None
    brightness: float = None


class Location(BaseModel):
    lat: float = Field(..., title='latitude, \u0b00N')
    lon: float = Field(..., title='longitude, \u0b00E')
    h: float = Field(0.0, title='height, [m] above WGS84 ellipsoid')
    name: str = None


class OverpassResultBase(BaseModel):
    location: Location


class SingleSatOverpassResult(OverpassResultBase):
    satellite: Satellite
    overpasses: List[Overpass]


class MultiSatOverpassResult(OverpassResultBase):
    overpasses: List[Overpass]