from datetime import datetime, timezone, timedelta

from astrodynamics import MemoryTLESource
from astrodynamics.sources import TLE
from astrodynamics import *


def main():
    db = MemoryTLESource()
    date_start = datetime(2021, 10, 4, tzinfo=timezone.utc)
    satid = 25544
    tle_lines = (
        "1 25544U 98067A   21277.86166359  .00005427  00000-0  10685-3 0  9994",
        "2 25544  51.6453 160.4350 0004170  58.5851  39.6969 15.48931550305594"
    )
    db.add_tle(satid, tle_lines, date_start)
    tle = TLE(satid, tle_lines, date_start)
    predictor = SatellitePredictor(satid)
    predictor.tle = tle
    # predictor._source = db
    predictor.set_propagator()
    location = Location("Austin", latitude_deg=30.2711, longitude_deg=-97.7437, elevation_m=0)
    date_end = date_start + timedelta(days=10)
    pass_iterator = predictor.pass_iterator(
        location, when_utc=date_start, limit_date=date_end,
        aos_at_dg=10, tolerance_s=1.0
    )
    passes = []
    for pass_ in pass_iterator:
        print(pass_)
        passes.append(pass_)
    return passes


if __name__ == "__main__":
    main()