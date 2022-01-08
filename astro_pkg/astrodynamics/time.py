import datetime
from functools import lru_cache

from . import _time
from .constants import DAYSEC


@lru_cache(maxsize=128)
def julian_date(year: int, mon: int, day: int, hr: int, minute: int, sec: float):
    return _time.julian_date(year, mon, day, hr, minute, sec)


def julian_date_from_datetime(dt: datetime.datetime):
    yr, mo, dy = dt.year, dt.month, dt.day
    hr, mn, sec = dt.hour, dt.minute, dt.second+dt.microsecond/1e6
    return julian_date(yr, mo, dy, hr, mn, sec)


def julian_date_round_to_second(jd: float) -> float:
    """
    Round julian date floating point value to nearest second
    """
    one_second = 1/DAYSEC
    jd, jdfr = divmod(jd, 1)
    quot, _ = divmod(jdfr, one_second)
    return jd + quot*one_second