from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from api.settings import config


__all__ = [
    "read_engine",
    "write_engine",
    "ReadSession",
    "WriteSession",
]


read_engine = create_async_engine(
    config.db.sqlalchemy_conn_url(read_only=True),
    echo=config.db.echo,
)


write_engine = create_async_engine(
    config.db.sqlalchemy_conn_url(),
    echo=config.db.echo,
)


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