import asyncio
from datetime import datetime, UTC, timedelta
import pickle
import logging
from typing import Annotated, cast
from collections.abc import Callable
from enum import Enum
from math import floor

from fastapi import APIRouter, BackgroundTasks, Depends, Request, Query, HTTPException
from redis.asyncio import Redis
from pydantic import BaseModel, Field, conlist, AfterValidator, conset

from api.settings import config
from api.satellites.routes import Satellite, get_satellite_service
from api.satellites.services import SatelliteService
from .services import ComputePassService


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/passes",
)


class OrdinalDirection(str, Enum):
    N = 'N'
    NNE = 'NNE'
    NE = 'NE'
    ENE = 'ENE'
    E = 'E'
    ESE = 'ESE'
    SE = 'SE'
    SSE = 'SSE'
    S = 'S'
    SSW = 'SSW'
    SW = 'SW'
    WSW = 'WSW'
    W = 'W'
    WNW = 'WNW'
    NW = 'NW'
    NNW = 'NNW'

    @staticmethod
    def _from_direction_index(n: int) -> str:
        directions = ('N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW')
        return directions[n]

    @classmethod
    def from_az(cls, az_deg: float):
        ''' Return direction from azimuth degree '''
        azm = az_deg % 360
        mod = 360/16. # number of degrees per coordinate heading
        start = 0 - mod/2
        n = floor((azm-start)/mod)
        if n == 16:
            n = 0
        ord_str = cls._from_direction_index(n)
        return cls(ord_str)


class SatelliteDetail(Satellite):
    datetime: list[datetime]
    latitude: list[float]
    longitude: list[float]
    altitude: list[float] = Field(None, description="Satellite altitude in km")


class SatelliteLatLng(BaseModel):
    satid: int
    timestamp: Annotated[list[float], Field(description="Unix timestamp in seconds in Jan 1 1970 UTC" )]
    latlng: Annotated[list[float], Field(min_items=2, max_items=2)]
    height: Annotated[float, Field(description="Average alititude of satellite [km]")] = None


class Point(BaseModel):
    datetime: datetime
    timestamp: Annotated[float, Field(description='Unix timestamp in seconds since Jan 1 1970 UTC')]
    az: Annotated[float, Field(title='Azimuth', description='azimuth [deg]')]
    az_ord: Annotated[OrdinalDirection, Field(description='Ordinal direction, eg. NE, NNW, WSW')]
    el: Annotated[float, Field(description='elevation [deg]')]
    range: Annotated[float, Field(description='range [km]')]
    dec: Annotated[float | None, Field(description='declination [deg]')] = None
    ra: Annotated[float | None, Field(description='right ascension [deg]')] = None
    brightness: Annotated[float | None, Field(description='brightness magnitude')] = None

    def __repr__(self):
        dtstr = self.datetime.strftime("%b %d %Y, %H:%M:%S")
        s = "{}UTC el={:.1f}d, az={:.1f}d, rng={:.1f}km".format(
            dtstr, self.el, self.az, self.range)
        return s


class PassType(str, Enum):
    daylight = 'daylight'
    unlit = 'unlit'
    visible = 'visible'


class Overpass(BaseModel):
    aos: Annotated[Point, Field(description='Acquisition of signal')]
    tca: Point = Field(..., description='Time of closest approach')
    los: Point = Field(..., description='Loss of signal')
    duration: float = Field(..., description='Duration of pass [sec]')
    max_elevation: float = Field(..., description='Maximum elevation [deg]')
    norad_id: int = Field(None, description='Satellite NORAD ID')
    type: PassType = None
    brightness: float = None
    vis_begin: Point = Field(None, description='Satellite visibility begins')
    vis_end: Point = Field(None, description='Satellite visibility ends')


class OverpassDetail(Overpass):
    datetime: list[datetime]
    azimuth: list[float]
    elevation: list[float]
    range: list[float]


class Location(BaseModel):
    latitude: Annotated[float, Field(description='Location latitude, \u0b00N')]
    longitude: Annotated[float, Field(description='Location longitude, \u0b00E')]
    height: Annotated[float, Field(0.0, description='Location height above WGS84 ellipsoid [m]')]


class OverpassResult(BaseModel):
    location: Location
    satellites: list[Satellite]
    overpasses: list[Overpass]
    start: datetime
    end: datetime
    page_size: int


class PassDetailResult(BaseModel):
    location: Location
    satellite: SatelliteDetail
    overpass: OverpassDetail


def round_float(n: int) -> Callable[[float], float]:
    def validator(value: float) -> float:
        return round(value, n)
    return validator


class OverpassQuery(BaseModel):
    norad_ids: Annotated[
        set[int],
        Field(min_length=1, max_length=config.predict.max_satellites, alias="norad_id", description="NORAD IDs of satellites to predict passes"),
    ]
    latitude: Annotated[
        float,
        Field(ge=-90, le=90, description="Location latitude in decimal degrees"),
        AfterValidator(round_float(6)),
    ]
    longitude: Annotated[
        float,
        Field(ge=-180, le=180, description="Location longitude in decimal degrees"),
        AfterValidator(round_float(6)),
    ]
    height: Annotated[
        float,
        Field(description="Location height in meters above WGS-84 ellipsoid"),
        AfterValidator(round_float(2)),
    ] = 0
    days: Annotated[
        float,
        Field(le=config.passes.max_days, description="Number of days to predict overpasses"),
    ] = config.passes.max_days



async def get_compute_pass_service(
    satellite_service: Annotated[SatelliteService, Depends(get_satellite_service)],
) -> ComputePassService:
    return ComputePassService(satellite_service=satellite_service)


@router.get(
    '/',
    response_model=OverpassResult,
    response_model_exclude_unset=True,
)
async def get_passes(
    params: Annotated[OverpassQuery, Depends()],
    service: Annotated[ComputePassService, Depends(get_compute_pass_service)],
    satellite_service: Annotated[SatelliteService, Depends(get_satellite_service)],
):
    start = datetime.now(UTC)
    end = start + timedelta(days=params.days)
    # Get satellite and orbit objects
    satellites = await satellite_service.query_satellite_orbit_time_range(
        norad_ids=params.norad_ids,
        start=start,
        end=end,
    )
    # Confirm we get all satellites back
    norad_ids_found = set(sat.norad_id for sat in satellites)
    norad_ids_missing = params.norad_ids - norad_ids_found
    if norad_ids_missing:
        raise HTTPException(status_code=404, detail=f"Norad IDs {norad_ids_missing} not found")
    # Confirm that all satellites have at least one orbit in time range
    for satellite in satellites:
        if not satellite.orbits:
            raise HTTPException(status_code=404, detail=f"No orbits found for satellite {satellite.name}, Norad ID {satellite.norad_id} in time range")
    # Compute passes
    passes = cast(list[Overpass], [])
    for satellite in satellites:
        satellite_passes = await asyncio.to_thread(
            service.get_passes,
            orbits=satellite.orbits,
            latitude=params.latitude,
            longitude=params.longitude,
            height=params.height,
            start=start,
            end=end,
        )
        passes.extend(satellite_passes)
    result = {
        "location": {
            "latitude": params.latitude,
            "longitude": params.longitude,
            "height": params.height,
        },
        "satellites": satellites,
        "passes": sorted(passes, key=lambda x: x.aos.datetime),
        "start": start,
        "end": end,
        "page_size": len(passes),
    }
    return result


# @router.get(
#     '/detail/',
#     response_model=PassDetailResult,
#     response_model_exclude_unset=True,
# )
# async def get_pass_detail(
#     background_tasks: BackgroundTasks,
#     satid: int,
#     aosdt: datetime.datetime,
#     lat: float,
#     lon: float,
#     h: float = 0.0,
#     db: Database = Depends(get_db),
#     cache: Redis = Depends(get_cache),
# ):
#     logger.info(f'route api/passes/detail/, satid={satid},lat={lat},lon={lon},h={h},aosdt={aosdt}')
#     # Check cache for data
#     key = f"passdetail:{satid}:aosdt{aosdt}:lat{lat}:lon{lon}:h{h}"
#     res = await cache.get(key)
#     if res:
#         data = pickle.loads(res)
#     else:
#         data = await _get_pass_detail(satid, aosdt, lat, lon, h, db, cache)
#         background_tasks.add_task(set_cache_with_pickle, cache, key, data, ttl=900)  # cache for 15 minutes
#     return data