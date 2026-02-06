# ENVIRONMENT SETUP (Run First — Before Anything Else)

This project runs in a cloud environment that starts fresh. You MUST set up dependencies and services before writing or running any code.

## Step 1: System Services

```bash
# Install and start PostgreSQL + Redis
sudo apt-get update && sudo apt-get install -y postgresql redis-server libpq-dev
sudo service postgresql start
sudo service redis-server start

# Create test database and user
sudo -u postgres psql -c "CREATE USER test WITH PASSWORD 'test' SUPERUSER;"
sudo -u postgres psql -c "CREATE DATABASE test OWNER test;"
sudo -u postgres psql -c "CREATE DATABASE forgex OWNER test;"
```

## Step 2: Backend Dependencies

```bash
cd backend
pip install -r requirements.txt --break-system-packages
pip install -r requirements-dev.txt --break-system-packages
```

## Step 3: Frontend Dependencies (Branch C only — skip for A and B)

```bash
cd frontend
npm install
```

## Step 4: Database Migrations

```bash
cd backend
DATABASE_URL=postgresql+asyncpg://test:test@localhost:5432/forgex alembic upgrade head
```

## Step 5: Verify Setup

```bash
cd backend
DATABASE_URL=postgresql+asyncpg://test:test@localhost:5432/test \
REDIS_URL=redis://localhost:6379/0 \
SECRET_KEY=test-secret-key-for-ci-minimum-32-chars-long \
ENVIRONMENT=test \
pytest tests/ -x -q --tb=short 2>&1 | head -20
```

If existing tests pass (or no tests exist yet), you're ready to proceed.

## Environment Variables

Set these for ALL test runs and commands:

```bash
export DATABASE_URL=postgresql+asyncpg://test:test@localhost:5432/test
export REDIS_URL=redis://localhost:6379/0
export SECRET_KEY=test-secret-key-for-ci-minimum-32-chars-long
export ENVIRONMENT=test
```

---

# TESTING PHILOSOPHY (Read Before Writing Any Code)

Every branch follows this testing contract. **Do not skip this.**

## The Contract

1. **Before writing any feature code**, check if `backend/tests/conftest.py` has the shared fixtures from `plans/11-TESTING-QA.md` (Task 11.1). If not, create them first. Same for `backend/tests/factories/` (Task 11.2).

2. **For every new module/service/route**, write tests in the SAME commit:

   - **Unit tests** for pure logic (services, utilities, calculations)
   - **Integration tests** for API endpoints (use `AsyncClient` + test DB)
   - **Edge case tests** for error paths, invalid inputs, auth/permission boundaries

3. **Test file naming**: Mirror the source path.

   - `app/services/export_service.py` → `tests/unit/test_export_service.py`
   - `app/api/routes/exports.py` → `tests/integration/test_exports_api.py`
   - `app/workers/export_tasks.py` → `tests/unit/test_export_tasks.py`

4. **Before committing**, run:

   ```bash
   cd backend
   pytest tests/ -v --tb=short --cov=app --cov-report=term-missing
   ```

   Fix any failures. Target 80%+ coverage on new code.

5. **Security tests** for every route: test missing auth, wrong project_id, invalid UUIDs, IDOR attempts.

6. **Regression check**: Run the full existing test suite to confirm nothing is broken.

## Test Infrastructure Checklist

Before writing any feature code on ANY branch, verify these exist. If they don't, create them:

### `backend/tests/conftest.py`

Must have these fixtures (from `plans/11-TESTING-QA.md` Task 11.1):

- `get_test_settings()` — test configuration
- `event_loop` — session-scoped asyncio loop
- `async_engine` — test DB engine (PostgreSQL or SQLite)
- `db_session` — async session with rollback after each test
- `app` — FastAPI app with dependency overrides
- `client` — `AsyncClient` for HTTP testing
- `mock_storage` — mocked S3/MinIO
- `mock_llm_client` — mocked LLM provider
- `sample_image_bytes`, `sample_pdf_bytes` — minimal valid test files

### `backend/tests/factories/`

Must have factories for (from Task 11.2):

- `ProjectFactory`
- `DocumentFactory`
- `PageFactory`
- `ConditionFactory`
- `MeasurementFactory`
- `TaskRecordFactory` ← **NEW** — add this for task-related tests

If `factory_boy` is not installed, add it to `requirements-dev.txt`.

### TaskRecord Factory (new)

```python
# backend/tests/factories/task_record.py
import uuid
from datetime import datetime, timezone
import factory
from app.models.task import TaskRecord

class TaskRecordFactory(factory.Factory):
    class Meta:
        model = TaskRecord

    task_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    project_id = factory.LazyFunction(uuid.uuid4)
    task_type = "document_processing"
    task_name = factory.Sequence(lambda n: f"Test Task {n}")
    status = "PENDING"
    progress_percent = 0
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    updated_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
```

---

# BRANCH A: Task Migration (Instrument Remaining Celery Tasks)

**Branch name**: `feature/task-migration`
**Base**: `main` (after PR #5 merge)
**Effort**: ~1 day
**Scope**: Backend only — 8 files modified, 0 new features

## Context

Read these files first:

1. `plans/16-UNIFIED-TASK-API.md` — Full task API spec
2. `backend/app/services/task_tracker.py` — TaskTracker service (already implemented and bug-fixed)
3. `backend/app/workers/takeoff_tasks.py` — Reference: how `generate_ai_takeoff_task` uses TaskTracker
4. `backend/app/api/routes/takeoff.py` — Reference: how the route registers with pre-generated ID

## Implementation

Follow the `migrate-tasks-to-tracker-prompt-v2.md` file in the project root. It has the complete task-by-task instructions with the corrected patterns (pre-generate ID, register before enqueue, retry-aware failure handling).

**Key pattern reminder** — every route does:

```python
task_id = str(uuid.uuid4())
await TaskTracker.register_async(db, task_id=task_id, ...)
some_task.apply_async(args=[...], task_id=task_id)
```

## Required Tests

### Unit Tests: `backend/tests/unit/test_task_migration.py`

Test that each worker task properly calls TaskTracker methods:

```python
"""Tests for TaskTracker integration in all Celery workers."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

class TestDocumentTaskTracking:
    """Verify process_document_task calls TaskTracker correctly."""

    @patch('app.workers.document_tasks.TaskTracker')
    def test_marks_started_on_entry(self, mock_tracker):
        """Task calls mark_started_sync at the beginning."""
        # Arrange: mock DB session, mock task self with request.id
        # Act: call the task function
        # Assert: mock_tracker.mark_started_sync.assert_called_once_with(ANY, task_id)

    @patch('app.workers.document_tasks.TaskTracker')
    def test_marks_completed_on_success(self, mock_tracker):
        """Task calls mark_completed_sync with result summary on success."""

    @patch('app.workers.document_tasks.TaskTracker')
    def test_marks_failed_on_error(self, mock_tracker):
        """Task calls mark_failed_sync on unrecoverable error."""

    @patch('app.workers.document_tasks.TaskTracker')
    def test_does_not_mark_failed_during_retry(self, mock_tracker):
        """Task does NOT call mark_failed_sync when retrying (max_retries > 0)."""

    @patch('app.workers.document_tasks.TaskTracker')
    def test_progress_updates_at_expected_points(self, mock_tracker):
        """Task calls update_progress_sync at defined percentage steps."""

# Repeat the same pattern for:
class TestOCRTaskTracking: ...
class TestClassificationTaskTracking: ...
class TestScaleDetectionTaskTracking: ...
class TestAutonomousTakeoffTaskTracking: ...
class TestCompareProvidersTaskTracking: ...
class TestBatchTakeoffTaskTracking: ...
```

### Integration Tests: `backend/tests/integration/test_task_registration_routes.py`

Test that each route properly registers tasks before enqueueing:

```python
"""Tests for task registration in API routes."""
import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient

class TestDocumentUploadRegistersTask:
    """POST /documents/ should register a task record."""

    @pytest.mark.asyncio
    async def test_upload_creates_task_record(self, client: AsyncClient, db_session):
        """Uploading a document creates a PENDING task record in the DB."""
        # Mock the Celery task to prevent actual execution
        with patch('app.api.routes.documents.process_document_task') as mock_task:
            mock_task.apply_async = MagicMock()
            response = await client.post("/api/v1/projects/{project_id}/documents", ...)
            # Assert: task record exists in DB with status PENDING
            # Assert: mock_task.apply_async was called with task_id matching DB record

    @pytest.mark.asyncio
    async def test_task_id_matches_between_db_and_celery(self, client, db_session):
        """The task_id in the DB record matches what was passed to Celery."""

class TestOCRReprocessRegistersTask:
    """POST /pages/{id}/reprocess-ocr should register a task record."""
    ...

class TestClassifyPageRegistersTask:
    """POST /pages/{id}/classify should register a task record."""
    ...

class TestScaleDetectionRegistersTask:
    """POST /pages/{id}/detect-scale should register a task record."""
    ...

class TestAutonomousTakeoffRegistersTask: ...
class TestCompareProvidersRegistersTask: ...
class TestBatchTakeoffRegistersTask: ...
```

### Edge Case Tests: `backend/tests/unit/test_task_tracker_edge_cases.py`

```python
"""Edge case tests for TaskTracker service."""

class TestTaskTrackerEdgeCases:

    def test_mark_started_nonexistent_task(self, db_session):
        """mark_started_sync with unknown task_id doesn't crash."""

    def test_mark_completed_already_completed(self, db_session):
        """mark_completed_sync on already-completed task is idempotent."""

    def test_mark_failed_already_failed(self, db_session):
        """mark_failed_sync on already-failed task is idempotent."""

    def test_update_progress_after_completion(self, db_session):
        """update_progress_sync after task is completed is a no-op."""

    def test_concurrent_progress_updates(self, db_session):
        """Two rapid progress updates don't cause DB conflicts."""
```

## Verification Gate

Before opening PR:

```bash
pytest tests/unit/test_task_migration.py tests/unit/test_task_tracker_edge_cases.py tests/integration/test_task_registration_routes.py -v --tb=short
pytest tests/ -v --tb=short  # Full regression
```

All tests pass, zero failures, zero warnings about unclosed sessions.

---

# WHAT NOT TO DO (ALL BRANCHES)

- Do NOT skip writing tests "to save time" — this is what caused the 15+ PR issues last time
- Do NOT commit without running the full test suite
- Do NOT add `# pragma: no cover` to skip coverage on new code
- Do NOT mock away the thing you're testing — mock the DEPENDENCIES
- Do NOT write tests that test the framework (e.g., "does FastAPI return 200?") — test YOUR logic
- Do NOT leave `TODO: add tests` comments — write them now or don't merge
- Do NOT write tests after the fact that just assert current behavior — write them to assert CORRECT behavior

---

# EXECUTION ORDER

1. Merge PR #5 to `main`
2. Create all 3 branches from `main`
3. Run Branch A first (smallest, fastest) — merge when green
4. Run Branch B and C in parallel — they don't overlap
5. After all 3 merge, create next wave (Assembly System + UI Overhaul Phase B+C)
