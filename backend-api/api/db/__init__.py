from ._base import Base
from ._models import Satellite
from ._models import Orbit


__all__ = [
    "Base",
    "Satellite",
    "Orbit",
]


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