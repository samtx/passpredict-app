import datetime
import logging
import pickle
import logging
from typing import List, Optional

from starlette.routing import Route
from starlette.responses import JSONResponse

from app.astrodynamics.overpass import (
    predict_all_visible_satellite_overpasses,
    predict_single_satellite_overpasses)
from app.schemas import Location, Overpass
from app.resources import cache, db
from app.settings import CORS_ORIGINS, MAX_DAYS
from app.resources import templates

logger = logging.getLogger(__name__)


def get_all_passes(request):
    """
    Render template for all passes page
    """
    lat = request.query_params.get('lat')
    lon = request.query_params.get('lon')
    h = request.query_params.get('h', 0.0)
    logger.info(f'route /passes/ lat={lat},lon={lon},h={h}')
    # Check cache with input string
    today = datetime.date.today()
    main_key = f'all_passes:lat{lat}:lon{lon}:h{h}:start{today.isoformat()}'
    result = cache.get(main_key)
    if result:
        response_data = pickle.loads(result)
    else:
        location = Location(lat=lat, lon=lon, h=h)
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
    return JSONResponse(response_data, status_code=200)


def get_passes(request):
    """
    Render template for satellite passes for one satellite
    """
    location_name = request.query_params.get('name')
    satellite_name = request.query_params.get('satname')
    lat = request.query_params.get('lat')
    lon = request.query_params.get('lon')
    h = request.query_params.get('h', 0.0)
    days = request.query_params.get('days', MAX_DAYS)
    context = {
        'request': request,
        'location_name': location_name,
        'satellite_name': satellite_name,
        'lat': lat,
        'lon': lon,
        'h': h,
        'days': days,
    }
    return templates.TemplateResponse('passes.html', context)


routes = [
    Route('/', get_all_passes),
    Route('/{satid:int}', get_passes),
]