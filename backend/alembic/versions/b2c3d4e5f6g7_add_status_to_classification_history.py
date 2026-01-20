"""add_status_to_classification_history

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-01-20 02:50:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6g7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add status and error_message columns to classification_history."""
    op.add_column(
        "classification_history",
        sa.Column("status", sa.String(20), nullable=False, server_default="success"),
    )
    op.add_column(
        "classification_history",
        sa.Column("error_message", sa.Text, nullable=True),
    )
    # Index for filtering by status
    op.create_index(
        "ix_classification_history_status",
        "classification_history",
        ["status"],
    )


def downgrade() -> None:
    """Remove status and error_message columns."""
    op.drop_index("ix_classification_history_status")
    op.drop_column("classification_history", "error_message")
    op.drop_column("classification_history", "status")
