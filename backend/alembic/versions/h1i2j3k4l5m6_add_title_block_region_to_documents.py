"""Add title block region to documents

Revision ID: h1i2j3k4l5m6
Revises: g4h5i6j7k8l9
Create Date: 2026-01-22 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "h1i2j3k4l5m6"
down_revision: Union[str, None] = "g4h5i6j7k8l9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("title_block_region", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("documents", "title_block_region")
