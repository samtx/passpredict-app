import asyncio
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from logging import getLogger, Formatter, StreamHandler
from logging.handlers import QueueHandler, QueueListener, RotatingFileHandler
from queue import SimpleQueue
from typing import TypedDict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncEngine, AsyncSession

from api.settings import config
from api import satellites
from api import passes


logger = getLogger(__name__)
log_queue = SimpleQueue()
queue_handler = QueueHandler(log_queue)
formatter = Formatter('{asctime} - {name} - {levelname} - {message}', style="{")
queue_handler.setFormatter(formatter)
file_handler = RotatingFileHandler(config.logging.filename)
stream_handler = StreamHandler()
queue_listener = QueueListener(log_queue, stream_handler, file_handler)
logger.addHandler(queue_handler)
logger.setLevel(config.logging.level)


class State(TypedDict):
    ReadSession: async_sessionmaker[AsyncSession]
    WriteSession: async_sessionmaker


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[State]:
    from api.db.session import ReadSession, WriteSession

    queue_listener.start()
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


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(satellites.v1_router)
app.include_router(passes.v1_router)
