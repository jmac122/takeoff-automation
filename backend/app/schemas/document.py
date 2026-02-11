"""Document schemas."""

import uuid
from datetime import date, datetime

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


class TitleBlockRegion(BaseModel):
    """Normalized title block region (0-1 coordinates)."""

    x: float = Field(..., ge=0.0, le=1.0)
    y: float = Field(..., ge=0.0, le=1.0)
    width: float = Field(..., gt=0.0, le=1.0)
    height: float = Field(..., gt=0.0, le=1.0)
    source_page_id: uuid.UUID | None = None


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
    title_block_region: TitleBlockRegion | None = None

    # Revision tracking
    revision_number: str | None = None
    revision_date: date | None = None
    revision_label: str | None = None
    supersedes_document_id: uuid.UUID | None = None
    is_latest_revision: bool = True


class DocumentListResponse(BaseModel):
    """Response for listing documents."""

    documents: list[DocumentResponse]
    total: int


class DocumentStatusResponse(BaseModel):
    """Document processing status response."""

    status: str
    page_count: int | None = None
    error: str | None = None


class TitleBlockRegionUpdateRequest(BaseModel):
    """Request to set a document title block region (normalized)."""

    x: float = Field(..., ge=0.0, le=1.0)
    y: float = Field(..., ge=0.0, le=1.0)
    width: float = Field(..., gt=0.0, le=1.0)
    height: float = Field(..., gt=0.0, le=1.0)
    source_page_id: uuid.UUID | None = None


class TitleBlockRegionUpdateResponse(BaseModel):
    """Response for title block region updates."""

    status: str
    document_id: uuid.UUID
    pages_queued: int
    title_block_region: TitleBlockRegion


class LinkRevisionRequest(BaseModel):
    """Request to link a document as a revision of another."""

    supersedes_document_id: uuid.UUID = Field(
        ..., description="ID of the document this one supersedes (previous revision)"
    )
    revision_number: str | None = Field(None, description="Revision identifier (e.g., 'A', 'Rev2')")
    revision_date: date | None = Field(None, description="Date of this revision")
    revision_label: str | None = Field(None, description="Free-form label (e.g., 'Issued for Permit')")


class RevisionChainItem(BaseModel):
    """A single document in a revision chain."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    original_filename: str
    revision_number: str | None = None
    revision_date: date | None = None
    revision_label: str | None = None
    is_latest_revision: bool = True
    page_count: int | None = None
    created_at: datetime


class RevisionChainResponse(BaseModel):
    """Full revision chain for a document."""

    chain: list[RevisionChainItem]
    current_document_id: uuid.UUID


class PageComparisonRequest(BaseModel):
    """Request to compare pages between two document revisions."""

    old_document_id: uuid.UUID
    new_document_id: uuid.UUID
    page_number: int = Field(..., ge=1)


class PageComparisonResponse(BaseModel):
    """Page comparison result with image URLs for overlay."""

    old_page_id: uuid.UUID | None = None
    new_page_id: uuid.UUID | None = None
    old_image_url: str | None = None
    new_image_url: str | None = None
    page_number: int
    has_both: bool = False
