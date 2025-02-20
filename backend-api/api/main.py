from logging import getLogger, Formatter, StreamHandler
from logging.handlers import QueueHandler, QueueListener, RotatingFileHandler
from queue import SimpleQueue
from contextlib import asynccontextmanager
# from importlib.metadata import version

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    queue_listener.start()
    yield


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

app.include_router(satellites.router)
app.include_router(passes.router)
