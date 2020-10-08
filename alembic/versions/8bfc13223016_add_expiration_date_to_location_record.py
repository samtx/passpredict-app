"""Add expiration date to location record

Revision ID: 8bfc13223016
Revises: 0f113aeb9ba7
Create Date: 2020-10-08 11:50:19.506761

"""
import datetime

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Column, Date


# revision identifiers, used by Alembic.
revision = '8bfc13223016'
down_revision = '0f113aeb9ba7'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('location', Column('expires', Date))  # used for expiring geocoding results after 30 days


def downgrade():
    op.drop_column('location', 'expires')
