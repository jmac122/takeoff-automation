"""ExportJob model for tracking export generation jobs."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, Integer, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.project import Project


class ExportJob(Base, UUIDMixin, TimestampMixin):
    """Tracks export generation jobs for a project."""

    __tablename__ = "export_jobs"

    # Project association
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Export configuration
    format: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # excel, ost, csv, pdf

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(50), default="pending", nullable=False
    )  # pending, processing, completed, failed

    # Result storage
    file_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Error info
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Export options (format-specific settings)
    options: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Timing
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="exports")
