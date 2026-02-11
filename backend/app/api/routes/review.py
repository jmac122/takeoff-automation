"""Review endpoints for measurement review workflow."""

import uuid
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.measurement import MeasurementResponse
from app.schemas.review import (
    ApproveRequest,
    AutoAcceptRequest,
    AutoAcceptResponse,
    MeasurementHistoryResponse,
    ModifyRequest,
    NextUnreviewedResponse,
    RejectRequest,
    ReviewActionResponse,
    ReviewStatisticsResponse,
)
from app.services.review_service import get_review_service

router = APIRouter()
logger = structlog.get_logger()


@router.post(
    "/measurements/{measurement_id}/approve",
    response_model=ReviewActionResponse,
)
async def approve_measurement(
    measurement_id: uuid.UUID,
    request: ApproveRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Approve a measurement."""
    service = get_review_service()

    try:
        measurement = await service.approve_measurement(
            session=db,
            measurement_id=measurement_id,
            reviewer=request.reviewer,
            notes=request.notes,
        )
        return ReviewActionResponse(
            status="approved",
            measurement_id=measurement.id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/measurements/{measurement_id}/reject",
    response_model=ReviewActionResponse,
)
async def reject_measurement(
    measurement_id: uuid.UUID,
    request: RejectRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Reject a measurement (soft-delete)."""
    service = get_review_service()

    try:
        measurement = await service.reject_measurement(
            session=db,
            measurement_id=measurement_id,
            reviewer=request.reviewer,
            reason=request.reason,
        )
        return ReviewActionResponse(
            status="rejected",
            measurement_id=measurement.id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/measurements/{measurement_id}/modify",
    response_model=ReviewActionResponse,
)
async def modify_measurement(
    measurement_id: uuid.UUID,
    request: ModifyRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Modify a measurement's geometry during review."""
    service = get_review_service()

    try:
        measurement = await service.modify_measurement(
            session=db,
            measurement_id=measurement_id,
            reviewer=request.reviewer,
            geometry_data=request.geometry_data,
            notes=request.notes,
        )
        return ReviewActionResponse(
            status="modified",
            measurement_id=measurement.id,
            new_quantity=measurement.quantity,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/projects/{project_id}/measurements/auto-accept",
    response_model=AutoAcceptResponse,
)
async def auto_accept_measurements(
    project_id: uuid.UUID,
    request: AutoAcceptRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Auto-accept high-confidence AI measurements for a project."""
    service = get_review_service()

    count = await service.auto_accept_batch(
        session=db,
        project_id=project_id,
        threshold=request.threshold,
        reviewer=request.reviewer,
    )

    return AutoAcceptResponse(
        auto_accepted_count=count,
        threshold=request.threshold,
    )


@router.get(
    "/projects/{project_id}/review-stats",
    response_model=ReviewStatisticsResponse,
)
async def get_review_stats(
    project_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get review statistics for a project."""
    service = get_review_service()

    stats = await service.get_review_stats(
        session=db,
        project_id=project_id,
    )

    return ReviewStatisticsResponse(**stats)


@router.get(
    "/pages/{page_id}/measurements/next-unreviewed",
    response_model=NextUnreviewedResponse,
)
async def get_next_unreviewed(
    page_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    after: uuid.UUID | None = Query(default=None),
):
    """Get the next unreviewed measurement on a page."""
    service = get_review_service()

    measurement, remaining_count = await service.get_next_unreviewed(
        session=db,
        page_id=page_id,
        after_id=after,
    )

    return NextUnreviewedResponse(
        measurement=MeasurementResponse.model_validate(measurement) if measurement else None,
        remaining_count=remaining_count,
    )


@router.get(
    "/measurements/{measurement_id}/history",
    response_model=list[MeasurementHistoryResponse],
)
async def get_measurement_history(
    measurement_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get the audit history for a measurement."""
    service = get_review_service()

    try:
        history = await service.get_measurement_history(
            session=db,
            measurement_id=measurement_id,
        )
        return [MeasurementHistoryResponse.model_validate(h) for h in history]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
