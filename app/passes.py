from datetime import timedelta, timezone
import logging

from starlette.routing import Route

from app.settings import MAX_DAYS
from app.resources import templates
from app.api.schemas import Location, Satellite
from app.api.passes import get_single_pass

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


async def get_pass_detail(request):
    """
    Render template for pass detail
    """
    satid = request.query_params.get('satid')
    location_name = request.query_params.get('name')
    satellite_name = request.query_params.get('satname')
    aos_dt = request.query_params.get('aosdt')
    lat = request.query_params.get('lat')
    lon = request.query_params.get('lon')
    h = request.query_params.get('h', 0.0)
    location = Location(lat=lat, lon=lon, h=h, name=location_name)
    satellite = Satellite(id=satid, name=satellite_name)
    aos_dt_utc = aos_dt.astimezone(timezone.utc)
    predictedpass = await get_single_pass(satid, aos_dt_utc, lat, lon, h)
    context = {
        'request': request,
        'satellite': satellite,
        'location': location,
        'pass': predictedpass,
    }
    return templates.TemplateResponse('pass_detail.html', context)


routes = [
    Route('/', get_passes, name='get_passes'),
    Route('/detail/', get_pass_detail)
]