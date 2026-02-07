"""add is_visible to conditions

Revision ID: n2o3p4q5r6s7
Revises: m1n2o3p4q5r6
Create Date: 2026-02-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'n2o3p4q5r6s7'
down_revision: Union[str, Sequence[str], None] = 'm1n2o3p4q5r6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'conditions',
        sa.Column('is_visible', sa.Boolean(), nullable=False, server_default=sa.text('true')),
    )


def downgrade() -> None:
    op.drop_column('conditions', 'is_visible')
