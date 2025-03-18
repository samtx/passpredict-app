# main.py
import logging
from urllib.parse import urlencode
from pathlib import Path
from functools import cache as functools_cache

from starlette.applications import Starlette
from starlette.responses import RedirectResponse
from starlette.requests import Request
from starlette.routing import Route, Mount
from starlette.status import HTTP_302_FOUND
import markdown

from app.utils import get_satellite_norad_ids
from app.resources import cache, db, templates, static_app
from app import settings
from app import passes
from .api import create_app as create_api_app


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


async def api_home(request: Request):
    """
    Render API homepage with explanation on how to use the API
    """
    # Get markdown content
    key = "markdown:api-home.md"
    cache = request.app.state.cache
    res = await cache.get(key)
    if not res:
        # html is not in cache, re-render it
        fpath = Path(templates.directory) / 'api-home.md'
        config = {
            'toc': {
                'permalink': True,
                'baselevel': 2,
            }
        }
        with open(fpath, 'r') as f:
            content = markdown.markdown(
                f.read(),
                extensions=['fenced_code', 'toc'],
                extension_configs=config,
            )
        await cache.set(key, content.encode('utf-8'), ex=86400)  # cache for one day
    else:
        content = res.decode('utf-8')
    context = {
        'request': request,
        'content': content,
    }
    return templates.TemplateResponse('api-home.html', context)


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


def create_app(db=db, cache=cache):
    api_app = create_api_app(db, cache)
    routes = [
        Route('/', home, name='home', methods=['GET', 'POST']),
        Route('/about', about, name='about'),
        Route('/help', help, name='help'),
        Route('/api', api_home, name='api_home'),
        Mount('/api', app=api_app, name='api'),
        Mount('/passes', routes=passes.routes, name='passes'),
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
    return app

app = create_app()
