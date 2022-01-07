# test_solar.py
import math
import datetime

import numpy as np
from numpy.linalg import norm

from astrodynamics import _solar
from astrodynamics import Location
from astrodynamics import _rotations
from astrodynamics.time import julian_date_from_datetime

import pytest
from pytest import approx

@pytest.mark.parametrize(
    'jd, r_expected',
    (
        pytest.param(2453827.5, [146186212.0, 28788976.0, 12481064.0], id="Vallado, Eg.5-1, p.280, April 2, 2006, 00:00 UTC"),
        pytest.param(2450540.547222222, [1.46082321e+08, 2.93211827e+07, 1.27158190e+07], id="Vallado, Eg.11-6, p.913, April 2, 1997, 01:08:0.00 UTC"),
    )
)
@pytest.mark.parametrize('tol', (1e-4,))
def test_sun_pos_mod(jd, r_expected, tol):
    """
    test solar position vector in MOD coordinates
    """
    r = np.empty(3, dtype=np.double)
    _solar.sun_pos_mod(jd, r)
    r_expected = np.asarray(r_expected)
    diff = norm(r - r_expected)
    rel = norm(r - r_expected) / norm(r_expected)
    assert rel < tol


@pytest.mark.parametrize(
    'jd, r_true',
    (
        pytest.param(2453827.5, [-1.48976308e+08, -2.44056699e+06,  1.24820833e+07], id="Vallado, Eg.5-1, p.280, April 2, 2006, 00:00 UTC"),
        pytest.param(2450540.547222222, [-1.43169570e+08, 4.12567046e+07, 1.27096677e+07], id="Vallado, Eg.11-6, p.913, April 2, 1997, 01:08:0.00 UTC"),
    )
)
@pytest.mark.parametrize('tol', (1e-4,))
def test_sun_pos(jd, r_true, tol):
    """
    test solar position vector in ECEF coordinates
    """
    r = _solar.sun_pos(jd)
    r_expected = np.asarray(r_true)
    rel = norm(r - r_expected) / norm(r_expected)
    assert rel < tol


def test_sun_sat_angle():
    """
    Vallado, Eg. 11-6, p.913
    jd = April 2, 1997, 01:08:0.00 UTC (2450540.547222222)
    """
    rsun = np.array([1.46078225e+08, 2.93174883e+07, 1.27109041e+07])
    rsat = np.array([-2811.2769, 3486.2632, 5069.5763])
    sunangle = _solar.sun_sat_angle(rsat, rsun)
    sunangle_expected = 76.0407 * math.pi / 180.0
    assert sunangle == approx(sunangle_expected, abs=1e-4)


def test_sun_sat_orthogonal_distance():
    """
    Vallado, Eg. 11-6, p.913
    """
    r = np.array([-2811.2769, 3486.2632, 5069.5763])  # sat, ECI coordinates
    zeta = 76.0407 * math.pi/180.0  # deg
    dist = _solar.sun_sat_orthogonal_distance(r, zeta)
    assert dist == approx(6564.6870, abs=1e-4)


@pytest.mark.parametrize(
    'hr_dt, el_expected',
    [
        (8, 30.67),
        (9, 45.36),
        (10, 60.16),
        (11, 74.64),
        (12, 84.55),
        (13, 73.5),
        (14, 58.96),
        (15, 44.14),
        (16, 29.26),
        (19, -15.55)
    ]
)
def test_sun_location_elevation_datetime_from_orbitpredictor(hr_dt, el_expected):
    """
    Test sun elevation angles relative to location.
    Uses test suite from orbit_predictor/tests/test_azimuth_elevation.py
    https://github.com/satellogic/orbit-predictor/blob/master/tests/test_azimuth_elevation.py
    """
    location = Location("", 0, 0, 0)
    d = datetime.datetime(2016, 9, 8) + datetime.timedelta(hours=hr_dt)
    jd, jdfr = julian_date_from_datetime(d)
    jd = jd + jdfr
    sun_recef = _solar.sun_pos(jd)
    el = _rotations.elevation_at(location.latitude_rad, location.longitude_rad, location.recef, sun_recef)
    assert el == approx(el_expected, abs=0.25)