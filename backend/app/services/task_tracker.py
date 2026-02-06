"""TaskTracker service for unified async task lifecycle management.

Provides both async (FastAPI) and sync (Celery worker) helpers so that
every task records its lifecycle in the task_records table.
"""

from datetime import datetime, timezone

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.models.task import TaskRecord, TaskStatus

logger = structlog.get_logger()


def _get_record_sync(db: Session, task_id: str, caller: str) -> TaskRecord | None:
    """Fetch a TaskRecord by PK, logging a warning if missing."""
    record = db.get(TaskRecord, task_id)
    if not record:
        logger.warning("TaskRecord not found", task_id=task_id, caller=caller)
    return record


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
            status=TaskStatus.PENDING,
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
        record = _get_record_sync(db, task_id, "mark_started")
        if not record:
            return
        record.status = TaskStatus.STARTED
        record.started_at = datetime.now(timezone.utc)
        db.commit()

    @staticmethod
    def _apply_progress_update(
        db: Session,
        task_id: str,
        percent: float,
        step: str | None,
    ) -> None:
        """Internal helper that writes progress to the DB."""
        record = _get_record_sync(db, task_id, "update_progress")
        if not record:
            return
        record.status = TaskStatus.PROGRESS
        record.progress_percent = percent
        record.progress_step = step
        db.commit()

    @staticmethod
    def update_progress_sync(
        db: Session,
        task_id: str,
        percent: float,
        step: str | None = None,
    ) -> None:
        """Update task progress from a worker.

        If the caller's session has uncommitted changes, an isolated session
        is used to avoid accidentally committing partial work.
        """
        if db.new or db.dirty or db.deleted:
            isolated_db = Session(db.bind)
            try:
                TaskTracker._apply_progress_update(
                    isolated_db,
                    task_id=task_id,
                    percent=percent,
                    step=step,
                )
            finally:
                isolated_db.close()
            return

        TaskTracker._apply_progress_update(
            db,
            task_id=task_id,
            percent=percent,
            step=step,
        )

    @staticmethod
    def mark_completed_sync(
        db: Session,
        task_id: str,
        result_summary: dict | None = None,
        *,
        commit: bool = True,
    ) -> None:
        """Mark a task as successfully completed."""
        record = _get_record_sync(db, task_id, "mark_completed")
        if not record:
            return
        record.status = TaskStatus.SUCCESS
        record.progress_percent = 100.0
        record.completed_at = datetime.now(timezone.utc)
        record.result_summary = result_summary
        if commit:
            db.commit()

    @staticmethod
    def mark_failed_sync(
        db: Session,
        task_id: str,
        error_message: str,
        error_traceback: str | None = None,
    ) -> None:
        """Mark a task as failed."""
        record = _get_record_sync(db, task_id, "mark_failed")
        if not record:
            return
        record.status = TaskStatus.FAILURE
        record.completed_at = datetime.now(timezone.utc)
        record.error_message = error_message
        record.error_traceback = error_traceback
        db.commit()
