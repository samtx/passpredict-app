from functools import lru_cache

from . import _solar


@lru_cache(maxsize=72)
def sun_pos(jd: float):
    return _solar.sun_pos(jd)