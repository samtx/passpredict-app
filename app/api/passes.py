import datetime
import logging
import pickle
import logging
from astrodynamics.sources import AsyncPasspredictTLESource

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from databases import Database
from aioredis import Redis
from sqlalchemy import select

from astrodynamics import (
    predict_single_satellite_overpasses,
    predict_next_overpass,
    Location,
)

from app import settings
from app.utils import get_satellite_norad_ids
from .serializers import (
    single_satellite_overpass_result_serializer,
    satellite_pass_detail_serializer,
)
from .schemas import Satellite, SingleSatOverpassResult, Overpass
from .tle import PasspredictTLESource


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/passes"
)


SATELLITE_DB = {s.id: s for s in get_satellite_norad_ids()}


def get_db(request: Request):
    return request.app.state.db


def get_cache(request: Request):
    return request.app.state.cache


async def set_cache_with_pickle(cache, key, value, ttl=None):
    """
    Add value to cache with ttl. To be used as Background task
    """
    pickled_value = pickle.dumps(value)
    await cache.set(key, pickled_value, ex=ttl)


@router.get(
    '/',
    response_model=SingleSatOverpassResult,
    response_model_exclude_unset=True,
)
async def get_passes(
    background_tasks: BackgroundTasks,
    satid: int,
    lat: float,
    lon: float,
    h: float = 0.0,
    days: int = settings.MAX_DAYS,
    db: Database = Depends(get_db),
    cache: Redis = Depends(get_cache),
):
    logger.info(f'route api/passes/{satid},lat={lat},lon={lon},h={h},days={days}')
    # Create cache key
    today = datetime.datetime.now(datetime.timezone.utc)
    main_key = f'passes:{satid}:lat{lat}:lon{lon}:h{h}:days{days}:start{today.strftime("%Y%m%d")}'
    # Check cache
    result = await cache.get(main_key)
    if result:
        data = pickle.loads(result)
    else:
        tle_source = PasspredictTLESource(db, cache)
        location = Location(
            name="",
            latitude_deg=lat,
            longitude_deg=lon,
            elevation_m=h
        )
        # Get TLE data for satellite
        tle = await tle_source.get_predictor(satid, today)

        overpass_result = await run_in_threadpool(
            predict_single_satellite_overpasses,
            tle,
            location,
            date_start=today,
            days=days,
            min_elevation=10.0,
        )
        # Query satellite data
        satellite = SATELLITE_DB.get(satid)

        data = single_satellite_overpass_result_serializer(location, satellite, overpass_result)
        # cache results for 30 minutes
        # maybe put this in a background task to do after returning response
        background_tasks.add_task(set_cache_with_pickle, cache, main_key, data, ttl=12)
        # await cache.set(main_key, pickle.dumps(data), ex=12)
    return data

@router.get(
    '/detail/',
    response_model=Overpass,
    response_model_exclude_unset=True,
)
async def get_pass_detail(
    satid: int,
    aosdt: datetime.datetime,
    lat: float,
    lon: float,
    h: float = 0.0,
    db: Database = Depends(get_db),
    cache: Redis = Depends(get_cache),
):
    logger.info(f'route api/passes/detail/, satid={satid},lat={lat},lon={lon},h={h},aosdt={aosdt}')
    data = await _get_pass_detail(satid, aosdt, lat, lon, h, db, cache)
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
    overpass_result = await run_in_threadpool(
        predict_next_overpass,
        predictor,
        location,
        date_start=aos_dt,
        min_elevation=10.0,
    )
    satellite = Satellite(id=satid)
    data = satellite_pass_detail_serializer(location, satellite, overpass_result)
    return data