"""Project schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProjectCreate(BaseModel):
    """Project creation schema."""

    name: str
    description: str | None = None
    client_name: str | None = None


class ProjectUpdate(BaseModel):
    """Project update schema."""

    name: str | None = None
    description: str | None = None
    client_name: str | None = None
    status: str | None = None


class ProjectResponse(BaseModel):
    """Project response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None = None
    client_name: str | None = None
    project_address: str | None = None
    status: str
    document_count: int = 0
    created_at: datetime
    updated_at: datetime


class ProjectListResponse(BaseModel):
    """Response for listing projects."""
    
    projects: list[ProjectResponse]
    total: int
