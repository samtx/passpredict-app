# main.py
import atexit
import datetime
import logging
import pickle
from typing import List, Optional

from flask import (
    Flask, flash, redirect, render_template,
    request, url_for, make_response
)
from app.tle import get_satellite_norad_ids
from app.resources import cache, db
from app.passes.routes import passes
from app.api.routes import api


logging.basicConfig(
    filename='app.log',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.register_blueprint(passes, url_prefix='/passes')
app.register_blueprint(api, url_prefix='/api')


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        satid = request.form.get('satid')
        lat = request.form.get('lat')
        lon = request.form.get('lon')
        url = url_for('passes.get_passes', satid=satid, lat=lat, lon=lon)
        return redirect(url)
    logger.info(f'route /')
    satellites = get_satellite_norad_ids()
    return render_template('home.html', satellites=satellites)


@app.route('/about', methods=['GET'])
def about():
    logger.info(f'route /about')
    return render_template('about.html')


# @atexit.register
# def shutdown():
#     close_db()
