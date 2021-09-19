import datetime
import logging
import pickle
import logging

from starlette.routing import Route
from starlette.responses import JSONResponse
from orbit_predictor.locations import Location

from app.astrodynamics import (
    predict_all_visible_satellite_overpasses,
    predict_single_satellite_overpasses,
)
from app.resources import cache, db
from app.settings import CORS_ORIGINS, MAX_DAYS

logger = logging.getLogger(__name__)


def get_all_passes(request):
    """
    Compute passes for top 100 visible satellites for 24 hours
    """
    lat = request.query_params.get('lat')
    lon = request.query_params.get('lon')
    h = request.query_params.get('h', 0.0)
    logger.info(f'route api/passes/ lat={lat},lon={lon},h={h}')
    # Check cache with input string
    today = datetime.date.today()
    main_key = f'all_passes:lat{lat}:lon{lon}:h{h}:start{today.isoformat()}'
    result = cache.get(main_key)
    if result:
        response_data = pickle.loads(result)
    else:
        location = Location(
            name="",
            latitude_deg=lat,
            longitude_deg=lon,
            elevation_m=h
        )
        overpass_result = predict_all_visible_satellite_overpasses(
            location,
            date_start=today,
            min_elevation=10.0,
            db=db,
            cache=cache
        )
        # cache results for 30 minutes
        response_data = overpass_result.json()
        cache.set(main_key, pickle.dumps(response_data), ex=1800)
    return JSONResponse(response_data)


def get_passes(request):
    satid = request.path_params.get('satid')
    lat = request.query_params.get('lat')
    lon = request.query_params.get('lon')
    h = request.query_params.get('h', 0.0)
    days = request.query_params.get('days', MAX_DAYS)
    logger.info(f'route api/passes/{satid},lat={lat},lon={lon},h={h},days={days}')
    # Create cache key
    today = datetime.date.today()
    main_key = f'passes:{satid}:lat{lat}:lon{lon}:h{h}:days{days}:start{today.isoformat()}'
    # Check cache
    result = cache.get(main_key)
    if result:
        response_data = pickle.loads(result)
    else:
        location = Location(
            name="",
            latitude_deg=lat,
            longitude_deg=lon,
            elevation_m=h
        )
        overpass_result = predict_single_satellite_overpasses(
            satid,
            location,
            date_start=today,
            days=days,
            db=db,
            cache=cache
        )
        # cache results for 30 minutes
        response_data = overpass_result.json()
        cache.set(main_key, pickle.dumps(response_data), ex=1800)
    return JSONResponse(response_data)


routes = [
    Route('/passes', get_all_passes, name="get_all_passes"),
    Route('/passes/{satid:int}', get_passes, name="get_passes"),
]