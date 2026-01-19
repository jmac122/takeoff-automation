"""Project routes."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_projects() -> dict:
    """List all projects."""
    return {"projects": []}


@router.post("/")
async def create_project() -> dict:
    """Create a new project."""
    return {"id": "stub", "message": "Project created"}