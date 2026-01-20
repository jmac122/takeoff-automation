"""Classification history model for tracking LLM classification runs."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import String, Integer, Float, ForeignKey, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.page import Page


class ClassificationHistory(Base):
    """Historical record of page classifications for BI and comparison."""

    __tablename__ = "classification_history"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Foreign key to page
    page_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Classification results
    classification: Mapped[str | None] = mapped_column(String(100), nullable=True)
    classification_confidence: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    discipline: Mapped[str | None] = mapped_column(String(50), nullable=True)
    discipline_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    page_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    page_type_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    concrete_relevance: Mapped[str | None] = mapped_column(String(20), nullable=True)
    concrete_elements: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # LLM metadata for BI
    llm_provider: Mapped[str] = mapped_column(String(50), nullable=False)
    llm_model: Mapped[str] = mapped_column(String(100), nullable=False)
    llm_latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Full raw response for debugging/analysis
    raw_response: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(20), default="success", nullable=False
    )  # success, failed, truncated
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    page: Mapped["Page"] = relationship("Page", back_populates="classification_history")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "page_id": str(self.page_id),
            "status": self.status,
            "error_message": self.error_message,
            "classification": self.classification,
            "classification_confidence": self.classification_confidence,
            "discipline": self.discipline,
            "discipline_confidence": self.discipline_confidence,
            "page_type": self.page_type,
            "page_type_confidence": self.page_type_confidence,
            "concrete_relevance": self.concrete_relevance,
            "concrete_elements": self.concrete_elements,
            "description": self.description,
            "llm_provider": self.llm_provider,
            "llm_model": self.llm_model,
            "llm_latency_ms": self.llm_latency_ms,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
