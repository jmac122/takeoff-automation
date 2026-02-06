"""Export API routes."""

import uuid
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.export_job import ExportJob
from app.models.project import Project
from app.schemas.export import (
    ExportJobResponse,
    ExportListResponse,
    StartExportRequest,
    StartExportResponse,
)
from app.services.task_tracker import TaskTracker
from app.utils.storage import get_storage_service
from app.workers.export_tasks import generate_export_task

logger = structlog.get_logger()

router = APIRouter()


def _export_to_response(export_job: ExportJob) -> ExportJobResponse:
    """Convert ExportJob model to response schema, adding download URL if completed."""
    download_url = None
    if export_job.status == "completed" and export_job.file_key:
        try:
            storage = get_storage_service()
            download_url = storage.get_presigned_url(export_job.file_key, expires_in=3600)
        except Exception as e:
            logger.warning("Failed to generate presigned URL for export", export_id=export_job.id, error=str(e))

    return ExportJobResponse(
        id=export_job.id,
        project_id=export_job.project_id,
        format=export_job.format,
        status=export_job.status,
        file_key=export_job.file_key,
        file_size=export_job.file_size,
        error_message=export_job.error_message,
        download_url=download_url,
        options=export_job.options,
        started_at=export_job.started_at,
        completed_at=export_job.completed_at,
        created_at=export_job.created_at,
        updated_at=export_job.updated_at,
    )


@router.post(
    "/projects/{project_id}/export",
    response_model=StartExportResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_export(
    project_id: uuid.UUID,
    request: StartExportRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StartExportResponse:
    """Start an export job for a project.

    Creates an ExportJob record and queues a Celery task to generate the file.
    """
    # Verify project exists
    proj_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = proj_result.scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    # Create ExportJob
    export_job = ExportJob(
        project_id=project_id,
        format=request.format,
        status="pending",
        options=request.options,
    )
    db.add(export_job)
    await db.flush()

    # Pre-generate task ID and register with TaskTracker
    task_id = str(uuid.uuid4())
    await TaskTracker.register_async(
        db,
        task_id=task_id,
        task_type="export",
        task_name=f"Export {request.format.upper()} for {project.name}",
        project_id=str(project_id),
        metadata={"export_job_id": str(export_job.id), "format": request.format},
    )

    await db.commit()

    # Queue the Celery task with the pre-generated ID
    generate_export_task.apply_async(
        args=[str(export_job.id), str(project_id), request.format, task_id],
        kwargs={"options": request.options},
        task_id=task_id,
    )

    return StartExportResponse(
        task_id=task_id,
        export_id=export_job.id,
        message=f"Export job started for format: {request.format}",
    )


@router.get(
    "/exports/{export_id}",
    response_model=ExportJobResponse,
)
async def get_export(
    export_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ExportJobResponse:
    """Get export job status and download URL."""
    result = await db.execute(
        select(ExportJob).where(ExportJob.id == export_id)
    )
    export_job = result.scalar_one_or_none()
    if not export_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Export {export_id} not found",
        )

    return _export_to_response(export_job)


@router.get(
    "/projects/{project_id}/exports",
    response_model=ExportListResponse,
)
async def list_exports(
    project_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ExportListResponse:
    """List all exports for a project, ordered by newest first."""
    # Verify project exists
    proj_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    if not proj_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    # Count
    count_result = await db.execute(
        select(func.count())
        .select_from(ExportJob)
        .where(ExportJob.project_id == project_id)
    )
    total = count_result.scalar_one()

    # Fetch exports
    result = await db.execute(
        select(ExportJob)
        .where(ExportJob.project_id == project_id)
        .order_by(ExportJob.created_at.desc())
    )
    exports = result.scalars().all()

    return ExportListResponse(
        exports=[_export_to_response(e) for e in exports],
        total=total,
    )


@router.delete(
    "/exports/{export_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_export(
    export_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete an export job and its associated file."""
    result = await db.execute(
        select(ExportJob).where(ExportJob.id == export_id)
    )
    export_job = result.scalar_one_or_none()
    if not export_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Export {export_id} not found",
        )

    # Delete file from storage if it exists
    if export_job.file_key:
        try:
            storage = get_storage_service()
            storage.delete_file(export_job.file_key)
        except Exception as e:
            logger.warning("Failed to delete export file", file_key=export_job.file_key, error=str(e))

    await db.delete(export_job)
    await db.commit()
