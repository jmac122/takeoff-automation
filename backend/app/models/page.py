"""Page model for individual sheets within documents."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.measurement import Measurement


class Page(Base, UUIDMixin, TimestampMixin):
    """Individual page/sheet from a document."""

    __tablename__ = "pages"

    # Foreign keys
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Page info
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # Dimensions (in pixels)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    dpi: Mapped[int] = mapped_column(Integer, default=150)

    # Storage keys
    image_key: Mapped[str] = mapped_column(String(500), nullable=False)
    thumbnail_key: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Classification (populated by AI in Phase 2)
    classification: Mapped[str | None] = mapped_column(String(100), nullable=True)
    classification_confidence: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )

    # Page title/name (extracted via OCR)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sheet_number: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Scale (populated by scale detection in Phase 2)
    scale_text: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # e.g., "1/4\" = 1'-0\""
    scale_value: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )  # pixels per foot
    scale_unit: Mapped[str] = mapped_column(String(20), default="foot")
    scale_calibrated: Mapped[bool] = mapped_column(Boolean, default=False)
    scale_calibration_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # OCR data
    ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    ocr_blocks: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Processing
    status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        nullable=False,
    )  # pending, processing, ready, error
    processing_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="pages")
    measurements: Mapped[list["Measurement"]] = relationship(
        "Measurement",
        back_populates="page",
        cascade="all, delete-orphan",
    )
