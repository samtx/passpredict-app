import datetime
import logging
import pickle
import logging
from typing import List, Optional

from flask import (
    Blueprint, flash, redirect, render_template, request, url_for, make_response
)

from app.astrodynamics.overpass import (
    predict_all_visible_satellite_overpasses,
    predict_single_satellite_overpasses)
from app.schemas import Location, Overpass
from app.resources import cache, db
from app.settings import CORS_ORIGINS, MAX_DAYS

logger = logging.getLogger(__name__)

passes = Blueprint('passes', __name__)


@passes.route("/")
def get_all_passes():
#     lat: float = Query(..., title="Location latitude North in decimals"),
#     lon: float = Query(..., title="Location longitude East in decimals"),
#     h: float = Query(0.0, title="Location elevation above WGS84 ellipsoid in meters"),
# ):
    """
    Compute passes for top 100 visible satellites for 24 hours
    """
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    h = request.args.get('h', 0.0)
    logger.info(f'route /passes/ lat={lat},lon={lon},h={h}')
    # Check cache with input string
    today = datetime.date.today()
    main_key = f'all_passes:lat{lat}:lon{lon}:h{h}:start{today.isoformat()}'
    result = cache.get(main_key)
    if result:
        response_data = pickle.loads(result)
    else:
        location = Location(lat=lat, lon=lon, h=h)
        overpass_result = predict_all_visible_satellite_overpasses(
            location,
            date_start=today,
            min_elevation=10.0,
            db=db,
            cache=cache
        )
        # cache results for 30 minutes
        response_data = overpass_result.json()
        cache.set(main_key, pickle.dumps(response_data), ex=1800)
    response = make_response(response_data)
    response.mimetype = 'application/json'
    return response


@passes.route("/<int:satid>")
def get_passes(satid):
    # satid: int = Path(..., title="Satellite NORAD ID number"),
    # lat: float = Query(..., title="Location latitude North in decimals"),
    # lon: float = Query(..., title="Location longitude East in decimals"),
    # h: float = Query(0.0, title="Location elevation above WGS84 ellipsoid in meters"),
    # days: int = Query(10, title="Future days to predict", le=MAX_DAYS),
    # db = Depends(get_db),
    # cache = Depends(get_cache)
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    h = request.args.get('h', 0.0)
    days = request.args.get('days', 10)
    logger.info(f'route /passes/{satid},lat={lat},lon={lon},h={h},days={days}')
    # Create cache key
    today = datetime.date.today()
    main_key = f'passes:{satid}:lat{lat}:lon{lon}:h{h}:days{days}:start{today.isoformat()}'
    # Check cache
    result = cache.get(main_key)
    if result:
        response_data = pickle.loads(result)
    else:
        location = Location(lat=lat, lon=lon, h=h)
        overpass_result = predict_single_satellite_overpasses(
            satid,
            location,
            date_start=today,
            days=days,
            db=db,
            cache=cache
        )
        # cache results for 30 minutes
        response_data = overpass_result.json()
        cache.set(main_key, pickle.dumps(response_data), ex=1800)
    response = make_response(response_data)
    response.mimetype = 'application/json'
    return response
