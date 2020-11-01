# main.py
import datetime
from typing import List, Optional
import pickle
import os
from itertools import zip_longest

from fastapi import FastAPI, Query, Path
from astropy.time import Time
import numpy as np
from pydantic import BaseModel

from .predictions import find_overpasses
from .propagate import compute_satellite_data
from .solar import compute_sun_data
from .timefn import julian_date_array_from_date
from .schemas import Location, Satellite, Overpass
from .tle import get_TLE
from .models import SatPredictData, SunPredictData
from .overpass import predict_all_visible_satellite_overpasses, predict_single_satellite_overpasses
from .cache import cache
from .settings import MAX_DAYS

app = FastAPI()

class OverpassResult(BaseModel):
    location: Location
    overpasses: List[Overpass]
    satid: Optional[int] = None


@app.get('/hello/')
def read_root():
    return {"msg": "Hello World"}


@app.get("/passes/", response_model=OverpassResult, response_model_exclude_unset=True)
def all_passes(
    lat: float = Query(..., title="Location latitude North in decimals"),
    lon: float = Query(..., title="Location longitude East in decimals"),
    h: float = Query(0.0, title="Location elevation above WGS84 ellipsoid in meters"),
):
    """
    Compute passes for top 100 visible satellites for 24 hours
    """
    # Check cache with input string
    today = datetime.date.today()
    main_key = f'all_passes:lat{lat}:lon{lon}:h{h}:start{today.isoformat()}'
    result = cache.get(main_key)
    if result:
        overpass_result = pickle.loads(result)
        return overpass_result
    overpass_result = predict_all_visible_satellite_overpasses(
        lat,
        lon, 
        date_start=today, 
        h=h, 
        min_elevation=10.0
    )
    # cache results for 5 minutes
    cache.set(main_key, pickle.dumps(overpass_result), ex=300)
    return overpass_result


@app.get("/passes/{satid}", response_model=OverpassResult, response_model_exclude_unset=True)
def passes(
    satid: int = Path(..., title="Satellite NORAD ID number"),
    lat: float = Query(..., title="Location latitude North in decimals"),
    lon: float = Query(..., title="Location longitude East in decimals"),
    h: float = Query(0.0, title="Location elevation above WGS84 ellipsoid in meters"),
    days: int = Query(10, title="Future days to predict", le=MAX_DAYS)
):
    # Create cache key
    today = datetime.date.today()
    main_key = f'passes:{satid}:lat{lat}:lon{lon}:h{h}:days{days}:start{today.isoformat()}'
    # Check cache
    result = cache.get(main_key)
    if result:
        overpass_result = pickle.loads(result)
        return overpass_result
    overpass_result = predict_single_satellite_overpasses(satid, lat, lon, date_start=today, days=days, h=h)
    # cache results for 5 minutes
    cache.set(main_key, pickle.dumps(overpass_result), ex=300)  
    return overpass_result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level='debug')
