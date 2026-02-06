"""Task schemas for the Unified Task API."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class TaskProgress(BaseModel):
    """Progress information for a running task."""

    percent: float = 0.0
    step: str | None = None


class TaskResponse(BaseModel):
    """Unified response for any task status query."""

    model_config = ConfigDict(from_attributes=True)

    task_id: str
    task_type: str | None = None
    task_name: str | None = None
    status: str
    progress: TaskProgress = TaskProgress()
    result: Any | None = None
    error: str | None = None
    created_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    project_id: str | None = None


class TaskListResponse(BaseModel):
    """Response for listing tasks within a project."""

    tasks: list[TaskResponse]
    total: int
    running: int
    completed: int
    failed: int
    cancelled: int


class StartTaskResponse(BaseModel):
    """Immediate response after launching a new async task."""

    task_id: str
    task_type: str
    task_name: str
    message: str


class CancelTaskResponse(BaseModel):
    """Response after requesting task cancellation."""

    task_id: str
    status: str
    message: str
