"""Condition model for takeoff line items."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String, Float, Integer, ForeignKey, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.assembly import Assembly
    from app.models.project import Project
    from app.models.measurement import Measurement


class Condition(Base, UUIDMixin, TimestampMixin):
    """Takeoff condition (line item) that groups measurements."""

    __tablename__ = "conditions"

    # Foreign keys
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Condition info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Scope/category
    scope: Mapped[str] = mapped_column(String(100), default="concrete")
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Measurement type
    measurement_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # linear, area, volume, count

    # Display
    color: Mapped[str] = mapped_column(String(20), default="#3B82F6")  # Hex color
    line_width: Mapped[int] = mapped_column(Integer, default=2)
    fill_opacity: Mapped[float] = mapped_column(Float, default=0.3)

    # Unit and modifiers
    unit: Mapped[str] = mapped_column(String(50), default="LF")  # LF, SF, CY, EA
    depth: Mapped[float | None] = mapped_column(Float, nullable=True)  # For volume calc
    thickness: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Calculated totals (denormalized for performance)
    total_quantity: Mapped[float] = mapped_column(Float, default=0.0)
    measurement_count: Mapped[int] = mapped_column(Integer, default=0)

    # Sort order
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    
    # AI generation tracking
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)

    # Visibility toggle (UI Phase B)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Extra metadata
    extra_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Spatial grouping (for future NL Query — Phase 10)
    building: Mapped[str | None] = mapped_column(String(100), nullable=True)
    area: Mapped[str | None] = mapped_column(String(100), nullable=True)
    elevation: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="conditions")
    measurements: Mapped[list["Measurement"]] = relationship(
        "Measurement",
        back_populates="condition",
        cascade="all, delete-orphan",
    )
    assembly: Mapped["Assembly | None"] = relationship(
        "Assembly",
        back_populates="condition",
        uselist=False,
        cascade="all, delete-orphan",
    )
