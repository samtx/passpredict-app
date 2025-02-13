import math
from typing import NamedTuple

from passpredict.constants import R_EARTH


class LatLon(NamedTuple):
    lat: float
    lon: float


def spherical_earth_distance(
    point_a: LatLon,
    point_b: LatLon,
) -> float:
    """Compute direct radius from location to AOS coordinate. Assumes the Earth is a sphere."""
    theta1 = math.radians(90 - point_a.lat)
    theta2 = math.radians(90 - point_b.lat)
    phi1 = math.radians(point_a.lon)
    phi2 = math.radians(point_b.lon)
    d = R_EARTH * math.sqrt(2 - 2*(math.sin(theta1)*math.sin(theta2)*math.cos(phi1 - phi2) + math.cos(theta1)*math.cos(theta2)))
    return d


get_visibility_radius = spherical_earth_distance
