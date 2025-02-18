
from datetime import datetime
from collections import namedtuple
from collections.abc import Iterable
import math
from typing import Protocol
from dataclasses import dataclass

from databases import Database
from aioredis import Redis
from starlette.concurrency import run_in_threadpool

from app.astrodynamics import (
    predict_single_satellite_overpasses,
    predict_next_overpass,
    get_next_pass_detail,
    R_EARTH,
)
from app.utils import get_satellite_norad_ids
from .schemas import Satellite, SatelliteDetail, OverpassDetail
from api.satellites.services import SatelliteService
from api.satellites.domain import Orbit
from .domain import Overpass, Location
from .serializers import (
    satellite_pass_detail_serializer,
    single_satellite_overpass_result_serializer,
)
from .tle import PasspredictTLESource


SATELLITE_DB = {s.id: s for s in get_satellite_norad_ids()}

Coordinate = namedtuple('Coordinate', 'lat lon h', defaults=(0.0,))


@dataclass
class Location:
    latitude: float
    longitude: float
    height: float = 0



class ComputePassService:

    def get_passes(
        self,
        orbits: Iterable[Orbit],
        latitude: float,
        longitude: float,
        height: float,
        start: datetime,
        end: datetime,
    ) -> list[Overpass]:
        """Compute overpasses for satellites over location"""
        overpasses = []
        for orbit in orbits:


    def __str__(self) -> str:
        return "ComputePassService()"



async def _get_passes(
    satid: int,
    lat: float,
    lon: float,
    h: float,
    start_date: datetime.datetime,
    days: int,
    db: Database,
    cache: Redis,
):
    tle_source = PasspredictTLESource(db, cache)
    location = Location(
        name="",
        latitude_deg=lat,
        longitude_deg=lon,
        elevation_m=h
    )
    # Get TLE data for satellite
    tle = await tle_source.get_predictor(satid, start_date)

    overpass_result = await run_in_threadpool(
        predict_single_satellite_overpasses,
        tle,
        location,
        date_start=start_date,
        days=days,
        min_elevation=10.0,
    )
    # Query satellite data
    satellite = SATELLITE_DB.get(satid)
    data = single_satellite_overpass_result_serializer(location, satellite, overpass_result)
    return data


async def _get_pass_detail(
    satid: int,
    aosdt: datetime.datetime,
    lat: float,
    lon: float,
    h: float,
    db: Database,
    cache: Redis,
):
    # Create cache key
    location = Location(
        name="",
        latitude_deg=lat,
        longitude_deg=lon,
        elevation_m=h
    )
    # Get TLE data for satellite
    tle_source = PasspredictTLESource(db, cache)
    predictor = await tle_source.get_predictor(satid, aosdt)
    aos_dt = aosdt - datetime.timedelta(minutes=10)
    pass_detail, llh = await run_in_threadpool(
        get_next_pass_detail,
        predictor,
        location,
        date_start=aos_dt,
        min_elevation=10.0,
    )
    satellite = SatelliteDetail(
        id=satid,
        latitude=llh.latitude.tolist(),
        longitude=llh.longitude.tolist(),
        altitude=llh.altitude.tolist(),
        datetime=llh.datetime
    )
    data = satellite_pass_detail_serializer(location, satellite, pass_detail)
    return data


def get_visibility_radius(
    location: Location,
    aos_pt: Coordinate,
) -> float:
    """
    Compute direct radius from location to AOS coordinate.
    Assumes the Earth is a sphere.
    """
    theta1 = math.radians(90 - location.lat)
    theta2 = math.radians(90 - aos_pt.lat)
    phi1 = math.radians(location.lon)
    phi2 = math.radians(aos_pt.lon)
    d = R_EARTH * math.sqrt(2 - 2*(math.sin(theta1)*math.sin(theta2)*math.cos(phi1 - phi2) + math.cos(theta1)*math.cos(theta2)));
    return d