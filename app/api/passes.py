import datetime
import logging
import pickle
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Request, Query
from databases import Database
from aioredis import Redis

from app import settings
from app.core.passes import (
    _get_pass_detail,
    _get_passes,
)
from app.core.schemas import SingleSatOverpassResult, PassDetailResult
from app.core.jobs import set_cache_with_pickle


logger = logging.getLogger(__name__)

router = APIRouter()


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
    days: int = Query(settings.MAX_DAYS, gt=0, le=settings.MAX_DAYS),
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
        data = await _get_passes(satid, lat, lon, h, today, days, db, cache)
        # cache results for 30 minutes
        background_tasks.add_task(set_cache_with_pickle, cache, main_key, data, ttl=12)
        # await cache.set(main_key, pickle.dumps(data), ex=12)
    return data


@router.get(
    '/detail/',
    response_model=PassDetailResult,
    response_model_exclude_unset=True,
)
async def get_pass_detail(
    background_tasks: BackgroundTasks,
    satid: int,
    aosdt: datetime.datetime,
    lat: float,
    lon: float,
    h: float = 0.0,
    db: Database = Depends(get_db),
    cache: Redis = Depends(get_cache),
):
    logger.info(f'route api/passes/detail/, satid={satid},lat={lat},lon={lon},h={h},aosdt={aosdt}')
    # Check cache for data
    key = f"passdetail:{satid}:aosdt{aosdt}:lat{lat}:lon{lon}:h{h}"
    res = await cache.get(key)
    if res:
        data = pickle.loads(res)
    else:
        data = await _get_pass_detail(satid, aosdt, lat, lon, h, db, cache)
        background_tasks.add_task(set_cache_with_pickle, cache, key, data, ttl=900)  # cache for 15 minutes
    return data
