# Write the benchmarking functions here.
# See "Writing benchmarks" in the asv docs for more information.
import datetime

import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.time import Time

# breakpoint()
import os, sys
print(sys.path)
from app.predictions import predict, find_overpasses, compute_sun_data, compute_satellite_data
from app.overpass import (
    compute_single_satellite_overpasses,
    predict_single_satellite_overpasses, 
    predict_all_visible_satellite_overpasses
)
from app.schemas import Location, Satellite, Tle, Point, Overpass
from app.models import SpaceObject, RhoVector, Sun, Sat, SatPredictData
from app.timefn import julian_date_array_from_date

class Predict:
    """
    An example benchmark that times the performance of various kinds
    of iterating over dictionaries in Python.
    """

    # SECONDS_PER_DAY = 3600*24*7

    params = [1, 5, 10, 20, 30, 60, 120]
    param_names = ['dt_seconds']

    def setup(self, dt_seconds, *args):
        satellite = Satellite(id=25544, name='ISS')
        location = Location(lat=30.2711, lon=-97.7434, h=0, name='Austin, Texas')
        tle1 = '1 25544U 98067A   20196.51422950 -.00000046  00000-0  72206-5 0  9999'
        tle2 = '2 25544  51.6443 213.2207 0001423 114.8006 342.8278 15.49514729236251'    
        tle = Tle.from_string(tle1, tle2)
        location = Location(lat=32.1234, lon=-97.9876)
        date_start = datetime.date(2020, 7, 14)
        date_end = date_start + datetime.timedelta(days=14)
        self.location = location
        # self.sat = {}
        # self.jd = {}
        # self.sun = {}
        # for dt in dt_seconds:
        jd = julian_date_array_from_date(date_start, date_end, dt_seconds)
        t = Time(jd, format='jd')
        sun = compute_sun_data(t)
        sat = compute_satellite_data(tle, t, sun)
        self.sat = sat
        self.jd = t.jd
        self.sun = sun
        
        
    def time_compute_single_satellite_overpasses(self, dt):
        compute_single_satellite_overpasses(
            self.sat[dt],
            jd=self.jd[dt],
            # sun_rECEF=self.sun[dt],
            location=self.location,
            min_elevation=10,
            visible_only=False,
            store_sat_id=False,
        )


    def peakmem_compute_single_satellite_overpasses(self, dt):
        compute_single_satellite_overpasses(
            self.sat[dt],
            jd=self.jd[dt],
            sun_rECEF=self.sun[dt],
            location=self.location,
            min_elevation=10,
            visible_only=False,
            store_sat_id=False,
        )

# class RhoVectorBenchmark:

#     def setup(self):
#         satellite = Satellite(id=25544, name='ISS')
#         location = Location(lat=30.2711, lon=-97.7434, h=0, name='Austin, Texas')
#         dt_seconds = 1.0
#         tle1 = '1 25544U 98067A   20196.51422950 -.00000046  00000-0  72206-5 0  9999'
#         tle2 = '2 25544  51.6443 213.2207 0001423 114.8006 342.8278 15.49514729236251'    
#         tle = Tle.from_string(tle1, tle2)
#         dt_seconds = 10
#         location = Location(lat=32.1234, lon=-97.9876)
#         date_start = datetime.date(2020, 7, 14)
#         date_end = date_start + datetime.timedelta(days=14)
#         jd = julian_date_array_from_date(date_start, date_end, dt_seconds)
#         t = Time(jd, format='jd')
#         sun = compute_sun_data(t)
#         sat = compute_satellite_data(tle, t, sun)
#         self.location = location
#         self.sat = sat
#         self.t = t
#         self.sun = sun
#         self.rho = RhoVector(t, sat, location, sun)
#         self.min_elevation = 10
#         self.rho_el = self.rho._el()

#     def time_start_end_index_elevation(self):
#         self.rho._start_end_index(self.rho.el - self.min_elevation)

#     def time_start_end_index(self):
#         self.rho._start_end_index(self.rho_el - self.min_elevation)

