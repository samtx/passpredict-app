# Write the benchmarking functions here.
# See "Writing benchmarks" in the asv docs for more information.
import datetime

from app.propagate import compute_satellite_data
from app.overpass import compute_single_satellite_overpasses
from app.schemas import Location, Tle
from app.timefn import julian_date_array_from_date
from app._solar import sun_pos_ecef


class Predict:
    """
    An example benchmark that times the performance of various kinds
    of iterating over dictionaries in Python.
    """

    params = [1, 5, 10, 20, 30, 60, 120]
    param_names = ['dt_seconds']

    def setup(self, dt_seconds, *args):
        location = Location(lat=30.2711, lon=-97.7434, h=0, name='Austin, Texas')
        tle1 = '1 25544U 98067A   20196.51422950 -.00000046  00000-0  72206-5 0  9999'
        tle2 = '2 25544  51.6443 213.2207 0001423 114.8006 342.8278 15.49514729236251'    
        tle = Tle.from_string(tle1, tle2)
        location = Location(lat=32.1234, lon=-97.9876)
        date_start = datetime.date(2020, 7, 14)
        date_end = date_start + datetime.timedelta(days=14)
        self.location = location
        jd = julian_date_array_from_date(date_start, date_end, dt_seconds)
        sun_rECEF = sun_pos_ecef(jd)
        sat = compute_satellite_data(tle, jd, sun_rECEF)
        self.sat = sat
        self.jd = jd
        self.sun = sun_rECEF

    def time_compute_single_satellite_overpasses(self, dt):
        compute_single_satellite_overpasses(
            self.sat,
            jd=self.jd,
            sun_rECEF=self.sun,
            location=self.location,
            min_elevation=10,
            visible_only=False,
            store_sat_id=False,
        )

    def peakmem_compute_single_satellite_overpasses(self, dt):
        compute_single_satellite_overpasses(
            self.sat,
            jd=self.jd,
            sun_rECEF=self.sun,
            location=self.location,
            min_elevation=10,
            visible_only=False,
            store_sat_id=False,
        )
