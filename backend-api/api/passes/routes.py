from datetime import datetime, UTC, timedelta
import logging
from typing import Annotated
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, Request, Query
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from api.settings import config
from api import domain
from api.satellites import service as satellite_service
from . import schemas
from . import service


logger = logging.getLogger(__name__)


v1_router = APIRouter(
    prefix="/v1/passes",
    tags=["passes"],
)


async def get_read_session(request: Request) -> AsyncIterator[AsyncSession]:
    ReadSession: async_sessionmaker[AsyncSession] = request.state.ReadSession
    async with ReadSession() as session:
        yield session


@v1_router.get(
    '',
    response_model=schemas.OverpassResult,
    response_model_exclude_unset=True,
)
async def get_passes(
    params: Annotated[schemas.OverpassQuery, Depends()],
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
    overpasses = await run_in_threadpool(
        service.compute_passes,
        satellites=satellites,
        location=location,
        start=start,
        end=end,
    )
    result = {
        "location": location,
        "satellites": satellites,
        "overpasses": overpasses,
        "start": start,
        "end": end,
    }
    return result
