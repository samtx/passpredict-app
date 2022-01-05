# test_solar.py
import math

import numpy as np
from numpy.testing import assert_allclose, assert_almost_equal

from astrodynamics import _solar

import pytest

@pytest.mark.parametrize(
    'jd, r_true, tol',
    (
        pytest.param(2453827.5, [146186212.0, 28788976.0, 12481064.0], 1e-4, id="Vallado, Eg.5-1, p.280, April 2, 2006, 00:00 UTC"),
        pytest.param(2450540.547222222, [1.46082321e+08, 2.93211827e+07, 1.27158190e+07], 1e-3, id="Vallado, Eg.11-6, p.913, April 2, 1997, 01:08:0.00 UTC"),
    )
)
def test_sun_pos(jd, r_true, tol):
    """
    test solar position vector
    """
    r = _solar.sun_pos(jd)
    r_expected = np.asarray(r_true)
    assert_allclose(r, r_expected, rtol=tol)


def test_sun_sat_angle():
    """
    Vallado, Eg. 11-6, p.913
    jd = April 2, 1997, 01:08:0.00 UTC (2450540.547222222)
    """
    rsun = np.array([1.46078225e+08, 2.93174883e+07, 1.27109041e+07])
    rsat = np.array([-2811.2769, 3486.2632, 5069.5763])
    sunangle = _solar.sun_sat_angle(rsat, rsun)
    sunangle_expected = 76.0407 * math.pi / 180.0
    assert_almost_equal(sunangle, sunangle_expected, decimal=5)


def test_sun_sat_orthogonal_distance():
    """
    Vallado, Eg. 11-6, p.913
    """
    r = np.array([-2811.2769, 3486.2632, 5069.5763])  # sat, ECI coordinates
    zeta = 76.0407 * math.pi/180.0  # deg
    dist = _solar.sun_sat_orthogonal_distance(r, zeta)
    assert_almost_equal(dist, 6564.6870, decimal=4)