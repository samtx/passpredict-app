from logging import getLogger
from typing import NamedTuple

from passpredict.satellites import SGP4Propagator as SGP4Propagator_
from passpredict.time import julian_date_from_datetime

from api.domain import Orbit, Satellite


__all__ = [
    "SGP4Propagator",
]


class DefaultSatellite(NamedTuple):
    norad_id: int = 0
    name: None = None


logger = getLogger(__name__)


class SGP4Propagator(SGP4Propagator_):

    def __init__(
        self,
        orbit: Orbit,
        satellite: Satellite = DefaultSatellite(),
    ):
        self.satid = satellite.norad_id
        self.name = satellite.name
        self.intrinsic_mag = 1.0   # ISS is -1.8
        jdepoch = sum(julian_date_from_datetime(orbit.epoch))
        self.set_propagator(
            jdepoch=jdepoch,
            bstar=orbit.bstar,
            ndot=orbit.mean_motion_dot,
            nddot=orbit.mean_motion_ddot,
            ecc=orbit.eccentricity,
            argp=orbit.arg_of_pericenter,
            inc=orbit.inclination,
            mo=orbit.mean_anomaly,
            no_kozai=orbit.mean_motion,
            raan=orbit.ra_of_asc_node,
        )
