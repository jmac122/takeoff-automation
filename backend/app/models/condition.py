"""Condition model for takeoff line items."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String, ForeignKey, Text, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.measurement import Measurement


class Condition(Base, UUIDMixin, TimestampMixin):
    """Takeoff line item (e.g., "4" Concrete Slab")."""

    __tablename__ = "conditions"

    # Foreign keys
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Condition info
    name: Mapped[str] = mapped_column(
        String(255), nullable=False
    )  # e.g., "4" Concrete Slab"
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    unit: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # sq ft, linear ft, etc.
    unit_cost: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="conditions")
    measurements: Mapped[list["Measurement"]] = relationship(
        "Measurement",
        back_populates="condition",
        cascade="all, delete-orphan",
    )
