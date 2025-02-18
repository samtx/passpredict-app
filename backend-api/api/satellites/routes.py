from datetime import date, datetime
import logging
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.ext.asyncio import AsyncConnection

from api.db.engine import read_conn, write_conn
from .services import SatelliteService


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="satellites",
)


class SatelliteDimensions(BaseModel):
    mass: float | None = Field(default=None, description="Mass in kilograms")
    length: float | None = Field(default=None, description="Length in meters")
    diameter: float | None = Field(default=None, description="Diameter in meters")
    span: float | None = Field(default=None, description="Span in meters")


class Satellite(BaseModel):
    model_config = ConfigDict(title="Satellite")

    norad_id: int
    intl_designator: str
    name: str
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    decayed_date: date | None = None
    launch_date: date | None = None
    dimensions: SatelliteDimensions | None = None


async def get_read_conn() -> AsyncConnection:
    return read_conn


async def get_write_conn() -> AsyncConnection:
    return write_conn


async def get_satellite_service(
    read_conn: Annotated[AsyncConnection, Depends(get_read_conn)],
    write_conn: Annotated[AsyncConnection, Depends(get_write_conn)],
) -> SatelliteService:
    service = SatelliteService(read_conn=read_conn, write_conn=write_conn)
    return service


@router.post(
    '',
    response_model=Satellite,
    response_model_exclude_unset=True,
)
async def insert_satellite(
    satellite: Satellite,
    service: Annotated[SatelliteService, Depends(get_satellite_service)],
):
    """Insert new satellite"""
    result = await service.insert_satellite(satellite)
    return result


class SatelliteQuery(BaseModel):
    norad_ids: list[int] = Field(alias="norad_id", default_factory=list)
    intl_designators: list[str] = Field(alias="intl_designator", default_factory=list)
    names:list[str] = Field(alias="name", default_factory=list)
    launch_date: date = Field(default=None, description="Search for satellites launched on this date")
    launch_date_before: date = Field(default=None, description="Search for satellites launched on or after this date")
    launch_date_after: date = Field(default=None, description="Search for satellites launched on or before this date")
    decay_date: date = Field(default=None, description="Search for satellites decayed on this date")
    decay_date_before: date = Field(default=None, description="Search for satellites decayed on or before this date")
    decay_date_after: date = Field(default=None, description="Search for satellites decayed on or after this date")
    q: str | None = Field(default=None, description="full text search query")
    page_size: int | None = Field(default=None, gt=0)
    cursor: str | None = None


class SatelliteQueryResponse(BaseModel):
    satellites: list[Satellite]
    page_size: int
    next_cursor: str | None = None


@router.get(
    '',
    response_model=SatelliteQueryResponse,
    response_model_exclude_unset=True,
)
async def query_satellites(
    params: Annotated[SatelliteQuery, Query()],
    service: Annotated[SatelliteService, Depends(get_satellite_service)],
):
    result = await service.query_satellites(params)
    return result


@router.get(
    '/{norad_id}',
    response_model=Satellite,
    response_model_exclude_unset=True,
)
async def get_satellite(
    norad_id: int,
    service: Annotated[SatelliteService, Depends(get_satellite_service)],
):
    satellite = await service.get_satellite(norad_id)
    return satellite


class OrbitQueryRequest(BaseModel):
    ids: list[UUID] = Field(alias="id", default_factory=list)
    norad_ids: list[int] = Field(alias="norad_id", default_factory=list)
    epoch_after: datetime | None = Field(default=None)
    epoch_before: datetime | None = Field(default=None)
    # originators: list[Literal['spacetrack', 'celestrak']] = Field(alias="originator", default_factory=list)
    created_after: datetime | None = Field(default=None)
    created_before: datetime | None = Field(default=None)
    page_size: int | None = Field(default=None, gt=0)
    cursor: str | None = None


class SatelliteOrbit(BaseModel):
    id: UUID
    norad_id: int
    epoch: datetime
    tle: str | None = Field(None, description="Two line element set")
    creation_date: datetime | None = None
    originator: str | None = None
    ref_frame: str | None = None
    time_system: str | None = None
    mean_element_theory: str | None = None
    mean_motion: float | None = None
    eccentricity: float | None = None
    ra_of_asc_node: float | None = None
    arg_of_pericenter: float | None = None
    mean_anomaly: float | None = None
    gm: float | None = None
    ephemeris_type: Literal[0, "SGP", "SGP4", "SDP4", "SGP8", "SDP8"] | None = None
    element_set_no: int | None = None
    rev_at_epoch: int | None = None
    bstar: float | None = None
    mean_motion_dot: float | None = None
    mean_motion_ddot: float | None = None
    perigee: float = Field(description="Orbit perigee in kilometers")
    apogee: float = Field(description="Orbit apogee in kilometers")
    inclination: float = Field(description="Orbit inclination in degrees")


class OrbitQueryResponse(BaseModel):
    orbits: list[SatelliteOrbit]
    page_size: int
    next_cursor: str | None = None


@router.get(
    "/orbits",
    response_model=OrbitQueryResponse,
)
async def query_orbit(
    params: Annotated[OrbitQueryRequest, Query()],
    service: Annotated[SatelliteService, Depends(get_satellite_service)],
):
    result = await service.query_orbits(params)
    return result
