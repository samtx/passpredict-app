# create SQLAlchemy declarative base

import sqlalchemy
import sqlalchemy.ext.declarative

from app import settings

engine = sqlalchemy.create_engine(
    settings.DATABASE_URI,
    connect_args={'check_same_thread': False},
    echo=settings.DB_ECHO,
)

Base = sqlalchemy.ext.declarative.declarative_base()


