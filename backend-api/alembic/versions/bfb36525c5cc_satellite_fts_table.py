"""satellite fts table

Revision ID: bfb36525c5cc
Revises: 12b8c4e0c00d
Create Date: 2025-03-06 17:32:22.348597

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bfb36525c5cc'
down_revision: Union[str, None] = '12b8c4e0c00d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS satellite_fts5
        USING fts5(
            name,
            intl_designator,
            description,
            content=satellite,
            content_rowid=id
        )
        """
    )

    op.execute(
        """
        CREATE TRIGGER IF NOT EXISTS satellite_insert AFTER INSERT ON satellite BEGIN
            INSERT INTO satellite_fts5 (rowid, name, intl_designator, description)
            VALUES (new.id, new.name, new.intl_designator, new.description);
        END
        """
    )

    op.execute(
        """
        CREATE TRIGGER IF NOT EXISTS satellite_update AFTER UPDATE ON satellite BEGIN
            INSERT INTO satellite_fts5 (satellite_fts5, rowid, name, intl_designator, description)
            VALUES ('delete', old.id, old.name, old.intl_designator, old.description);
            INSERT INTO satellite_fts5 (rowid, name, intl_designator, description)
            VALUES (new.id, new.name, new.intl_designator, new.description);
        END
        """
    )

    op.execute(
        """
        CREATE TRIGGER IF NOT EXISTS satellite_delete AFTER DELETE ON satellite BEGIN
            INSERT INTO satellite_fts5 (satellite_fts5, rowid, name, intl_designator, description)
            VALUES ('delete', old.id, old.name, old.intl_designator, old.description);
        END
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS satellite_delete;")
    op.execute("DROP TRIGGER IF EXISTS satellite_update;")
    op.execute("DROP TRIGGER IF EXISTS satellite_insert;")
    op.execute("DROP TABLE IF EXISTS satellite_fts5;")
