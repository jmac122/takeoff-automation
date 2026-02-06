"""Sheets endpoint — aggregated sheet tree for the workspace UI.

Provides a single query returning all pages for a project grouped by
discipline/group_name, with classification, scale, and measurement data
pre-joined to avoid N+1 queries.
"""

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db
from app.models.page import Page
from app.models.document import Document
from app.models.project import Project
from app.models.measurement import Measurement
from app.utils.storage import get_storage_service

router = APIRouter()


# ============================================================================
# Schemas
# ============================================================================

class SheetInfoResponse(BaseModel):
    """Single sheet in the tree."""
    id: uuid.UUID
    document_id: uuid.UUID
    page_number: int
    sheet_number: str | None = None
    title: str | None = None
    display_name: str | None = None
    display_order: int | None = None
    group_name: str | None = None
    discipline: str | None = None
    page_type: str | None = None
    classification: str | None = None
    classification_confidence: float | None = None
    scale_text: str | None = None
    scale_value: float | None = None
    scale_calibrated: bool = False
    scale_detection_method: str | None = None
    measurement_count: int = 0
    thumbnail_url: str | None = None
    image_url: str | None = None
    width: int = 0
    height: int = 0
    is_relevant: bool = True


class SheetGroupResponse(BaseModel):
    """Group of sheets (by discipline or group_name)."""
    group_name: str
    sheets: list[SheetInfoResponse]


class SheetsResponse(BaseModel):
    """Top-level response for GET /projects/{id}/sheets."""
    groups: list[SheetGroupResponse]
    total: int


class PageDisplayUpdateRequest(BaseModel):
    """Request to update page display fields."""
    display_name: str | None = None
    display_order: int | None = None
    group_name: str | None = None


class PageRelevanceUpdateRequest(BaseModel):
    """Request to update page relevance."""
    is_relevant: bool


class BatchScaleRequest(BaseModel):
    """Batch scale update request."""
    page_ids: list[uuid.UUID]
    scale_value: float
    scale_text: str | None = None
    scale_unit: str = "foot"


# ============================================================================
# Helpers
# ============================================================================

def _get_viewer_image_key(image_key: str) -> str:
    """Get the PNG viewer image key from a TIFF storage key."""
    if image_key.endswith(".tiff"):
        return image_key.replace(".tiff", ".png")
    return image_key


def _natural_sort_key(page_row: Any) -> tuple:
    """Natural sort key for sheet ordering."""
    import re

    # Prefer display_order if set
    display_order = getattr(page_row, 'display_order', None)
    if display_order is not None:
        return (0, display_order, 0)

    # Fall back to sheet_number natural sort
    sheet_number = getattr(page_row, 'sheet_number', None)
    if sheet_number:
        parts = re.split(r"(\d+\.?\d*)", sheet_number)
        key_parts = []
        for p in parts:
            if p:
                if p.replace(".", "", 1).isdigit():
                    key_parts.append((1, float(p)))
                else:
                    key_parts.append((0, p.lower()))
        return (1, 0, key_parts)

    page_number = getattr(page_row, 'page_number', 0)
    return (2, page_number, [])


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/projects/{project_id}/sheets", response_model=SheetsResponse)
async def get_project_sheets(
    project_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get all sheets for a project, grouped by discipline.

    Returns sheets with classification, scale, and measurement count data
    pre-joined in a single query. Only relevant (is_relevant=True) pages
    are included.
    """
    # Verify project exists
    project_result = await db.execute(
        select(Project.id).where(Project.id == project_id)
    )
    if not project_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Single query: pages with measurement count
    # Subquery for measurement counts
    measurement_count_subq = (
        select(
            Measurement.page_id,
            func.count(Measurement.id).label("measurement_count"),
        )
        .group_by(Measurement.page_id)
        .subquery()
    )

    # Main query: pages for project, joined with documents
    query = (
        select(
            Page,
            func.coalesce(measurement_count_subq.c.measurement_count, 0).label(
                "measurement_count"
            ),
        )
        .join(Document, Page.document_id == Document.id)
        .outerjoin(
            measurement_count_subq,
            Page.id == measurement_count_subq.c.page_id,
        )
        .where(Document.project_id == project_id)
        .where(Page.is_relevant == True)  # noqa: E712
        .order_by(Page.page_number)
    )

    result = await db.execute(query)
    rows = result.all()

    # Build grouped response
    storage = get_storage_service()
    groups_dict: dict[str, list[SheetInfoResponse]] = {}

    for row in rows:
        page = row[0]
        mcount = row[1]

        # Determine group name
        group_name = (
            page.group_name
            or page.discipline
            or "Unclassified"
        )

        sheet_info = SheetInfoResponse(
            id=page.id,
            document_id=page.document_id,
            page_number=page.page_number,
            sheet_number=page.sheet_number,
            title=page.title,
            display_name=page.display_name,
            display_order=page.display_order,
            group_name=page.group_name,
            discipline=page.discipline,
            page_type=page.page_type,
            classification=page.classification,
            classification_confidence=page.classification_confidence,
            scale_text=page.scale_text,
            scale_value=page.scale_value,
            scale_calibrated=page.scale_calibrated,
            scale_detection_method=page.scale_detection_method,
            measurement_count=mcount,
            thumbnail_url=(
                storage.get_presigned_url(page.thumbnail_key, 3600)
                if page.thumbnail_key
                else None
            ),
            image_url=storage.get_presigned_url(
                _get_viewer_image_key(page.image_key), 3600
            ),
            width=page.width,
            height=page.height,
            is_relevant=page.is_relevant,
        )

        groups_dict.setdefault(group_name, []).append(sheet_info)

    # Sort sheets within each group
    for sheets in groups_dict.values():
        sheets.sort(key=lambda s: _natural_sort_key(s))

    # Build response
    groups = [
        SheetGroupResponse(group_name=name, sheets=sheets)
        for name, sheets in sorted(groups_dict.items())
    ]

    total = sum(len(g.sheets) for g in groups)

    return SheetsResponse(groups=groups, total=total)


@router.put("/pages/{page_id}/display")
async def update_page_display(
    page_id: uuid.UUID,
    request: PageDisplayUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update display fields for a page (display_name, display_order, group_name)."""
    result = await db.execute(select(Page).where(Page.id == page_id))
    page = result.scalar_one_or_none()

    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found",
        )

    if "display_name" in request.model_fields_set:
        page.display_name = request.display_name
    if "display_order" in request.model_fields_set:
        page.display_order = request.display_order
    if "group_name" in request.model_fields_set:
        page.group_name = request.group_name

    await db.commit()

    return {
        "status": "success",
        "page_id": str(page_id),
        "display_name": page.display_name,
        "display_order": page.display_order,
        "group_name": page.group_name,
    }


@router.put("/pages/{page_id}/relevance")
async def update_page_relevance(
    page_id: uuid.UUID,
    request: PageRelevanceUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update relevance flag for a page. Irrelevant pages are excluded from sheets."""
    result = await db.execute(select(Page).where(Page.id == page_id))
    page = result.scalar_one_or_none()

    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found",
        )

    page.is_relevant = request.is_relevant
    await db.commit()

    return {
        "status": "success",
        "page_id": str(page_id),
        "is_relevant": page.is_relevant,
    }


@router.post("/pages/batch-scale")
async def batch_update_scale(
    request: BatchScaleRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Apply the same scale to multiple pages at once."""
    # Fetch all pages in a single query to avoid N+1
    result = await db.execute(
        select(Page).where(Page.id.in_(request.page_ids))
    )
    pages = result.scalars().all()

    if not pages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No pages found for the provided page_ids",
        )

    found_ids = {str(p.id) for p in pages}
    requested_ids = {str(pid) for pid in request.page_ids}
    missing_ids = list(requested_ids - found_ids)

    updated = []
    for page in pages:
        page.scale_value = request.scale_value
        page.scale_unit = request.scale_unit
        page.scale_calibrated = True
        page.scale_detection_method = "manual_calibration"
        page.scale_text = request.scale_text
        page.scale_calibration_data = {
            **(page.scale_calibration_data or {}),
            "batch_applied": True,
        }
        updated.append(str(page.id))

    await db.commit()

    response: dict[str, Any] = {
        "status": "success",
        "updated_pages": updated,
        "count": len(updated),
    }
    if missing_ids:
        response["missing_ids"] = missing_ids

    return response
