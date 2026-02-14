"""API routes for Auto Count feature."""

import uuid
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.condition import Condition
from app.models.page import Page
from app.models.document import Document
from app.schemas.auto_count import (
    AutoCountCreateRequest,
    AutoCountStartResponse,
    BulkConfirmRequest,
    DetectionResponse,
    SessionDetailResponse,
    SessionResponse,
)
from app.schemas.task import StartTaskResponse
from app.services.auto_count.orchestrator import get_auto_count_service
from app.services.task_tracker import TaskTracker

router = APIRouter()
logger = structlog.get_logger()


# ---------------------------------------------------------------------------
# Start auto count
# ---------------------------------------------------------------------------


@router.post(
    "/pages/{page_id}/auto-count",
    response_model=AutoCountStartResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_auto_count(
    page_id: uuid.UUID,
    request: AutoCountCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Start an auto-count detection on a page.

    Creates a session and dispatches a background task for detection.
    """
    # Verify page exists
    page = await db.get(Page, page_id)
    if page is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found",
        )

    # Verify condition exists
    condition = await db.get(Condition, request.condition_id)
    if condition is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Condition not found",
        )

    # Verify page and condition belong to same project
    result = await db.execute(
        select(Document).where(Document.id == page.document_id)
    )
    document = result.scalar_one_or_none()
    if document and document.project_id != condition.project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page and condition must belong to the same project",
        )

    service = get_auto_count_service()

    try:
        session = await service.create_session(
            db=db,
            page_id=page_id,
            condition_id=request.condition_id,
            template_bbox=request.template_bbox.model_dump(),
            confidence_threshold=request.confidence_threshold,
            scale_tolerance=request.scale_tolerance,
            rotation_tolerance=request.rotation_tolerance,
            detection_method=request.detection_method,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Register and dispatch Celery task
    task_id = str(uuid.uuid4())
    project_id = str(document.project_id) if document else ""

    await TaskTracker.register_async(
        db,
        task_id=task_id,
        task_type="auto_count",
        task_name=f"Auto Count on page",
        project_id=project_id,
        metadata={
            "session_id": str(session.id),
            "page_id": str(page_id),
            "condition_id": str(request.condition_id),
            "detection_method": request.detection_method,
        },
    )

    from app.workers.auto_count_tasks import auto_count_task

    auto_count_task.apply_async(
        args=[str(session.id)],
        kwargs={
            "provider": request.provider,
        },
        task_id=task_id,
    )

    return AutoCountStartResponse(
        session_id=session.id,
        task_id=task_id,
        status="pending",
    )


# ---------------------------------------------------------------------------
# Session endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/auto-count-sessions/{session_id}",
    response_model=SessionDetailResponse,
)
async def get_session(
    session_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get an auto-count session with all detections."""
    service = get_auto_count_service()

    try:
        session = await service.get_session(db, session_id)
        return SessionDetailResponse.model_validate(session)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/pages/{page_id}/auto-count-sessions",
    response_model=list[SessionResponse],
)
async def list_page_sessions(
    page_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    condition_id: uuid.UUID | None = Query(default=None),
):
    """List auto-count sessions for a page."""
    service = get_auto_count_service()
    sessions = await service.list_sessions(
        db, page_id=page_id, condition_id=condition_id
    )
    return [SessionResponse.model_validate(s) for s in sessions]


# ---------------------------------------------------------------------------
# Detection review
# ---------------------------------------------------------------------------


@router.post(
    "/auto-count-detections/{detection_id}/confirm",
    response_model=DetectionResponse,
)
async def confirm_detection(
    detection_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Confirm a single detection."""
    service = get_auto_count_service()

    try:
        detection = await service.confirm_detection(db, detection_id)
        return DetectionResponse.model_validate(detection)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/auto-count-detections/{detection_id}/reject",
    response_model=DetectionResponse,
)
async def reject_detection(
    detection_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Reject a single detection."""
    service = get_auto_count_service()

    try:
        detection = await service.reject_detection(db, detection_id)
        return DetectionResponse.model_validate(detection)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/auto-count-sessions/{session_id}/bulk-confirm",
)
async def bulk_confirm(
    session_id: uuid.UUID,
    request: BulkConfirmRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Bulk-confirm all pending detections above a confidence threshold."""
    service = get_auto_count_service()

    try:
        count = await service.bulk_confirm_above_threshold(
            db, session_id, request.threshold
        )
        return {"confirmed_count": count, "threshold": request.threshold}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/auto-count-sessions/{session_id}/create-measurements",
)
async def create_measurements(
    session_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create point measurements for all confirmed detections."""
    service = get_auto_count_service()

    try:
        count = await service.create_measurements_from_confirmed(db, session_id)
        return {"measurements_created": count}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
