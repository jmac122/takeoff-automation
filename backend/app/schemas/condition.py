"""Condition schemas."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ConditionCreate(BaseModel):
    """Request to create a condition."""
    
    name: str
    description: str | None = None
    scope: str = "concrete"
    category: str | None = None
    measurement_type: str  # linear, area, volume, count
    color: str = "#3B82F6"
    line_width: int = 2
    fill_opacity: float = 0.3
    unit: str = "LF"  # LF, SF, CY, EA
    depth: float | None = None
    thickness: float | None = None
    sort_order: int = 0
    extra_metadata: dict[str, Any] | None = None


class ConditionUpdate(BaseModel):
    """Request to update a condition."""
    
    name: str | None = None
    description: str | None = None
    scope: str | None = None
    category: str | None = None
    measurement_type: str | None = None
    color: str | None = None
    line_width: int | None = None
    fill_opacity: float | None = None
    unit: str | None = None
    depth: float | None = None
    thickness: float | None = None
    sort_order: int | None = None
    extra_metadata: dict[str, Any] | None = None


class ConditionResponse(BaseModel):
    """Condition response schema."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    description: str | None
    scope: str
    category: str | None
    measurement_type: str
    color: str
    line_width: int
    fill_opacity: float
    unit: str
    depth: float | None
    thickness: float | None
    total_quantity: float
    measurement_count: int
    sort_order: int
    extra_metadata: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


class ConditionListResponse(BaseModel):
    """Response for listing conditions."""
    
    conditions: list[ConditionResponse]
    total: int


class MeasurementSummary(BaseModel):
    """Brief measurement info for condition details."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    page_id: uuid.UUID
    geometry_type: str
    quantity: float
    unit: str
    is_ai_generated: bool
    is_verified: bool


class ConditionWithMeasurementsResponse(ConditionResponse):
    """Condition with its measurements."""

    measurements: list[MeasurementSummary] = []


class ConditionTemplateResponse(BaseModel):
    """Condition template response."""

    name: str
    scope: str
    category: str | None = None
    measurement_type: str
    unit: str
    depth: float | None = None
    thickness: float | None = None
    color: str
    line_width: int = 2
    fill_opacity: float = 0.3
