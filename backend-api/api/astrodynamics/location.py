from datetime import datetime
from functools import cached_property
from math import degrees, radians, sin, cos

import numpy as np
from orbit_predictor import coordinate_systems
from passpredict.time import make_utc
from passpredict._time import datetime2mjd
from passpredict.solar import sun_pos_mjd
from passpredict._rotations import elevation_at_rad


class Location:

    def __init__(
        self,
        latitude_deg: float,
        longitude_deg: float,
        elevation_m: float = 0,
        name: str | None = None,
    ):
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
        position_ecef = coordinate_systems.geodetic_to_ecef(
            self.latitude_rad,
            self.longitude_rad,
            elevation_m / 1000.)
        self.recef = np.array(position_ecef)

    def dict(self) -> dict:
        d = {
            'name': self.name,
            'lat': self.lat,
            'lon': self.lon,
            'h': self.h
        }
        return d

    @property
    def lat(self) -> float:
        return self.latitude_deg

    @property
    def lon(self) -> float:
        return self.longitude_deg

    @property
    def h(self) -> float:
        return self.elevation_m

    @cached_property
    def _cached_elevation_calculation_data(self):
        """
        Cache trig values used for rotating ECEF to SEZ topocentric coordinates
        """
        sin_lat, sin_long = sin(self.latitude_rad), sin(self.longitude_rad)
        cos_lat, cos_long = cos(self.latitude_rad), cos(self.longitude_rad)
        return (cos_lat * cos_long, cos_lat * sin_long, sin_lat)

    def _sun_elevation_mjd(self, mjd: float) -> float:
        """
        Computes elevation angle of sun relative to location. Returns degrees.
        """
        sun_recef = sun_pos_mjd(mjd)
        coslatcoslon, coslatsinlon, sinlat = self._cached_elevation_calculation_data
        el = elevation_at_rad(coslatcoslon, coslatsinlon, sinlat, self.recef, sun_recef)
        return degrees(el)

    def sun_elevation(self, d: datetime) -> float:
        """
        Computes elevation angle of sun relative to location. Returns degrees.
        """
        d2 = make_utc(d)
        mjd = datetime2mjd(d2)
        return self._sun_elevation_mjd(mjd)

    def is_sunlit(self, dt: datetime) -> bool:
        """
        Computes elevation angle of sun relative to location
        Returns True if elevation > -6 degrees
        """
        el = self.sun_elevation(dt)
        return el > -6

    def _is_sunlit_mjd(self, mjd: float) -> bool:
        """
        Computes elevation angle of sun relative to location
        Returns True if elevation > -6 degrees
        """
        el = self._sun_elevation_mjd(mjd)
        return el > -6

    def __repr__(self):
        deg = u'\N{DEGREE SIGN}'
        s = '<Location '
        if self.name:
            s += self.name + ' '
        s += f'({self.latitude_deg}{deg} , {self.longitude_deg}{deg})'
        s += '>'
        return s


