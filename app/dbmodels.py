# Database models

import datetime

from sqlalchemy import (
    MetaData, Table, Column, Integer, String, Boolean, Date, Float, Text,
    ForeignKey, Unicode, DateTime
)
from sqlalchemy.sql.functions import now as sql_now

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

launch_site = Table(
    'launch_site', metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String(100), unique=True, nullable=False),
    Column('short_name', String(10), unique=True),
    Column('description', Text),
    Column('latitude', Float),
    Column('longitude', Float),
)

satellite_owner = Table(
    'satellite_owner', metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String(100), unique=True, nullable=False),
    Column('short_name', String(10), unique=True),
    Column('description', Text),
)

satellite_status = Table(
    'satellite_status', metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String(100), unique=True, nullable=False),
    Column('short_name', String(10), unique=True),
    Column('description', Text),
)


satellite_type = Table(
    'satellite_type', metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String(100), unique=True, nullable=False),
    Column('short_name', String(10), unique=True),
    Column('description', Text),
)


satellite = Table(
    'satellite', metadata,
    Column('id', Integer, primary_key=True),  # NORAD ID
    Column('cospar_id', String(30), unique=True),  # Intl. designator, COSPAR ID
    Column('name', String(100)),
    Column('description', Text),
    Column('decayed', Boolean, index=True),
    Column('launch_date', Date),
    Column('launch_year', Integer),
    Column('decay_date', Date),
    Column('launch_site_id', Integer, ForeignKey('launch_site.id', ondelete='SET NULL')),
    # Column('orbit_type', Integer, ForeignKey('orbit_type.id')),
    # Column('constellation', Integer, ForeignKey('constellation.id')),
    Column('mass', Float),
    Column('length', Float),
    Column('diameter', Float),
    Column('span', Float),
    # Column('shape', Integer, ForeignKey('shape.id')),
    Column('perigee', Float),
    Column('period', Float),
    Column('apogee', Float),
    Column('inclination', Float),
    Column('rcs', Float),
    Column('status_id', Integer, ForeignKey('satellite_status.id', ondelete='SET NULL')),
    Column('owner_id', Integer, ForeignKey('satellite_owner.id', ondelete='SET NULL')),
    Column('type_id', Integer, ForeignKey('satellite_type.id', ondelete='SET NULL')),
    Column('updated', DateTime(timezone=True), onupdate=datetime.datetime.utcnow()),
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