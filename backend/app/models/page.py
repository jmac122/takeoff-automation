"""Page model."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Float, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class Page(Base):
    """Page model representing an individual sheet/page from a document."""

    __tablename__ = "pages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    page_number = Column(Integer, nullable=False)
    width = Column(Float, nullable=False)
    height = Column(Float, nullable=False)
    scale = Column(Float, nullable=True)  # Detected scale (e.g., 1/4" = 1')
    classification = Column(String(100), nullable=True)  # foundation, framing, etc.
    ocr_text = Column(Text, nullable=True)
    image_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)

    # Relationships
    document = relationship("Document", back_populates="pages")
    measurements = relationship("Measurement", back_populates="page", cascade="all, delete-orphan")