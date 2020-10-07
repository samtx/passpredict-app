"""Create Location table

Revision ID: bd0d4301150d
Revises: 
Create Date: 2020-10-07 16:27:46.014660

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Column, Unicode, Float, Integer


# revision identifiers, used by Alembic.
revision = 'bd0d4301150d'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'location',
        Column('id', Integer, primary_key=True),
        Column('name', Unicode(200), index=True, unique=True, nullable=False),
        Column('lat', Float, nullable=False),
        Column('lon', Float, nullable=False),
        Column('height', Float)
    )

def downgrade():
    op.drop_table('location')
