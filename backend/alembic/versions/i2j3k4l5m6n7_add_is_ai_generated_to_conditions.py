"""add_is_ai_generated_to_conditions

Revision ID: i2j3k4l5m6n7
Revises: 066b86f9af2c
Create Date: 2026-01-23 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'i2j3k4l5m6n7'
down_revision: Union[str, Sequence[str], None] = '066b86f9af2c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add is_ai_generated column to conditions table."""
    op.add_column('conditions', sa.Column('is_ai_generated', sa.Boolean(), server_default='false', nullable=False))


def downgrade() -> None:
    """Remove is_ai_generated column from conditions table."""
    op.drop_column('conditions', 'is_ai_generated')
