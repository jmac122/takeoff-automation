"""Measurement endpoints."""

import uuid
from typing import Annotated

import structlog

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db
from app.models.measurement import Measurement
from app.schemas.measurement import (
    MeasurementCreate,
    MeasurementUpdate,
    MeasurementResponse,
    MeasurementListResponse,
)
from app.schemas.geometry_adjust import GeometryAdjustRequest, GeometryAdjustResponse
from app.services.measurement_engine import get_measurement_engine
from app.services.geometry_adjuster import get_geometry_adjuster

router = APIRouter()
logger = structlog.get_logger()


@router.get(
    "/conditions/{condition_id}/measurements", response_model=MeasurementListResponse
)
async def list_condition_measurements(
    condition_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List all measurements for a condition."""
    result = await db.execute(
        select(Measurement)
        .where(Measurement.condition_id == condition_id)
        .order_by(Measurement.created_at)
    )
    measurements = result.scalars().all()

    return MeasurementListResponse(
        measurements=[MeasurementResponse.model_validate(m) for m in measurements],
        total=len(measurements),
    )


@router.get("/pages/{page_id}/measurements", response_model=MeasurementListResponse)
async def list_page_measurements(
    page_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List all measurements on a page."""
    result = await db.execute(
        select(Measurement)
        .options(selectinload(Measurement.condition))
        .where(Measurement.page_id == page_id)
    )
    measurements = result.scalars().all()

    return MeasurementListResponse(
        measurements=[MeasurementResponse.model_validate(m) for m in measurements],
        total=len(measurements),
    )


@router.post(
    "/conditions/{condition_id}/measurements",
    response_model=MeasurementResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_measurement(
    condition_id: uuid.UUID,
    request: MeasurementCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new measurement."""
    engine = get_measurement_engine()

    try:
        measurement = await engine.create_measurement(
            session=db,
            condition_id=condition_id,
            page_id=request.page_id,
            geometry_type=request.geometry_type,
            geometry_data=request.geometry_data,
            notes=request.notes,
        )
        return MeasurementResponse.model_validate(measurement)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/measurements/{measurement_id}", response_model=MeasurementResponse)
async def get_measurement(
    measurement_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get measurement details."""
    result = await db.execute(
        select(Measurement).where(Measurement.id == measurement_id)
    )
    measurement = result.scalar_one_or_none()

    if not measurement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Measurement not found",
        )

    return MeasurementResponse.model_validate(measurement)


@router.put("/measurements/{measurement_id}", response_model=MeasurementResponse)
async def update_measurement(
    measurement_id: uuid.UUID,
    request: MeasurementUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update a measurement."""
    engine = get_measurement_engine()

    try:
        measurement = await engine.update_measurement(
            session=db,
            measurement_id=measurement_id,
            geometry_data=request.geometry_data,
            notes=request.notes,
        )
        return MeasurementResponse.model_validate(measurement)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/measurements/{measurement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_measurement(
    measurement_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete a measurement."""
    engine = get_measurement_engine()

    try:
        await engine.delete_measurement(db, measurement_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/measurements/{measurement_id}/recalculate", response_model=MeasurementResponse
)
async def recalculate_measurement(
    measurement_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Recalculate a measurement (e.g., after scale change)."""
    engine = get_measurement_engine()

    try:
        measurement = await engine.recalculate_measurement(db, measurement_id)
        return MeasurementResponse.model_validate(measurement)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


async def _recalculate_measurements_batch(
    db: AsyncSession,
    measurement_ids: list[uuid.UUID],
    log_context: dict[str, str],
) -> dict:
    """Helper to recalculate a list of measurements and log failures.

    Args:
        db: Database session
        measurement_ids: List of measurement UUIDs to recalculate
        log_context: Additional context for logging (e.g., page_id or condition_id)

    Returns:
        Dict with status, recalculated_count, failed_count, and failed_ids
    """
    engine = get_measurement_engine()
    recalculated_count = 0
    failed_ids: list[str] = []

    for mid in measurement_ids:
        try:
            await engine.recalculate_measurement(db, mid)
            recalculated_count += 1
        except ValueError as exc:
            failed_ids.append(str(mid))
            logger.warning(
                "measurement_recalculate_failed",
                measurement_id=str(mid),
                **log_context,
                error=str(exc),
                exc_info=True,
            )

    return {
        "status": "success",
        "recalculated_count": recalculated_count,
        "failed_count": len(failed_ids),
        "failed_ids": failed_ids,
    }


@router.post("/pages/{page_id}/recalculate-all")
async def recalculate_page_measurements(
    page_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Recalculate all measurements on a page (after scale change)."""
    result = await db.execute(
        select(Measurement.id).where(Measurement.page_id == page_id)
    )
    measurement_ids = [row[0] for row in result.all()]

    return await _recalculate_measurements_batch(
        db, measurement_ids, {"page_id": str(page_id)}
    )


@router.post("/conditions/{condition_id}/recalculate-all")
async def recalculate_condition_measurements(
    condition_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Recalculate all measurements for a condition (after unit/type change)."""
    result = await db.execute(
        select(Measurement.id).where(Measurement.condition_id == condition_id)
    )
    measurement_ids = [row[0] for row in result.all()]

    return await _recalculate_measurements_batch(
        db, measurement_ids, {"condition_id": str(condition_id)}
    )


@router.put(
    "/measurements/{measurement_id}/adjust",
    response_model=GeometryAdjustResponse,
)
async def adjust_measurement(
    measurement_id: uuid.UUID,
    request: GeometryAdjustRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Apply a quick-adjust geometry operation to a measurement.

    Supported actions: nudge, snap_to_grid, extend, trim, offset, split, join.
    """
    adjuster = get_geometry_adjuster()

    try:
        measurement, created_id = await adjuster.adjust_measurement(
            session=db,
            measurement_id=measurement_id,
            action=request.action,
            params=request.params,
        )

        return GeometryAdjustResponse(
            action=request.action,
            measurement_id=str(measurement.id),
            new_geometry_type=measurement.geometry_type,
            new_geometry_data=measurement.geometry_data,
            new_quantity=measurement.quantity,
            new_unit=measurement.unit,
            created_measurement_id=str(created_id) if created_id else None,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
