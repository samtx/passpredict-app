# test rotations.py
from math import radians, degrees
import numpy as np
from numpy.linalg import norm
from numpy.testing import assert_allclose
import pytest
from pytest import approx

from orbit_predictor.coordinate_systems import ecef_to_llh, to_horizon, horizon_to_az_elev

from astrodynamics import _rotations, Location

np.set_printoptions(precision=8)


@pytest.mark.parametrize(
    ('lat', 'lon', 'h', 'location_ecef', 'satellite_ecef'),
    (
        pytest.param(42.38, -71.13, 24, [1526.122, -4465.064, 4276.894], [885.7296, -4389.3856, 5070.1765], id="Vallado, Eg 11-6, p. 912"),
    )
)
class TestECEFtoRazelRotations:

    def test_ecef_to_razel_compare_with_orbit_predictor(self, lat, lon, h, location_ecef, satellite_ecef):
        lat_rad = radians(lat)
        lon_rad = radians(lon)
        location_ecef = np.array(location_ecef)
        satellite_ecef = np.array(satellite_ecef)
        range_, az, el = _rotations.razel(lat_rad, lon_rad, location_ecef, satellite_ecef)
        # Use Orbit-Predictor functions and classes
        location = Location("", lat, lon, h)
        op_s, op_e, op_z = to_horizon(location.latitude_rad, location.longitude_rad, location.position_ecef, satellite_ecef)
        op_azimuth, op_elevation = horizon_to_az_elev(op_s, op_e, op_z)
        op_azimuth = degrees(op_azimuth)
        op_elevation = degrees(op_elevation)
        op_range = location.slant_range_km(satellite_ecef)
        assert_allclose(range_, op_range, atol=1e-4)
        assert_allclose(az, op_azimuth, atol=1e-5)
        assert_allclose(el, op_elevation, atol=1e-4)

    def test_ecef_to_razel(self, lat, lon, h, location_ecef, satellite_ecef):
        location_ecef = np.array(location_ecef)
        satellite_ecef = np.array(satellite_ecef)
        range_, az, el = _rotations.razel(radians(lat), radians(lon), location_ecef, satellite_ecef)
        assert_allclose(range_, 1022.3143, atol=1e-4)
        assert_allclose(az, 323.0780, atol=1e-4)
        assert_allclose(el, 18.7619, atol=1e-4)



@pytest.mark.parametrize(
    'ecef, llh, tol',
    (
        pytest.param([2750.19, -4476.679, -3604.011],[-34.628284, -58.436045, 0.0], 1e-2, id="orbit_predictor tests, buenos aires"),
        pytest.param([2922.48, -4757.126, -3831.311],[-34.628284, -58.436045, 400.0], 1e-2, id="orbit_predictor tests, buenos aires high altitude"),
        pytest.param([4919.4248, 793.8355, 3967.8253],[38.716666, 9.16666, 0.0], 1e-2, id="orbit_predictor tests, lisbon"),
        pytest.param([5266.051, 849.7698, 4249.2854],[38.716666, 9.16666, 450.0], 1e-2, id="orbit_predictor tests, lisbon high altitude"),
        pytest.param([.382, -1.0495, 6356.7772], [89.99, -70, 0.025], 1e-2, id="orbit_predictor tests, north pole"),
        pytest.param([.382, -1.0495, -6356.777], [-89.99, -70, 0.025], 1e-2, id="orbit_predictor tests, south pole"),
    )
)
def test_ecef_to_llh(ecef, llh, tol):
    ecef_ary = np.array(ecef)
    llh_computed = _rotations.ecef_to_llh(ecef_ary)
    for i in range(3):
        assert_allclose(llh_computed[i], llh[i], atol=tol)


@pytest.mark.parametrize(
    'jd, tt_expected, tol',
    (
        pytest.param(2453750.5+0.892100694, 2453750.5+0.892855139, 1e-8, id="SOFA t_utctai and t_taitt test cases"),
    )
)
def test_jd2tt(jd, tt_expected, tol):
    tt = _rotations.jd2tt(jd)
    assert tt == approx(tt_expected, abs=tol)


@pytest.mark.parametrize(
    'jd, rmod, rpef_expected',
    (
        pytest.param(2453827.5, [146186212.0, 28788976.0, 12481064.0], [-148973886.6, -2444152.8, 12481902.6], id="Vallado, Eg.5-1, p.280, April 2, 2006, 00:00 UTC"),
        pytest.param(2450540.547222222, [146082321., 29321182.7, 12715819.0], [-143170456.9, 41255716.8, 12714338.5], id="Vallado, Eg.11-6, p.913, April 2, 1997, 01:08:0.00 UTC"),
    )
)
@pytest.mark.parametrize(
    'tol', (1e-5,)
)
def test_mod2ecef(jd, rmod, rpef_expected, tol):
    """
    Test MOD to ECEF transformation
    Validates result using julia SatelliteToolbox MOD to PEF
    """
    rmod = np.asarray(rmod)
    rpef_expected = np.asarray(rpef_expected)
    rpef = np.empty(3, dtype=np.double)
    _rotations.mod2ecef(jd, rmod, rpef)
    rel = norm(rpef - rpef_expected) / norm(rpef_expected)
    assert rel < tol
