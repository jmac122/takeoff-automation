"""TaskRecord model for unified async task tracking."""

from datetime import datetime

from sqlalchemy import DateTime, Float, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class TaskRecord(Base, TimestampMixin):
    """Tracks the lifecycle of every async (Celery) task.

    Uses Celery's string task_id as the primary key instead of UUIDMixin.
    """

    __tablename__ = "task_records"

    # Primary key — Celery task ID (string, not UUID)
    task_id: Mapped[str] = mapped_column(String(255), primary_key=True)

    # Project association
    project_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
    )

    # Task classification
    task_type: Mapped[str] = mapped_column(String(100), nullable=False)
    task_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(50), default="PENDING", nullable=False
    )  # PENDING | STARTED | PROGRESS | SUCCESS | FAILURE | REVOKED

    # Progress
    progress_percent: Mapped[float] = mapped_column(Float, default=0.0)
    progress_step: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Timing
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Results
    result_summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Error info
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_traceback: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Metadata
    task_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        Index("ix_task_records_project_status", "project_id", "status"),
        Index("ix_task_records_project_type", "project_id", "task_type"),
    )
