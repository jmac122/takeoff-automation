"""Document routes."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_documents() -> dict:
    """List all documents."""
    return {"documents": []}