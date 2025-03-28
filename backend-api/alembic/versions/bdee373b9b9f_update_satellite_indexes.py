"""update satellite indexes

Revision ID: bdee373b9b9f
Revises: 9e56b08db8b0
Create Date: 2025-03-07 16:16:32.479162

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bdee373b9b9f'
down_revision: Union[str, None] = '9e56b08db8b0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_satellite_intl_designator', table_name='satellite')
    op.create_index(op.f('ix_satellite_intl_designator'), 'satellite', ['intl_designator'], unique=False)
    op.create_index(op.f('ix_satellite_decay_date'), 'satellite', ['decay_date'], unique=False)
    op.create_index(op.f('ix_satellite_launch_date'), 'satellite', ['launch_date'], unique=False)
    op.create_index(op.f('ix_satellite_name'), 'satellite', ['name'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_satellite_name'), table_name='satellite')
    op.drop_index(op.f('ix_satellite_launch_date'), table_name='satellite')
    op.drop_index(op.f('ix_satellite_decay_date'), table_name='satellite')
    op.drop_index(op.f('ix_satellite_intl_designator'), table_name='satellite')
    op.create_index('ix_satellite_intl_designator', 'satellite', ['intl_designator'], unique=1)
    # ### end Alembic commands ###
