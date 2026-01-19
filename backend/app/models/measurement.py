"""Measurement model."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class Measurement(Base):
    """Measurement model representing geometry on a page linked to a condition."""

    __tablename__ = "measurements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    page_id = Column(UUID(as_uuid=True), ForeignKey("pages.id"), nullable=False)
    condition_id = Column(UUID(as_uuid=True), ForeignKey("conditions.id"), nullable=False)
    geometry_type = Column(String(50), nullable=False)  # polygon, polyline, line, point
    geometry_data = Column(JSON, nullable=False)  # Coordinate data
    quantity = Column(Float, nullable=False)  # Calculated quantity
    area = Column(Float, nullable=True)  # Area in sq ft
    perimeter = Column(Float, nullable=True)  # Perimeter in linear ft
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    page = relationship("Page", back_populates="measurements")
    condition = relationship("Condition", back_populates="measurements")