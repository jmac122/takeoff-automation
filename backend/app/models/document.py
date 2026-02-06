"""Document model for uploaded plan sets."""

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, String, Integer, BigInteger, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.page import Page


class Document(Base, UUIDMixin, TimestampMixin):
    """Uploaded document (PDF or TIFF plan set)."""

    __tablename__ = "documents"

    # Foreign keys
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )

    # File info
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)  # pdf, tiff
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)  # bytes
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)

    # Storage
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)

    # Processing
    status: Mapped[str] = mapped_column(
        String(50),
        default="uploaded",
        nullable=False,
    )  # uploaded, processing, ready, error
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    processing_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    processing_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Title block region (normalized coordinates, applies to all pages)
    title_block_region: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Revision tracking (for future Plan Overlay — Phase 7B)
    revision_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    revision_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    revision_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    supersedes_document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_latest_revision: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="documents")
    supersedes: Mapped["Document | None"] = relationship(
        "Document",
        remote_side="Document.id",
        foreign_keys=[supersedes_document_id],
    )
    pages: Mapped[list["Page"]] = relationship(
        "Page",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="Page.page_number",
    )
