"""Review schemas for measurement review workflow."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.measurement import MeasurementResponse


# ============================================================================
# Request Schemas
# ============================================================================


class ApproveRequest(BaseModel):
    """Request to approve a measurement."""

    reviewer: str = Field(..., min_length=1)
    notes: str | None = None


class RejectRequest(BaseModel):
    """Request to reject a measurement."""

    reviewer: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)


class ModifyRequest(BaseModel):
    """Request to modify a measurement's geometry during review."""

    reviewer: str = Field(..., min_length=1)
    geometry_data: dict[str, Any]
    notes: str | None = None


class AutoAcceptRequest(BaseModel):
    """Request to auto-accept high-confidence measurements."""

    threshold: float = Field(default=0.90, ge=0.5, le=1.0)
    reviewer: str | None = None


# ============================================================================
# Response Schemas
# ============================================================================


class ReviewActionResponse(BaseModel):
    """Response after a review action."""

    status: str
    measurement_id: uuid.UUID
    new_quantity: float | None = None


class AutoAcceptResponse(BaseModel):
    """Response after auto-accept batch operation."""

    auto_accepted_count: int
    threshold: float


class NextUnreviewedResponse(BaseModel):
    """Response for next-unreviewed navigation."""

    measurement: MeasurementResponse | None = None
    remaining_count: int


# ============================================================================
# Statistics Schemas
# ============================================================================


class ConfidenceDistribution(BaseModel):
    """Distribution of AI confidence levels."""

    high: int = 0   # >= 0.9
    medium: int = 0  # 0.7 - 0.9
    low: int = 0     # < 0.7


class ReviewStatisticsResponse(BaseModel):
    """Review statistics for a project."""

    total: int = 0
    pending: int = 0
    approved: int = 0
    rejected: int = 0
    modified: int = 0
    ai_generated_count: int = 0
    ai_accuracy_percent: float = 0.0
    confidence_distribution: ConfidenceDistribution = ConfidenceDistribution()


# ============================================================================
# History Schema
# ============================================================================


class MeasurementHistoryResponse(BaseModel):
    """Response for a measurement history entry."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    measurement_id: uuid.UUID
    action: str
    actor: str
    actor_type: str
    previous_status: str | None = None
    new_status: str | None = None
    previous_quantity: float | None = None
    new_quantity: float | None = None
    change_description: str | None = None
    notes: str | None = None
    created_at: datetime
