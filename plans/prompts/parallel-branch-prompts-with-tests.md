# ForgeX Parallel Implementation — 3 Branches

> **Created**: February 2026
> **Prerequisites**: Merge PR #5 (Unified Task API) to `main` before creating these branches
> **Each branch is independent** — no cross-branch dependencies

---

# TESTING PHILOSOPHY (applies to ALL branches)

Every prompt below follows this testing contract. **Do not skip this.**

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

# BRANCH C: UI Overhaul Phase A (Workspace Shell + Sheet Manager)

**Branch name**: `feature/ui-overhaul-phase-a`
**Base**: `main` (after PR #5 merge)
**Effort**: ~2-3 weeks
**Scope**: Frontend heavy + 1 backend endpoint

## Context

Read these files first (IN THIS ORDER — per the audit):
1. `plans/18A-UI-OVERHAUL-AUDIT.md` — **Read Part 1 (critical gaps) and Part 4 (architecture additions) FIRST**
2. `plans/18-UI-OVERHAUL.md` (the `forgex-ui-overhaul-spec.docx` content) — Full spec
3. `plans/18B-UI-OVERHAUL-PHASE-CONTEXTS.md` — Phase-specific AI context
4. `.cursor/rules/forgex-rules.md` or `CLAUDE_RULES.md` — UI conventions

**Critical architecture decisions from the audit (must follow):**
- **State**: Zustand for UI state, React Query for server data. Never mix.
- **Migration**: New `/projects/:id` route with `ENABLE_NEW_WORKSPACE` feature flag
- **Error handling**: No error loses user work. Toast + retry everywhere.
- **Focus system**: `FocusContext` with `focusRegion` for keyboard shortcut routing.
- **Constants**: All magic numbers in `frontend/src/lib/constants.ts`

## Implementation Tasks

### A.0: Architecture Foundation (MUST BE FIRST)

1. **Zustand Store Architecture** (`frontend/src/stores/workspaceStore.ts`)
   - `activeSheetId`, `activeConditionId`, `activeTool`, `viewportState`
   - `focusRegion`, `leftPanelWidth`, `rightPanelWidth`
   - Selectors for derived state

2. **Constants File** (`frontend/src/lib/constants.ts`)
   - All values from the audit Section 4.2

3. **FocusContext** (`frontend/src/contexts/FocusContext.tsx`)
   - Track which region has focus for keyboard shortcut routing

### A.1: Workspace Layout

4. **TakeoffWorkspace** (`frontend/src/components/workspace/TakeoffWorkspace.tsx`)
   - Three-panel layout using `react-resizable-panels`
   - TopToolbar, LeftSidebar, CenterCanvas, RightPanel, BottomStatusBar
   - New route: `/projects/:id` with feature flag check

### A.2: SheetTree

5. **SheetTree Component** (`frontend/src/components/sheets/SheetTree.tsx`)
   - Grouped by discipline/group_name
   - Expand/collapse state persisted to localStorage
   - Click → loads sheet in canvas
   - Scale indicators per sheet

6. **GET /projects/{id}/sheets Backend Endpoint** (`backend/app/api/routes/sheets.py`)
   - Returns all pages with classification, scale, display fields pre-joined
   - Grouped by discipline
   - Includes measurement counts per page
   - Single query, no N+1

### A.3-A.12: Remaining Phase A Tasks

7. Keyboard navigation (Arrow keys, Enter to select)
8. Sheet → canvas load with loading state
9. Scale indicators (confidence-colored badges)
10. Batch scale operations
11. Sheet search (client-side name filter)
12. Thumbnail strip view
13. Context menu (rename, set scale, copy scale)
14. Backend: `display_name`, `display_order`, `group_name`, `is_relevant` page fields
15. Page Up/Page Down navigation

## Required Tests

### Frontend Tests: `frontend/src/components/workspace/__tests__/`

Use React Testing Library + Vitest (or Jest, whichever is configured).

#### `TakeoffWorkspace.test.tsx`
```typescript
describe('TakeoffWorkspace', () => {
  it('renders three-panel layout', () => {
    // Assert: LeftSidebar, CenterCanvas, RightPanel all present
  });

  it('renders feature flag gate', () => {
    // When ENABLE_NEW_WORKSPACE is false, redirects to old UI
  });

  it('loads project data on mount', () => {
    // Assert: React Query fires for project + sheets
  });

  it('handles project not found', () => {
    // Assert: 404 state shown, no crash
  });
});
```

#### `SheetTree.test.tsx`
```typescript
describe('SheetTree', () => {
  it('renders sheets grouped by discipline', () => {
    // Given: sheets with different disciplines
    // Assert: group headers shown, sheets under correct groups
  });

  it('clicking a sheet sets it as active', () => {
    // Assert: workspaceStore.activeSheetId updated
  });

  it('shows scale badge per sheet', () => {
    // Given: sheet with scale detected at 85% confidence
    // Assert: green badge shown with scale text
  });

  it('shows no-scale indicator for uncalibrated sheets', () => {
    // Given: sheet with no scale
    // Assert: warning indicator shown
  });

  it('persists expand/collapse to localStorage', () => {
    // Act: collapse a group
    // Assert: localStorage updated
    // Act: re-render
    // Assert: group still collapsed
  });

  it('keyboard navigation works', () => {
    // Act: press ArrowDown
    // Assert: next sheet highlighted
    // Act: press Enter
    // Assert: sheet becomes active
  });

  it('search filters sheets by name', () => {
    // Given: sheets S1.01, S1.02, A1.01
    // Act: type "S1" in search
    // Assert: only S1.01 and S1.02 visible
  });

  it('handles empty project gracefully', () => {
    // Given: project with no documents/pages
    // Assert: empty state message, no crash
  });
});
```

#### `workspaceStore.test.ts`
```typescript
describe('WorkspaceStore', () => {
  it('initializes with default values', () => {
    // Assert: activeTool is 'select', no activeSheetId, etc.
  });

  it('setActiveSheet updates activeSheetId', () => {
    // Act + Assert
  });

  it('setActiveTool prevents tool activation without active condition', () => {
    // Given: no activeConditionId
    // Act: try to set activeTool to 'polygon'
    // Assert: tool not changed (or warning issued)
  });

  it('panel widths respect min/max bounds', () => {
    // Act: try to set leftPanelWidth to 50 (below min)
    // Assert: clamped to LEFT_PANEL_MIN_WIDTH
  });
});
```

### Backend Tests: `backend/tests/integration/test_sheets_api.py`

```python
"""Tests for the sheets endpoint."""
import pytest
from httpx import AsyncClient

class TestGetProjectSheets:

    @pytest.mark.asyncio
    async def test_returns_all_pages_for_project(self, client, db_session):
        """GET /projects/{id}/sheets returns all pages."""

    @pytest.mark.asyncio
    async def test_includes_classification_data(self, client, db_session):
        """Each sheet includes discipline, page_type from classification."""

    @pytest.mark.asyncio
    async def test_includes_scale_data(self, client, db_session):
        """Each sheet includes scale_text, pixels_per_foot, confidence."""

    @pytest.mark.asyncio
    async def test_includes_measurement_counts(self, client, db_session):
        """Each sheet includes count of measurements on that page."""

    @pytest.mark.asyncio
    async def test_grouped_by_discipline(self, client, db_session):
        """Response groups sheets by discipline field."""

    @pytest.mark.asyncio
    async def test_sorted_by_display_order(self, client, db_session):
        """Sheets within groups are sorted by display_order, then sheet_number."""

    @pytest.mark.asyncio
    async def test_no_n_plus_one_queries(self, client, db_session):
        """Endpoint uses single query with joins, not N+1."""
        # Use SQLAlchemy event listener to count queries

    @pytest.mark.asyncio
    async def test_nonexistent_project_returns_404(self, client):
        """GET for unknown project_id returns 404."""

    @pytest.mark.asyncio
    async def test_empty_project_returns_empty_list(self, client, db_session):
        """Project with no documents returns empty sheets array."""
```

### Backend Tests: `backend/tests/integration/test_page_display_fields.py`

```python
"""Tests for page display field endpoints."""

class TestUpdatePageDisplay:

    @pytest.mark.asyncio
    async def test_set_display_name(self, client, db_session):
        """PUT /pages/{id}/display updates display_name."""

    @pytest.mark.asyncio
    async def test_set_display_order(self, client, db_session):
        """PUT /pages/{id}/display updates display_order."""

    @pytest.mark.asyncio
    async def test_set_group_name(self, client, db_session):
        """PUT /pages/{id}/display updates group_name."""

class TestUpdatePageRelevance:

    @pytest.mark.asyncio
    async def test_mark_irrelevant(self, client, db_session):
        """PUT /pages/{id}/relevance with is_relevant=false works."""

    @pytest.mark.asyncio
    async def test_irrelevant_pages_excluded_from_sheets(self, client, db_session):
        """Irrelevant pages don't appear in GET /projects/{id}/sheets."""
```

## Verification Gate

```bash
# Backend tests
cd backend
pytest tests/integration/test_sheets_api.py tests/integration/test_page_display_fields.py -v --tb=short
pytest tests/ -v --tb=short  # Full regression

# Frontend tests
cd frontend
npm test -- --run  # or npx vitest run
npm run lint
npm run type-check  # tsc --noEmit
```

All tests pass. No TypeScript errors. No lint warnings on new files.

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
