import asyncio
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from typing import TypedDict

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncEngine, AsyncSession

from api.settings import config
from api import satellites
from api import passes
from api import home


class State(TypedDict):
    ReadSession: async_sessionmaker[AsyncSession]
    WriteSession: async_sessionmaker


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[State]:
    from api.logging import init_logging
    from api.db.session import ReadSession, WriteSession

    init_logging(__name__)

    state = {
        "ReadSession": ReadSession,
        "WriteSession": WriteSession,
    }
    yield state
    read_engine: AsyncEngine = ReadSession.kw["bind"]
    write_engine: AsyncEngine = WriteSession.kw["bind"]
    await asyncio.gather(read_engine.dispose(), write_engine.dispose())


app = FastAPI(
    debug=config.debug,
    version="2.0.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory=config.static_dir), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(satellites.v1_router, prefix="/api")
app.include_router(passes.v1_router, prefix="/api")
app.add_api_route(
    "/",
    home.home_page,
    methods=["GET"],
    response_class=HTMLResponse,
    include_in_schema=False,
)

