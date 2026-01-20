"""Measurement schemas."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class MeasurementCreate(BaseModel):
    """Request to create a measurement."""

    page_id: uuid.UUID
    geometry_type: str
    geometry_data: dict[str, Any]
    notes: str | None = None


class MeasurementUpdate(BaseModel):
    """Request to update a measurement."""

    geometry_data: dict[str, Any] | None = None
    notes: str | None = None


class MeasurementResponse(BaseModel):
    """Measurement response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    condition_id: uuid.UUID
    page_id: uuid.UUID
    geometry_type: str
    geometry_data: dict[str, Any]
    quantity: float
    unit: str
    pixel_length: float | None = None
    pixel_area: float | None = None
    is_ai_generated: bool
    ai_confidence: float | None = None
    is_modified: bool
    is_verified: bool
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class MeasurementListResponse(BaseModel):
    """Response for listing measurements."""

    measurements: list[MeasurementResponse]
    total: int
