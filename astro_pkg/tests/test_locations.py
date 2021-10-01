# test rotations.py
from math import radians
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
