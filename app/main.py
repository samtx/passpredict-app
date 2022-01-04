# main.py
import logging
from urllib.parse import urlencode
from functools import cache as functools_cache

from starlette.applications import Starlette
from starlette.responses import RedirectResponse
from starlette.requests import Request
from starlette.routing import Route, Mount
from starlette.status import HTTP_302_FOUND

from app.utils import get_satellite_norad_ids
from app.resources import cache, db, templates, static_app
from app import settings
from app import passes
from . import api


logging.basicConfig(
    filename='app.log',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def home(request: Request):
    if request.method == 'POST':
        form = await request.form()
        satid = form.get('satid')
        lat = form.get('lat')
        lon = form.get('lon')
        location_name = form.get('name')
        h = form.get('h')
        sat_name = form.get('satname')
        url = request.url_for('passes:get_passes')
        params = urlencode({
            'satid': satid,
            'lat': lat,
            'lon': lon,
            'name': location_name,
            'satname': sat_name,
        })
        url += '?' + params
        response = RedirectResponse(url, status_code=HTTP_302_FOUND)
        return response
    logger.info(f'route /')
    satellites = _satellite_db()
    context = {
        'request': request,
        'satellites': satellites,
        'ignore_navbar_brand': True,
    }
    response = templates.TemplateResponse('home.html', context)
    return response


@functools_cache
def _satellite_db():
    satellites = get_satellite_norad_ids()
    db = [sat._asdict() for sat in satellites]
    return db


async def about(request: Request):
    logger.info(f'route /about')
    return templates.TemplateResponse('about.html', {'request': request})


async def help(request: Request):
    logger.info(f'route /help')
    return templates.TemplateResponse('help.html', {'request': request})


async def connect_to_db_and_cache():
    try:
        ping = await app.state.cache.ping()
        if not ping:
            raise
    except:
        raise Exception("Can't connect to redis instance")
    try:
        await app.state.db.connect()
    except:
        raise Exception("Can't connect to postgres database")


async def disconnect_from_db_and_cache():
    await app.state.cache.close()
    await app.state.db.disconnect()


routes = [
    Route('/', home, name='home', methods=['GET', 'POST']),
    Route('/about', about, name='about'),
    Route('/help', help, name='help'),
    Mount('/passes', routes=passes.routes, name='passes'),
    Mount('/api', app=api.app, name='api'),
    Mount('/static', app=static_app, name='static'),
]


app = Starlette(
    debug=settings.DEBUG,
    routes=routes,
    on_startup=[connect_to_db_and_cache],
    on_shutdown=[disconnect_from_db_and_cache],
)


# attach database and cache connections onto application state
app.state.db = db
app.state.cache = cache
api.app.state.db = db
api.app.state.cache = cache