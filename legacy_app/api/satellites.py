
import datetime
import logging
import pickle
import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Request, Query
from fastapi.exceptions import HTTPException
from databases import Database
from aioredis import Redis

from app.core.satellites import (
    _get_satellite_latlng
)
from app.core.schemas import SatelliteLatLng
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
    '/latlng/',
    response_model=SatelliteLatLng,
    response_model_exclude_unset=True,
)
async def get_satellite_latlng(
    background_tasks: BackgroundTasks,
    satid: int,
    aosdt: datetime.datetime,
    losdt: Optional[datetime.datetime] = None,
    dtsec: Optional[float] = Query(1, gt=0),
    db: Database = Depends(get_db),
    cache: Redis = Depends(get_cache),
):
    logger.info(f'route api/satellite/latlng, satid={satid},aosdt={aosdt},losdt={losdt},dtsec={dtsec}')
    if losdt and (aosdt > losdt):
        raise HTTPException(status_code=422, detail="losdt must come after aosdt")
    # Check cache for data
    key = f"satellite:latlng:{satid}:aosdt{aosdt}:losdt{losdt}:dtsec{dtsec}"
    res = await cache.get(key)
    if res:
        data = pickle.loads(res)
    else:
        data = await _get_satellite_latlng(satid, aosdt, losdt, dtsec, db, cache)
        background_tasks.add_task(set_cache_with_pickle, cache, key, data, ttl=900)  # cache for 15 minutes
    return data