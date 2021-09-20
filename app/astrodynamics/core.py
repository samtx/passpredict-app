import datetime

from orbit_predictor.locations import Location

from .sources import TLE


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
    tle: TLE,
    location: Location,
    date_start: datetime.date,
    days: int,
    min_elevation: float
):
    return None