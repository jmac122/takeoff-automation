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

# BRANCH B: Export System

**Branch name**: `feature/export-system`
**Base**: `main` (after PR #5 merge)
**Effort**: ~1-2 weeks
**Scope**: Backend heavy + minimal frontend (export button + download)

## Context

Read these files first:

1. `plans/10-EXPORT-SYSTEM.md` — Full export spec
2. `plans/11-TESTING-QA.md` — Testing standards and coverage targets
3. `backend/app/models/condition.py` — Condition model (source of export data)
4. `backend/app/models/measurement.py` — Measurement model
5. `backend/app/services/task_tracker.py` — Use TaskTracker for export job tracking

## Implementation Tasks

### Backend

1. **Export Job Model** (`backend/app/models/export_job.py`)

   - ExportJob model: id, project_id, format (excel/ost/csv/pdf), status, file_key, error_message, options (JSON), timestamps
   - Alembic migration

2. **Base Export Service** (`backend/app/services/export/base.py`)

   - Abstract `BaseExporter` class with `generate(project_id, options) -> bytes`
   - Shared query logic: fetch conditions + measurements + pages for a project

3. **Excel Exporter** (`backend/app/services/export/excel_exporter.py`)

   - Summary sheet: condition totals grouped by type
   - Detail sheets: per-condition measurement list with page references
   - Per-page sheets: measurements grouped by page
   - Use openpyxl

4. **OST XML Exporter** (`backend/app/services/export/ost_exporter.py`)

   - On Screen Takeoff compatible XML format
   - Map conditions → OST conditions, measurements → OST takeoff items

5. **CSV Exporter** (`backend/app/services/export/csv_exporter.py`)

   - Flat CSV with one row per measurement
   - Headers: condition, page, type, quantity, unit, coordinates

6. **PDF Report Exporter** (`backend/app/services/export/pdf_exporter.py`)

   - Project summary report
   - Condition breakdown tables
   - Use reportlab

7. **Export Celery Task** (`backend/app/workers/export_tasks.py`)

   - `generate_export_task` with TaskTracker integration (pre-generate ID pattern)
   - Progress updates: 10% start → per-exporter progress → 90% uploading → complete
   - Upload result to MinIO/S3, store file_key in ExportJob

8. **Export API Endpoints** (`backend/app/api/routes/exports.py`)
   - `POST /api/v1/projects/{project_id}/export` — Start export (returns task_id)
   - `GET /api/v1/exports/{export_id}` — Get export status + download URL
   - `GET /api/v1/projects/{project_id}/exports` — List project exports
   - `DELETE /api/v1/exports/{export_id}` — Delete export

### Frontend (minimal)

9. **Export Button** in project toolbar → opens format selector dialog
10. **Export Status** using existing `useTaskPolling` hook
11. **Download link** when export completes

## Required Tests

### Unit Tests: `backend/tests/unit/test_export/`

#### `test_excel_exporter.py`

```python
"""Tests for Excel export generation."""
import pytest
from openpyxl import load_workbook
from io import BytesIO

class TestExcelExporter:

    @pytest.fixture
    def sample_project_data(self):
        """Create a project with conditions and measurements for export."""
        # Use factories to create realistic test data
        ...

    def test_summary_sheet_has_correct_totals(self, sample_project_data):
        """Summary sheet shows correct total quantity per condition."""

    def test_detail_sheet_per_condition(self, sample_project_data):
        """Each condition with measurements gets its own detail sheet."""

    def test_empty_project_exports_cleanly(self):
        """Project with no measurements produces valid Excel with summary only."""

    def test_special_characters_in_condition_names(self):
        """Condition names with slashes, quotes, etc. don't break sheet names."""

    def test_large_dataset_performance(self):
        """Export with 1000+ measurements completes in under 10 seconds."""

    def test_measurement_types_formatted_correctly(self):
        """Area shows SF, linear shows LF, volume shows CY, count shows EA."""

    def test_page_references_included(self):
        """Each measurement row includes the page/sheet number it came from."""
```

#### `test_ost_exporter.py`

```python
"""Tests for OST XML export generation."""
import pytest
from xml.etree import ElementTree

class TestOSTExporter:

    def test_generates_valid_xml(self, sample_project_data):
        """Output is well-formed XML."""
        result = exporter.generate(...)
        tree = ElementTree.fromstring(result)  # Should not raise

    def test_conditions_mapped_to_ost_format(self, sample_project_data):
        """ForgeX conditions correctly map to OST condition elements."""

    def test_measurements_have_coordinates(self, sample_project_data):
        """Each measurement includes its geometry coordinates in OST format."""

    def test_scale_factors_included(self):
        """Page scale factors are included for coordinate translation."""

    def test_empty_project_valid_xml(self):
        """Empty project produces valid minimal OST XML."""
```

#### `test_csv_exporter.py`

```python
"""Tests for CSV export generation."""
import pytest
import csv
from io import StringIO

class TestCSVExporter:

    def test_header_row_present(self, sample_project_data):
        """First row contains expected column headers."""

    def test_one_row_per_measurement(self, sample_project_data):
        """Row count matches measurement count (plus header)."""

    def test_unicode_handling(self):
        """Condition names with unicode characters export correctly."""

    def test_commas_in_values_escaped(self):
        """Values containing commas are properly quoted."""
```

#### `test_pdf_exporter.py`

```python
"""Tests for PDF report generation."""
import pytest

class TestPDFExporter:

    def test_generates_valid_pdf(self, sample_project_data):
        """Output starts with %PDF magic bytes."""
        result = exporter.generate(...)
        assert result[:5] == b'%PDF-'

    def test_contains_project_name(self, sample_project_data):
        """PDF contains the project name in text content."""

    def test_condition_tables_present(self, sample_project_data):
        """PDF contains a table for each condition with totals."""
```

#### `test_base_exporter.py`

```python
"""Tests for shared export query logic."""
class TestExportDataQuery:

    @pytest.mark.asyncio
    async def test_fetches_all_conditions_for_project(self, db_session):
        """Query returns all conditions belonging to the project."""

    @pytest.mark.asyncio
    async def test_includes_measurements_with_page_info(self, db_session):
        """Each measurement includes its page sheet_number and title."""

    @pytest.mark.asyncio
    async def test_excludes_other_project_data(self, db_session):
        """Data from other projects is not included."""

    @pytest.mark.asyncio
    async def test_handles_conditions_with_no_measurements(self, db_session):
        """Conditions with zero measurements are included (for completeness)."""

    @pytest.mark.asyncio
    async def test_filter_by_status(self, db_session):
        """Can filter to only include verified/approved measurements."""
```

### Integration Tests: `backend/tests/integration/test_exports_api.py`

```python
"""Integration tests for export API endpoints."""
import pytest
from httpx import AsyncClient

class TestStartExport:

    @pytest.mark.asyncio
    async def test_start_export_returns_task_id(self, client, db_session):
        """POST /projects/{id}/export returns a task_id."""

    @pytest.mark.asyncio
    async def test_start_export_creates_export_job(self, client, db_session):
        """POST creates an ExportJob record in PENDING status."""

    @pytest.mark.asyncio
    async def test_start_export_registers_task(self, client, db_session):
        """POST creates a TaskRecord (via TaskTracker) for polling."""

    @pytest.mark.asyncio
    async def test_invalid_format_rejected(self, client, db_session):
        """POST with unsupported format returns 400."""

    @pytest.mark.asyncio
    async def test_nonexistent_project_returns_404(self, client):
        """POST to unknown project_id returns 404."""

class TestGetExport:

    @pytest.mark.asyncio
    async def test_completed_export_has_download_url(self, client, db_session):
        """GET for completed export includes presigned download URL."""

    @pytest.mark.asyncio
    async def test_pending_export_has_no_url(self, client, db_session):
        """GET for in-progress export has null download_url."""

    @pytest.mark.asyncio
    async def test_nonexistent_export_returns_404(self, client):
        """GET for unknown export_id returns 404."""

class TestListExports:

    @pytest.mark.asyncio
    async def test_lists_only_project_exports(self, client, db_session):
        """GET /projects/{id}/exports only returns that project's exports."""

    @pytest.mark.asyncio
    async def test_ordered_by_created_at_desc(self, client, db_session):
        """Exports are returned newest first."""

class TestDeleteExport:

    @pytest.mark.asyncio
    async def test_delete_removes_record(self, client, db_session):
        """DELETE removes the export job record."""

    @pytest.mark.asyncio
    async def test_delete_cleans_up_file(self, client, db_session, mock_storage):
        """DELETE also removes the file from storage."""

    @pytest.mark.asyncio
    async def test_delete_nonexistent_returns_404(self, client):
        """DELETE for unknown export_id returns 404."""
```

### Worker Tests: `backend/tests/unit/test_export_tasks.py`

```python
"""Tests for export Celery task."""
from unittest.mock import patch, MagicMock

class TestGenerateExportTask:

    @patch('app.workers.export_tasks.TaskTracker')
    def test_marks_started(self, mock_tracker):
        """Task calls mark_started_sync at entry."""

    @patch('app.workers.export_tasks.TaskTracker')
    def test_progress_updates_during_generation(self, mock_tracker):
        """Task reports progress at defined intervals."""

    @patch('app.workers.export_tasks.TaskTracker')
    def test_marks_completed_with_file_key(self, mock_tracker):
        """Task calls mark_completed_sync with the storage file key."""

    @patch('app.workers.export_tasks.TaskTracker')
    def test_marks_failed_on_error(self, mock_tracker):
        """Task calls mark_failed_sync when generation fails."""

    def test_uploads_result_to_storage(self, mock_storage):
        """Generated file is uploaded to S3/MinIO."""

    def test_updates_export_job_status(self, db_session):
        """ExportJob status moves from PENDING → PROCESSING → COMPLETED."""
```

## Verification Gate

```bash
# Unit tests for all exporters
pytest tests/unit/test_export/ -v --tb=short

# Integration tests for API
pytest tests/integration/test_exports_api.py -v --tb=short

# Worker tests
pytest tests/unit/test_export_tasks.py -v --tb=short

# Coverage check — new export code should be 85%+
pytest tests/ -v --cov=app/services/export --cov=app/api/routes/exports --cov=app/workers/export_tasks --cov-report=term-missing

# Full regression
pytest tests/ -v --tb=short
```

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
