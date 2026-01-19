"""Document schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentCreate(BaseModel):
    """Schema for creating a document."""

    project_id: uuid.UUID = Field(..., description="Project to upload document to")


class PageSummary(BaseModel):
    """Brief page information for document responses."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    page_number: int
    classification: str | None = None
    scale_calibrated: bool = False
    thumbnail_url: str | None = None


class DocumentResponse(BaseModel):
    """Document response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    status: str
    page_count: int | None = None
    processing_error: str | None = None
    created_at: datetime
    updated_at: datetime
    pages: list[PageSummary] = []


class DocumentListResponse(BaseModel):
    """Response for listing documents."""

    documents: list[DocumentResponse]
    total: int


class DocumentStatusResponse(BaseModel):
    """Document processing status response."""

    status: str
    page_count: int | None = None
    error: str | None = None
