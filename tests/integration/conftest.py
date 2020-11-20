from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Tuple

import pytest
import numpy as np
from astropy.time import Time

from app.schemas import Location, Satellite, Tle
from app.timefn import julian_date_array_from_date
from app.propagate import compute_satellite_data
from app._solar import sun_pos_ecef
from app.overpass import DT_SECONDS

@pytest.fixture(scope='session')
def init_find_overpasses() -> Tuple['np.ndarray', 'Location', 'SunPredictData', 'SatPredictData']:
    tle1 = "1 25544U 98067A   20154.57277630  .00016717  00000-0  10270-3 0  9118"
    tle2 = "2 25544  51.6443  60.8122 0001995  12.6931 347.4269 15.49438452 29742"
    tle = Tle.from_string(tle1=tle1, tle2=tle2)
    date_start = tle.epoch.date()
    date_end = date_start + timedelta(days=10)
    jd = julian_date_array_from_date(date_start, date_end, DT_SECONDS)
    sun_rECEF = sun_pos_ecef(jd)
    sat = compute_satellite_data(tle, jd, sun_rECEF)
    location = Location(lat=32.1234, lon=-97.9876)
    return jd, location, sun_rECEF, sat


@pytest.fixture(scope='session')
def init_predict():
    satellite = Satellite(id=25544, name='ISS')
    location = Location(lat=30.2711, lon=-97.7434, h=0, name='Austin, Texas')
    date_start = datetime.now(tz=timezone.utc).date()
    date_end = date_start + timedelta(days=10)
    return location, satellite, date_start, date_end
    