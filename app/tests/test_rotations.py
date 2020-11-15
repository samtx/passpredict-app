# test rotations.py
import datetime

import numpy as np
from numpy.testing import assert_allclose, assert_almost_equal
import pytest

from .. import _rotations
from .. import rotations
from .. import topocentric
from ..models import RhoVector


def test_ecef2sez():
    """
    Vallado, Eg. 11-6, p.912
    """
    phi = 42.38  # latitude, deg
    lmda = -71.13  # longitude, deg
    # lmda = 136.2944
    h = 24  # height, m
    rsat = np.array([885.7296, -4389.3856, 5070.1765])
    rsite = topocentric.site_ECEF2(phi, lmda, h)
    rhoECEF = rsat - rsite
    print(rhoECEF)
    rSEZ = rotations.ecef2sez(rhoECEF, phi, lmda)
    rSEZ_true = np.array([-773.8654, -581.4980, 328.8145])
    np.set_printoptions(precision=8)
    assert_allclose(rSEZ, rSEZ_true)
    # for i in [0, 1, 2]:
    #     assert_almost_equal(rSEZ[i], rSEZ_true[i], decimal=0, verbose=True)


def test_c_ecef2sez():
    """
    Vallado, Eg. 11-6, p.912
    """
    phi = 42.38  # latitude, deg
    lmda = -71.13  # longitude, deg
    # lmda = 136.2944
    h = 24  # height, m
    rsat = np.array([885.7296, -4389.3856, 5070.1765])
    rsite = topocentric.site_ECEF2(phi, lmda, h)
    rhoECEF = rsat - rsite
    print(rhoECEF)
    rhoECEF = rhoECEF[np.newaxis, :]
    rSEZ = _rotations.ecef2sez(rhoECEF, phi, lmda)
    rSEZ_true = np.array([[-773.8654, -581.4980, 328.8145]])
    np.set_printoptions(precision=8)
    assert_allclose(rSEZ, rSEZ_true)
    # for i in [0, 1, 2]:
    #     assert_almost_equal(rSEZ[i], rSEZ_true[i], decimal=0, verbose=True)

def test_teme2ecef():
    """
    Vallado matlab files, exsgp4_teme.m
    """
    jd = np.array([453101.50000000])
    rECEF = np.array([[-1033.4793830, 7901.2952754, 6380.3565958]])
    rTEME = np.array([[5094.1801072, 6127.6447052, 6380.3445327]])
    rTEME_2 = _rotations.teme2ecef(jd, rECEF)
    assert_allclose(rTEME_2, rTEME)


if __name__ == "__main__":
    import pytest
    pytest.main(['-v', __file__])