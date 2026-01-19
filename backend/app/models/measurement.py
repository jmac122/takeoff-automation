"""Measurement model for geometry on pages."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String, ForeignKey, Float, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.page import Page
    from app.models.condition import Condition


class Measurement(Base, UUIDMixin, TimestampMixin):
    """Geometry on a page linked to a condition."""

    __tablename__ = "measurements"

    # Foreign keys
    page_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pages.id", ondelete="CASCADE"),
        nullable=False,
    )
    condition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conditions.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Geometry
    geometry_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # polygon, polyline, line, point
    geometry_data: Mapped[dict] = mapped_column(JSON, nullable=False)  # Coordinate data
    quantity: Mapped[float] = mapped_column(
        Float, nullable=False
    )  # Calculated quantity
    area: Mapped[float | None] = mapped_column(Float, nullable=True)  # Area in sq ft
    perimeter: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )  # Perimeter in linear ft

    # Metadata
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    page: Mapped["Page"] = relationship("Page", back_populates="measurements")
    condition: Mapped["Condition"] = relationship(
        "Condition", back_populates="measurements"
    )
