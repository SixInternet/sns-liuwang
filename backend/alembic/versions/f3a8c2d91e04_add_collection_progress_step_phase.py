"""add step_phase and source counts to collection_progress

Revision ID: f3a8c2d91e04
Revises: e45a641704d6
Create Date: 2026-05-21 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f3a8c2d91e04'
down_revision: Union[str, Sequence[str], None] = 'e45a641704d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'collection_progress',
        sa.Column('step_phase', sa.String(length=20), nullable=True, comment='planned / running / done'),
    )
    op.add_column(
        'collection_progress',
        sa.Column('sources_collected', sa.Integer(), nullable=True, comment='当前已 ingest 数'),
    )
    op.add_column(
        'collection_progress',
        sa.Column('max_sources', sa.Integer(), nullable=True, comment='本轮上限'),
    )


def downgrade() -> None:
    op.drop_column('collection_progress', 'max_sources')
    op.drop_column('collection_progress', 'sources_collected')
    op.drop_column('collection_progress', 'step_phase')
