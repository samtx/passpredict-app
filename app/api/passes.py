import datetime
import logging
import pickle
import logging

from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from app.astrodynamics import (
    predict_all_visible_satellite_overpasses,
    predict_single_satellite_overpasses,
    predict_next_overpass,
)
from app.astrodynamics import PasspredictTLESource, Location
from app.resources import cache
from app import settings
from app.api.serializers import (
    single_satellite_overpass_result_serializer,
    satellite_pass_detail_serializer,
)
from app.api.schemas import Satellite, SingleSatOverpassResult, Overpass


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/passes"
)

tle_source = PasspredictTLESource()


async def set_cache_with_pickle(key, value, ttl=None):
    """
    Add value to cache with ttl. To be used as Background task
    """
    pickled_value = pickle.dumps(value)
    await cache.set(key, pickled_value, ex=ttl)


# @router.get('/')
# async def get_all_passes(
#     lat: float,
#     lon:float,
#     h: float = 0.0,
# ):
#     """
#     Compute passes for top 100 visible satellites for 24 hours
#     """
#     logger.info(f'route api/passes/ lat={lat},lon={lon},h={h}')
#     # Check cache with input string
#     today = datetime.date.today()
#     main_key = f'all_passes:lat{lat}:lon{lon}:h{h}:start{today.isoformat()}'
#     result = await cache.get(main_key)
#     if result:
#         response_data = pickle.loads(result)
#     else:
#         location = Location(
#             name="",
#             latitude_deg=lat,
#             longitude_deg=lon,
#             elevation_m=h
#         )
#         # Get list of TLEs for visible satellites
#         tles = None

#         overpass_result = run_in_threadpool(
#             predict_all_visible_satellite_overpasses,
#             tles,
#             location,
#             date_start=today,
#             min_elevation=10.0,
#         )
#         # cache results for 30 minutes
#         response_data = overpass_result.json()
#         await cache.set(main_key, pickle.dumps(response_data), ex=1800)
#     return JSONResponse(response_data)


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
        satellite = Satellite(id=satid)
        data = single_satellite_overpass_result_serializer(location, satellite, overpass_result)
        # cache results for 30 minutes
        # maybe put this in a background task to do after returning response
        background_tasks.add_task(set_cache_with_pickle, main_key, data, ttl=12)
        # await cache.set(main_key, pickle.dumps(data), ex=12)
    return data

@router.get(
    '/detail/',
    response_model=Overpass,
    response_model_exclude_unset=True,
)
async def get_single_pass(
    satid: int,
    aosdt: datetime.datetime,
    lat: float,
    lon: float,
    h: float,
):
    logger.info(f'route api/passes/detail/, satid={satid},lat={lat},lon={lon},h={h},aosdt={aosdt}')
    # Create cache key
    location = Location(
        name="",
        latitude_deg=lat,
        longitude_deg=lon,
        elevation_m=h
    )
    # Get TLE data for satellite
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