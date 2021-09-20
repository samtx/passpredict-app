import logging

from starlette.routing import Route

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