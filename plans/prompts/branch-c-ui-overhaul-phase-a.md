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
describe("TakeoffWorkspace", () => {
  it("renders three-panel layout", () => {
    // Assert: LeftSidebar, CenterCanvas, RightPanel all present
  });

  it("renders feature flag gate", () => {
    // When ENABLE_NEW_WORKSPACE is false, redirects to old UI
  });

  it("loads project data on mount", () => {
    // Assert: React Query fires for project + sheets
  });

  it("handles project not found", () => {
    // Assert: 404 state shown, no crash
  });
});
```

#### `SheetTree.test.tsx`

```typescript
describe("SheetTree", () => {
  it("renders sheets grouped by discipline", () => {
    // Given: sheets with different disciplines
    // Assert: group headers shown, sheets under correct groups
  });

  it("clicking a sheet sets it as active", () => {
    // Assert: workspaceStore.activeSheetId updated
  });

  it("shows scale badge per sheet", () => {
    // Given: sheet with scale detected at 85% confidence
    // Assert: green badge shown with scale text
  });

  it("shows no-scale indicator for uncalibrated sheets", () => {
    // Given: sheet with no scale
    // Assert: warning indicator shown
  });

  it("persists expand/collapse to localStorage", () => {
    // Act: collapse a group
    // Assert: localStorage updated
    // Act: re-render
    // Assert: group still collapsed
  });

  it("keyboard navigation works", () => {
    // Act: press ArrowDown
    // Assert: next sheet highlighted
    // Act: press Enter
    // Assert: sheet becomes active
  });

  it("search filters sheets by name", () => {
    // Given: sheets S1.01, S1.02, A1.01
    // Act: type "S1" in search
    // Assert: only S1.01 and S1.02 visible
  });

  it("handles empty project gracefully", () => {
    // Given: project with no documents/pages
    // Assert: empty state message, no crash
  });
});
```

#### `workspaceStore.test.ts`

```typescript
describe("WorkspaceStore", () => {
  it("initializes with default values", () => {
    // Assert: activeTool is 'select', no activeSheetId, etc.
  });

  it("setActiveSheet updates activeSheetId", () => {
    // Act + Assert
  });

  it("setActiveTool prevents tool activation without active condition", () => {
    // Given: no activeConditionId
    // Act: try to set activeTool to 'polygon'
    // Assert: tool not changed (or warning issued)
  });

  it("panel widths respect min/max bounds", () => {
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
