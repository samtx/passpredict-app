# Database models

import datetime

import sqlalchemy as sa
from sqlalchemy import (
    MetaData, Table, Column, Integer, String, Boolean, Date, Float, Text,
    ForeignKey, Unicode, DateTime
)

# from app.database import Base, engine

metadata = MetaData()

# Jonathan Space Report Satcat Phases/Status column descriptors
# https://planet4589.org/space/gcat/web/intro/phases.html
JSR_status_decayed = {
    "E", # exploded
    "R", # reentered
    "D", # deorbited
    "L", # landed
    "AR", # reentered attached
    "AR IN", # reentered inside
    "AL", # landed attached
    "AL IN", # landed inside
}


# Orbit type from Jonathan Space Report
# https://planet4589.org/space/gcat/web/intro/orbits.html
# orbit_type = Table(
#     'orbit_type', metadata,
#     Column('id', Integer, primary_key=True),
#     Column('name', String(75)),      # eg. low earth orbit, geostationary orbit
#     Column('short_name', String(6), unique=True), # eg. LEO, GEO
#     Column('description', Text)      # eg. period < 2hr, h > 600 km, incl. < 85deg, ecc ~= .5
# )

# constellation = Table(
#     'constellation', metadata,
#     Column('id', Integer, primary_key=True),
#     Column('name', String(30), unique=True),      # eg. Starlink-1, NOAA
# )

# sat_type = Table(
#     'sat_type', metadata,
#     Column('id', Integer, primary_key=True),
#     Column('name', String(30), unique=True)  # Communication, Military, Weather, Radio, Rocket Body
# )

# shape = Table(
#     'shape', metadata,
#     Column('id', Integer, primary_key=True),
#     Column('name', String(30), unique=True)
# )

satellite = Table(
    'satellite', metadata,
    Column('id', Integer, primary_key=True),  # NORAD ID
    Column('cospar_id', String(30), unique=True),  # Intl. designator, COSPAR ID
    Column('name', String(100)),
    Column('description', Text),
    Column('decayed', Boolean),
    Column('launch_date', Date),
    Column('launch_year', Integer),
    # Column('orbit_type', Integer, ForeignKey('orbit_type.id')),
    # Column('constellation', Integer, ForeignKey('constellation.id')),
    Column('mass', Float),
    Column('length', Float),
    Column('diameter', Float),
    Column('span', Float),
    # Column('shape', Integer, ForeignKey('shape.id')),
    Column('perigee', Float),
    Column('apogee', Float),
    Column('inclination', Float),
)


tle = Table(
    'tle', metadata,
    Column('id', Integer, primary_key=True),
    Column('tle1', String(70)),
    Column('tle2', String(70)),
    Column('epoch', DateTime(timezone=True)),
    Column('satellite_id', Integer, ForeignKey('satellite.id', ondelete='CASCADE'), index=True),
    Column('created', DateTime(timezone=True), onupdate=datetime.datetime.now())
)

# # many to many association table for satellite tags
# satellite_tags = Table(
#     'satellite_tags', metadata,
#     Column('satellite_id', ForeignKey('satellite.id')),
#     Column('tag_id', ForeignKey('tags.id'))
# )

# tags = Table(
#     'tags', metadata,
#     Column('id', Integer, primary_key=True),
#     Column('name', String(30), unique=True)
# )