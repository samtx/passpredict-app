import logging

from starlette.routing import Route

from app.settings import MAX_DAYS
from app.resources import templates
from app.api.schemas import Location, Satellite

logger = logging.getLogger(__name__)


def get_passes(request):
    """
    Render template for satellite passes for one satellite
    """
    satid = request.query_params.get('satid')
    location_name = request.query_params.get('name')
    satellite_name = request.query_params.get('satname')
    lat = request.query_params.get('lat')
    lon = request.query_params.get('lon')
    h = request.query_params.get('h', 0.0)
    location = Location(lat=lat, lon=lon, h=h, name=location_name)
    satellite = Satellite(id=satid, name=satellite_name)
    days = request.query_params.get('days', MAX_DAYS)
    context = {
        'request': request,
        'satellite': satellite,
        'location': location,
        'days': days,
    }
    return templates.TemplateResponse('passes.html', context)


routes = [
    Route('/', get_passes, name='get_passes'),
]