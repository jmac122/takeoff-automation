"""Page model for individual sheets within documents."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.measurement import Measurement
    from app.models.classification_history import ClassificationHistory


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

    # Physical page dimensions (in inches) - from PDF metadata
    # Used to calculate accurate pixels_per_inch for scale measurements
    page_width_inches: Mapped[float | None] = mapped_column(Float, nullable=True)
    page_height_inches: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Storage keys
    image_key: Mapped[str] = mapped_column(String(500), nullable=False)
    thumbnail_key: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Classification (populated by AI in Phase 2)
    classification: Mapped[str | None] = mapped_column(String(100), nullable=True)
    classification_confidence: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    discipline: Mapped[str | None] = mapped_column(String(100), nullable=True)
    discipline_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    page_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    page_type_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    concrete_relevance: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # high, medium, low, none
    concrete_elements: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    llm_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    llm_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    classification_metadata: Mapped[dict | None] = mapped_column(
        JSON, nullable=True
    )  # Full classification result with LLM metadata

    # Page title/name (extracted via OCR)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sheet_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sheet_title: Mapped[str | None] = mapped_column(String(255), nullable=True)

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
    scale_detection_method: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # vision_llm, ocr_predetected, ocr_pattern_match, manual_calibration, scale_bar

    # OCR data
    ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    ocr_blocks: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Vector PDF detection (for future Vector PDF Extraction — Phase 9)
    is_vector: Mapped[bool] = mapped_column(Boolean, default=False)
    has_extractable_geometry: Mapped[bool] = mapped_column(Boolean, default=False)
    vector_path_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    vector_text_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pdf_origin: Mapped[str | None] = mapped_column(String(50), nullable=True)  # autocad, revit, bluebeam, scanned, unknown

    # Display fields (UI Overhaul Phase A)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    display_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    group_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_relevant: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"), nullable=False)

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
    classification_history: Mapped[list["ClassificationHistory"]] = relationship(
        "ClassificationHistory",
        back_populates="page",
        cascade="all, delete-orphan",
        order_by="desc(ClassificationHistory.created_at)",
    )
