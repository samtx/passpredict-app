# create SQLAlchemy declarative base

import sqlalchemy
import sqlalchemy.ext.declarative

from app.settings import database_uri, db_echo

SQLALCHEMY_DATABASE_URL = database_uri

engine = sqlalchemy.create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={'check_same_thread': False},
    echo=db_echo,
)

Base = sqlalchemy.ext.declarative.declarative_base()


