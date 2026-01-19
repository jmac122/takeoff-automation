"""Project schemas."""

from pydantic import BaseModel, ConfigDict


class ProjectCreate(BaseModel):
    """Project creation schema."""

    name: str
    description: str | None = None
    client_name: str | None = None


class ProjectResponse(BaseModel):
    """Project response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None = None
    client_name: str | None = None
    status: str
    created_at: str
    updated_at: str
