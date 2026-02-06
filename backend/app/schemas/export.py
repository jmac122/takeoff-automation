"""Export schemas for request/response models."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class StartExportRequest(BaseModel):
    """Request to start an export job."""

    format: Literal["excel", "ost", "csv", "pdf"]
    options: dict | None = None


class ExportJobResponse(BaseModel):
    """Response for a single export job."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    format: str
    status: str
    file_key: str | None = None
    file_size: int | None = None
    error_message: str | None = None
    download_url: str | None = None
    options: dict | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class StartExportResponse(BaseModel):
    """Response after starting an export."""

    task_id: str
    export_id: uuid.UUID
    message: str


class ExportListResponse(BaseModel):
    """Response for listing exports."""

    exports: list[ExportJobResponse]
    total: int
