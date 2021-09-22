from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from timezonefinder import TimeZoneFinder

from .schemas import OverpassResultBase

tf = TimeZoneFinder()


def set_timezone_on_datetime(dt: OverpassResultBase):
    """
    Parse through
    """
    pass


def get_timezone_from_latlon(latitude: float, longitude: float):
    """
    Returns timezone string. E.g. 'Europe/Berlin'
    """
    tz = tf.timezone_at(lng=longitude, lat=latitude)
    return tz


def get_utc_offset(tz_str: str) -> float:
    """
    Get hours offset from UTC for timezone
    """
    zone = ZoneInfo(tz_str)
