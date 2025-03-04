import asyncio
from datetime import datetime, UTC, timedelta
from decimal import Decimal
import logging
from typing import Annotated, cast
from collections.abc import Callable, AsyncIterator
from enum import Enum
from math import floor

from fastapi import APIRouter, Depends, Request, Query, HTTPException
from redis.asyncio import Redis
from pydantic import BaseModel, Field, computed_field
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from api.settings import config
from api import domain
from api.satellites.routes import Satellite as SatelliteSchema
from api.satellites import service as satellite_service
from . import service



logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/passes",
    tags=["passes"],
)


class SatelliteDetail(SatelliteSchema):
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
    azimuth: Annotated[float, Field(description='azimuth [deg]')]
    elevation: Annotated[float, Field(description='elevation [deg]')]
    range: Annotated[float, Field(description='range [km]')]
    brightness: Annotated[float | None, Field(description='brightness magnitude')] = None

    def __repr__(self):
        dtstr = self.datetime.strftime("%b %d %Y, %H:%M:%S")
        s = "{}UTC el={:.1f}d, az={:.1f}d, rng={:.1f}km".format(
            dtstr, self.elevation, self.azimuth, self.range)
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
    satellites: list[SatelliteSchema]
    overpasses: list[Overpass]
    start: datetime
    end: datetime

    @computed_field
    @property
    def page_size(self) -> int:
        return len(self.overpasses)


class PassDetailResult(BaseModel):
    location: Location
    satellite: SatelliteDetail
    overpass: OverpassDetail


def round_float(n: int) -> Callable[[float], float]:
    def validator(value: float) -> float:
        return round(value, n)
    return validator


class OverpassQuery:

    def __init__(
        self,
        norad_ids: Annotated[
            set[int],
            Query(min_length=1, max_length=config.predict.max_satellites, alias="norad_id", description="NORAD IDs of satellites to predict passes"),
        ],
        latitude: Annotated[
            Decimal,
            Query(ge=-90, le=90, decimal_places=6, description="Location latitude in decimal degrees"),
        ],
        longitude: Annotated[
            Decimal,
            Query(ge=-180, le=180, decimal_places=6, description="Location longitude in decimal degrees"),
        ],
        height: Annotated[
            Decimal,
            Query(decimal_places=2, description="Location height in meters above WGS-84 ellipsoid"),
        ] = 0,
        days: Annotated[
            float,
            Query(le=config.predict.max_days, description="Number of days to predict overpasses"),
        ] = config.predict.max_days,
    ):
        self.norad_ids = norad_ids
        self.latitude = float(latitude)
        self.longitude = float(longitude)
        self.height = float(height)
        self.days = days


async def get_read_session(request: Request) -> AsyncIterator[AsyncSession]:
    ReadSession: async_sessionmaker[AsyncSession] = request.state.ReadSession
    async with ReadSession() as session:
        yield session


@router.get(
    '',
    response_model=OverpassResult,
    response_model_exclude_unset=True,
)
async def get_passes(
    params: Annotated[OverpassQuery, Depends()],
    db_session: Annotated[AsyncSession, Depends(get_read_session)],
):
    # Get satellite and orbit objects
    satellites = await satellite_service.query_latest_satellite_orbit(
        db_session=db_session,
        norad_ids=params.norad_ids,
    )
    # TODO: Emit warning if orbit epoch is greater than 7 days old

    # Compute passes
    start = datetime.now(UTC)
    end = start + timedelta(days=params.days)
    location = domain.Location(
        latitude=params.latitude,
        longitude=params.longitude,
        height=params.height,
    )
    overpasses = await asyncio.to_thread(
        service.compute_passes,
        satellites=satellites,
        location=location,
        start=start,
        end=end,
    )
    overpasses.sort(key=lambda op: op.aos.datetime)
    result = {
        "location": {
            "latitude": params.latitude,
            "longitude": params.longitude,
            "height": params.height,
        },
        "satellites": satellites,
        "overpasses": overpasses,
        "start": start,
        "end": end,
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