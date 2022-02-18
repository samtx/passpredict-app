import datetime

from databases import Database
from aioredis import Redis
from starlette.concurrency import run_in_threadpool

from app.astrodynamics import (
    get_satellite_llh,
)
from app.utils import get_satellite_norad_ids
from .schemas import SatelliteLatLng
from .serializers import satellite_latlng_serializer
from .tle import PasspredictTLESource


async def _get_satellite_latlng(
    satid: int,
    aosdt: datetime.datetime,
    losdt: datetime.datetime,
    dtsec: float,
    db: Database,
    cache: Redis,
) -> SatelliteLatLng:
    # Get TLE data for satellite
    tle_source = PasspredictTLESource(db, cache)
    predictor = await tle_source.get_predictor(satid, aosdt)
    llh = await run_in_threadpool(
        get_satellite_llh,
        predictor,
        date_start=aosdt,
        date_end=losdt,
        dt_seconds=dtsec,
    )
    data = satellite_latlng_serializer(satid, llh)
    return data