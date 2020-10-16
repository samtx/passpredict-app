import datetime

from pydantic import BaseModel


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
    name: str
    lat: float
    lon: float
    

class Location(LocationResult):
    """
    Location record in database
    """
    id: int
    query: str
    height: float = None


class Tle(BaseModel):
    id: int
    tle1: str
    tle2: str
    epoch: datetime.datetime
    satellite_id: int
    created: datetime.datetime
