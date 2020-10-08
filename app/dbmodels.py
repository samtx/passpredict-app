# Database models

import datetime

import sqlalchemy as sa
from sqlalchemy import (
    MetaData, Table, Column, Integer, String, Boolean, Date, Float, Text,
    ForeignKey, Unicode, DateTime
)
import numpy as np

from .database import Base, engine


metadata = MetaData()

orbit_type = Table(
    'orbit_type', metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String(30)),      # eg. low earth orbit, geostationary orbit
    Column('short_name', String(4))  # eg. LEO, GEO
)

constellation = Table(
    'constellation', metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String(30), unique=True),      # eg. Starlink-1, NOAA
)

sat_type = Table(
    'sat_type', metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String(30), unique=True)  # Communication, Military, Weather, Radio, Rocket Body
)

shape = Table(
    'shape', metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String(30), unique=True)
)

satellite = Table(
    'satellite', metadata,
    Column('id', Integer, primary_key=True),  # NORAD ID
    Column('cospar_id', String(30), unique=True),  # Intl. designator, COSPAR ID
    Column('name', String(40)),
    Column('description', Text),
    Column('decayed', Boolean),
    Column('launch_date', Date),
    Column('launch_year', Integer),
    Column('orbit_type', Integer, ForeignKey('orbit_type.id')),
    Column('constellation', Integer, ForeignKey('constellation.id')),
    Column('mass', Float),
    Column('length', Float),
    Column('diameter', Float),
    Column('span', Integer, ForeignKey('shape.id')),
    Column('shape', Float),
    Column('perigee', Float),
    Column('apogee', Float),
    Column('inclination', Float),
)

location = Table(
    'location', metadata,
    Column('id', primary_key=True),
    Column('name', Unicode(50), index=True, unique=True),
    Column('lat', Float),
    Column('lon', Float),
    Column('height', Float)
)

tle = Table(
    'tle', metadata,
    Column('id', primary_key=True),
    Column('tle1', String(70)),
    Column('tle2', String(70)),
    Column('epoch', DateTime),
    Column('satellite_id', ForeignKey('satellite.id', ondelete='CASCADE')),
    Column('created', DateTime, onupdate=datetime.datetime.now())
)

# many to many association table for satellite tags
satellite_tags = Table(
    'satellite_tags', metadata,
    Column('satellite_id', ForeignKey('satellite.id')),
    Column('tag_id', ForeignKey('tags.id'))
)

tags = Table(
    'tags', metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String(30), unique=True)
)