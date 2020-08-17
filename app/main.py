# main.py
import datetime
from typing import List

from fastapi import FastAPI, Query
import numpy as np

from passpredict.predictions import find_overpasses
from passpredict.propagate import compute_satellite_data
from passpredict.solar import compute_sun_data
from passpredict.timefn import compute_time_array_from_date
from passpredict.models import SatPredictData, SunPredictData
from passpredict.schemas import Location, Satellite, Overpass
from passpredict.utils import Cache, get_TLE

app = FastAPI()

cache = Cache()

@app.get('/')
def read_root():
    return {"Hello": "World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}

@app.get("/overpasses/", response_model=List[Overpass])
def predict_passes(
    satid: int = Query(..., title="Satellite NORAD ID number"),
    lat: float = Query(..., title="Location latitude North in decimals"),
    lon: float = Query(..., title="Location longitude East in decimals"),
    h: float = Query(0.0, title="Location elevation above ellipsoid in meters"),
    days: int = Query(10, title="Future days to predict, max 14", le=14)
    ):
    satellite = Satellite(id=satid)
    location = Location(lat=lat, lon=lon, h=h)
    tle = get_TLE(satellite)
    date_start = datetime.date.today()# - datetime.timedelta(days=1)
    date_end = date_start + datetime.timedelta(days=days)
    dt_seconds = 10
    min_elevation = 10.01 # degrees
    
    with cache:

        time_key = date_start.strftime('%Y%m%d') + date_end.strftime('%Y%m%d') + str(dt_seconds)
        
        t = cache.get(time_key)
        if t is None:
            t = compute_time_array_from_date(date_start, date_end, dt_seconds)
            cache.set(time_key, t, ttl=86400)
        
        sun_key = 'sun_' + time_key
        sun = cache.get(sun_key)
        if sun is None:
            sun = compute_sun_data(t)
            sun = SunPredictData(rECEF=sun.rECEF)
            cache.set(sun_key, sun, ttl=86400)

        tle_key = str(satellite.id) + '_tle'
        tle = cache.get(tle_key)
        if tle is None:
            tle = get_TLE(satellite)
            cache.set(tle_key, tle, ttl=86400)

        sat_key = tle_key + time_key + '_sat'
        sat = cache.get(sat_key)
        if sat is None:    
            sat = compute_satellite_data(tle, t, sun)
            sat = SatPredictData(id=sat.id, rECEF=sat.rECEF, illuminated=sat.illuminated)
            cache.set(sat_key, sat, ttl=86400)

    overpasses = find_overpasses(t, location, [sat], sun, min_elevation)
    return overpasses
    

if __name__ == "__main__":

    # id = 25544
    # sat = Satellite(id=id, name="ISS")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, interface='WSGI')