import datetime
import logging
import pickle
import logging
from typing import List, Optional

from starlette.routing import Route
from starlette.responses import JSONResponse

from app.astrodynamics import (
    predict_all_visible_satellite_overpasses,
    predict_single_satellite_overpasses)
from app.schemas import Location, Overpass
from app.resources import cache, db
from app.settings import CORS_ORIGINS, MAX_DAYS
from app.resources import templates

logger = logging.getLogger(__name__)


def get_passes(request):
    """
    Render template for satellite passes for one satellite
    """
    satid = request.path_params.get('satid')
    location_name = request.query_params.get('name')
    satellite_name = request.query_params.get('satname')
    lat = request.query_params.get('lat')
    lon = request.query_params.get('lon')
    h = request.query_params.get('h', 0.0)
    days = request.query_params.get('days', MAX_DAYS)
    context = {
        'request': request,
        'satid': satid,
        'location_name': location_name,
        'satellite_name': satellite_name,
        'lat': lat,
        'lon': lon,
        'h': h,
        'days': days,
    }
    return templates.TemplateResponse('passes.html', context)


routes = [
    Route('/{satid:int}', get_passes, name='get_passes'),
]