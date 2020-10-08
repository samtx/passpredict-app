"""Add satellite category tables

Revision ID: ee841944c50c
Revises: bd0d4301150d
Create Date: 2020-10-07 18:51:47.811629

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import (
    Table, Column, Integer, String, Boolean, Date, Float, Text,
    ForeignKey, Unicode, DateTime
)

# revision identifiers, used by Alembic.
revision = 'ee841944c50c'
down_revision = 'bd0d4301150d'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'orbit_type',
        Column('id', Integer, primary_key=True),
        Column('name', String(30)),      # eg. low earth orbit, geostationary orbit
        Column('short_name', String(4))  # eg. LEO, GEO
    )
    op.create_table(
        'constellation',
        Column('id', Integer, primary_key=True),
        Column('name', String(30), unique=True, nullable=False),      # eg. Starlink-1, NOAA
    )
    op.create_table(
        'sat_type',
        Column('id', Integer, primary_key=True),
        Column('name', String(30), unique=True, nullable=False)  # Communication, Military, Weather, Radio, Rocket Body
    )
    op.create_table(
        'shape',
        Column('id', Integer, primary_key=True),
        Column('name', String(30), unique=True, nullable=False)
    )


def downgrade():
    op.drop_table('orbit_type')
    op.drop_table('constellation')
    op.drop_table('sat_type')
    op.drop_table('shape')
