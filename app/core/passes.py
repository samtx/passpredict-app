import datetime

from databases import Database
from aioredis import Redis
from starlette.concurrency import run_in_threadpool

from astrodynamics import (
    predict_single_satellite_overpasses,
    predict_next_overpass,
    get_next_pass_detail,
    Location,
)
from app.utils import get_satellite_norad_ids
from .schemas import Satellite, SatelliteDetail, OverpassDetail
from .serializers import (
    satellite_pass_detail_serializer,
    single_satellite_overpass_result_serializer,
)
from .tle import PasspredictTLESource


SATELLITE_DB = {s.id: s for s in get_satellite_norad_ids()}


async def _get_passes(
    satid: int,
    lat: float,
    lon: float,
    h: float,
    start_date: datetime.datetime,
    days: int,
    db: Database,
    cache: Redis,
):
    tle_source = PasspredictTLESource(db, cache)
    location = Location(
        name="",
        latitude_deg=lat,
        longitude_deg=lon,
        elevation_m=h
    )
    # Get TLE data for satellite
    tle = await tle_source.get_predictor(satid, start_date)

    overpass_result = await run_in_threadpool(
        predict_single_satellite_overpasses,
        tle,
        location,
        date_start=start_date,
        days=days,
        min_elevation=10.0,
    )
    # Query satellite data
    satellite = SATELLITE_DB.get(satid)
    data = single_satellite_overpass_result_serializer(location, satellite, overpass_result)
    return data


async def _get_pass_detail(
    satid: int,
    aosdt: datetime.datetime,
    lat: float,
    lon: float,
    h: float,
    db: Database,
    cache: Redis,
):
    # Create cache key
    location = Location(
        name="",
        latitude_deg=lat,
        longitude_deg=lon,
        elevation_m=h
    )
    # Get TLE data for satellite
    tle_source = PasspredictTLESource(db, cache)
    predictor = await tle_source.get_predictor(satid, aosdt)
    aos_dt = aosdt - datetime.timedelta(minutes=10)
    pass_detail, llh = await run_in_threadpool(
        get_next_pass_detail,
        predictor,
        location,
        date_start=aos_dt,
        min_elevation=10.0,
    )
    satellite = SatelliteDetail(
        id=satid,
        latitude=llh.latitude.tolist(),
        longitude=llh.longitude.tolist(),
        altitude=llh.altitude.tolist(),
        datetime=llh.datetime
    )
    data = satellite_pass_detail_serializer(location, satellite, pass_detail)
    return data


def get_visibility_circle(
    lat: float,
    lon: float,
    h: float,    # location elevation above ellipsoid [m]
    alt: float,  # satellite altitude [km]
):
    """ Compute visibility circle around satellite at location with satellite altitude """
    pass