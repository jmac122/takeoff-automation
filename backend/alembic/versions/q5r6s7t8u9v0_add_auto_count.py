"""Add auto count tables.

Revision ID: q5r6s7t8u9v0
Revises: p4q5r6s7t8u9
Create Date: 2026-02-11
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "q5r6s7t8u9v0"
down_revision = "p4q5r6s7t8u9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Auto count sessions
    op.create_table(
        "auto_count_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "page_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("pages.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "condition_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("conditions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("template_bbox", postgresql.JSONB, nullable=False),
        sa.Column("template_image_key", sa.String(500), nullable=True),
        sa.Column("confidence_threshold", sa.Float, nullable=False, server_default="0.80"),
        sa.Column("scale_tolerance", sa.Float, nullable=False, server_default="0.20"),
        sa.Column("rotation_tolerance", sa.Float, nullable=False, server_default="15.0"),
        sa.Column(
            "detection_method", sa.String(50), nullable=False, server_default="hybrid"
        ),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("total_detections", sa.Integer, nullable=False, server_default="0"),
        sa.Column("confirmed_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("rejected_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("processing_time_ms", sa.Float, nullable=True),
        sa.Column("template_match_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("llm_match_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_auto_count_sessions_page_id",
        "auto_count_sessions",
        ["page_id"],
    )
    op.create_index(
        "ix_auto_count_sessions_condition_id",
        "auto_count_sessions",
        ["condition_id"],
    )

    # Auto count detections
    op.create_table(
        "auto_count_detections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auto_count_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "measurement_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("measurements.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("bbox", postgresql.JSONB, nullable=False),
        sa.Column("center_x", sa.Float, nullable=False),
        sa.Column("center_y", sa.Float, nullable=False),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column(
            "detection_source", sa.String(50), nullable=False, server_default="template"
        ),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("is_auto_confirmed", sa.Boolean, nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_auto_count_detections_session_id",
        "auto_count_detections",
        ["session_id"],
    )


def downgrade() -> None:
    op.drop_table("auto_count_detections")
    op.drop_table("auto_count_sessions")
