"""Page schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PageSummaryResponse(BaseModel):
    """Brief page information for document responses."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    page_number: int
    width: int
    height: int
    dpi: int
    thumbnail_key: str | None = None
    classification: str | None = None
    scale_calibrated: bool = False
    status: str


class PageResponse(BaseModel):
    """Full page response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_id: uuid.UUID
    page_number: int
    width: int
    height: int
    dpi: int
    image_key: str
    thumbnail_key: str | None = None
    classification: str | None = None
    classification_confidence: float | None = None
    title: str | None = None
    sheet_number: str | None = None
    scale_text: str | None = None
    scale_value: float | None = None
    scale_unit: str = "foot"
    scale_calibrated: bool = False
    scale_calibration_data: dict | None = None
    ocr_text: str | None = None
    ocr_blocks: dict | None = None
    status: str
    processing_error: str | None = None
    created_at: datetime
    updated_at: datetime


class PageListResponse(BaseModel):
    """Response for listing pages."""

    pages: list[PageSummaryResponse]
    total: int


class PageOCRResponse(BaseModel):
    """OCR data response."""

    ocr_text: str | None = None
    ocr_blocks: dict | None = None
    detected_scale_texts: list[str] = []
    detected_sheet_numbers: list[str] = []
    detected_titles: list[str] = []


class ScaleUpdateRequest(BaseModel):
    """Request to update page scale."""

    scale_text: str | None = None
    scale_value: float
    scale_unit: str = "foot"
    scale_calibrated: bool = True
    scale_calibration_data: dict | None = None
