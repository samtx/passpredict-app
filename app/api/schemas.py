import datetime as dt
from enum import Enum
from math import floor
from typing import List, Sequence, Tuple, Optional

from pydantic import BaseModel, Field, validator


class OrdinalDirection(int, Enum):
    N = 0
    NNE = 1
    NE = 2
    ENE = 3
    E = 4
    ESE = 5
    SE = 6
    SSE = 7
    S = 8
    SSW = 9
    SW = 10
    WSW = 11
    W = 12
    WNW = 13
    NW = 14
    NNW = 15

    @classmethod
    def from_az(cls, az_deg: float):
        ''' Return direction from azimuth degree '''
        azm = az_deg % 360
        mod = 360/16. # number of degrees per coordinate heading
        start = 0 - mod/2
        n = floor((azm-start)/mod)
        return cls(n)


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
    timestamp: float = Field(..., description='Unix timestamp in seconds since Jan 1 1970 UTC')
    az: float = Field(..., title='Azimuth', description='azimuth [deg]')
    az_ord: str = Field(..., description='Ordinal direction, eg. NE, NNW, WSW')
    el: float = Field(..., description='elevation [deg]')
    range: float = Field(..., description='range [km]')
    dec: float = Field(None, description='declination [deg]')
    ra: float = Field(None, description='right ascension [deg]')

    def __repr__(self):
        dtstr = self.datetime.strftime("%b %d %Y, %H:%M:%S")
        s = "{}UTC el={:.1f}d, az={:.1f}d, rng={:.1f}km".format(
            dtstr, self.el, self.az, self.range)
        return s

    @validator('az_ord')
    def validate_ordinal_direction_string(cls, v):
        """ Try and select OrdinalDirection by name """
        if isinstance(v, str):
            assert OrdinalDirection[v.upper()]
        return v


    # class Config:
    #     use_enum_values = True


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
    aos: Point = Field(..., description='Acquisition of signal')
    tca: Point = Field(..., description='Time of closest approach')
    los: Point = Field(..., description='Loss of signal')
    duration: float = Field(..., description='Duration of pass [sec]')
    max_elevation: float = Field(..., description='Maximum elevation [deg]')
    satid: int = Field(None, description='Satellite NORAD ID')
    type: PassType = None
    brightness: float = None


class Location(BaseModel):
    lat: float = Field(..., description='latitude, \u0b00N')
    lon: float = Field(..., description='longitude, \u0b00E')
    h: float = Field(0.0, description='height, [m] above WGS84 ellipsoid')
    name: str = None


class OverpassResultBase(BaseModel):
    location: Location


class SingleSatOverpassResult(OverpassResultBase):
    satellite: Satellite
    overpasses: List[Overpass]


class PassDetailResult(OverpassResultBase):
    satellite: Satellite
    overpass: Overpass


class MultiSatOverpassResult(OverpassResultBase):
    overpasses: List[Overpass]