"""populate satellite fts table

Revision ID: 9e56b08db8b0
Revises: bfb36525c5cc
Create Date: 2025-03-06 18:28:24.244297

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9e56b08db8b0'
down_revision: Union[str, None] = 'bfb36525c5cc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO satellite_fts5 (rowid, name, intl_designator, description)
        SELECT s.id, s.name, s.intl_designator, s.description FROM satellite s
        WHERE true;
        """
    )


def downgrade() -> None:
    pass
