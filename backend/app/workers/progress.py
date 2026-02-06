"""Shared progress-reporting helper for Celery worker tasks."""

from app.services.task_tracker import TaskTracker


def report_progress(task, db, percent: float, step: str) -> None:
    """Send progress updates to both Celery and the task-tracker DB row.

    This is the single authoritative implementation of the two-call pattern
    (update_state + TaskTracker.update_progress_sync) used across all worker
    modules.  Keeping it in one place ensures the calls never drift out of
    sync.
    """
    task.update_state(state="PROGRESS", meta={"percent": percent, "step": step})
    TaskTracker.update_progress_sync(db, task.request.id, percent, step)
