"""Export routes."""

from fastapi import APIRouter

router = APIRouter()


@router.post("/")
async def create_export() -> dict:
    """Create an export."""
    return {"id": "stub", "message": "Export created"}