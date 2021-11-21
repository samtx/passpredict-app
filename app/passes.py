from datetime import date, datetime, timedelta, timezone
import logging
import urllib.parse
import typing

from starlette.routing import Route
from starlette.requests import Request
from starlette.exceptions import HTTPException
from dateutil.parser import isoparse

from app.settings import MAX_DAYS
from app.resources import templates, mapbox_tile_token
from app.core.schemas import Location, Satellite
from app.core.passes import _get_pass_detail

logger = logging.getLogger(__name__)


def get_passes(request: Request):
    """
    Render template for satellite passes for one satellite
    """
    location = _get_location_query_params(request)
    satellite = _get_satellite_query_params(request)
    days = request.query_params.get('days', MAX_DAYS)
    start_datetime = datetime.utcnow()
    start_date = date(start_datetime.year, start_datetime.month, start_datetime.day)
    end_date = start_date + timedelta(days=days)
    context = {
        'request': request,
        'satellite': satellite,
        'location': location,
        'days': days,
        'start_date': start_date,
        'end_date': end_date,
    }
    return templates.TemplateResponse('passes.html', context)


async def get_pass_detail(request):
    """
    Render template for pass detail
    """
    location = _get_location_query_params(request)
    satellite = _get_satellite_query_params(request)
    db = request.app.state.db
    cache = request.app.state.cache
    aos_dt_str = request.query_params.get('aosdt')
    aos = isoparse(aos_dt_str)  # create datetime object
    aos_dt_utc = aos.astimezone(timezone.utc)
    pass_ = await _get_pass_detail(satellite.id, aos_dt_utc, location.lat, location.lon, location.h, db, cache)
    pass_list_url = request.url_for('passes:get_passes')
    pass_list_url += '?' + urllib.parse.urlencode({
        'satid': satellite.id,
        'lat': location.lat,
        'lon': location.lon,
        'h': location.h,
        'satname': satellite.name,
        'name': location.name,
    })
    context = {
        'request': request,
        'satellite': satellite,
        'location': location,
        'pass': pass_.overpass,
        'pass_list_url': pass_list_url,
        'satellite_coordinates': [[lon, lat] for lon, lat in zip(pass_.satellite.longitude, pass_.satellite.latitude)],
        'visibility_circle': [],
        'access_token': mapbox_tile_token,
    }
    return templates.TemplateResponse('pass_detail.html', context)


def _get_location_query_params(request: Request) -> Location:
    """
    Parse request object query parameters to get location object
    """
    name = request.query_params.get('name', "")
    lat = request.query_params.get('lat')
    lon = request.query_params.get('lon')
    h = request.query_params.get('h', 0.0)
    lat, lon, h = _convert_coordinates_to_floats(lat, lon, h)
    name = name.title()
    lat = round(lat, 4)
    lon = round(lon, 4)
    h = round(h, 0)
    return Location(lat=lat, lon=lon, h=h, name=name)


def _convert_coordinates_to_floats(lat: str, lon: str, h: str) -> typing.Tuple[float, float, float]:
    """ Convert coordinates to valid floats """
    lat2 = _convert_string_number_to_float(lat)
    lon2 = _convert_string_number_to_float(lon)
    h2 = _convert_string_number_to_float(h)
    return (lat2, lon2, h2)


def _convert_string_number_to_float(x: str) -> float:
    try:
        return float(x)
    except ValueError:
        raise HTTPException(status_code=404, detail="Location coordinates not found")


def _get_satellite_query_params(request: Request) -> Satellite:
    """
    Parse request object query parameters to get satellite object
    """
    satname = request.query_params.get('satname')
    satid = request.query_params.get('satid')
    return Satellite(id=satid, name=satname)


routes = [
    Route('/', get_passes, name='get_passes'),
    Route('/detail/', get_pass_detail, name='pass_detail')
]