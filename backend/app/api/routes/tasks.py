"""Unified Task API routes.

Single router for querying status, cancelling, and listing all async tasks
regardless of their type (document processing, AI takeoff, export, etc.).
"""

import uuid
from datetime import datetime, timezone
from typing import Annotated

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.task import TaskRecord
from app.schemas.task import (
    CancelTaskResponse,
    TaskListResponse,
    TaskProgress,
    TaskResponse,
)
from app.workers.celery_app import celery_app

router = APIRouter(prefix="/tasks", tags=["Tasks"])


def _build_task_response(
    celery_result: AsyncResult,
    record: TaskRecord | None,
) -> TaskResponse:
    """Merge live Celery state with persisted TaskRecord."""
    # Start from Celery's authoritative runtime state
    celery_status = celery_result.status
    celery_meta = celery_result.info if isinstance(celery_result.info, dict) else {}

    progress = TaskProgress(
        percent=celery_meta.get("percent", 0.0),
        step=celery_meta.get("step"),
    )

    result_data = None
    error = None
    traceback = None

    if celery_result.ready():
        if celery_result.successful():
            result_data = celery_result.result
        else:
            error = str(celery_result.result) if celery_result.result else "Task failed"
            traceback = celery_result.traceback

    # Overlay with DB record when available (richer metadata)
    if record:
        # DB progress may be more detailed than Celery meta
        if (
            record.progress_percent is not None
            and record.progress_percent > progress.percent
        ):
            progress = TaskProgress(
                percent=record.progress_percent,
                step=record.progress_step,
            )
        # Use DB result/error if Celery state is terminal
        if celery_status in ("SUCCESS", "FAILURE", "REVOKED"):
            if record.result_summary and not result_data:
                result_data = record.result_summary
            if record.error_message and not error:
                error = record.error_message
            if record.error_traceback and not traceback:
                traceback = record.error_traceback

    return TaskResponse(
        task_id=celery_result.id,
        task_type=record.task_type if record else None,
        task_name=record.task_name if record else None,
        status=celery_status,
        progress=progress,
        result=result_data,
        error=error,
        traceback=traceback,
        created_at=record.created_at if record else None,
        started_at=record.started_at if record else None,
        completed_at=record.completed_at if record else None,
        project_id=str(record.project_id) if record and record.project_id else None,
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task_status(
    task_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TaskResponse:
    """Get the status of any async task by its Celery task ID."""
    celery_result = AsyncResult(task_id, app=celery_app)

    result = await db.execute(
        select(TaskRecord).where(TaskRecord.task_id == task_id)
    )
    record = result.scalar_one_or_none()

    return _build_task_response(celery_result, record)


@router.post("/{task_id}/cancel", response_model=CancelTaskResponse)
async def cancel_task(
    task_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CancelTaskResponse:
    """Cancel a running task."""
    # Send revoke signal to Celery
    celery_app.control.revoke(task_id, terminate=True, signal="SIGTERM")

    # Update DB record if it exists
    result = await db.execute(
        select(TaskRecord).where(TaskRecord.task_id == task_id)
    )
    record = result.scalar_one_or_none()
    if record and record.status not in ("SUCCESS", "FAILURE", "REVOKED"):
        record.status = "REVOKED"
        record.completed_at = datetime.now(timezone.utc)
        await db.commit()

    return CancelTaskResponse(
        task_id=task_id,
        status="REVOKED",
        message="Cancellation signal sent",
    )


@router.get("/project/{project_id}", response_model=TaskListResponse)
async def list_project_tasks(
    project_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    status_filter: str | None = Query(None, alias="status"),
    task_type: str | None = Query(None),
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
) -> TaskListResponse:
    """List all tasks for a project with optional filters."""
    base_filters = [TaskRecord.project_id == project_id]

    if status_filter:
        base_filters.append(TaskRecord.status == status_filter)
    if task_type:
        base_filters.append(TaskRecord.task_type == task_type)

    base = select(TaskRecord).where(*base_filters)

    # Counts
    count_q = select(func.count()).select_from(
        base.subquery()
    )
    total = (await db.execute(count_q)).scalar() or 0

    running_q = select(func.count()).where(
        *base_filters,
        TaskRecord.status.in_(["PENDING", "STARTED", "PROGRESS"]),
    )
    running = (await db.execute(running_q)).scalar() or 0

    completed_q = select(func.count()).where(
        *base_filters,
        TaskRecord.status == "SUCCESS",
    )
    completed = (await db.execute(completed_q)).scalar() or 0

    failed_q = select(func.count()).where(
        *base_filters,
        TaskRecord.status == "FAILURE",
    )
    failed = (await db.execute(failed_q)).scalar() or 0

    # Fetch records
    query = base.order_by(TaskRecord.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    records = result.scalars().all()

    tasks = []
    for rec in records:
        celery_result = AsyncResult(rec.task_id, app=celery_app)
        tasks.append(_build_task_response(celery_result, rec))

    return TaskListResponse(
        tasks=tasks,
        total=total,
        running=running,
        completed=completed,
        failed=failed,
    )
