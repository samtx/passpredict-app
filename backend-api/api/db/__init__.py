from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from api.settings import config
from ._base import Base
from ._models import Satellite
from ._models import Tle
from ._models import Orbit


__all__ = [
    "Base",
    "Satellite",
    "Tle",
    "Orbit",
    "ReadSession",
    "WriteSession",
]


read_engine = create_async_engine(f"{config.db_url}?immutable=1&mode=ro")

write_engine = create_async_engine(config.db_url)

ReadSession = async_sessionmaker(
    bind=read_engine,
    expire_on_commit=False,
)

WriteSession = async_sessionmaker(
    bind=write_engine,
    expire_on_commit=False,
)

# from sqlalchemy.engine import Engine
# from sqlalchemy import event, Connection
# @event.listens_for(read_conn.sync_engine, "connect")
# def set_sqlite_wal_mode(dbapi_connection, connection_record):
#     cursor = dbapi_connection.cursor()
#     cursor.execute("PRAGMA journal_mode=WAL;")
#     cursor.close()

# @event.listens_for(write_conn.sync_engine, "connect")
# def set_sqlite_wal_mode(dbapi_connection, connection_record):
#     cursor = dbapi_connection.cursor()
#     cursor.execute("PRAGMA journal_mode=WAL;")
#     cursor.close()