import logging
from typing import Annotated
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from . import schemas
from . import service


logger = logging.getLogger(__name__)


v1_router = APIRouter(
    prefix="/v1/satellites",
    tags=["satellites"],
)


async def get_write_session(request: Request) -> AsyncIterator[AsyncSession]:
    WriteSession: async_sessionmaker[AsyncSession] = request.state.WriteSession
    async with WriteSession.begin() as session:
        yield session


async def get_read_session(request: Request) -> AsyncIterator[AsyncSession]:
    ReadSession: async_sessionmaker[AsyncSession] = request.state.ReadSession
    async with ReadSession() as session:
        yield session



# @v1_router.post(
#     '',
#     response_model=schemas.Satellite,
#     response_model_exclude_unset=True,
# )
# async def insert_satellite(
#     satellite: schemas.Satellite,
#     db_session: Annotated[AsyncSession, Depends(get_write_session)],
# ):
#     """Insert new satellite"""
#     result = await service.insert_satellite(db_session, satellite)
#     return result


@v1_router.get(
    '',
    response_model=schemas.SatelliteQueryResponse,
    response_model_exclude_unset=True,
)
async def query_satellites(
    db_session: Annotated[AsyncSession, Depends(get_read_session)],
    satellite_filter: Annotated[schemas.SatelliteQueryFilter, Depends(schemas.SatelliteQueryFilter)],
    # q: Annotated[
    #     str | None,
    #     Query(
    #         description="Full text search query on satellite's name, intl_designator, and description"
    #     )
    # ] = None,
):
    satellites = await service.query_satellites(
        db_session=db_session,
        satellite_filter=satellite_filter,
    )
    return {
        "satellites": satellites,
        "limit": satellite_filter.limit,
        "offset": satellite_filter.offset,
    }


@v1_router.get(
    '/{satellite_id}',
    response_model=schemas.Satellite,
    response_model_exclude_unset=True,
)
async def get_satellite_by_id(
    satellite_id: int,
    db_session: Annotated[AsyncSession, Depends(get_read_session)],
):
    satellite = await service.get_satellite(db_session, satellite_id)
    return satellite


@v1_router.get(
    '/norad_id/{norad_id}',
    response_model=schemas.Satellite,
    response_model_exclude_unset=True,
)
async def get_satellite_by_norad_id(
    norad_id: int,
    db_session: Annotated[AsyncSession, Depends(get_read_session)],
):
    satellite_id = await service.get_satellite_id_from_norad_id(db_session, norad_id)
    satellite = await service.get_satellite(db_session, satellite_id)
    return satellite



# @router.get(
#     "/orbits",
#     response_model=OrbitQueryResponse,
# )
# async def query_satellite_orbits(
#     params: Annotated[OrbitQueryRequest, Query()],
#     db_session: Annotated[AsyncSession, Depends(get_read_session)],
# ):
#     result = await service.query_orbits(db_session, params)
#     return result
