# test rotations.py
import datetime

import numpy as np
from numpy.testing import assert_allclose, assert_almost_equal
import pytest

from .. import _rotations
from .. import rotations
from .. import topocentric
from ..constants import ASEC2RAD
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

    input data

year  2004  mon    4  day   6   7:51:28.386009
 dut1 -0.439962 s dat  32 s xp -0.140682 " yp 0.333309 " lod 0.001556 s
 ddpsi -0.052195 " ddeps  -0.003875
 ddx -0.000205 " ddy  -0.000136
order 106  eqeterms   2
units are km and km/s
convtime results
ut1 28287.946047 tut1   0.042623611411 jdut1 2453101.50000000000


 start from ecef
ecef-teme
 rteme   5094.1801072   6127.6447052   6380.3445327 vteme   -4.746131494    0.785817998    5.531931288
teme-ecef
 recef  -1033.4793830   7901.2952754   6380.3565958 vecef   -3.225636520   -2.872451450    5.531924446
diff in teme      0.0000000      0.0000000      0.0000000      0.0000000


    """
    sec = 28.386009
    d_ut1 = -0.439962
    jd = julian_date(2004, 4, 6, 7, 51, sec + d_ut1)
    jd = np.array([jd])
    rTEME = np.array([[5094.1801072, 6127.6447052, 6380.3445327]])
    rECEF = np.array([[-1033.4793830, 7901.2952754, 6380.3565958]])
    rECEF_2 = _rotations.teme2ecef(jd, rTEME)
    assert_allclose(rECEF_2, rECEF)


def test_appendix_c_conversion_from_TEME_to_ITRF_UTC1():
    """Test TEME to ITRF conversion

    References:
        Vallado et al., Revision 2
        Rhodes, Skyfield library, test_earth_satellites.py
    """
    seconds_per_day = 24.0 * 60.0 * 60.0
    rTEME = np.array([[5094.18016210, 6127.64465950, 6380.34453270]])
    vTEME = np.array([[-4.746131487, 0.785818041, 5.531931288]])
    vTEME = vTEME * seconds_per_day  # km/s to km/day

    # Apr 6, 2004,  07:51:28.386 UTC
    jd = julian_date(2004, 4, 6, 7, 51, 28.386)
    deltaUTC1 = -0.439961 # seconds
    jd += deltaUTC1/86400.0
    jd = np.array([jd])
    
    # Polar motion
    xp = -0.140682 * ASEC2RAD # arcseconds
    yp = 0.333309 * ASEC2RAD # arcseconds
    rITRF = _rotations.teme2ecef(jd, rTEME) #, xp, yp)

    print(rITRF)
    assert_almost_equal(rITRF[0], -1033.47938300, decimal=4)
    assert_almost_equal(rITRF[1], 7901.29527540, decimal=4)
    assert_almost_equal(rITRF[2], 6380.35659580, decimal=4)

    # vITRF /= seconds_per_day  # km/day to km/s
    # print(vITRF)
    # assert_almost_equal(vITRF[0], -3.225636520, decimal=6)
    # assert_almost_equal(vITRF[1], -2.872451450, decimal=6)
    # assert_almost_equal(vITRF[2], 5.531924446, decimal=6)

if __name__ == "__main__":
    import pytest
    pytest.main(['-v', __file__])