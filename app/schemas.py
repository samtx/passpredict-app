import datetime
from typing import List
from enum import Enum
from functools import cached_property
from math import floor

import numpy as np
from pydantic import BaseModel, Field

from .timefn import jday2datetime
from .utils import epoch_from_tle, satid_from_tle

COORDINATES = ['N','NNE','NE','ENE','E','ESE','SE','SSE','S','SSW','SW','WSW','W','WNW','NW','NNW','N']


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


class LocationResult(BaseModel):
    """
    Location result from geocoder
    """
    lat: float
    lon: float
    name: str = None
    

class Location(LocationResult):
    height: float = Field(0.0, alias='h')


class LocationInDB(Location):
    """
    Location record in database

    Inherited attributes:
        name: str
        lat: float
        lon: float
    """
    id: int
    query: str


class Tle(BaseModel):
    tle1: str
    tle2: str
    epoch: datetime.datetime
    satid: int

    @classmethod    
    def from_string(cls, tle1: str, tle2: str):
        epoch = epoch_from_tle(tle1)
        satid = satid_from_tle(tle1)
        return cls(
            tle1=tle1,
            tle2=tle2,
            epoch=epoch,
            satid=satid,
        )
    
    class Config:
        title = 'TLE'


class Point(BaseModel):
    # __slots__ = ['datetime', 'azimuth', 'elevation', 'range', 'declination', 'right_ascension']
    datetime: datetime.datetime
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
    
    @classmethod
    def from_rho(cls, rho, idx):
        """Create a Point object directly from the rho vector and index without validation"""
        return cls.construct(
            datetime=jday2datetime(rho.time.jd[idx]),
            azimuth=rho.az[idx],
            elevation=rho.el[idx],
            range=rho.rng[idx]
        )

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


class Overpass(BaseModel):
    start_pt: Point
    max_pt: Point
    end_pt: Point
    satellite_id: int = None
    type: PassType = None
    vis_start_pt: Point = None
    vis_end_pt: Point = None
    brightness: float = None
    

class OverpassResultBase(BaseModel):
    location: Location


class SingleSatOverpassResult(OverpassResultBase):
    satellite: Satellite
    overpasses: List[Overpass]


class MultiSatOverpassResult(OverpassResultBase):
    overpasses: List[Overpass]

