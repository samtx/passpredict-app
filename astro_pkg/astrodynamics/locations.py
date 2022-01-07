from functools import cached_property
from zoneinfo import ZoneInfo
from datetime import datetime, timezone as py_timezone
from math import radians

import numpy as np
from orbit_predictor.locations import Location as LocationBase
from orbit_predictor import coordinate_systems

from .utils import get_timezone_from_latlon
from .time import julian_date_from_datetime
from .solar import sun_pos
from ._rotations import razel


class Location(LocationBase):

    def __init__(self, name, latitude_deg, longitude_deg, elevation_m):
        """Location.
        Parameters
        ----------
        latitude_deg : float
            Latitude in degrees.
        longitude_deg : float
            Longitude in degrees.
        elevation_m : float
            Elevation in meters.
        """
        self.name = name
        self.latitude_deg = latitude_deg
        self.longitude_deg = longitude_deg
        self.latitude_rad = radians(latitude_deg)
        self.longitude_rad = radians(longitude_deg)
        self.elevation_m = elevation_m
        self.position_ecef = coordinate_systems.geodetic_to_ecef(
            self.latitude_rad,
            self.longitude_rad,
            elevation_m / 1000.)
        self.position_llh = latitude_deg, longitude_deg, elevation_m
        self.recef = np.array(self.position_ecef)

    @cached_property
    def timezone(self) -> ZoneInfo:
        """ Find timezone """
        return get_timezone_from_latlon(self.latitude_deg, self.longitude_deg)

    @cached_property
    def offset(self) -> float:
        """  Compute timezone offset in hours from UTC  """
        now = datetime.now(self.timezone)
        delta = now.utcoffset().total_seconds() / 3600
        return delta

    def is_sunlit(self, dt: datetime):
        jd, jdfr = julian_date_from_datetime(dt)
        jd = jd + jdfr
        sun_recef = sun_pos(jd)
        _, _, el = razel(self.latitude_rad, self.longitude_rad, self.recef, sun_recef)


        # sun_rho = self.sun.rECEF[:,idx0:idxf+1] - self.rsiteECEF
        # sun_sez = ecef2sez(sun_rho, self.location.lat, self.location.lon)
        # sun_rng = np.linalg.norm(sun_sez, axis=0)
        # sun_el = np.arcsin(sun_sez[2] / sun_rng) * RAD2DEG
        # site_in_sunset = sun_el - sunset_el < 0
        # site_in_sunset_idx = np.nonzero(site_in_sunset)[0]


    def __repr__(self):
        deg = u'\N{DEGREE SIGN}'
        s = '<Location '
        if self.name:
            s += self.name + ' '
        s += f'({self.latitude_deg}{deg} , {self.longitude_deg}{deg})'
        s += '>'
        return s


