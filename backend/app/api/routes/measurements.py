"""Measurement routes."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_measurements() -> dict:
    """List all measurements."""
    return {"measurements": []}