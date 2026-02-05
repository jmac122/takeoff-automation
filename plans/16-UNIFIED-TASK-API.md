# Phase 2.5: Unified Async Task API
## Shared Task Polling, Progress Tracking, and Cancellation

> **Duration**: Weeks 5-6 (parallel with Document Ingestion)
> **Prerequisites**: Project setup complete (Phase 1), Celery configured
> **Outcome**: Single unified API for tracking all async operations with consistent schemas, progress reporting, and frontend polling hook

---

## Context for LLM Assistant

You are implementing a unified task management API that replaces the current ad-hoc task status checking scattered across multiple routers. Currently, `GET /tasks/{task_id}/status` exists only in the takeoff router (`api/routes/takeoff.py`), while document processing, OCR, classification, and scale detection tasks have no standardized polling endpoints.

### Current State (What Exists)

The codebase already has:

1. **Celery app** (`workers/celery_app.py`) with task tracking enabled (`task_track_started=True`)
2. **Six task modules**: `document_tasks.py`, `ocr_tasks.py`, `classification_tasks.py`, `scale_tasks.py`, `takeoff_tasks.py`, `tasks.py`
3. **One polling endpoint**: `GET /tasks/{task_id}/status` in `api/routes/takeoff.py`
4. **Task response schema**: `TaskStatusResponse` in `api/routes/takeoff.py`

### What This Phase Builds

A shared `/api/tasks/` router that:
- Replaces the existing takeoff-scoped task endpoint
- Adds progress reporting (percent complete, current step name)
- Adds task cancellation
- Adds project-level task listing (see all running/recent tasks)
- Provides a consistent `TaskResponse` schema all routes use
- Provides a frontend `useTaskPolling()` hook that all components share

### Why This Matters

Without this, every new async feature (auto count, export generation, batch operations) would need its own polling implementation. The frontend would have multiple competing polling patterns. This is cheap to build now and prevents significant duplication.

### Design Principles

1. **Backward compatible**: Old `GET /tasks/{task_id}/status` continues to work (redirects)
2. **Celery-native**: Uses `AsyncResult` and Celery's built-in state machine
3. **Progress-aware**: Tasks can report incremental progress via `self.update_state()`
4. **Cancelable**: Tasks check for revocation between steps
5. **Listable**: Frontend can show "3 tasks running" in a project status bar

---

## Database Models

### Task 16.1: Task Metadata Model (Optional Persistence)

Celery stores task state in Redis (the result backend), which is ephemeral. For audit trails and historical task listing, we optionally persist task metadata to PostgreSQL.

Create `backend/app/models/task.py`:

```python
"""Task tracking model for persistent task history."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import String, Float, Integer, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class TaskRecord(Base, TimestampMixin):
    """
    Persistent record of an async task.
    
    Supplements Celery's ephemeral Redis state with a durable record
    for audit trails and historical task listing. Not all tasks need
    persistence — only those where history matters (AI takeoff, 
    document processing, exports).
    
    The primary key is the Celery task_id (string), not a UUID,
    because Celery assigns its own IDs.
    """

    __tablename__ = "task_records"

    # Celery task ID as primary key
    task_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    
    # Link to project (for project-level task listing)
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    
    # Task classification
    task_type: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True,
    )  # e.g., "document_processing", "ai_takeoff", "auto_count", "export"
    
    task_name: Mapped[str] = mapped_column(
        String(255), nullable=False,
    )  # Human-readable: "Processing Structural IFCs.pdf"
    
    # Status tracking (mirrors Celery states but persisted)
    status: Mapped[str] = mapped_column(
        String(50), default="PENDING", index=True,
    )  # PENDING, STARTED, PROGRESS, SUCCESS, FAILURE, REVOKED
    
    # Progress tracking
    progress_percent: Mapped[float] = mapped_column(Float, default=0.0)
    progress_step: Mapped[str | None] = mapped_column(String(255), nullable=True)
    progress_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Entity references (what this task operates on)
    entity_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True,
    )  # "page", "document", "condition", "project"
    entity_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True,
    )
    
    # Result/error storage
    result_summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_traceback: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Timing
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Who initiated
    initiated_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Provider info (for AI tasks)
    provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Metadata
    metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        Index("ix_task_records_project_status", "project_id", "status"),
        Index("ix_task_records_project_type", "project_id", "task_type"),
    )
```

### Migration

```sql
-- Alembic migration
CREATE TABLE task_records (
    task_id VARCHAR(255) PRIMARY KEY,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    task_type VARCHAR(100) NOT NULL,
    task_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    progress_percent FLOAT DEFAULT 0.0,
    progress_step VARCHAR(255),
    progress_detail TEXT,
    entity_type VARCHAR(50),
    entity_id VARCHAR(255),
    result_summary JSONB,
    error_message TEXT,
    error_traceback TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_ms INTEGER,
    initiated_by VARCHAR(255),
    provider VARCHAR(50),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX ix_task_records_project_status ON task_records(project_id, status);
CREATE INDEX ix_task_records_project_type ON task_records(project_id, task_type);
CREATE INDEX ix_task_records_status ON task_records(status);
CREATE INDEX ix_task_records_task_type ON task_records(task_type);
```

---

## Shared Schemas

### Task 16.2: Unified Task Schemas

Create `backend/app/schemas/task.py`:

```python
"""Shared task schemas used by all async operations."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TaskProgress(BaseModel):
    """Progress information for a running task."""
    percent: float = Field(0.0, ge=0.0, le=100.0, description="Completion percentage")
    step: str | None = Field(None, description="Current step name")
    detail: str | None = Field(None, description="Current step detail")


class TaskResponse(BaseModel):
    """
    Unified response for any async task.
    
    All endpoints that start async operations return this shape.
    The frontend useTaskPolling() hook expects this shape.
    """
    task_id: str
    task_type: str  # "document_processing", "ai_takeoff", etc.
    task_name: str  # Human-readable description
    status: str  # PENDING, STARTED, PROGRESS, SUCCESS, FAILURE, REVOKED
    progress: TaskProgress = Field(default_factory=TaskProgress)
    result: Any | None = None
    error: str | None = None
    traceback: str | None = None
    
    # Timing
    created_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: int | None = None
    
    # Context
    project_id: str | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    provider: str | None = None

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """Response for listing tasks."""
    tasks: list[TaskResponse]
    total: int
    running: int
    completed: int
    failed: int


class StartTaskResponse(BaseModel):
    """
    Minimal response when starting a new task.
    
    Routes that kick off async work return this immediately.
    The frontend then polls GET /api/tasks/{task_id} for full status.
    """
    task_id: str
    task_type: str
    task_name: str
    message: str


class CancelTaskResponse(BaseModel):
    """Response when canceling a task."""
    task_id: str
    status: str
    message: str
```

---

## API Router

### Task 16.3: Unified Tasks Router

Create `backend/app/api/routes/tasks.py`:

```python
"""Unified task management API.

Provides a single router for tracking, polling, and canceling
all async operations regardless of which Celery task module
they originate from.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.task import TaskRecord
from app.schemas.task import (
    TaskResponse,
    TaskListResponse,
    TaskProgress,
    CancelTaskResponse,
)
from app.workers.celery_app import celery_app

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _celery_to_task_response(
    task_id: str,
    celery_result: AsyncResult,
    db_record: TaskRecord | None = None,
) -> TaskResponse:
    """
    Build a TaskResponse from Celery state + optional DB record.
    
    Celery state is authoritative for running tasks.
    DB record supplements with metadata (task_type, name, project_id).
    """
    status_str = celery_result.status or "PENDING"
    
    # Extract progress from Celery meta (set via self.update_state)
    progress = TaskProgress()
    if status_str == "PROGRESS" and isinstance(celery_result.info, dict):
        progress = TaskProgress(
            percent=celery_result.info.get("percent", 0),
            step=celery_result.info.get("step"),
            detail=celery_result.info.get("detail"),
        )
    elif status_str == "SUCCESS":
        progress = TaskProgress(percent=100.0, step="Complete")
    
    # Result and error
    result = None
    error = None
    traceback = None
    
    if celery_result.ready():
        if celery_result.successful():
            result = celery_result.result
        else:
            error = str(celery_result.result) if celery_result.result else "Task failed"
            traceback = celery_result.traceback
    
    # Merge DB record metadata if available
    task_type = "unknown"
    task_name = f"Task {task_id[:8]}..."
    project_id = None
    entity_type = None
    entity_id = None
    provider = None
    created_at = None
    started_at = None
    completed_at = None
    duration_ms = None
    
    if db_record:
        task_type = db_record.task_type
        task_name = db_record.task_name
        project_id = str(db_record.project_id) if db_record.project_id else None
        entity_type = db_record.entity_type
        entity_id = db_record.entity_id
        provider = db_record.provider
        created_at = db_record.created_at
        started_at = db_record.started_at
        completed_at = db_record.completed_at
        duration_ms = db_record.duration_ms
    
    return TaskResponse(
        task_id=task_id,
        task_type=task_type,
        task_name=task_name,
        status=status_str,
        progress=progress,
        result=result,
        error=error,
        traceback=traceback,
        project_id=project_id,
        entity_type=entity_type,
        entity_id=entity_id,
        provider=provider,
        created_at=created_at,
        started_at=started_at,
        completed_at=completed_at,
        duration_ms=duration_ms,
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task_status(
    task_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TaskResponse:
    """
    Get status of any async task by ID.
    
    Combines live Celery state with persistent DB record for
    full context including progress, result, and metadata.
    """
    # Get live Celery state
    celery_result = AsyncResult(task_id, app=celery_app)
    
    # Get DB record if it exists
    result = await db.execute(
        select(TaskRecord).where(TaskRecord.task_id == task_id)
    )
    db_record = result.scalar_one_or_none()
    
    return _celery_to_task_response(task_id, celery_result, db_record)


@router.post("/{task_id}/cancel", response_model=CancelTaskResponse)
async def cancel_task(
    task_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CancelTaskResponse:
    """
    Cancel a running task.
    
    Sends SIGTERM to the Celery worker. The task must check for
    revocation between steps for graceful cancellation.
    """
    celery_result = AsyncResult(task_id, app=celery_app)
    
    if celery_result.ready():
        return CancelTaskResponse(
            task_id=task_id,
            status=celery_result.status,
            message="Task already completed, cannot cancel",
        )
    
    # Revoke the task
    celery_app.control.revoke(task_id, terminate=True, signal="SIGTERM")
    
    # Update DB record if exists
    result = await db.execute(
        select(TaskRecord).where(TaskRecord.task_id == task_id)
    )
    db_record = result.scalar_one_or_none()
    if db_record:
        db_record.status = "REVOKED"
        db_record.completed_at = datetime.now(timezone.utc)
        await db.commit()
    
    return CancelTaskResponse(
        task_id=task_id,
        status="REVOKED",
        message="Task cancellation requested",
    )


@router.get("/project/{project_id}", response_model=TaskListResponse)
async def list_project_tasks(
    project_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    status_filter: str | None = Query(None, alias="status"),
    task_type: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> TaskListResponse:
    """
    List all tasks for a project.
    
    Returns recent tasks with optional filtering by status and type.
    Used by the frontend project status bar to show running operations.
    """
    project_uuid = project_id
    
    # Base query
    query = select(TaskRecord).where(TaskRecord.project_id == project_uuid)
    
    if status_filter:
        query = query.where(TaskRecord.status == status_filter.upper())
    if task_type:
        query = query.where(TaskRecord.task_type == task_type)
    
    # Count queries
    count_base = select(func.count()).select_from(TaskRecord).where(
        TaskRecord.project_id == project_uuid
    )
    
    total_result = await db.execute(count_base)
    total = total_result.scalar() or 0
    
    running_result = await db.execute(
        count_base.where(TaskRecord.status.in_(["PENDING", "STARTED", "PROGRESS"]))
    )
    running = running_result.scalar() or 0
    
    completed_result = await db.execute(
        count_base.where(TaskRecord.status == "SUCCESS")
    )
    completed = completed_result.scalar() or 0
    
    failed_result = await db.execute(
        count_base.where(TaskRecord.status == "FAILURE")
    )
    failed = failed_result.scalar() or 0
    
    # Fetch records
    query = query.order_by(TaskRecord.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    records = result.scalars().all()
    
    # Build responses (enrich with live Celery state for non-terminal tasks)
    tasks = []
    for record in records:
        if record.status in ("PENDING", "STARTED", "PROGRESS"):
            # Get live state from Celery
            celery_result = AsyncResult(record.task_id, app=celery_app)
            tasks.append(_celery_to_task_response(record.task_id, celery_result, record))
        else:
            # Terminal state — use DB record directly
            tasks.append(TaskResponse(
                task_id=record.task_id,
                task_type=record.task_type,
                task_name=record.task_name,
                status=record.status,
                progress=TaskProgress(
                    percent=record.progress_percent or 0,
                    step=record.progress_step,
                    detail=record.progress_detail,
                ),
                result=record.result_summary,
                error=record.error_message,
                traceback=record.error_traceback,
                project_id=str(record.project_id) if record.project_id else None,
                entity_type=record.entity_type,
                entity_id=record.entity_id,
                provider=record.provider,
                created_at=record.created_at,
                started_at=record.started_at,
                completed_at=record.completed_at,
                duration_ms=record.duration_ms,
            ))
    
    return TaskListResponse(
        tasks=tasks,
        total=total,
        running=running,
        completed=completed,
        failed=failed,
    )
```

---

## Task Registration Helper

### Task 16.4: Task Registration Service

Create `backend/app/services/task_tracker.py`:

```python
"""
Task tracker service for registering and updating task records.

Called by API routes when starting tasks, and by Celery tasks
when reporting progress or completion.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session  # Sync session for Celery workers

from app.models.task import TaskRecord


class TaskTracker:
    """Manages TaskRecord creation and updates."""
    
    @staticmethod
    async def register_async(
        db: AsyncSession,
        task_id: str,
        task_type: str,
        task_name: str,
        project_id: uuid.UUID | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        provider: str | None = None,
        initiated_by: str | None = None,
        metadata: dict | None = None,
    ) -> TaskRecord:
        """
        Register a new task record (async, called from FastAPI routes).
        
        Call this immediately after celery_task.delay() to persist
        the task metadata before the worker picks it up.
        """
        record = TaskRecord(
            task_id=task_id,
            project_id=project_id,
            task_type=task_type,
            task_name=task_name,
            status="PENDING",
            entity_type=entity_type,
            entity_id=entity_id,
            provider=provider,
            initiated_by=initiated_by,
            metadata=metadata,
        )
        db.add(record)
        await db.commit()
        return record
    
    @staticmethod
    def update_progress_sync(
        db: Session,
        task_id: str,
        percent: float,
        step: str | None = None,
        detail: str | None = None,
    ) -> None:
        """
        Update task progress (sync, called from Celery workers).
        
        Also updates Celery state so polling sees progress immediately.
        """
        record = db.query(TaskRecord).filter(
            TaskRecord.task_id == task_id
        ).one_or_none()
        
        if record:
            record.status = "PROGRESS"
            record.progress_percent = percent
            record.progress_step = step
            record.progress_detail = detail
            if not record.started_at:
                record.started_at = datetime.now(timezone.utc)
            db.commit()
    
    @staticmethod
    def mark_started_sync(db: Session, task_id: str) -> None:
        """Mark task as started (sync, called from Celery workers)."""
        record = db.query(TaskRecord).filter(
            TaskRecord.task_id == task_id
        ).one_or_none()
        
        if record:
            record.status = "STARTED"
            record.started_at = datetime.now(timezone.utc)
            db.commit()
    
    @staticmethod
    def mark_completed_sync(
        db: Session,
        task_id: str,
        result_summary: dict | None = None,
    ) -> None:
        """Mark task as completed (sync, called from Celery workers)."""
        record = db.query(TaskRecord).filter(
            TaskRecord.task_id == task_id
        ).one_or_none()
        
        if record:
            now = datetime.now(timezone.utc)
            record.status = "SUCCESS"
            record.progress_percent = 100.0
            record.progress_step = "Complete"
            record.completed_at = now
            record.result_summary = result_summary
            if record.started_at:
                record.duration_ms = int(
                    (now - record.started_at).total_seconds() * 1000
                )
            db.commit()
    
    @staticmethod
    def mark_failed_sync(
        db: Session,
        task_id: str,
        error_message: str,
        error_traceback: str | None = None,
    ) -> None:
        """Mark task as failed (sync, called from Celery workers)."""
        record = db.query(TaskRecord).filter(
            TaskRecord.task_id == task_id
        ).one_or_none()
        
        if record:
            now = datetime.now(timezone.utc)
            record.status = "FAILURE"
            record.completed_at = now
            record.error_message = error_message
            record.error_traceback = error_traceback
            if record.started_at:
                record.duration_ms = int(
                    (now - record.started_at).total_seconds() * 1000
                )
            db.commit()
```

---

## Celery Task Integration

### Task 16.5: Progress-Reporting Task Pattern

Show how existing tasks integrate with the tracker. This is the pattern all tasks should follow:

Update `backend/app/workers/takeoff_tasks.py` (example integration):

```python
# Add at the top of generate_ai_takeoff_task, after the try:
from app.services.task_tracker import TaskTracker

@celery_app.task(bind=True, max_retries=3)
def generate_ai_takeoff_task(self, page_id, condition_id, provider=None):
    """Generate AI takeoff with progress tracking."""
    try:
        with SyncSession() as db:
            # Mark started
            TaskTracker.mark_started_sync(db, self.request.id)
            
            # ... existing page/condition validation ...
            
            # Report progress: loading image
            self.update_state(state="PROGRESS", meta={
                "percent": 10,
                "step": "Loading page image",
            })
            TaskTracker.update_progress_sync(
                db, self.request.id, 10, "Loading page image"
            )
            
            # ... get image from storage ...
            
            # Report progress: AI analysis
            self.update_state(state="PROGRESS", meta={
                "percent": 30,
                "step": "Running AI analysis",
                "detail": f"Provider: {provider or 'default'}",
            })
            TaskTracker.update_progress_sync(
                db, self.request.id, 30, "Running AI analysis",
                f"Provider: {provider or 'default'}"
            )
            
            # ... run AI analysis ...
            
            # Report progress: creating measurements
            self.update_state(state="PROGRESS", meta={
                "percent": 70,
                "step": "Creating measurements",
                "detail": f"{len(result.elements)} elements detected",
            })
            TaskTracker.update_progress_sync(
                db, self.request.id, 70, "Creating measurements",
                f"{len(result.elements)} elements detected"
            )
            
            # ... create measurements ...
            
            # Mark completed
            result_summary = {
                "elements_detected": len(result.elements),
                "measurements_created": measurements_created,
                "provider": result.llm_provider,
            }
            TaskTracker.mark_completed_sync(db, self.request.id, result_summary)
            
            return result_summary
            
    except ValueError as e:
        with SyncSession() as db:
            TaskTracker.mark_failed_sync(db, self.request.id, str(e))
        raise
    except Exception as e:
        with SyncSession() as db:
            TaskTracker.mark_failed_sync(
                db, self.request.id, str(e), 
                traceback.format_exc()
            )
        raise self.retry(exc=e, countdown=60)
```

### Task 16.5b: Revocation Check Pattern

Tasks should check for cancellation between expensive steps:

```python
from celery.exceptions import Reject

def _check_cancelled(self):
    """Check if this task has been revoked. Call between expensive steps."""
    if self.is_revoked():
        raise Reject("Task was cancelled", requeue=False)

# Usage inside a task:
@celery_app.task(bind=True)
def some_long_task(self, ...):
    # ... step 1 ...
    _check_cancelled(self)
    # ... step 2 ...
    _check_cancelled(self)
    # ... step 3 ...
```

---

## Route Registration

### Task 16.6: Register Tasks Router and Backward Compatibility

Update `backend/app/main.py`:

```python
from app.api.routes.tasks import router as tasks_router

# Add the unified tasks router
app.include_router(tasks_router, prefix="/api")
```

Add backward-compatible redirect in `backend/app/api/routes/takeoff.py`:

```python
from fastapi.responses import RedirectResponse

@router.get("/tasks/{task_id}/status", include_in_schema=False)
async def get_task_status_legacy(task_id: str):
    """Legacy endpoint — redirects to unified tasks API."""
    return RedirectResponse(
        url=f"/api/tasks/{task_id}",
        status_code=status.HTTP_301_MOVED_PERMANENTLY,
    )
```

---

## Route Integration Pattern

### Task 16.7: How Routes Register Tasks

Show how any route starts a task and registers it. Example for the takeoff route:

```python
from app.schemas.task import StartTaskResponse
from app.services.task_tracker import TaskTracker

@router.post("/pages/{page_id}/ai-takeoff", response_model=StartTaskResponse)
async def generate_ai_takeoff(
    page_id: uuid.UUID,
    request: GenerateTakeoffRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    page_data: Annotated[CalibratedPageData, Depends(get_calibrated_page)],
) -> StartTaskResponse:
    """Generate AI takeoff for a page."""
    # ... existing validation ...
    
    # Queue the Celery task
    task = generate_ai_takeoff_task.delay(
        str(page_id),
        str(request.condition_id),
        provider=provider,
    )
    
    # Register in DB for tracking
    await TaskTracker.register_async(
        db=db,
        task_id=task.id,
        task_type="ai_takeoff",
        task_name=f"AI takeoff: {condition.name} on page {page_data.page.page_number}",
        project_id=page_data.document.project_id,
        entity_type="page",
        entity_id=str(page_id),
        provider=provider,
    )
    
    return StartTaskResponse(
        task_id=task.id,
        task_type="ai_takeoff",
        task_name=f"AI takeoff: {condition.name} on page {page_data.page.page_number}",
        message=f"AI takeoff started for page {page_id}",
    )
```

---

## Frontend Hook

### Task 16.8: useTaskPolling Hook

Create `frontend/src/hooks/useTaskPolling.ts`:

```typescript
import { useState, useEffect, useCallback, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';

export interface TaskProgress {
  percent: number;
  step: string | null;
  detail: string | null;
}

export interface TaskStatus {
  task_id: string;
  task_type: string;
  task_name: string;
  status: 'PENDING' | 'STARTED' | 'PROGRESS' | 'SUCCESS' | 'FAILURE' | 'REVOKED';
  progress: TaskProgress;
  result: any | null;
  error: string | null;
  traceback: string | null;
  project_id: string | null;
  entity_type: string | null;
  entity_id: string | null;
  provider: string | null;
  created_at: string | null;
  started_at: string | null;
  completed_at: string | null;
  duration_ms: number | null;
}

interface UseTaskPollingOptions {
  /** Polling interval in ms (default: 2000) */
  interval?: number;
  /** Stop polling on these statuses (default: SUCCESS, FAILURE, REVOKED) */
  terminalStatuses?: string[];
  /** Callback when task completes successfully */
  onSuccess?: (result: any) => void;
  /** Callback when task fails */
  onError?: (error: string) => void;
  /** Query keys to invalidate on success (e.g., refresh measurements list) */
  invalidateOnSuccess?: string[][];
  /** Whether polling is enabled (default: true when taskId is set) */
  enabled?: boolean;
}

export function useTaskPolling(
  taskId: string | null,
  options: UseTaskPollingOptions = {},
) {
  const {
    interval = 2000,
    terminalStatuses = ['SUCCESS', 'FAILURE', 'REVOKED'],
    onSuccess,
    onError,
    invalidateOnSuccess = [],
    enabled = true,
  } = options;

  const [taskStatus, setTaskStatus] = useState<TaskStatus | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const queryClient = useQueryClient();

  const isTerminal = taskStatus
    ? terminalStatuses.includes(taskStatus.status)
    : false;

  const poll = useCallback(async () => {
    if (!taskId) return;

    try {
      const response = await api.get<TaskStatus>(`/api/tasks/${taskId}`);
      const data = response.data;
      setTaskStatus(data);

      if (terminalStatuses.includes(data.status)) {
        // Stop polling
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
        setIsPolling(false);

        if (data.status === 'SUCCESS') {
          onSuccess?.(data.result);
          // Invalidate related queries so lists refresh
          for (const key of invalidateOnSuccess) {
            queryClient.invalidateQueries({ queryKey: key });
          }
        } else if (data.status === 'FAILURE') {
          onError?.(data.error || 'Task failed');
        }
      }
    } catch (err) {
      console.error('Task polling error:', err);
    }
  }, [taskId, terminalStatuses, onSuccess, onError, invalidateOnSuccess, queryClient]);

  // Start/stop polling when taskId changes
  useEffect(() => {
    if (!taskId || !enabled) {
      setIsPolling(false);
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      return;
    }

    // Reset state for new task
    setTaskStatus(null);
    setIsPolling(true);

    // Immediate first poll
    poll();

    // Start interval
    intervalRef.current = setInterval(poll, interval);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [taskId, interval, enabled, poll]);

  // Cancel function
  const cancel = useCallback(async () => {
    if (!taskId) return;
    try {
      await api.post(`/api/tasks/${taskId}/cancel`);
      // Poll immediately to get updated status
      await poll();
    } catch (err) {
      console.error('Task cancel error:', err);
    }
  }, [taskId, poll]);

  return {
    taskStatus,
    isPolling,
    isTerminal,
    isSuccess: taskStatus?.status === 'SUCCESS',
    isError: taskStatus?.status === 'FAILURE',
    progress: taskStatus?.progress || { percent: 0, step: null, detail: null },
    cancel,
  };
}
```

### Task 16.9: TaskProgressBar Component

Create `frontend/src/components/shared/TaskProgressBar.tsx`:

```tsx
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { X, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { TaskStatus } from '@/hooks/useTaskPolling';

interface TaskProgressBarProps {
  task: TaskStatus;
  onCancel?: () => void;
  showDetail?: boolean;
}

export function TaskProgressBar({
  task,
  onCancel,
  showDetail = true,
}: TaskProgressBarProps) {
  const isRunning = ['PENDING', 'STARTED', 'PROGRESS'].includes(task.status);
  const isSuccess = task.status === 'SUCCESS';
  const isError = task.status === 'FAILURE';

  return (
    <div className="rounded-lg border p-3 space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {isRunning && <Loader2 className="h-4 w-4 animate-spin text-blue-500" />}
          {isSuccess && <CheckCircle className="h-4 w-4 text-green-500" />}
          {isError && <XCircle className="h-4 w-4 text-red-500" />}
          <span className="text-sm font-medium">{task.task_name}</span>
        </div>
        
        {isRunning && onCancel && (
          <Button variant="ghost" size="sm" onClick={onCancel}>
            <X className="h-3 w-3" />
          </Button>
        )}
      </div>

      {isRunning && (
        <Progress value={task.progress.percent} className="h-2" />
      )}

      {showDetail && task.progress.step && (
        <div className="text-xs text-muted-foreground">
          {task.progress.step}
          {task.progress.detail && ` — ${task.progress.detail}`}
        </div>
      )}

      {isError && task.error && (
        <div className="text-xs text-red-500">{task.error}</div>
      )}
    </div>
  );
}
```

---

## Verification Checklist

After completing all tasks, verify:

- [ ] `GET /api/tasks/{task_id}` returns status for any Celery task
- [ ] `POST /api/tasks/{task_id}/cancel` revokes running tasks
- [ ] `GET /api/tasks/project/{project_id}` lists all tasks for a project
- [ ] Legacy `GET /tasks/{task_id}/status` redirects to new endpoint
- [ ] TaskRecord created when AI takeoff starts
- [ ] Progress updates visible during AI analysis
- [ ] Task marked SUCCESS on completion with result summary
- [ ] Task marked FAILURE on error with message and traceback
- [ ] `useTaskPolling` hook polls and stops at terminal state
- [ ] `onSuccess` callback fires and invalidates related queries
- [ ] `cancel()` function revokes task and updates UI
- [ ] TaskProgressBar shows progress, completion, and errors
- [ ] All existing Celery tasks continue to work unchanged

### Test Cases

1. Start AI takeoff → poll → see PENDING → STARTED → PROGRESS → SUCCESS
2. Start AI takeoff → cancel mid-flight → see REVOKED
3. Start AI takeoff with bad page → see FAILURE with error message
4. List project tasks → see running + completed tasks
5. Filter project tasks by status → only matching tasks returned
6. Legacy endpoint → 301 redirect to new endpoint
7. Multiple concurrent tasks → all independently trackable
8. Frontend hook → progress bar updates in real-time

---

## Migration Path for Existing Tasks

Each existing task module should be updated to integrate with TaskTracker. Priority order:

| Task Module | Priority | Integration Effort |
|-------------|----------|-------------------|
| `takeoff_tasks.py` | High (already has polling) | Low — add TaskTracker calls |
| `document_tasks.py` | High (users wait for processing) | Low — add progress for page extraction |
| `classification_tasks.py` | Medium | Low — add progress per page |
| `scale_tasks.py` | Medium | Low — simple start/complete |
| `ocr_tasks.py` | Medium | Low — add progress per page |

Each integration follows the same pattern shown in Task 16.5. The existing task logic stays the same — you just add `TaskTracker.mark_started_sync()`, `update_progress_sync()`, and `mark_completed_sync()` calls at appropriate points.

---

## Next Phase

Once verified, continue with **Phase 3A: OCR & Text Extraction** (`03-OCR-TEXT-EXTRACTION.md`). All subsequent phases that create async operations should use the patterns established here.
