"""add_classification_fields_to_pages

Revision ID: 576b3ce9ef71
Revises: d707bfb8a266
Create Date: 2026-01-19 19:27:39.729540

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "576b3ce9ef71"
down_revision: Union[str, Sequence[str], None] = "d707bfb8a266"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add concrete_relevance column
    op.add_column(
        "pages", sa.Column("concrete_relevance", sa.String(length=20), nullable=True)
    )

    # Add classification_metadata column (JSON)
    op.add_column(
        "pages", sa.Column("classification_metadata", sa.JSON(), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Remove classification_metadata column
    op.drop_column("pages", "classification_metadata")

    # Remove concrete_relevance column
    op.drop_column("pages", "concrete_relevance")
