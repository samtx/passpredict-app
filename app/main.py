# main.py
import datetime
import logging
from urllib.parse import urlencode

from starlette.applications import Starlette
from starlette.staticfiles import StaticFiles
from starlette.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from starlette.requests import Request
from starlette.routing import Route, Mount
from starlette.status import HTTP_302_FOUND

from app.tle import get_satellite_norad_ids
from app.resources import cache, db, templates
from app import settings
from app import passes
from app.api import app as api_app


logging.basicConfig(
    filename='app.log',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def home(request):
    if request.method == 'POST':
        form = await request.form()
        satid = form.get('satid')
        lat = form.get('lat')
        lon = form.get('lon')
        url = request.url_for('passes:get_passes', satid=satid)
        params = urlencode({'lat':lat, 'lon':lon})
        url += '?' + params
        response = RedirectResponse(url, status_code=HTTP_302_FOUND)
        return response
    logger.info(f'route /')
    satellites = get_satellite_norad_ids()
    context = {
        'request': request,
        'satellites': satellites,
    }
    response = templates.TemplateResponse('home.html', context)
    return response


async def about(request):
    logger.info(f'route /about')
    return templates.TemplateResponse('about.html', {'request': request})


routes = [
    Route('/', home, name='home', methods=['GET', 'POST']),
    Route('/about', about, name='about'),
    Mount('/passes', routes=passes.routes, name='passes'),
    Mount('/api', app=api_app, name='api'),
    Mount('/static', app=StaticFiles(directory='app/static'), name='static'),
]

async def connect_to_db_and_cache():
    ping = await cache.ping()
    if not ping:
        raise Exception("Can't connect to redis instance")
    await db.connect()


async def disconnect_from_db_and_cache():
    await cache.close()
    await db.disconnect()


app = Starlette(
    debug=settings.DEBUG,
    routes=routes,
    on_startup=[connect_to_db_and_cache],
    on_shutdown=[disconnect_from_db_and_cache],
)