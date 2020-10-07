# main.py
import datetime
from typing import List, Optional
import pickle
import os
from itertools import zip_longest

from fastapi import FastAPI, Query, Path
from astropy.time import Time
import redis
from redis.client import Pipeline
import numpy as np
from pydantic import BaseModel

from .passpredict.predictions import find_overpasses
from .passpredict.propagate import compute_satellite_data
from .passpredict.solar import compute_sun_data
from .passpredict.timefn import julian_date_array_from_date
from .passpredict.schemas import Location, Satellite, Overpass
from .passpredict.tle import get_TLE
from .passpredict.models import SatPredictData, SunPredictData

from .utils import get_visible_satellites

app = FastAPI()
redis_host = os.getenv('REDIS_HOST', 'localhost')
cache = redis.Redis(host=redis_host, port=6379)

MAX_DAYS = 14  # maximum days to predict overpasses
DT_SECONDS = 30
SEC_PER_DAY = 86400
# Make sure that dt_seconds evenly divides into number of seconds per day
assert SEC_PER_DAY % DT_SECONDS == 0 
NUM_TIMESTEPS_PER_DAY = int(SEC_PER_DAY / DT_SECONDS)
TIME_KEY_SUFFIX = ':' + str(MAX_DAYS) + ':' + str(DT_SECONDS)


VISIBLE_SATS = get_visible_satellites()
print(f'{len(VISIBLE_SATS)} visible satellites found')


class OverpassResult(BaseModel):
    location: Location
    overpasses: List[Overpass]
    satid: Optional[int] = None


@app.get('/hello/')
def read_root():
    return {"Hello": "World"}


@app.get("/passes/", response_model=OverpassResult, response_model_exclude_unset=True)
def all_passes(
    lat: float = Query(..., title="Location latitude North in decimals"),
    lon: float = Query(..., title="Location longitude East in decimals"),
    h: float = Query(0.0, title="Location elevation above WGS84 ellipsoid in meters"),
):
    """
    Compute passes for top 100 visible satellites for 24 hours
    """
    # Check cache with input string
    main_key = f'all_passes:lat{lat}:lon{lon}:h{h}'
    result = cache.get(main_key)
    if result:
        overpass_result = pickle.loads(result)
        return overpass_result
    date_start = datetime.date.today()
    date_end = date_start + datetime.timedelta(days=1)
    location = Location(lat=lat, lon=lon, h=h)
    min_elevation = 10.01

    jd = julian_date_array_from_date(date_start, date_end, DT_SECONDS)
    time_key = 'time:' + date_start.strftime('%Y%m%d') + ':1:' + str(DT_SECONDS)
    sun_key = 'sun:' + time_key

    with cache.pipeline() as pipe:

        pipe.hgetall(sun_key)
        for satid in visible_sats:
            sat_key = 'sat:' + str(satid) + ':' + time_key
            pipe.hgetall(sat_key)
        sun, *sats = pipe.execute()

        if not sun:
            t = Time(jd, format='jd')
            sun = compute_sun_data(t)
            pipe = set_sun_cache(sun_key, sun, pipe, 86400)
        else:
            sun = get_sun_cache(sun)
        
        num_visible_sats = len(VISIBLE_SATS)
        sat_list = [None] * num_visible_sats

        for i, satid, satdata in zip(range(num_visible_sats), VISIBLE_SATS, sats):
            if not satdata:
                print(f'Computing satellite position for satellite {satid}')
                tle = get_TLE(satid)
                t = Time(jd, format='jd')
                sat = compute_satellite_data(tle, t, sun)
                sat_key = 'sat:' + str(satid) + ':' + time_key
                pipe = set_sat_cache(sat_key, sat, pipe, 86400)
            else:
                sat = get_sat_cache(satdata, satid)
            sat_list[i] = sat

        overpasses = find_overpasses(jd, location, sat_list, sun, min_elevation, visible_only=True)
        overpass_result = OverpassResult(
            location=location,
            overpasses=overpasses
        )
        # cache results for 5 minutes
        pipe.set(main_key, pickle.dumps(overpass_result), ex=300)
        if len(pipe) > 0:
            pipe.execute()

    return overpass_result


@app.get("/passes/{satid}", response_model=OverpassResult, response_model_exclude_unset=True)
def passes(
    satid: int = Path(..., title="Satellite NORAD ID number"),
    lat: float = Query(..., title="Location latitude North in decimals"),
    lon: float = Query(..., title="Location longitude East in decimals"),
    h: float = Query(0.0, title="Location elevation above WGS84 ellipsoid in meters"),
    days: int = Query(10, title="Future days to predict", le=MAX_DAYS)
):
    # Check cache with input string
    main_key = f'passes:{satid}:lat{lat}:lon{lon}:h{h}:days{days}'
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
    time_key = 'time:' + date_start.strftime('%Y%m%d') + TIME_KEY_SUFFIX
    sun_key = 'sun:' + time_key
    sat_key = 'sat:' + str(satid) + ':' + time_key

    with cache.pipeline() as pipe:

        pipe.hgetall(sun_key)
        pipe.hgetall(sat_key)
        sun, sat = pipe.execute()

        if not sun:
            t = Time(jd, format='jd')
            sun = compute_sun_data(t)
            pipe = set_sun_cache(sun_key, sun, pipe, 86400)
        else:
            sun = get_sun_cache(sun)

        if not sat:
            tle = get_TLE(satellite.id)
            t = Time(jd, format='jd')
            sat = compute_satellite_data(tle, t, sun)
            pipe = set_sat_cache(sat_key, sat, pipe, 86400)
        else:
            sat = get_sat_cache(sat, satid)

        # Only use slice of position and time arrays requested
        if days < MAX_DAYS:
            end_index = NUM_TIMESTEPS_PER_DAY * days
            jd = jd[:end_index]
            sat = sat[:end_index]
            sun = sun[:end_index]

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


def set_sun_cache(
    sun_key: str,
    sun: SunPredictData,
    pipe: Pipeline,
    ttl=86400
):
    """
    Add sun hashdata to redis pipeline
    """
    rECEF = sun.rECEF
    rECEF_value = {
        'n': rECEF.shape[1],
        'dtype': str(rECEF.dtype),
        'array': rECEF.tobytes()
    }
    pipe.hset(sun_key, mapping=rECEF_value)
    pipe.expire(sun_key, ttl)
    return pipe


def get_sun_cache(sun: bytes):
    """
    Get SunPredictData object from Redis bytes
    """
    n = int(sun[b'n'])
    dtype = sun[b'dtype'].decode()
    arr = np.frombuffer(sun[b'array'], dtype=dtype).reshape((3, n))
    return SunPredictData(rECEF=arr)


def set_sat_cache(sat_key: str, sat: SatPredictData, pipe: Pipeline, ttl: int=86400):
    """
    Set satellite hashtable cache data to pipeline
    """
    sat_rECEF = sat.rECEF
    data = {
        'n': sat_rECEF.shape[1],
        'dtype': str(sat_rECEF.dtype),
        'rECEF': sat_rECEF.tobytes(),
        'illuminated': sat.illuminated.tobytes()
    }
    pipe.hset(sat_key, mapping=data)
    pipe.expire(sat_key, ttl)
    return pipe


def get_sat_cache(sat: bytes, satid: int):
    n = int(sat[b'n'])
    dtype = sat[b'dtype'].decode()
    rECEF = np.frombuffer(sat[b'rECEF'], dtype=dtype).reshape((3, n))
    illuminated = np.frombuffer(sat[b'illuminated'], dtype=bool)
    return SatPredictData(id=satid, rECEF=rECEF, illuminated=illuminated)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level='debug')
