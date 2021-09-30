import logging
from math import pi
import datetime
from itertools import zip_longest
from typing import Dict
from pathlib import Path
from functools import lru_cache
from collections import namedtuple

from app.dbmodels import location, satellite
from app.resources import static_app


logger = logging.getLogger(__name__)


def shift_angle(x: float) -> float:
    """Shift angle in radians to [-pi, pi)

    Args:
        x: float, angle in radians

    Reference:
        https://stackoverflow.com/questions/15927755/opposite-of-numpy-unwrap/32266181#32266181
    """
    return (x + pi) % (2 * pi) - pi


def grouper(iterable, n, fillvalue=None):
    """
    from itertools recipes https://docs.python.org/3.7/library/itertools.html#itertools-recipes
    Collect data into fixed-length chunks or blocks
    """
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


def get_visible_satellites():
    """
    Download the latest TLEs from celestrak's visible.txt file
    """
    # Read satellite IDs from visible.txt file
    p = Path(__file__).parent / 'visible.txt'
    with open(p, 'r') as f:
        sat_id_strings = f.readlines()
        logger.info(f'{len(sat_id_strings)} visible satellites found')
        visible_sat_ids = [int(sat) for sat in sat_id_strings]
    return visible_sat_ids


def parse_tle(tle_string_list):
    """
    Parse a single 3-line TLE from celestrak
    """
    tle0, tle1, tle2 = tle_string_list
    name = tle0.strip()  # satellite name
    satellite_id = satid_from_tle(tle1)
    return {satellite_id : {'name': name, 'tle1': tle1, 'tle2': tle2}}


def empty_string_to_None(data: Dict) -> Dict:
    """
    Take a dictionary and convert any empty string values to None
    """
    for key, value in data.items():
        if value == "":
            data[key] = None
    return data


def epoch_from_tle_datetime(epoch_string: str) -> datetime:
    """
    Return datetime object from tle epoch string
    """
    epoch_year = int(epoch_string[0:2])
    if epoch_year < 57:
        epoch_year += 2000
    else:
        epoch_year += 1900
    epoch_day = float(epoch_string[2:])
    epoch_day, epoch_day_fraction = divmod(epoch_day, 1)
    epoch_microseconds = epoch_day_fraction * 24 * 60 * 60 * 1e6
    return datetime.datetime(epoch_year, month=1, day=1, tzinfo=datetime.timezone.utc) + \
        datetime.timedelta(days=int(epoch_day-1)) + \
        datetime.timedelta(microseconds=int(epoch_microseconds)
    )


def epoch_from_tle(tle1: str) -> datetime:
    """
    Extract epoch as datetime from tle line 1
    """
    epoch_string = tle1[18:32]
    return epoch_from_tle_datetime(epoch_string)


def satid_from_tle(tle1: str) -> int:
    """
    Extract satellite NORAD ID as int from tle line 1
    """
    return int(tle1[2:7])


@lru_cache(maxsize=1)
def get_satellite_norad_ids():
    """
    Return list of satellites with their names and norad ids
    """
    Satellite = namedtuple('Satellite', 'id name')
    satellites = [
        Satellite(25544, "International Space Station"),
        Satellite(20580, "Hubble Space Telescope"),
        Satellite(25338, "NOAA-15"),
        Satellite(28654, "NOAA-18"),
        Satellite(33591, "NOAA-19"),
        Satellite(44420, "Lightsail 2"),
        Satellite(29155, "GOES 13"),
        Satellite(25994, "TERRA"),
        Satellite(40069, "METEOR M2"),
    ]
    return satellites

