"""Models for the Auto Count feature — template-based object detection and counting."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.condition import Condition
    from app.models.measurement import Measurement


class AutoCountSession(Base, UUIDMixin, TimestampMixin):
    """Tracks a single auto-count run — template crop → detections."""

    __tablename__ = "auto_count_sessions"

    # Foreign keys
    page_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    condition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conditions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Template definition
    template_bbox: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, comment='{"x": float, "y": float, "w": float, "h": float}'
    )
    template_image_key: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="Storage key for cropped template image"
    )

    # Detection settings
    confidence_threshold: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.80
    )
    scale_tolerance: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.20, comment="±20% by default"
    )
    rotation_tolerance: Mapped[float] = mapped_column(
        Float, nullable=False, default=15.0, comment="±15 degrees by default"
    )
    detection_method: Mapped[str] = mapped_column(
        String(50), nullable=False, default="hybrid",
        comment="template | llm | hybrid"
    )

    # Results summary
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending",
        comment="pending | processing | completed | failed"
    )
    total_detections: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    confirmed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rejected_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Execution metadata
    processing_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    template_match_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    llm_match_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationships
    detections: Mapped[list["AutoCountDetection"]] = relationship(
        "AutoCountDetection",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="AutoCountDetection.confidence.desc()",
    )
    condition: Mapped["Condition"] = relationship("Condition")

    def __repr__(self) -> str:
        return (
            f"<AutoCountSession(id={self.id}, page_id={self.page_id}, "
            f"status={self.status}, detections={self.total_detections})>"
        )


class AutoCountDetection(Base, UUIDMixin, TimestampMixin):
    """A single detected instance from an auto-count session."""

    __tablename__ = "auto_count_detections"

    # Foreign keys
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("auto_count_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    measurement_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("measurements.id", ondelete="SET NULL"),
        nullable=True,
        comment="Set when detection is confirmed and measurement is created",
    )

    # Location
    bbox: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, comment='{"x": float, "y": float, "w": float, "h": float}'
    )
    center_x: Mapped[float] = mapped_column(Float, nullable=False)
    center_y: Mapped[float] = mapped_column(Float, nullable=False)

    # Detection quality
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    detection_source: Mapped[str] = mapped_column(
        String(50), nullable=False, default="template",
        comment="template | llm | both"
    )

    # Review status
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending",
        comment="pending | confirmed | rejected"
    )
    is_auto_confirmed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        comment="True if auto-confirmed above threshold"
    )

    # Relationships
    session: Mapped["AutoCountSession"] = relationship(
        "AutoCountSession", back_populates="detections"
    )
    measurement: Mapped["Measurement | None"] = relationship("Measurement")

    def __repr__(self) -> str:
        return (
            f"<AutoCountDetection(id={self.id}, confidence={self.confidence:.2f}, "
            f"status={self.status})>"
        )
