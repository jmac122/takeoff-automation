"""Measurement model for geometric shapes on pages."""

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import String, Float, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.condition import Condition
    from app.models.page import Page


class Measurement(Base, UUIDMixin, TimestampMixin):
    """Individual measurement (geometric shape) on a page."""

    __tablename__ = "measurements"

    # Foreign keys
    condition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conditions.id", ondelete="CASCADE"),
        nullable=False,
    )
    page_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pages.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Geometry
    geometry_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # line, polyline, polygon, rectangle, circle, point

    geometry_data: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
    )
    # Structure varies by type:
    # line: {start: {x, y}, end: {x, y}}
    # polyline: {points: [{x, y}, ...]}
    # polygon: {points: [{x, y}, ...]}
    # rectangle: {x, y, width, height, rotation?}
    # circle: {center: {x, y}, radius}
    # point: {x, y}

    # Calculated values (in real-world units)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)

    # Pixel values (for reference)
    pixel_length: Mapped[float | None] = mapped_column(Float, nullable=True)
    pixel_area: Mapped[float | None] = mapped_column(Float, nullable=True)

    # AI generation tracking
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_model: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # User modifications
    is_modified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Extra metadata
    extra_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    condition: Mapped["Condition"] = relationship(
        "Condition", back_populates="measurements"
    )
    page: Mapped["Page"] = relationship("Page", back_populates="measurements")
