# Remaining Phases: Comprehensive Task List (Phases 7, 8, 9)

**Generated:** February 11, 2026
**Status:** Phases 1-6 complete, committed, and pushed to `claude/create-phase-1-tasks-OBEE7`
**Purpose:** Thorough task breakdown for every remaining phase with specific file references, gaps, and implementation details.

---

## Table of Contents

1. [Phase 7: Export & Reporting in Workspace](#phase-7-export--reporting-in-workspace)
2. [Phase 8: Plan Overlay / Version Comparison](#phase-8-plan-overlay--version-comparison)
3. [Phase 9: Housekeeping & Quality](#phase-9-housekeeping--quality)

---

## Phase 7: Export & Reporting in Workspace

**Effort:** 1-2 days | **Priority:** MEDIUM | **Depends on:** Phase 3 (Assembly System — complete)

### What Already Exists

**Backend (90% complete):**

| Component | File | Status |
|-----------|------|--------|
| Export API (4 endpoints) | `backend/app/api/routes/exports.py` | Complete |
| ExportJob model | `backend/app/models/export_job.py` | Complete |
| Export schemas | `backend/app/schemas/export.py` | Complete |
| Celery worker | `backend/app/workers/export_tasks.py` | Complete |
| Excel exporter | `backend/app/services/export/excel_exporter.py` | Missing cost columns |
| CSV exporter | `backend/app/services/export/csv_exporter.py` | Complete |
| PDF exporter | `backend/app/services/export/pdf_exporter.py` | Missing cost summary |
| OST exporter | `backend/app/services/export/ost_exporter.py` | Complete |
| Base exporter + data classes | `backend/app/services/export/base.py` | Missing cost fields |
| Assembly model | `backend/app/models/assembly.py` | Complete |
| Assembly service | `backend/app/services/assembly_service.py` | Complete |
| Export API docs | `docs/api/EXPORTS_API.md` | Complete |

**Backend API Endpoints Already Working:**
- `POST /projects/{project_id}/export` → 202 Accepted (returns `task_id`, `export_id`)
- `GET /exports/{export_id}` → 200 OK (with presigned `download_url` when completed)
- `GET /projects/{project_id}/exports` → 200 OK (list with pagination)
- `DELETE /exports/{export_id}` → 204 No Content

**Export Worker Flow:**
1. Fetches data via `_fetch_export_data_sync()` (sync SQLAlchemy — Celery requirement)
2. Dispatches to format-specific exporter class
3. Uploads to MinIO: `exports/{project_id}/{export_job_id}{extension}`
4. Updates ExportJob with `status`, `file_key`, `file_size`, `completed_at`
5. Progress: 10% init → 20% fetching → 50% generating → 90% uploading → 100% done

**Frontend (0% complete):**
- No export components exist anywhere in `frontend/src/`
- TopToolbar has no export button
- No export hooks, dialogs, or download handlers

**Condition ↔ Assembly relationship already wired:**
```python
# In Condition model
assembly: Mapped["Assembly | None"] = relationship(
    "Assembly", back_populates="condition", uselist=False, cascade="all, delete-orphan"
)
```

### Gap Analysis

| Gap | Description | Impact |
|-----|-------------|--------|
| No cost fields in `ConditionData` | `base.py` `ConditionData` has no cost columns | Exporters can't access assembly costs |
| No assembly join in data fetch | `_fetch_export_data_sync()` doesn't eagerly load `assembly` | DB N+1 or missing data |
| Excel missing cost columns | `excel_exporter.py` Summary sheet has no cost data | Export lacks pricing |
| PDF missing cost summary | `pdf_exporter.py` has no cost section | Reports lack financials |
| No `ExportDropdown` component | Frontend has no way to trigger exports | Users can't export |
| No `ExportOptionsDialog` | No way to configure export parameters | No condition filtering or format options |
| No download handler | No presigned URL handling in frontend | Can't retrieve files |
| TopToolbar has no export button | No entry point for export flow | Feature unreachable |

### Tasks

#### EX-001: Add Assembly Cost Fields to Export Data Classes

**Modified file:** `backend/app/services/export/base.py`

Add cost fields to `ConditionData`:
```python
# Assembly cost fields (nullable — condition may have no assembly)
material_cost: float | None = None
labor_cost: float | None = None
equipment_cost: float | None = None
subcontract_cost: float | None = None
other_cost: float | None = None
total_cost: float | None = None
unit_cost: float | None = None
overhead_percent: float | None = None
profit_percent: float | None = None
total_with_markup: float | None = None
has_assembly: bool = False
```

**Modified file:** `backend/app/workers/export_tasks.py`

Update `_fetch_export_data_sync()`:
- Add `.joinedload(Condition.assembly)` to the query's eager loading options
- When building `ConditionData`, check `condition.assembly` and populate cost fields:
  - `has_assembly = condition.assembly is not None`
  - `material_cost = float(condition.assembly.material_cost)` etc.
  - Convert `Decimal` to `float` for serialization

#### EX-002: Add Cost Columns to Excel Exporter

**Modified file:** `backend/app/services/export/excel_exporter.py`

Update Summary Sheet:
- Current headers: Condition | Type | Unit | Quantity | Measurements | Category | Scope
- New headers: ...Quantity | **Unit Cost | Material | Labor | Equipment | Total Cost | W/Markup** | Measurements | Category | Scope
- Only show cost columns if ANY condition has `has_assembly == True`
- Format cost cells as currency (`$#,##0.00`)

Add per-condition cost breakdown:
- Below measurement table on each condition's detail sheet
- Section: "Assembly Cost Breakdown"
- Table: Component | Type | Unit | Unit Cost | Qty | Waste% | Extended Cost
- Would require loading `AssemblyComponent` list — add to `ConditionData` or a new `AssemblyCostDetail` dataclass

#### EX-003: Add Cost Summary to PDF Exporter

**Modified file:** `backend/app/services/export/pdf_exporter.py`

Add "Cost Summary" section after "Project Summary":
- Table: Condition | Quantity | Unit | Unit Cost | Material | Labor | Equipment | Total | W/Markup
- Only include conditions with assemblies
- Grand total row at bottom
- Format as currency

#### EX-004: Create Export Types and API Client

**New file:** `frontend/src/types/export.ts` (or add to `frontend/src/types/index.ts`)

Types:
- `ExportFormat` — `'excel' | 'csv' | 'pdf' | 'ost'`
- `ExportOptions` — `{ format: ExportFormat; condition_ids?: string[]; include_unverified?: boolean; include_costs?: boolean; ... }`
- `StartExportResponse` — `{ task_id: string; export_id: string; message: string }`
- `ExportJobResponse` — `{ id, project_id, format, status, file_key, file_size, download_url, error_message, ... }`

**New file or modify:** `frontend/src/api/exports.ts`

API functions:
- `startExport(projectId, options)` → `StartExportResponse`
- `getExport(exportId)` → `ExportJobResponse`
- `listExports(projectId)` → `ExportListResponse`
- `deleteExport(exportId)` → void

#### EX-005: Create Export Dropdown Component

**New file:** `frontend/src/components/workspace/ExportDropdown.tsx`

Component:
- Trigger button with `Download` icon from lucide-react
- Dropdown menu with 4 format options: Excel (.xlsx), CSV, PDF Report, OST XML
- Each option shows format icon and description
- Clicking an option opens the `ExportOptionsDialog` with that format pre-selected
- Show loading spinner if any export is in progress
- Uses Radix UI Popover or simple dropdown state

**Modified file:** `frontend/src/components/workspace/TopToolbar.tsx`

- Import and render `<ExportDropdown>` in the toolbar (between Search and Auto Count, or after AI Confidence toggle)
- Pass `projectId` prop

#### EX-006: Create Export Options Dialog

**New file:** `frontend/src/components/workspace/ExportOptionsDialog.tsx`

Modal dialog component:
- **Header:** "Export {format}" with format icon
- **Condition filter:** Checklist of all conditions with checkboxes (default: all selected)
  - Each row: checkbox + color swatch + condition name + measurement count
  - "Select All" / "Deselect All" buttons
- **Common options:**
  - "Include unverified measurements" toggle (default: off)
  - "Include cost data" toggle (only when assemblies exist, default: on)
- **Format-specific options:**
  - Excel: "Include summary sheet" toggle (default: on)
  - CSV: delimiter dropdown (comma, tab, semicolon)
  - PDF: "Include page images" toggle (default: off — heavy)
  - OST: version dropdown (1.0)
- **Actions:** "Export" button (primary), "Cancel" button
- **On submit:** calls `startExport()` → stores `task_id` and `export_id` in state → starts polling

#### EX-007: Create Export Progress Hook and Download Handler

**New file:** `frontend/src/hooks/useExport.ts`

`useExport(projectId)` hook:
- State: `activeExportId`, `activeTaskId`, `exportStatus`, `downloadUrl`
- `startExport(options)`:
  1. Call `exportsApi.startExport(projectId, options)`
  2. Set `activeExportId` and `activeTaskId`
- Uses `useTaskPolling(activeTaskId, { onSuccess, onError })` for progress tracking
- `onSuccess`:
  1. Call `exportsApi.getExport(activeExportId)` to get `download_url`
  2. Trigger browser download: `window.open(download_url)` or `<a download>` trick
  3. Show success toast
  4. Clear active state
- `onError`: show error toast, clear active state
- Returns `{ startExport, isExporting, progress, downloadUrl, cancel }`

**Modified file:** `frontend/src/components/workspace/BottomStatusBar.tsx`

- Show export progress bar when `isExporting` is true
- Display: "Exporting {format}... {progress}%" or "Export complete — downloading"

#### EX-008: Write Tests + Commit

**New file:** `backend/tests/unit/test_export_with_costs.py`

Tests:
- Excel exporter includes cost columns when assembly data present
- Excel exporter omits cost columns when no assemblies
- PDF exporter includes cost summary section
- `_fetch_export_data_sync` loads assembly data correctly
- `ConditionData` cost fields populated from Assembly model

**New file (or modify):** Frontend test for ExportDropdown + ExportOptionsDialog

Tests:
- Dropdown renders 4 format options
- Clicking format opens dialog with correct options
- Condition checklist reflects loaded conditions
- Submit calls API with correct parameters
- Progress polling and download trigger

---

## Phase 8: Plan Overlay / Version Comparison

**Effort:** 2-3 days | **Priority:** LOW (post-MVP) | **Depends on:** Phase 1 (canvas)

### What Already Exists

**Database Schema (100% ready):**

Document model (`backend/app/models/document.py` lines 54-71):
```python
revision_number: Mapped[str | None]        # e.g., "Rev C"
revision_date: Mapped[date | None]         # revision date
revision_label: Mapped[str | None]         # e.g., "ASI #3 Updates"
supersedes_document_id: Mapped[UUID | None] # FK to documents.id (SET NULL on delete)
is_latest_revision: Mapped[bool]           # default True

# Self-referential relationship
supersedes: Mapped["Document | None"] = relationship(...)
```

Migration: `j3k4l5m6n7o8_add_task_records_and_architecture_prep.py` — columns exist in DB.

Page model fields for sheet matching:
- `sheet_number: str | None` (e.g., "S2.01")
- `sheet_title: str | None` (e.g., "Second Floor Plan")
- `title: str | None` (full extracted page title)

Natural sort by `sheet_number` implemented in `/documents/{id}/pages` endpoint.

**API Schema Gap:**
`DocumentResponse` schema (`backend/app/schemas/document.py`) does NOT include the revision fields:
- Missing: `revision_number`, `revision_date`, `revision_label`, `supersedes_document_id`, `is_latest_revision`
- Fields exist in DB and ORM but are invisible to the frontend

**Backend Routes (documents):**
- `POST /projects/{project_id}/documents` — upload
- `GET /projects/{project_id}/documents` — list
- `GET /documents/{document_id}` — detail (with pages)
- `GET /documents/{document_id}/status` — processing status
- `PUT /documents/{document_id}/title-block-region` — title block
- `DELETE /documents/{document_id}` — delete

**Frontend:**
- `DocumentCard.tsx`, `DocumentUploader.tsx` — exist but no revision UI
- `PageCard.tsx`, `PageBrowser.tsx` — page browsing exists
- No overlay viewer, diff tool, or revision chain UI

### Tasks

#### PO-001: Update Document Schema to Expose Revision Fields

**Modified file:** `backend/app/schemas/document.py`

Add to `DocumentResponse`:
```python
revision_number: str | None = None
revision_date: date | None = None
revision_label: str | None = None
supersedes_document_id: uuid.UUID | None = None
is_latest_revision: bool = True
```

Add new schema:
```python
class LinkRevisionRequest(BaseModel):
    revision_number: str
    revision_label: str | None = None
    revision_date: date | None = None
    supersedes_document_id: uuid.UUID  # the older document this replaces

class RevisionChainItem(BaseModel):
    id: uuid.UUID
    filename: str
    revision_number: str | None
    revision_label: str | None
    revision_date: date | None
    is_latest_revision: bool
    page_count: int | None
```

#### PO-002: Add Revision Linking API Endpoints

**Modified file:** `backend/app/api/routes/documents.py`

Add endpoints:
- `PUT /documents/{document_id}/revision` — Link as revision
  - Body: `LinkRevisionRequest`
  - Sets `revision_number`, `revision_label`, `revision_date`, `supersedes_document_id`
  - Sets `is_latest_revision = True` on this doc, `False` on superseded doc
  - Returns updated `DocumentResponse`

- `GET /documents/{document_id}/revisions` — Get revision chain
  - Walk `supersedes_document_id` chain backwards
  - Return ordered list: `[Rev C (latest), Rev B, Rev A (original)]`
  - Returns `list[RevisionChainItem]`

#### PO-003: Add Page Comparison Endpoint

**New file or modified:** `backend/app/api/routes/pages.py`

Add endpoint:
- `GET /pages/{page_id}/compare/{other_page_id}` — Get comparison data
  - Returns: `{ page_a: PageDetail, page_b: PageDetail, match_method: "sheet_number" | "page_number" | "title" }`
  - Includes image URLs for both pages
  - Match score/method so frontend knows how pages were paired

Add endpoint:
- `GET /documents/{document_id}/compare/{other_document_id}` — Get matched page pairs
  - Auto-match pages by `sheet_number` first, then `page_number` fallback
  - Returns: `list[{ page_a_id, page_b_id, sheet_number, match_confidence }]`
  - Unmatched pages listed separately (pages added/removed between revisions)

#### PO-004: Create Frontend Revision Chain Panel

**New file:** `frontend/src/components/documents/RevisionChainPanel.tsx`

Component:
- Displays document revision chain as vertical timeline
- Each node: revision label, date, page count
- "Latest" badge on current revision
- "Link Revision" button to open linking dialog
- Click a revision to navigate to that document

**New file:** `frontend/src/components/documents/LinkRevisionDialog.tsx`

Modal dialog:
- Select the document this supersedes (dropdown of project documents)
- Enter revision number, label, date
- Submit calls `PUT /documents/{id}/revision`

#### PO-005: Create Plan Overlay Viewer

**New file:** `frontend/src/components/viewer/PlanOverlayView.tsx`

Component (Konva-based):
- **Side-by-side mode:** Two Konva stages with synchronized pan/zoom
  - Left: older revision page, Right: newer revision page
  - Linked viewport: pan/zoom one → the other follows
- **Overlay mode:** Single Konva stage with two image layers
  - Opacity slider (0-100%) controls newer revision opacity
  - Older revision always at 100%
  - Toggle between "fade" and "swipe" comparison modes
- **Controls:**
  - Mode toggle: Side-by-side / Overlay
  - Opacity slider (overlay mode only)
  - Page pair navigation (prev/next matched pair)
  - "Unmatched" indicator for pages only in one revision
- **Entry point:** Button in document detail or toolbar when viewing a document with revisions

#### PO-006: Write Tests

**Backend tests:**
- `test_revision_linking.py` — link/unlink revisions, chain traversal
- `test_page_comparison.py` — page matching by sheet_number, fallback to page_number

**Frontend tests:**
- `RevisionChainPanel.test.tsx` — renders chain, click navigation
- `PlanOverlayView.test.tsx` — opacity slider, mode toggle, synchronized viewport

---

## Phase 9: Housekeeping & Quality

**Effort:** 1-2 days | **Priority:** HIGH | **Can run anytime**

### Current State Assessment

| Item | Status | Details |
|------|--------|---------|
| `STATUS.md` | Outdated | Last updated Jan 26. Claims Phase 3A "in progress" — but Phases 1-6 are all complete |
| `.bak` files | 3 dead files | `Dashboard.ORIGINAL_BACKUP.tsx.bak`, `Dashboard.tsx.bak`, `DashboardRefactored.tsx.bak` in `frontend/src/pages/` |
| Old viewer route | Active, no redirect | `/documents/:documentId/pages/:pageId` → `TakeoffViewer.tsx` (1265 lines, fully functional) |
| New workspace route | Active | `/projects/:id/workspace` → `TakeoffWorkspace.tsx` |
| Migration chain | Healthy | 22 migrations, 3 merge commits (all no-op), linear tail to `q5r6s7t8u9v0` |
| Assembly migrations | Present | `p4q5r6s7t8u9_add_assembly_system` ✓ |
| Auto count migrations | Present | `q5r6s7t8u9v0_add_auto_count` ✓ |
| MeasurementHistory | Present | In `o3p4q5r6s7t8_add_review_fields_and_history` ✓ |

### Router Configuration (`frontend/src/App.tsx`)

```
/                          → Redirect to /projects
/projects                  → Projects list
/projects/:projectId       → ProjectDetail
/projects/:id/workspace    → TakeoffWorkspace (NEW)
/projects/:projectId/documents/:documentId → DocumentDetail
/documents/:documentId/pages/:pageId → TakeoffViewer (OLD)
/testing                   → Testing page
/ai-evaluation             → AIEvaluation page
```

Both old (`/documents/.../pages/...`) and new (`/projects/.../workspace`) routes active. Main header hidden on both viewer/workspace routes.

### Tasks

#### HK-001: Update STATUS.md

**Modified file:** `STATUS.md` (repo root)

Full rewrite to reflect current state (Feb 11, 2026):

**Sections to include:**
1. **Project Overview** — ForgeX Takeoff Automation platform description
2. **Architecture** — Backend (FastAPI + Celery + PostgreSQL + MinIO) + Frontend (React + Vite + Konva.js + Zustand)
3. **Completed Phases:**
   - Phase 1: Canvas Migration (Konva.js in workspace)
   - Phase 2: Enhanced Review Interface (review mode, keyboard shortcuts, auto-accept)
   - Phase 3: Assembly System (cost models, formula engine, templates)
   - Phase 4: Auto Count (template matching, LLM similarity, orchestrator)
   - Phase 5: Quick Adjust Tools (geometry adjuster, 7 operations, grid overlay)
   - Phase 6: AI Assist Layer (AutoTab, Batch AI, confidence visualization)
4. **Remaining Phases:** 7 (Export UI), 8 (Plan Overlay), 9 (Housekeeping)
5. **Database Schema** — All 22 migrations listed, latest head: `q5r6s7t8u9v0`
6. **API Endpoints** — Full listing of all routes across all route files
7. **Frontend Components** — Key components by directory
8. **Docker Services** — PostgreSQL, Redis, MinIO, API, Frontend, Worker
9. **Key Configuration** — Environment variables, feature flags

#### HK-002: Delete Dead .bak Files

**Delete 3 files:**
- `frontend/src/pages/Dashboard.ORIGINAL_BACKUP.tsx.bak` (~54 KB)
- `frontend/src/pages/Dashboard.tsx.bak` (~9.4 KB)
- `frontend/src/pages/DashboardRefactored.tsx.bak` (~12 KB)

These are backup files from the old Dashboard → Projects refactoring. The current `Projects.tsx` page is the active replacement. No code references these files.

#### HK-003: Reconcile Old Viewer Route with New Workspace

**Decision context:**
- Old `TakeoffViewer.tsx` (1265 lines) at `/documents/:documentId/pages/:pageId` is fully functional with Konva drawing tools, AI takeoff, conditions panel, measurements CRUD
- New `TakeoffWorkspace.tsx` at `/projects/:id/workspace` is the target architecture with resizable panels, Zustand store, FocusContext
- Both routes currently active with no redirect between them

**Recommended approach: Add redirect with deprecation notice**

**Modified file:** `frontend/src/App.tsx`

- Add redirect from `/documents/:documentId/pages/:pageId` → `/projects/:projectId/workspace` (will need to resolve `projectId` from `documentId`)
- OR: Add a banner on `TakeoffViewer` indicating the new workspace is available with a link
- OR: Simply document which route is used when (viewer for single-page focus, workspace for multi-sheet project-level work)

**Investigation note:** `TakeoffViewer.tsx` contains debug/telemetry code (lines 80-84, 103-107, 132-141, 264-271, 272-276, 293-296) that sends fetch requests to `http://127.0.0.1:7244/ingest/...`. This appears to be development debugging code and should be removed regardless of the route decision.

#### HK-004: Database Migration Audit

**Verify clean migration chain:**

```bash
cd backend && alembic downgrade base && alembic upgrade head
```

**Current chain (22 migrations, 3 merge points):**
```
b01e3b57e974 (root: initial_schema)
  └─ d707bfb8a266 (fulltext_search)
    └─ 576b3ce9ef71 (classification_fields)
      └─ a1b2c3d4e5f6 (classification_history)
        └─ b2c3d4e5f6g7 (status_field)
          └─ e1f2g3h4i5j6 (measurement_engine)
            └─ f3g4h5i6j7k8 (scale_detection_method)
              └─ g4h5i6j7k8l9 (page_physical_dimensions)
                ├─ [Branch A] 0f19e78be270 → d5b881957963
                └─ [Branch B] h1i2j3k4l5m6 (title_block_region)
                  └─ 927c822fd041 (MERGE A)
                    └─ 066b86f9af2c (MERGE B)
                      └─ i2j3k4l5m6n7 (is_ai_generated)
                        └─ j3k4l5m6n7o8 (task_records + architecture_prep)
                          ├─ k4l5m6n7o8p9 (page_display_fields)
                          └─ 0f0c3a5014cf (export_jobs)
                            └─ m1n2o3p4q5r6 (MERGE C)
                              └─ n2o3p4q5r6s7 (is_visible)
                                └─ o3p4q5r6s7t8 (review_fields + history)
                                  └─ p4q5r6s7t8u9 (assembly_system)
                                    └─ q5r6s7t8u9v0 (auto_count) ← HEAD
```

- All 3 merge migrations are no-op (`pass` in upgrade/downgrade) — correct
- Linear tail from last merge to HEAD — clean
- No orphaned branches detected

**Checks to perform:**
1. Full `downgrade base → upgrade head` cycle passes
2. No duplicate column additions (check each migration for `add_column` vs. existing)
3. All foreign keys have proper `ondelete` behavior
4. All indexes are properly created

#### HK-005: Remove Debug/Telemetry Code

**Modified file:** `frontend/src/pages/TakeoffViewer.tsx`

Remove all `#region agent log` blocks that contain `fetch('http://127.0.0.1:7244/ingest/...')` calls:
- Lines ~80-84: Agent log sending page data
- Lines ~103-107: Agent log sending conditions
- Lines ~132-141: Agent log sending measurements
- Lines ~264-276: Agent log sending geometry data
- Lines ~293-296: Agent log sending additional data

Also found in `frontend/src/components/viewer/MeasurementShape.tsx` (line ~270) — same debug endpoint.

These are local development debugging endpoints that:
- POST telemetry to `http://127.0.0.1:7244`
- Silently fail with `.catch(() => {})` if endpoint is down
- Are not related to any production feature
- Should be removed to prevent unnecessary network requests

---

## Summary: All Remaining Tasks

| Phase | Task ID | Description | Effort |
|-------|---------|-------------|--------|
| **7** | EX-001 | Add assembly cost fields to export data classes | S |
| **7** | EX-002 | Add cost columns to Excel exporter | M |
| **7** | EX-003 | Add cost summary to PDF exporter | M |
| **7** | EX-004 | Create export types and API client | S |
| **7** | EX-005 | Create ExportDropdown component | M |
| **7** | EX-006 | Create ExportOptionsDialog component | L |
| **7** | EX-007 | Create export progress hook + download handler | M |
| **7** | EX-008 | Write tests + commit | M |
| **8** | PO-001 | Update DocumentResponse schema for revision fields | S |
| **8** | PO-002 | Add revision linking API endpoints | M |
| **8** | PO-003 | Add page comparison endpoint | M |
| **8** | PO-004 | Create RevisionChainPanel + LinkRevisionDialog | M |
| **8** | PO-005 | Create PlanOverlayView (Konva dual-image viewer) | L |
| **8** | PO-006 | Write tests | M |
| **9** | HK-001 | Update STATUS.md (full rewrite) | M |
| **9** | HK-002 | Delete dead .bak files | XS |
| **9** | HK-003 | Reconcile old viewer route / add redirect | S |
| **9** | HK-004 | Database migration audit (downgrade/upgrade cycle) | S |
| **9** | HK-005 | Remove debug/telemetry code from TakeoffViewer + MeasurementShape | S |

**Sizing:** XS = <15min, S = 15-30min, M = 30-90min, L = 90min+

---

## Dependency Graph

```
Phase 7: Export UI
  EX-001 (cost data classes)
    ├── EX-002 (Excel cost columns)
    └── EX-003 (PDF cost summary)
  EX-004 (frontend API client)
    └── EX-005 (ExportDropdown)
          └── EX-006 (ExportOptionsDialog)
                └── EX-007 (progress hook + download)
  EX-008 (tests) — depends on all above

Phase 8: Plan Overlay
  PO-001 (schema update)
    └── PO-002 (revision linking API)
          └── PO-004 (RevisionChainPanel)
  PO-003 (page comparison API)
    └── PO-005 (PlanOverlayView)
  PO-006 (tests) — depends on all above

Phase 9: Housekeeping (all independent)
  HK-001 (STATUS.md) — standalone
  HK-002 (.bak cleanup) — standalone
  HK-003 (route reconciliation) — standalone
  HK-004 (migration audit) — standalone
  HK-005 (debug code removal) — standalone
```

## Recommended Execution Order

1. **Phase 9** (HK-001 → HK-005) — Quick wins, reduces tech debt
2. **Phase 7** (EX-001 → EX-008) — High user value, backend mostly ready
3. **Phase 8** (PO-001 → PO-006) — Post-MVP, lowest priority
