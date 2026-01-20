"""add_classification_history

Revision ID: a1b2c3d4e5f6
Revises: 576b3ce9ef71
Create Date: 2026-01-20 02:40:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "576b3ce9ef71"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create classification_history table."""
    op.create_table(
        "classification_history",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "page_id",
            UUID(as_uuid=True),
            sa.ForeignKey("pages.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("classification", sa.String(100), nullable=True),
        sa.Column("classification_confidence", sa.Float, nullable=True),
        sa.Column("discipline", sa.String(50), nullable=True),
        sa.Column("discipline_confidence", sa.Float, nullable=True),
        sa.Column("page_type", sa.String(50), nullable=True),
        sa.Column("page_type_confidence", sa.Float, nullable=True),
        sa.Column("concrete_relevance", sa.String(20), nullable=True),
        sa.Column("concrete_elements", JSON, nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        # LLM metadata for BI
        sa.Column("llm_provider", sa.String(50), nullable=False),
        sa.Column("llm_model", sa.String(100), nullable=False),
        sa.Column("llm_latency_ms", sa.Float, nullable=True),
        sa.Column("input_tokens", sa.Integer, nullable=True),
        sa.Column("output_tokens", sa.Integer, nullable=True),
        # Full raw response for debugging
        sa.Column("raw_response", JSON, nullable=True),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # Index for querying history by provider/model for BI
    op.create_index(
        "ix_classification_history_provider_model",
        "classification_history",
        ["llm_provider", "llm_model"],
    )

    # Index for time-based queries
    op.create_index(
        "ix_classification_history_created_at",
        "classification_history",
        ["created_at"],
    )


def downgrade() -> None:
    """Drop classification_history table."""
    op.drop_index("ix_classification_history_created_at")
    op.drop_index("ix_classification_history_provider_model")
    op.drop_table("classification_history")
