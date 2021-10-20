import datetime

from .satellites import SatellitePredictor
from .observers import Observer
from .locations import Location


def predict_all_visible_satellite_overpasses(
    tles,
    location: Location,
    date_start: datetime.date,
    min_elevation: float,
):
    results = []
    for tle in tles:
        sat_results = predict_single_satellite_overpasses(
            tle, location,
            date_start=date_start,
            days=1,
            min_elevation=min_elevation
        )
        results.extend(sat_results)
    return results


def predict_single_satellite_overpasses(
    satellite: SatellitePredictor,
    location: Location,
    date_start: datetime.date,
    days: int,
    min_elevation: float
):
    date_end = date_start + datetime.timedelta(days=days)
    observer = Observer(location, satellite, aos_at_dg=min_elevation, tolerance_s=1.0)
    pass_iterator = observer.iter_passes(date_start, limit_date=date_end)
    passes = list(pass_iterator)
    return passes


def predict_next_overpass(
    satellite: SatellitePredictor,
    location: Location,
    date_start: datetime.date,
    min_elevation: float = 10.0
):
    observer = Observer(location, satellite, aos_at_dg=min_elevation, tolerance_s=1.0)
    pass_ = observer.get_next_pass(date_start)
    return pass_


def get_next_pass_detail(
    satellite: SatellitePredictor,
    location: Location,
    date_start: datetime.datetime,
    min_elevation: float = 10.0,
):
    observer = Observer(location, satellite, aos_at_dg=min_elevation, tolerance_s=1.0)
    pass_detail, llh = observer.get_next_pass_detail(date_start)
    return pass_detail, llh
