# test rotations.py
from zoneinfo import ZoneInfo

import numpy as np
from numpy.testing import assert_allclose
import pytest

from astrodynamics import Location


def test_location_instance_ecef_position():
    """
    Vallado, Eg. 11-6, p.912
    """
    phi = 42.38  # latitude, deg
    lmda = -71.13  # longitude, deg
    h = 24  # height, m
    location = Location("", latitude_deg=phi, longitude_deg=lmda, elevation_m=h)
    location_ecef = np.array([1526.122, -4465.064, 4276.894])
    assert_allclose(location.position_ecef, location_ecef, atol=1e-3)

@pytest.mark.parametrize(
    'name, lat, lon, zoneinfo_str, offset_tuple',
    (
        pytest.param('Austin', 30.2672, -97.7431, 'America/Chicago', (-5, -6,), id='Austin, Texas'),
        pytest.param('London', 51.5072, 0.1276, 'Europe/London', (0, +1,), id='London, UK'),
        pytest.param('Phoenix', 33.4484, -112.0740, 'America/Phoenix', (-7,), id='Phoenix, Arizona'),
        pytest.param('Petropavlovsk-Kamchatsky', 53.01667, 158.65, 'Asia/Kamchatka', (+12,), id="Petropavlovsk-Kamchatsky, Kamchatka"),
    )
)
def test_location_timezone(name, lat, lon, zoneinfo_str, offset_tuple):
    location = Location(name, lat, lon, 0)
    assert location.timezone == ZoneInfo(zoneinfo_str)
    assert location.offset in offset_tuple


