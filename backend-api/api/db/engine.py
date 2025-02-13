
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from api.settings import config


read_conn = create_async_engine(f"{config.db_url}?immutable=1&mode=ro")

write_conn = create_async_engine(config.db_url)


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




def session_factory(bind) -> async_sessionmaker:
    sessionmaker = async_sessionmaker(bind=bind)
    return sessionmaker