"""Condition model."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class Condition(Base):
    """Condition model representing a takeoff line item."""

    __tablename__ = "conditions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    name = Column(String(255), nullable=False)  # e.g., "4" Concrete Slab"
    description = Column(Text, nullable=True)
    unit = Column(String(50), nullable=False)  # sq ft, linear ft, etc.
    unit_cost = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="conditions")
    measurements = relationship("Measurement", back_populates="condition", cascade="all, delete-orphan")