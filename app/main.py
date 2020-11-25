# main.py
import datetime
from typing import List, Optional
import pickle
import logging

from fastapi import FastAPI, Query, Path, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.schemas import Location, Overpass
from app.overpass import (
    predict_all_visible_satellite_overpasses,
    predict_single_satellite_overpasses
)
from app.settings import MAX_DAYS
from app.database import engine
from app.cache import cache


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = FastAPI()

origins = ['*']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_headers=['*']
)

class OverpassResult(BaseModel):
    location: Location
    overpasses: List[Overpass]
    satid: Optional[int] = None


def get_db():
    db = engine.connect()
    try:
        yield db
    finally:
        db.close()


def get_cache():
    return cache


@app.get('/hello/')
def read_root():
    return {"msg": "Hello World"}


@app.get("/passes/", response_model=OverpassResult, response_model_exclude_unset=True)
def all_passes(
    lat: float = Query(..., title="Location latitude North in decimals"),
    lon: float = Query(..., title="Location longitude East in decimals"),
    h: float = Query(0.0, title="Location elevation above WGS84 ellipsoid in meters"),
    db = Depends(get_db),
    cache = Depends(get_cache)
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
    location = Location(lat=lat, lon=lon, h=h)
    overpass_result = predict_all_visible_satellite_overpasses(
        location,
        date_start=today, 
        min_elevation=10.0,
        db=db,
        cache=cache
    )
    # cache results for 30 minutes
    cache.set(main_key, pickle.dumps(overpass_result), ex=1800)
    return overpass_result


@app.get("/passes/{satid}", response_model=OverpassResult, response_model_exclude_unset=True)
def passes(
    satid: int = Path(..., title="Satellite NORAD ID number"),
    lat: float = Query(..., title="Location latitude North in decimals"),
    lon: float = Query(..., title="Location longitude East in decimals"),
    h: float = Query(0.0, title="Location elevation above WGS84 ellipsoid in meters"),
    days: int = Query(10, title="Future days to predict", le=MAX_DAYS),
    db = Depends(get_db),
    cache = Depends(get_cache)
):
    logger.info(f'route /passes/{satid}')
    # Create cache key
    today = datetime.date.today()
    main_key = f'passes:{satid}:lat{lat}:lon{lon}:h{h}:days{days}:start{today.isoformat()}'
    # Check cache
    result = cache.get(main_key)
    if result:
        overpass_result = pickle.loads(result)
        return overpass_result
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
    cache.set(main_key, pickle.dumps(overpass_result), ex=1800)  
    return overpass_result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level='debug')
