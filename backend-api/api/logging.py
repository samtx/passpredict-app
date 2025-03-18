from datetime import datetime
from logging import getLogger, Formatter, StreamHandler, LogRecord
from logging.handlers import QueueHandler, QueueListener, RotatingFileHandler
from queue import SimpleQueue

from api.settings import config


def formatTime(self, record: LogRecord, datefmt: str = None):
    return datetime.fromtimestamp(record.created).astimezone().isoformat(timespec='milliseconds')

Formatter.formatTime = formatTime


def init_logging(api_root: str):
    logger = getLogger(api_root)
    log_queue = SimpleQueue()
    queue_handler = QueueHandler(log_queue)
    formatter = Formatter(
        '{asctime} - {name} - {levelname} - {message}',
        style="{",
    )
    queue_handler.setFormatter(formatter)
    file_handler = RotatingFileHandler(config.logging.filename)
    stream_handler = StreamHandler()
    queue_listener = QueueListener(log_queue, stream_handler, file_handler)
    logger.addHandler(queue_handler)
    logger.setLevel(config.logging.level)
    queue_listener.start()