# Write the benchmarking functions here.
# See "Writing benchmarks" in the asv docs for more information.
import datetime
import sys

from app.propagate import compute_satellite_data
from app.schemas import Tle
from app.timefn import julian_date_array_from_date
from app._solar import sun_pos_ecef


class Propagate:
    """
    An example benchmark that times the performance of various kinds
    of iterating over dictionaries in Python.
    """

    params = [1, 5, 10, 20, 30, 60, 120]
    # params = [120]
    param_names = ['dt_seconds']

    def setup(self, dt_seconds, *args):
        tle1 = '1 25544U 98067A   20196.51422950 -.00000046  00000-0  72206-5 0  9999'
        tle2 = '2 25544  51.6443 213.2207 0001423 114.8006 342.8278 15.49514729236251'    
        tle = Tle.from_string(tle1, tle2)
        date_start = datetime.date(2020, 7, 14)
        date_end = date_start + datetime.timedelta(days=14)
        jd = julian_date_array_from_date(date_start, date_end, dt_seconds)
        sun_rECEF = sun_pos_ecef(jd)
        self.jd = jd
        self.tle = tle
        self.sun_rECEF = sun_rECEF

    def time_compute_satellite_data(self, dt):
        compute_satellite_data(
            self.tle,
            self.jd,
            self.sun_rECEF
        )

    def peakmem_compute_satellite_data(self, dt):
        compute_satellite_data(
            self.tle,
            self.jd,
            self.sun_rECEF
        )

    def track_sat_cache_data_kilobytes(self, dt):
        sat = compute_satellite_data(
            self.tle,
            self.jd,
            self.sun_rECEF
        )
        nbytes = sat.rECEF.nbytes
        nbytes += sat.sun_sat_dist.nbytes
        nbytes += sys.getsizeof(sat.intrinsic_mag)
        nkilobytes = nbytes/1000
        return nkilobytes
