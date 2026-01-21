"""Add physical page dimension fields

Revision ID: g4h5i6j7k8l9
Revises: f3g4h5i6j7k8
Create Date: 2026-01-21 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'g4h5i6j7k8l9'
down_revision: Union[str, None] = 'f3g4h5i6j7k8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add physical page dimension fields for accurate scale calculations
    op.add_column('pages', sa.Column('page_width_inches', sa.Float(), nullable=True))
    op.add_column('pages', sa.Column('page_height_inches', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('pages', 'page_height_inches')
    op.drop_column('pages', 'page_width_inches')
