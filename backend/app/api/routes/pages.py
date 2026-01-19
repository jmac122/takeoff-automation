"""Page routes."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_pages() -> dict:
    """List all pages."""
    return {"pages": []}