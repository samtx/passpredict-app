import datetime
from enum import Enum
from math import floor
from typing import List

from pydantic import BaseModel, Field, validator, conlist


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
        if n == 16:
            n = 0
        return cls(n)


class Satellite(BaseModel):
    id: int   # NORAD ID
    cospar_id: str = None
    name: str = None
    description: str = None
    decayed: bool = None
    launch_date: datetime.date = None
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


class SatelliteDetail(Satellite):
    datetime: List[datetime.datetime]
    latitude: List[float]
    longitude: List[float]
    altitude: List[float] = Field(None, description="Satellite altitude in km")


class SatelliteLatLng(BaseModel):
    satid: int
    timestamp: List[float] = Field(..., description="Unix timestamp in seconds in Jan 1 1970 UTC" )
    latlng: List[conlist(float, min_items=2, max_items=2)]
    height: float = Field(None, description="Average alititude of satellite [km]")


class Point(BaseModel):
    # __slots__ = ['datetime', 'azimuth', 'elevation', 'range', 'declination', 'right_ascension']
    datetime: datetime.datetime
    timestamp: float = Field(..., description='Unix timestamp in seconds since Jan 1 1970 UTC')
    az: float = Field(..., title='Azimuth', description='azimuth [deg]')
    az_ord: str = Field(..., description='Ordinal direction, eg. NE, NNW, WSW')
    el: float = Field(..., description='elevation [deg]')
    range: float = Field(..., description='range [km]')
    dec: float = Field(None, description='declination [deg]')
    ra: float = Field(None, description='right ascension [deg]')
    brightness: float = Field(None, description='brightness magnitude')

    def __repr__(self):
        dtstr = self.datetime.strftime("%b %d %Y, %H:%M:%S")
        s = "{}UTC el={:.1f}d, az={:.1f}d, rng={:.1f}km".format(
            dtstr, self.el, self.az, self.range)
        return s

    @validator('az_ord')
    def validate_ordinal_direction_string(cls, v):
        """ Try and select OrdinalDirection by name """
        if isinstance(v, str):
            assert v.upper() in OrdinalDirection.__members__
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


class Overpass(BaseModel):
    aos: Point = Field(..., description='Acquisition of signal')
    tca: Point = Field(..., description='Time of closest approach')
    los: Point = Field(..., description='Loss of signal')
    duration: float = Field(..., description='Duration of pass [sec]')
    max_elevation: float = Field(..., description='Maximum elevation [deg]')
    satid: int = Field(None, description='Satellite NORAD ID')
    type: PassType = None
    brightness: float = None


class OverpassDetail(Overpass):
    datetime: List[datetime.datetime]
    azimuth: List[float]
    elevation: List[float]
    range: List[float]


class Timezone(BaseModel):
    name: str
    utc_offset: float


class Location(BaseModel):
    lat: float = Field(..., description='latitude, \u0b00N')
    lon: float = Field(..., description='longitude, \u0b00E')
    h: float = Field(0.0, description='height, [m] above WGS84 ellipsoid')
    name: str = None
    timezone: Timezone = None


class OverpassResultBase(BaseModel):
    location: Location


class SingleSatOverpassResult(OverpassResultBase):
    satellite: Satellite
    overpasses: List[Overpass]


class PassDetailResult(OverpassResultBase):
    satellite: SatelliteDetail
    overpass: OverpassDetail


class MultiSatOverpassResult(OverpassResultBase):
    overpasses: List[Overpass]