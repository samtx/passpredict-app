"""Add satellite table

Revision ID: 0f113aeb9ba7
Revises: ee841944c50c
Create Date: 2020-10-07 19:37:45.404769

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import (
    Table, Column, Integer, String, Boolean, Date, Float, Text,
    ForeignKey, Unicode, DateTime
)


# revision identifiers, used by Alembic.
revision = '0f113aeb9ba7'
down_revision = 'ee841944c50c'
branch_labels = None
depends_on = None


def upgrade():
     op.create_table(
        'satellite',
        Column('id', Integer, primary_key=True),  # NORAD ID
        Column('cospar_id', String(30), unique=True),  # Intl. designator, COSPAR ID
        Column('name', String(40)),
        Column('description', Text),
        Column('decayed', Boolean, nullable=False),
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


def downgrade():
    op.drop_table('satellite')
