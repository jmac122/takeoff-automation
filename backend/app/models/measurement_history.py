"""MeasurementHistory model for tracking review actions on measurements."""

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import String, Float, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.measurement import Measurement


class MeasurementHistory(Base, UUIDMixin, TimestampMixin):
    """Audit trail record for measurement review actions."""

    __tablename__ = "measurement_history"

    # Foreign key to measurement
    measurement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("measurements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Action tracking
    action: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # created, approved, rejected, modified, auto_accepted

    actor: Mapped[str] = mapped_column(
        String(255), nullable=False
    )  # username or "system"

    actor_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="user"
    )  # user, system, auto_accept

    # Status change tracking
    previous_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    new_status: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Geometry change tracking
    previous_geometry: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True
    )
    new_geometry: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True
    )

    # Quantity change tracking
    previous_quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    new_quantity: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Description and notes
    change_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    measurement: Mapped["Measurement"] = relationship(
        "Measurement", back_populates="history"
    )
