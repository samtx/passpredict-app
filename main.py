# main.py

from fastapi import FastAPI, Query
from pydantic import BaseModel, Field
import datetime
import numpy as np
from typing import List
from passpredict.predict import predict_passes
from passpredict.propagate import propagate, get_TLE 
from passpredict.timefn import truncate_datetime
from passpredict.models import *

app = FastAPI()


# class Point(BaseModel):
#     # __slots__ = ['datetime', 'azimuth', 'elevation', 'range', 'declination', 'right_ascension']
#     datetime: datetime.datetime
#     azimuth: float
#     elevation: float
#     range: float
#     declination: float = None
#     right_ascension: float = None

#     def direction_from_azimuth(self):
#         ''' Return direction from azimuth degree '''
#         azm = self.azimuth % 360
#         mod = 360/16. # number of degrees per coordinate heading
#         start = 0 - mod/2
#         n = np.floor((azm-start)/mod).astype(int)
#         COORDINATES = ['N','NNE','NE','ENE','E','ESE','SE','SSE','S','SSW','SW','WSW','W','WNW','NW','NNW','N']
#         return COORDINATES[n]


    # def __repr__(self):
    #     dtstr = self.datetime.strftime("%b %d %Y, %H:%M:%S")
    #     s = "{}UTC el={:.1f}d, az={:.1f}d, rng={:.1f}km".format(
    #         dtstr, self.elevation, self.azimuth, self.range)
    #     return s

# utc = Timezone(offset=0.0, name='UTC')

# class Location(BaseModel):
#     # __slots__ = ['lat', 'lon', 'h', 'name', 'tz']
#     lat: float       # latitude, decimal degrees, positive is North
#     lon: float       # longitude, decimal degrees, positive is East
#     h: float = 0.0   # elevation [m]
#     name: str = None
#     # tz: Timezone = utc  # timezone object

# Satellte = passpredict.models.Satellite
# Overpass = passpredict.models.Overpass
# Location = passpredict.models.Location

# class Satellite(BaseModel):
#     id: int # = Field(title="Satellite NORAD ID number")
#     name: str = "" #Field(None, title="Satellite name")


# class Tle(BaseModel):
#     __slots__ = ['tle1','tle2','epoch','satellite']
#     tle1: str
#     tle2: str
#     epoch: datetime.datetime
#     satellite: Satellite


# class Overpass(BaseModel):
#     # __slots__ = ['location', 'satellite', 'start_pt', 'max_pt', 'end_pt', 't', 'r']
#     location: Location
#     satellite: Satellite
#     start_pt: Point
#     max_pt: Point
#     end_pt: Point
    # t: Array[float]
    # r: Array[float]


@app.get('/')
def read_root():
    return {"Hello": "World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}

@app.get("/overpasses/", response_model=List[Overpass])
def find_overpasses(
    satid: int = Query(..., title="Satellite NORAD ID number"),
    lat: float = Query(..., title="Location latitude North in decimals"),
    lon: float = Query(..., title="Location longitude East in decimals"),
    h: float = Query(0.0, title="Location elevation above ellipsoid in meters"),
    days: int = Query(10, title="Future days to predict, max 14", le=14)
    ):
    satellite = Satellite(id=satid)
    location = Location(lat=lat, lon=lon, h=h)
    tle = get_TLE(satellite)
    dt_start = truncate_datetime(datetime.datetime.now())# - datetime.timedelta(days=1)
    dt_end = dt_start + datetime.timedelta(days=days)
    dt_seconds = 20
    min_elevation = 10.01 # degrees
    tle = get_TLE(satellite)
    satellite_rv = propagate(tle.tle1, tle.tle2, dt_start, dt_end, dt_seconds)
    satellite_rv.satellite = satellite
    satellite_rv.tle = tle
    # Compute sun-satellite quantities
    # jdt = satellite_rv.julian_date
    # rsunECI = sun_pos(jdt)
    # satellite_rv.visible = is_sat_illuminated(satellite_rv.rECI, rsunECI)
            
    #        with open(f'satellite_{satellite.id:d}.pkl', 'wb') as f:
    #            pickle.dump(satellite_rv, f)
    #    else:
    #         with open(f'satellite_{satellite.id:d}.pkl', 'rb') as f:
    #             satellite_rv = pickle.load(f)
        # print('begin prediction...')
        # set minimum elevation parameter: min_elevation = 10 degrees
    overpasses = predict_passes(
        location.lat, location.lon, location.h,
        satellite_rv.rECEF, satellite_rv.rECI, satellite_rv.julian_date,
        min_elevation=min_elevation,
        loc=location, sat=satellite)
    pass_list = overpasses.tolist()
    return pass_list

if __name__ == "__main__":

    # id = 25544
    # sat = Satellite(id=id, name="ISS")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, interface='WSGI')