# create SQLAlchemy declarative base

import sqlalchemy
import sqlalchemy.ext.declarative

from .settings import database_uri

SQLALCHEMY_DATABASE_URL = database_uri

engine = sqlalchemy.create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={'check_same_thread': False}
)

Base = sqlalchemy.ext.declarative.declarative_base()


