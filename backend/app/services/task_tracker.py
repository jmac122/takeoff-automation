"""TaskTracker service for unified async task lifecycle management.

Provides both async (FastAPI) and sync (Celery worker) helpers so that
every task records its lifecycle in the task_records table.
"""

import traceback as tb_module
from datetime import datetime, timezone

import structlog
from sqlalchemy import func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.models.task import TaskRecord

logger = structlog.get_logger()


class TaskTracker:
    """Static helper methods for task lifecycle tracking."""

    # ------------------------------------------------------------------
    # Async methods — called from FastAPI routes (AsyncSession)
    # ------------------------------------------------------------------

    @staticmethod
    async def register_async(
        db: AsyncSession,
        *,
        task_id: str,
        task_type: str,
        task_name: str,
        project_id: str | None = None,
        metadata: dict | None = None,
    ) -> TaskRecord:
        """Register a newly queued task in the database.

        Called from API route handlers immediately after `task.delay()`.
        """
        record = TaskRecord(
            task_id=task_id,
            project_id=project_id,
            task_type=task_type,
            task_name=task_name,
            status="PENDING",
            progress_percent=0.0,
            task_metadata=metadata,
        )
        db.add(record)
        await db.commit()
        logger.info(
            "Task registered",
            task_id=task_id,
            task_type=task_type,
            task_name=task_name,
        )
        return record

    # ------------------------------------------------------------------
    # Sync methods — called from Celery workers (Session)
    # ------------------------------------------------------------------

    @staticmethod
    def mark_started_sync(db: Session, task_id: str) -> None:
        """Mark a task as started."""
        record = db.query(TaskRecord).filter(TaskRecord.task_id == task_id).one_or_none()
        if not record:
            logger.warning("TaskRecord not found for mark_started", task_id=task_id)
            return
        record.status = "STARTED"
        record.started_at = datetime.now(timezone.utc)
        db.commit()

    @staticmethod
    def update_progress_sync(
        db: Session,
        task_id: str,
        percent: float,
        step: str | None = None,
    ) -> None:
        """Update task progress from a worker."""
        record = db.query(TaskRecord).filter(TaskRecord.task_id == task_id).one_or_none()
        if not record:
            logger.warning("TaskRecord not found for update_progress", task_id=task_id)
            return
        record.status = "PROGRESS"
        record.progress_percent = percent
        record.progress_step = step
        db.commit()

    @staticmethod
    def mark_completed_sync(
        db: Session,
        task_id: str,
        result_summary: dict | None = None,
    ) -> None:
        """Mark a task as successfully completed."""
        record = db.query(TaskRecord).filter(TaskRecord.task_id == task_id).one_or_none()
        if not record:
            logger.warning("TaskRecord not found for mark_completed", task_id=task_id)
            return
        record.status = "SUCCESS"
        record.progress_percent = 100.0
        record.completed_at = datetime.now(timezone.utc)
        record.result_summary = result_summary
        db.commit()

    @staticmethod
    def mark_failed_sync(
        db: Session,
        task_id: str,
        error_message: str,
        error_traceback: str | None = None,
    ) -> None:
        """Mark a task as failed."""
        record = db.query(TaskRecord).filter(TaskRecord.task_id == task_id).one_or_none()
        if not record:
            logger.warning("TaskRecord not found for mark_failed", task_id=task_id)
            return
        record.status = "FAILURE"
        record.completed_at = datetime.now(timezone.utc)
        record.error_message = error_message
        record.error_traceback = error_traceback
        db.commit()
