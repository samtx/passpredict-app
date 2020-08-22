# main.py
import datetime
from typing import List

from fastapi import FastAPI, Query
from astropy.time import Time
import redis
import numpy as np

from passpredict.predictions import find_overpasses
from passpredict.propagate import compute_satellite_data
from passpredict.solar import compute_sun_data
from passpredict.timefn import julian_date_array_from_date
from passpredict.schemas import Location, Satellite, Overpass
from passpredict.utils import get_TLE
from passpredict.models import SatPredictData, SunPredictData

app = FastAPI()
cache = redis.Redis(host='0.0.0.0', port=6379)

@app.get('/')
def read_root():
    return {"Hello": "World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}

@app.get("/overpasses/", response_model=List[Overpass], response_model_exclude_unset=True)
def predict(
    satid: int = Query(..., title="Satellite NORAD ID number"),
    lat: float = Query(..., title="Location latitude North in decimals"),
    lon: float = Query(..., title="Location longitude East in decimals"),
    h: float = Query(0.0, title="Location elevation above ellipsoid in meters"),
    days: int = Query(10, title="Future days to predict, max 14", le=14)
    ):
    date_start = datetime.date.today()
    date_end = date_start + datetime.timedelta(days=days)
    dt_seconds = 10

    satellite = Satellite(id=satid)
    location = Location(lat=lat, lon=lon, h=h)
    min_elevation = 10.01

    jd = julian_date_array_from_date(date_start, date_end, dt_seconds)
    time_key = 'time:' + date_start.strftime('%Y%m%d') + date_end.strftime('%Y%m%d') + str(dt_seconds)
    sun_key = 'sun:' + time_key
    sat_key = 'sat:' + str(satid) + time_key

    with cache.pipeline() as pipe:

        pipe.hgetall(sun_key)
        pipe.hgetall(sat_key)
        sun, sat = pipe.execute()

        if not sun:
            t = Time(jd, format='jd')
            sun = compute_sun_data(t)
            sun_rECEF = sun.rECEF
            sun_rECEF_value = {
                'n': sun_rECEF.shape[1],
                'dtype': str(sun_rECEF.dtype),
                'array': sun_rECEF.tobytes()
            }
            pipe.hset(sun_key, mapping=sun_rECEF_value)
            pipe.expire(sun_key, 86400)
        else:
            # print(sun)
            n = int(sun[b'n'])
            dtype = sun[b'dtype'].decode()
            arr = np.frombuffer(sun[b'array'], dtype=dtype).reshape((3,n))
            sun = SunPredictData(rECEF=arr)

        if not sat:
            tle = get_TLE(satellite.id)
            t = Time(jd, format='jd')
            sat = compute_satellite_data(tle, t, sun)
            sat_rECEF = sat.rECEF
            data = {
                'n': sat_rECEF.shape[1],
                'dtype': str(sat_rECEF.dtype),
                'rECEF': sat_rECEF.tobytes(),
                'illuminated': sat.illuminated.tobytes()
            }
            pipe.hset(sat_key, mapping=data)
            pipe.expire(sat_key, 86400)
        else:
            n = int(sat[b'n'])
            rECEF_dtype = sat[b'dtype'].decode()
            sat_rECEF = np.frombuffer(sat[b'rECEF'], dtype=dtype).reshape((3,n))
            sat_illuminated = np.frombuffer(sat[b'illuminated'], dtype=bool)
            sat = SatPredictData(id=satid, rECEF=sat_rECEF, illuminated=sat_illuminated)

        if len(pipe) > 0:
            pipe.execute()

    overpasses = find_overpasses(jd, location, [sat], sun, min_elevation)
    return overpasses


if __name__ == "__main__":
    import uvicorn
    uvicorn.run('main:app', host="0.0.0.0", port=8000, log_level='debug')