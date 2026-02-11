"""Pydantic schemas for the auto-count feature."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class BBox(BaseModel):
    """Bounding box in pixel coordinates."""

    x: float
    y: float
    w: float = Field(gt=0)
    h: float = Field(gt=0)


class AutoCountCreateRequest(BaseModel):
    """Request to start an auto-count session."""

    condition_id: uuid.UUID
    template_bbox: BBox
    confidence_threshold: float = Field(default=0.80, ge=0.0, le=1.0)
    scale_tolerance: float = Field(default=0.20, ge=0.0, le=1.0)
    rotation_tolerance: float = Field(default=15.0, ge=0.0, le=90.0)
    detection_method: str = Field(
        default="hybrid", pattern=r"^(template|llm|hybrid)$"
    )
    provider: str | None = None


class BulkConfirmRequest(BaseModel):
    """Request to bulk-confirm detections above a confidence threshold."""

    threshold: float = Field(ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class DetectionResponse(BaseModel):
    """Response for a single auto-count detection."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    measurement_id: uuid.UUID | None
    bbox: dict[str, Any]
    center_x: float
    center_y: float
    confidence: float
    detection_source: str
    status: str
    is_auto_confirmed: bool
    created_at: datetime
    updated_at: datetime


class SessionResponse(BaseModel):
    """Response for an auto-count session (without detections)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    page_id: uuid.UUID
    condition_id: uuid.UUID
    template_bbox: dict[str, Any]
    confidence_threshold: float
    scale_tolerance: float
    rotation_tolerance: float
    detection_method: str
    status: str
    total_detections: int
    confirmed_count: int
    rejected_count: int
    error_message: str | None
    processing_time_ms: float | None
    template_match_count: int
    llm_match_count: int
    created_at: datetime
    updated_at: datetime


class SessionDetailResponse(SessionResponse):
    """Session response with nested detections."""

    detections: list[DetectionResponse] = []


class AutoCountStartResponse(BaseModel):
    """Response when starting an auto-count task."""

    session_id: uuid.UUID
    task_id: str
    status: str = "pending"
