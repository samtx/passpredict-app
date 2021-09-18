# main.py
import atexit
import datetime
import logging

from starlette.applications import Starlette
from starlette.staticfiles import StaticFiles
from starlette.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from starlette.requests import Request
from starlette.routing import Route, Mount

from app.tle import get_satellite_norad_ids
from app.resources import cache, db, templates
from app import passes
from app import api


logging.basicConfig(
    filename='app.log',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def home(request):
    if request.method == 'POST':
        satid = request.form.get('satid')
        lat = request.form.get('lat')
        lon = request.form.get('lon')
        url = request.url_for('passes:get_passes', satid=satid, lat=lat, lon=lon)
        return RedirectResponse(url)
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
    Route('/', home, name='home'),
    Route('/about', about, name='about'),
    Mount('/passes', routes=passes.routes, name='passes'),
    Mount('/api', routes=api.routes, name='api'),
    Mount('/static', app=StaticFiles(directory='app/static'), name='static'),
]

# @atexit.register
# def shutdown():
#     close_db()

app = Starlette(debug=True, routes=routes)
