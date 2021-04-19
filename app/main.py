# main.py
import atexit
import datetime
import logging
import pickle
from typing import List, Optional

from flask import Flask, flash, redirect, render_template, request, url_for
from app.resources import cache, db
from app.passes.routes import passes


logging.basicConfig(
    filename='app.log',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.register_blueprint(passes, url_prefix='/passes')


@app.route('/')
def home():
    logger.info(f'route /')
    return {"msg": "Hello from the home page"}


# @atexit.register
# def shutdown():
#     close_db()
