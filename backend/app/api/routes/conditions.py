"""Condition routes."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_conditions() -> dict:
    """List all conditions."""
    return {"conditions": []}