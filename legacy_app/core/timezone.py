from datetime import timezone as py_timezone
from zoneinfo import ZoneInfo
from functools import lru_cache

from timezonefinder import TimeZoneFinder

from .schemas import OverpassResultBase

tf = TimeZoneFinder()


def set_timezone_on_datetime(dt: OverpassResultBase):
    """
    Parse through
    """
    pass


@lru_cache(maxsize=128)
def get_timezone_from_latlon(latitude: float, longitude: float) -> ZoneInfo:
    """
    Returns timezone string. E.g. 'Europe/Berlin'
    """
    tz_str = tf.timezone_at(lng=longitude, lat=latitude)
    tz = py_timezone.utc if not tz_str else ZoneInfo(tz_str)
    return tz


def get_utc_offset(tz_str: str) -> float:
    """
    Get hours offset from UTC for timezone
    """
    zone = ZoneInfo(tz_str)
