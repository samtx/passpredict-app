import datetime

from orbit_predictor.locations import Location

from .predictors import SatellitePredictor


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
    predictor: SatellitePredictor,
    location: Location,
    date_start: datetime.date,
    days: int,
    min_elevation: float
):
    date_end = date_start + datetime.timedelta(days=days)
    pass_iterator = predictor.passes_over(
        location, when_utc=date_start, limit_date=date_end,
        aos_at_dg=min_elevation, tolerance_s=1.0
    )
    passes = list(pass_iterator)
    return passes
