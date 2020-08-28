# main.py
import datetime
from typing import List
import pickle
import os

from fastapi import FastAPI, Query
from astropy.time import Time
import redis
import numpy as np
from pydantic import BaseModel

from passpredict.predictions import find_overpasses
from passpredict.propagate import compute_satellite_data
from passpredict.solar import compute_sun_data
from passpredict.timefn import julian_date_array_from_date
from passpredict.schemas import Location, Satellite, Overpass
from passpredict.utils import get_TLE
from passpredict.models import SatPredictData, SunPredictData

app = FastAPI()
redis_host = os.getenv('REDIS_HOST', 'localhost')
cache = redis.Redis(host=redis_host, port=6379)

MAX_DAYS = 14  # maximum days to predict overpasses
DT_SECONDS = 15
SEC_PER_DAY = 86400
# Make sure that dt_seconds evenly divides into number of seconds per day
assert SEC_PER_DAY % DT_SECONDS == 0 
NUM_TIMESTEPS_PER_DAY = SEC_PER_DAY / DT_SECONDS


class OverpassResult(BaseModel):
    location: Location
    satid: int
    overpasses: List[Overpass]


@app.get('/hello/')
def read_root():
    return {"Hello": "World"}


@app.get("/overpasses/", response_model=OverpassResult, response_model_exclude_unset=True)
def predict(
    satid: int = Query(..., title="Satellite NORAD ID number"),
    lat: float = Query(..., title="Location latitude North in decimals"),
    lon: float = Query(..., title="Location longitude East in decimals"),
    h: float = Query(0.0, title="Location elevation above ellipsoid in meters"),
    days: int = Query(10, title="Future days to predict", le=MAX_DAYS)
):
    # Check cache with input string
    main_key = f'overpasses:{satid}:lat{lat}:lon{lon}:h{h}:days{days}'
    result = cache.get(main_key)
    if result:
        overpass_result = pickle.loads(result)
        return overpass_result

    date_start = datetime.date.today()
    date_end = date_start + datetime.timedelta(days=MAX_DAYS)
    
    time_slice = slice(0, days*NUM_TIMESTEPS_PER_DAY)

    satellite = Satellite(id=satid)
    location = Location(lat=lat, lon=lon, h=h)
    min_elevation = 10.01

    jd = julian_date_array_from_date(date_start, date_end, DT_SECONDS)
    time_key = 'time:' + date_start.strftime('%Y%m%d') + date_end.strftime('%Y%m%d') + str(DT_SECONDS)
    sun_key = 'sun:' + time_key
    sat_key = 'sat:' + str(satid) + time_key

    with cache.pipeline() as pipe:

        pipe.hgetall(sun_key)
        pipe.hgetall(sat_key)
        sun, sat = pipe.execute()

        if not sun:
            t = Time(jd, format='jd')
            sun = compute_sun_data(t)
            rECEF = sun.rECEF
            rECEF_value = {
                'n': rECEF.shape[1],
                'dtype': str(rECEF.dtype),
                'array': rECEF.tobytes()
            }
            pipe.hset(sun_key, mapping=rECEF_value)
            pipe.expire(sun_key, 86400)
        else:
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
            dtype = sat[b'dtype'].decode()
            rECEF = np.frombuffer(sat[b'rECEF'], dtype=dtype).reshape((3, n))
            illuminated = np.frombuffer(sat[b'illuminated'], dtype=bool)
            sat = SatPredictData(
                id=satid,
                rECEF=rECEF,
                illuminated=illuminated
            )

        overpasses = find_overpasses(jd, location, [sat], sun, min_elevation)
        overpass_result = OverpassResult(
            location=location,
            satid=satid,
            overpasses=overpasses
        )
        # cache results for 5 minutes
        pipe.set(main_key, pickle.dumps(overpass_result), ex=300)
        if len(pipe) > 0:
            pipe.execute()

    return overpass_result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run('main:app', host="0.0.0.0", port=8000, log_level='debug')
