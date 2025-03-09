"""update orbit indexes

Revision ID: 2645b2d61634
Revises: bdee373b9b9f
Create Date: 2025-03-07 19:53:22.649202

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2645b2d61634'
down_revision: Union[str, None] = 'bdee373b9b9f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_epoch', table_name='orbit')
    op.create_index('ix_satellite_id_epoch_desc', 'orbit', ['satellite_id', sa.text('epoch DESC')], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_satellite_id_epoch_desc', table_name='orbit')
    op.create_index('ix_epoch', 'orbit', ['epoch'], unique=False)
    # ### end Alembic commands ###
