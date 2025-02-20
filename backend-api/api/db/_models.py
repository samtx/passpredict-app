from datetime import datetime, date
from uuid import uuid4, UUID

from sqlalchemy import (
    Integer,
    String,
    Text,
    Date,
    Float,
    ForeignKey,
    DateTime,
    Uuid,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import (
    mapped_column,
    Mapped,
    relationship,
)
from sqlalchemy.schema import ExecutableDDLElement
from sqlalchemy.event import listen
from sqlalchemy.ext.compiler import compiles


from ._base import Base


class Satellite(Base):
    __tablename__ = "satellite"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # NORAD ID
    cospar_id: Mapped[str] = mapped_column(String(30), unique=True, index=True)  # Intl. designator, COSPAR ID
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default='CURRENT_TIMESTAMP')
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_onupdate='CURRENT_TIMESTAMP')
    decayed_date: Mapped[date] = mapped_column(Date)
    launch_date: Mapped[date] = mapped_column(Date)
    launch_year: Mapped[int] = mapped_column(Integer)
    # Column('constellation', Integer, ForeignKey('constellation.id')),
    mass: Mapped[float] = mapped_column(Float)
    length: Mapped[float] = mapped_column(Float)
    diameter: Mapped[float] = mapped_column(Float)
    span: Mapped[float] = mapped_column(Float)
    # Column('shape', Integer, ForeignKey('shape.id')),


class CreateFTS5Table(ExecutableDDLElement):

    def __init__(
        self,
        table,
        columns,
    ):
        self.table = table
        self.columns = columns

# @compiles(CreateFTS5Table)
# def create_fts5_table(element: CreateFTS5Table, compiler, **kwargs):
#     sql_compiler = compiler.sql_compiler
#     table_name = element.table.__tablename__
#     fts_table_name = f"{table_name}_fts"
#     columns = ", ".join((col for col in element.columns))
#     row_id = sql_compiler.render_literal_value(element.table.primary_key, String())
#     stmt = (
#         f"CREATE VIRTUAL TABLE {fts_table_name} IF NOT EXISTS USING fts5("
#         f"{columns}, content={table_name}, content_rowid={row_id});"
#     )
#     return stmt



# listen(Satellite, "after_create", CreateFTS5Table() )


class Tle(Base):
    __tablename__ = "tle"
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=uuid4())
    tle1: Mapped[str] = mapped_column(String(70))
    tle2: Mapped[str] = mapped_column(String(70))
    epoch: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    satellite_id = mapped_column(ForeignKey("satellite.id"), index=True)
    satellite: Mapped[Satellite] = relationship()
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default='CURRENT_TIMESTAMP')


class Orbit(Base):
    __tablename__ = "orbit"
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=uuid4())
    epoch: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    satellite_id = mapped_column(ForeignKey("satellite.id"), index=True, nullable=False)
    satellite: Mapped[Satellite] = relationship()
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default='CURRENT_TIMESTAMP')
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_onupdate='CURRENT_TIMESTAMP')
    originator: Mapped[str] = mapped_column(String)
    originator_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    downloaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ref_frame: Mapped[str] = mapped_column(String)
    time_system: Mapped[str] = mapped_column(String)
    mean_element_theory: Mapped[str] = mapped_column(String)
    eccentricity:Mapped[float] = mapped_column(Float, nullable=False)
    ra_of_asc_node: Mapped[float] = mapped_column(Float, nullable=False)
    arg_of_pericenter: Mapped[float] = mapped_column(Float, nullable=False)
    mean_anomaly: Mapped[float] = mapped_column(Float, nullable=False)
    gm: Mapped[float] = mapped_column(Float)
    ephemeris_type: Mapped[String] = mapped_column(String)
    element_set_no: Mapped[int] = mapped_column(Integer)
    rev_at_epoch: Mapped[int] = mapped_column(Integer)
    bstar: Mapped[float] = mapped_column(Float, server_default='0.0', nullable=False)
    mean_motion: Mapped[float] = mapped_column(Float, nullable=False)
    mean_motion_dot: Mapped[float] = mapped_column(Float, nullable=False)
    mean_motion_ddot: Mapped[float] = mapped_column(Float, server_default='0.0', nullable=False)
    perigee: Mapped[float] = mapped_column(Float)
    apogee: Mapped[float] = mapped_column(Float)
    inclination:Mapped[float] = mapped_column(Float, nullable=False)
    tle: Mapped[str] = mapped_column(String(141))
    # Column('orbit_type', Integer, ForeignKey('orbit_type.id')),

    __table_args__ = (
        Index("ix_epoch", epoch.desc()),
        UniqueConstraint("satellite_id", "epoch", "originator", name="uix_satelliteid_epoch_originator"),
    )


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