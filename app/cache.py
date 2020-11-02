import numpy as np
import redis
from redis.client import Pipeline

from .models import SunPredictData, SatPredictData
from .settings import REDIS_HOST


cache = redis.Redis(host=REDIS_HOST, port=6379)


def set_sun_cache(
    sun_key: str,
    rECEF: np.ndarray,
    pipe: Pipeline,
    ttl: int = 86400
):
    """
    Add sun hashdata to redis pipeline
    """
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
    Get numpy array from Redis bytes
    """
    n = int(sun[b'n'])
    dtype = sun[b'dtype'].decode()
    arr = np.frombuffer(sun[b'array'], dtype=dtype).reshape((3, n))
    return arr


def set_sat_cache(sat_key: str, sat: SatPredictData, pipe: Pipeline, ttl: int=86400):
    """
    Set satellite hashtable cache data to pipeline
    """
    sat_rECEF = sat.rECEF
    data = {
        'n': sat_rECEF.shape[1],
        'dtype': str(sat_rECEF.dtype),
        'rECEF': sat_rECEF.tobytes(),
        'illuminated': sat.illuminated.tobytes(),
        'sun_sat_dist': sat.sun_sat_dist.tobytes()
    }
    pipe.hset(sat_key, mapping=data)
    pipe.expire(sat_key, ttl)
    return pipe


def get_sat_cache(sat: bytes, satid: int):
    n = int(sat[b'n'])
    dtype = sat[b'dtype'].decode()
    rECEF = np.frombuffer(sat[b'rECEF'], dtype=dtype).reshape((3, n))
    illuminated = np.frombuffer(sat[b'illuminated'], dtype=bool)
    sun_sat_dist = np.frombuffer(sat[b'sun_sat_dist'], dtype=dtype)
    return SatPredictData(id=satid, rECEF=rECEF, illuminated=illuminated, sun_sat_dist=sun_sat_dist)
