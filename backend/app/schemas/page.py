"""Page schemas."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class PageResponse(BaseModel):
    """Page response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_id: uuid.UUID
    page_number: int
    width: int
    height: int
    classification: str | None = None
    classification_confidence: float | None = None
    concrete_relevance: str | None = None
    title: str | None = None
    sheet_number: str | None = None
    scale_text: str | None = None
    scale_value: float | None = None
    scale_unit: str = "foot"
    scale_calibrated: bool = False
    status: str
    image_url: str | None = None
    thumbnail_url: str | None = None


class PageSummaryResponse(BaseModel):
    """Brief page response for listings."""

    id: uuid.UUID
    document_id: uuid.UUID
    page_number: int
    width: int
    height: int
    classification: str | None = None
    concrete_relevance: str | None = None
    title: str | None = None
    sheet_number: str | None = None
    scale_text: str | None = None
    scale_calibrated: bool = False
    status: str
    image_url: str | None = None  # Full resolution image
    thumbnail_url: str | None = None  # Small preview


class PageListResponse(BaseModel):
    """Response for listing pages."""

    pages: list[PageSummaryResponse]
    total: int


class PageOCRResponse(BaseModel):
    """OCR data response."""

    full_text: str | None = None
    blocks: list[dict[str, Any]] = []
    detected_scales: list[str] = []
    detected_sheet_numbers: list[str] = []
    detected_titles: list[str] = []
    sheet_number: str | None = None
    title: str | None = None
    scale_text: str | None = None


class ScaleUpdateRequest(BaseModel):
    """Request to update page scale."""

    scale_value: float  # pixels per foot
    scale_unit: str = "foot"
    scale_text: str | None = None
