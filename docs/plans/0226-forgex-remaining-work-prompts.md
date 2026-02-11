# ForgeX Takeoffs — Remaining Work: Phased Implementation Prompt

> **Generated:** February 10, 2026
> **Purpose:** Single comprehensive prompt file for LLM-assisted development of all remaining features, refactors, and enhancements beyond the A/B/C branch merges and UI Overhaul Phase A/B.
> **Usage:** Feed individual phases to Claude Code / Cursor as self-contained development sessions.

---

## Current State Audit (Post-Branch Merge)

### What Has Been Built & Merged to `main`

| Component | Status | Evidence |
|-----------|--------|----------|
| **Branch A: Task Migration** | ✅ Complete | All Celery tasks use TaskTracker, register-before-enqueue pattern. `workers/progress.py` added. Tests in `tests/unit/test_task_migration.py`, `test_task_tracker_edge_cases.py`, `tests/integration/test_task_registration_routes.py` |
| **Branch B: Export System** | ✅ Complete | `ExportJob` model, 4 exporters (`excel_exporter.py`, `csv_exporter.py`, `pdf_exporter.py`, `ost_exporter.py`), `export_tasks.py` worker, full API routes in `exports.py` (start, get, list, delete). Tests in `tests/unit/test_export/`, `test_export_tasks.py`, `tests/integration/test_exports_api.py` |
| **Branch C: UI Overhaul Phase A** | ✅ Complete | Three-panel workspace layout (`TakeoffWorkspace.tsx`), `SheetTree.tsx` with grouping/expand/collapse, `ScaleBadge.tsx`, `ThumbnailStrip.tsx`, `SheetContextMenu.tsx`, `workspaceStore.ts` (Zustand), `FocusContext.tsx`, `constants.ts`, `TopToolbar.tsx`, `BottomStatusBar.tsx`, `CenterCanvas.tsx` (shell), `RightPanel.tsx`. Backend: `sheets.py` route, page display fields migration. Tests present. |
| **UI Overhaul Phase B (Partial)** | ✅ Complete | `ConditionPanel.tsx`, `ConditionList.tsx`, `QuickCreateBar.tsx`, `PropertiesInspector.tsx`, `ConditionContextMenu.tsx`. `is_visible` field on conditions. Tests in `tests/integration/test_condition_visibility.py` |
| **Unified Task API (Phase 2.5)** | ✅ Complete | `tasks.py` route, `TaskRecord` model, `TaskTracker` service, `useTaskPolling` hook |
| **Architecture Prep (Phase 17)** | ✅ Schema Only | Revision fields on `Document` model, vector PDF detection fields on `Page` model, `building`/`area`/`elevation` on `Condition` model |
| **Core Backend Pipeline** | ✅ Complete | Document ingestion, OCR, page classification, scale detection, measurement engine, AI takeoff generation, conditions CRUD |
| **Drawing Tools (Old Viewer)** | ⚠️ Partial | `DrawingToolbar.tsx` exists in old `viewer/` directory with tool definitions. `useCanvasControls.ts`, `useCanvasEvents.ts`, `useDrawingState.ts`, `useUndoRedo.ts` hooks exist. But these are NOT integrated into the new `TakeoffWorkspace` |

### What Does NOT Exist Yet

| Feature | Plan Doc | Status |
|---------|----------|--------|
| **Assembly System** (cost breakdowns, material/labor/equipment, formulas, waste factors) | `13-ASSEMBLY-SYSTEM.md` | 🔴 Not started — no models, services, routes, or UI |
| **Auto Count** (template matching, find-all-similar) | `14-AUTO-COUNT.md` | 🔴 Not started |
| **Enhanced Review Interface** (keyboard shortcuts for approve/reject, auto-accept, confidence filtering, bulk ops, measurement history) | `09-REVIEW-INTERFACE-ENHANCED.md` | 🔴 Not started — no `MeasurementHistory` model, no review service, no review UI in new workspace |
| **Quick Adjust Tools** (keyboard nudge, snap, extend, trim, offset, split) | `15-QUICK-ADJUST-TOOLS.md` | 🔴 Not started |
| **UI Phase C: Plan Viewer & Drawing Tools** (Konva canvas in new workspace, undo/redo with server sync, snap-to-grid, drawing tools, measurement overlays, selection) | `18-UI-OVERHAUL.md` Phase C, `18B-UI-OVERHAUL-PHASE-CONTEXTS.md` | 🔴 Not started — `CenterCanvas.tsx` is a placeholder shell (just shows `<img>`, no Konva) |
| **UI Phase D: AI Assist Layer** (AutoTab, ghost points, batch AI inline, AI suggestion overlays) | `18-UI-OVERHAUL.md` Phase D | 🔴 Not started |
| **UI Phase E: Export & Reporting** (export dropdown in workspace, format picker, progress tracking) | `18-UI-OVERHAUL.md` Phase E | 🔴 Not started — backend export API exists but no workspace UI integration |
| **Plan Overlay / Version Comparison** (Phase 7B) | `17-KREO-ARCHITECTURE-PREP.md` | 🔴 Not started — schema prep done (revision fields on Document) |
| **Vector PDF Extraction** (Phase 9) | `17-KREO-ARCHITECTURE-PREP.md` | 🔴 Not started — detection flags exist on Page model |
| **Natural Language Query / AI Assistant** (Phase 10) | `17-KREO-ARCHITECTURE-PREP.md` | 🔴 Not started — spatial grouping fields exist on Condition model |

### Key Gaps Requiring Attention

1. **CenterCanvas is empty** — The new workspace's canvas is just an `<img>` tag. All drawing, measurement overlay, and interaction must be rebuilt with Konva.js in the new workspace context. The old `TakeoffViewer.tsx` + `viewer/` components exist but are a separate route/paradigm.
2. **Old viewer vs. new workspace disconnect** — Drawing hooks (`useCanvasControls`, `useCanvasEvents`, `useDrawingState`, `useUndoRedo`) and `DrawingToolbar.tsx` exist in the old viewer pattern. These need to be migrated/refactored into the new workspace architecture (Zustand store, FocusContext, resizable panels).
3. **No review workflow in new workspace** — The enhanced review interface (approve/reject/skip with keyboard shortcuts, auto-accept, confidence filtering) has no implementation.
4. **Export UI missing** — Backend is complete but the workspace has no export trigger UI.
5. **STATUS.md is very outdated** (last updated Jan 26) — needs full rewrite.

---

## Implementation Phases

The phases below are ordered by dependency chain and value delivery. Each phase is self-contained and optimized for a single LLM coding session.

---

## Phase 1: Canvas Migration — Konva.js in New Workspace
**Effort:** 3-4 days | **Priority:** CRITICAL (blocks everything)
**Why first:** Every subsequent feature (drawing, review, auto-count overlay, AI assist) requires a functional Konva canvas in the new workspace.

### Context Files to Read (in order)
1. `plans/18B-UI-OVERHAUL-PHASE-CONTEXTS.md` — Phase C context section
2. `plans/18A-UI-OVERHAUL-AUDIT.md` — Parts 1 and 4 (architecture decisions)
3. `plans/06-MEASUREMENT-ENGINE.md` — Geometry types and measurement model
4. `plans/06B-MANUAL-DRAWING-TOOLS.md` — Drawing tool specs
5. `frontend/src/stores/workspaceStore.ts` — Current Zustand store (extend it)
6. `frontend/src/hooks/useCanvasControls.ts` — Existing hook (refactor for new workspace)
7. `frontend/src/hooks/useCanvasEvents.ts` — Existing hook (refactor)
8. `frontend/src/hooks/useDrawingState.ts` — Existing hook (refactor)
9. `frontend/src/hooks/useUndoRedo.ts` — Existing undo/redo logic
10. `frontend/src/pages/TakeoffViewer.tsx` — Old viewer for reference on what works
11. `frontend/src/components/viewer/DrawingToolbar.tsx` — Existing toolbar component

### Tasks

#### 1.1 Replace CenterCanvas shell with Konva Stage
- Replace the `<img>` in `frontend/src/components/workspace/CenterCanvas.tsx` with a `<Stage>` / `<Layer>` from `react-konva`
- Load the sheet image as a Konva `Image` node on a base layer
- Implement pan (drag stage) and zoom (scroll wheel) with viewport state stored in `workspaceStore`
- Add a measurements overlay layer on top of the image layer
- Add a drawing-in-progress layer for the active tool

#### 1.2 Migrate drawing tools into workspace
- Create `frontend/src/components/workspace/DrawingToolbar.tsx` (new, workspace-aware version)
- Wire tool selection to `workspaceStore.activeTool`
- Support tools: select, line, polyline, polygon, rectangle, circle, point
- Each tool has a `useDrawingTool` hook pattern that listens to canvas clicks/moves in the drawing layer
- On tool completion, POST to `POST /projects/{project_id}/conditions/{condition_id}/measurements` and add to the overlay layer

#### 1.3 Measurement overlay rendering
- Query `GET /conditions/{condition_id}/measurements` (or load all for active sheet via page_id)
- Render each measurement as Konva shapes: lines, polylines, polygons, rectangles, circles
- Color-code by condition color
- Show dimension labels (feet/inches) alongside shapes
- Click on a measurement to select it (highlight, show properties in RightPanel)

#### 1.4 Undo/redo with server sync
- Refactor `useUndoRedo.ts` to work with the Zustand store
- Each drawing action pushes to an undo stack
- Undo/redo both update local state AND send DELETE/POST to backend
- Keyboard: Ctrl+Z / Ctrl+Shift+Z (respect FocusContext — only when canvas focused)

#### 1.5 Viewport persistence
- Save viewport position/zoom per sheet in workspaceStore
- When switching sheets, restore last viewport
- Fit-to-page on first load of a sheet

### Tests to Write
- `CenterCanvas.test.tsx` — renders Konva stage, loads image, responds to zoom/pan
- `DrawingToolbar.test.tsx` — tool selection syncs with store
- `useDrawingTool.test.ts` — line/polygon completion creates measurement
- `measurementOverlay.test.tsx` — renders correct shapes from measurement data

### Verification Gate
```bash
cd frontend && npm run type-check && npm run lint && npm test -- --run
```

---

## Phase 2: Enhanced Review Interface
**Effort:** 3-4 days | **Priority:** HIGH
**Depends on:** Phase 1 (Konva canvas must exist for measurement highlighting)

### Context Files to Read
1. `plans/09-REVIEW-INTERFACE-ENHANCED.md` — Full spec
2. `plans/18B-UI-OVERHAUL-PHASE-CONTEXTS.md` — Phase C/D context
3. `backend/app/models/measurement.py` — Current measurement model
4. `backend/app/api/routes/measurements.py` — Current measurement routes
5. `backend/app/services/ai_takeoff.py` — AI generation service (produces measurements to review)

### Tasks

#### 2.1 Backend: MeasurementHistory model
- Create `backend/app/models/measurement_history.py`
  - Fields: `id`, `measurement_id` (FK), `action` (created/modified/verified/rejected/auto_accepted), `previous_data` (JSONB), `new_data` (JSONB), `user_id` (nullable for now), `created_at`
- Add Alembic migration
- Add relationship to `Measurement` model

#### 2.2 Backend: Review service
- Create `backend/app/services/review_service.py`
  - `approve_measurement(id)` → sets `is_verified=True`, logs history
  - `reject_measurement(id)` → deletes or marks rejected, logs history
  - `modify_measurement(id, new_geometry)` → updates geometry, recalculates quantity, logs history
  - `auto_accept_batch(page_id, confidence_threshold)` → bulk accept all measurements above threshold
  - `get_review_stats(project_id)` → counts by status (pending, verified, rejected)
  - `get_next_unreviewed(page_id, current_id)` → returns next measurement needing review

#### 2.3 Backend: Review API endpoints
- `PUT /measurements/{id}/verify` — approve
- `DELETE /measurements/{id}/reject` — reject (or soft-delete with status)
- `PUT /measurements/{id}/geometry` — modify geometry and recalculate
- `POST /projects/{project_id}/measurements/auto-accept` — batch auto-accept
- `GET /projects/{project_id}/review-stats` — dashboard data
- `GET /pages/{page_id}/measurements/next-unreviewed?after={id}` — review navigation

#### 2.4 Frontend: Review mode in workspace
- Add review mode toggle to `TopToolbar.tsx`
- When in review mode:
  - Highlight current measurement being reviewed (pulsing outline on canvas)
  - Show measurement details in RightPanel (geometry, confidence, AI model, quantity)
  - Keyboard shortcuts: `A` = approve, `R` = reject, `S` = skip/next, `E` = edit geometry
  - Arrow keys navigate between measurements on current sheet
  - Auto-advance to next unreviewed after approve/reject
- Confidence filtering: slider in toolbar to show only measurements below threshold
- Bulk operations: "Accept all above 90%" button

#### 2.5 Frontend: Review statistics
- Add review stats summary to `BottomStatusBar.tsx` (verified/pending/rejected counts)
- Optional: small review progress bar in TopToolbar

### Tests to Write
- Backend: `tests/unit/test_review_service.py` — all service methods
- Backend: `tests/integration/test_review_api.py` — endpoint tests
- Frontend: `ReviewMode.test.tsx` — keyboard shortcuts, navigation, approve/reject flow

### Verification Gate
```bash
cd backend && pytest tests/ -v --tb=short
cd frontend && npm run type-check && npm run lint && npm test -- --run
```

---

## Phase 3: Assembly System
**Effort:** 4-5 days | **Priority:** HIGH
**Depends on:** Phase 2 (review interface should exist so assemblies have measurements to price)

### Context Files to Read
1. `plans/13-ASSEMBLY-SYSTEM.md` — **Full spec** (this is the primary document)
2. `plans/07-CONDITION-MANAGEMENT.md` — Current condition model
3. `backend/app/models/condition.py` — Current condition code
4. `backend/app/schemas/condition.py` — Current condition schemas
5. `backend/app/api/routes/conditions.py` — Current condition routes

### Tasks

#### 3.1 Backend: Assembly models
- Create `backend/app/models/assembly.py`:
  - `Assembly` — linked to a Condition, contains breakdown items
    - Fields: `id`, `condition_id` (FK), `name`, `description`, `total_unit_cost`, `waste_factor_percent`, `overhead_percent`, `profit_percent`, `extra_metadata` (JSONB)
  - `AssemblyItem` — individual line item in an assembly
    - Fields: `id`, `assembly_id` (FK), `category` (material/labor/equipment/subcontractor), `name`, `description`, `unit`, `unit_cost`, `quantity_formula` (string expression), `calculated_quantity`, `total_cost`, `sort_order`
- Create `backend/app/models/assembly_template.py`:
  - `AssemblyTemplate` — reusable templates (e.g., "4-inch slab on grade")
  - `AssemblyTemplateItem` — template line items
- Alembic migration for all new tables

#### 3.2 Backend: Formula engine
- Create `backend/app/services/formula_engine.py`
  - Parse simple expressions: `quantity * 1.05` (waste), `quantity * depth`, `area / 27` (CY conversion)
  - Variables: `quantity`, `depth`, `thickness`, `length`, `area`, `perimeter`, `count`
  - Safe eval using AST parsing (no `eval()`)
  - Recalculate all assembly items when measurement quantity changes

#### 3.3 Backend: Assembly service & API
- Create `backend/app/services/assembly_service.py`
  - CRUD for assemblies and items
  - Create assembly from template
  - Recalculate totals when measurements change
- Create/update `backend/app/api/routes/assemblies.py`
  - `POST /conditions/{id}/assembly` — create assembly for condition
  - `POST /conditions/{id}/assembly/from-template` — create from template
  - `GET /conditions/{id}/assembly` — get assembly with items
  - `PUT /assemblies/{id}` — update assembly
  - `POST /assemblies/{id}/items` — add item
  - `PUT /assembly-items/{id}` — update item
  - `DELETE /assembly-items/{id}` — remove item
  - `GET /assembly-templates` — list templates
  - `GET /projects/{id}/cost-summary` — project cost rollup

#### 3.4 Frontend: Assembly panel in workspace
- Add "Cost" tab to the RightPanel (alongside Conditions)
- When a condition is selected and has an assembly:
  - Show assembly items table (category, name, unit, unit cost, qty formula, total)
  - Editable inline cells
  - Add/remove item buttons
  - Waste factor, overhead, profit adjustments
  - Total cost display
- "Create from template" dropdown in condition context menu
- Project-level cost summary accessible from TopToolbar

### Tests to Write
- `tests/unit/test_formula_engine.py` — formula parsing, variable substitution, edge cases
- `tests/unit/test_assembly_service.py` — CRUD, template creation, recalculation
- `tests/integration/test_assemblies_api.py` — all endpoints
- Frontend: `AssemblyPanel.test.tsx` — renders items, edits, template creation

### Verification Gate
```bash
cd backend && pytest tests/ -v --tb=short --cov=app/services/formula_engine --cov=app/services/assembly_service --cov-report=term-missing
cd frontend && npm run type-check && npm test -- --run
```

---

## Phase 4: Auto Count Feature
**Effort:** 3-4 days | **Priority:** MEDIUM-HIGH
**Depends on:** Phase 1 (canvas with measurement overlays needed for visual results)

### Context Files to Read
1. `plans/14-AUTO-COUNT.md` — **Full spec**
2. `plans/08-AI-TAKEOFF-GENERATION.md` — Existing AI takeoff flow
3. `backend/app/services/ai_takeoff.py` — Current AI service
4. `backend/app/services/llm_client.py` — LLM client abstraction

### Tasks

#### 4.1 Backend: Template matching service (OpenCV)
- Create `backend/app/services/auto_count/template_matcher.py`
  - Accept a crop region (bounding box on a page image) as the "template"
  - Use OpenCV `matchTemplate` with normalized cross-correlation
  - Support scale tolerance (±20%) and rotation tolerance (±15°)
  - Return list of match locations with confidence scores
  - Filter by configurable threshold (default 0.80)

#### 4.2 Backend: LLM similarity service
- Create `backend/app/services/auto_count/llm_similarity.py`
  - Send template crop + full page image to vision LLM
  - Prompt: "Find all instances of this element on the drawing. Return bounding boxes as JSON."
  - Parse response into standardized match format
  - Use as fallback/validation when template matching produces ambiguous results

#### 4.3 Backend: Auto count orchestration
- Create `backend/app/services/auto_count/orchestrator.py`
  - Strategy: template match first → LLM validation for low-confidence matches
  - Deduplicate overlapping detections (non-maximum suppression)
  - Create measurements for each detection (geometry_type=point, quantity=1 each)
  - Link all to the selected condition
- Create Celery task: `backend/app/workers/auto_count_tasks.py`

#### 4.4 Backend: Auto count API
- `POST /pages/{page_id}/auto-count` — body: `{ condition_id, template_bbox: {x,y,w,h}, options }`
- Returns task_id for polling
- Results: list of detected locations with confidence

#### 4.5 Frontend: Auto count tool
- Add "Auto Count" tool to DrawingToolbar
- Workflow:
  1. User selects a condition
  2. User draws a bounding box around one instance of the element
  3. System shows "Searching..." loading state
  4. Results appear as point markers on the canvas with confidence badges
  5. User can approve/reject individual detections
- Threshold slider for filtering low-confidence matches

### Tests to Write
- `tests/unit/test_template_matcher.py` — matching with synthetic images
- `tests/unit/test_auto_count_orchestrator.py` — deduplication, measurement creation
- `tests/integration/test_auto_count_api.py` — endpoint flow
- Frontend: `AutoCountTool.test.tsx` — bbox drawing, result display

### Verification Gate
```bash
cd backend && pytest tests/ -v --tb=short
cd frontend && npm run type-check && npm test -- --run
```

---

## Phase 5: Quick Adjust Tools
**Effort:** 2-3 days | **Priority:** MEDIUM
**Depends on:** Phase 1 (Konva canvas) + Phase 2 (measurement selection/editing)

### Context Files to Read
1. `plans/15-QUICK-ADJUST-TOOLS.md` — **Full spec**
2. `plans/06-MEASUREMENT-ENGINE.md` — Geometry operations
3. `backend/app/services/measurement_engine.py` — Existing measurement calculations

### Tasks

#### 5.1 Backend: Geometry adjustment service
- Create `backend/app/services/geometry_adjuster.py`
  - `nudge(measurement_id, direction, distance_px)` — move geometry by offset
  - `snap_to_grid(measurement_id, grid_size_px)` — snap vertices to grid
  - `extend(measurement_id, endpoint, distance)` — extend line from endpoint
  - `trim(measurement_id, trim_point)` — shorten to intersection or point
  - `offset(measurement_id, distance, direction)` — parallel offset (for walls)
  - `split(measurement_id, split_point)` — split line/polyline at point into two measurements
  - Each operation recalculates quantity via measurement engine
- Add API endpoint: `PUT /measurements/{id}/adjust` with `{ action, params }`

#### 5.2 Frontend: Quick adjust toolbar & keyboard bindings
- Create `frontend/src/components/workspace/QuickAdjustToolbar.tsx`
  - Appears when a measurement is selected
  - Buttons: Nudge arrows, Snap, Extend, Trim, Offset, Split
  - Keyboard shortcuts (when canvas focused):
    - Arrow keys: nudge selected measurement 1px (Shift+Arrow: 10px)
    - `G`: toggle snap-to-grid
    - `X`: extend
    - `T`: trim
    - `O`: offset (enter distance)
    - `/`: split at click point

#### 5.3 Frontend: Snap-to-grid system
- Add grid overlay toggle to canvas (configurable grid size)
- Snap cursor to grid when drawing (if enabled)
- Visual grid lines on canvas (subtle, toggleable)

### Tests to Write
- `tests/unit/test_geometry_adjuster.py` — each operation with expected geometry output
- Frontend: `QuickAdjustToolbar.test.tsx` — keyboard shortcuts, action dispatch

### Verification Gate
```bash
cd backend && pytest tests/ -v --tb=short
cd frontend && npm run type-check && npm test -- --run
```

---

## Phase 6: UI Phase D — AI Assist Layer
**Effort:** 2-3 days | **Priority:** MEDIUM
**Depends on:** Phase 1 (canvas), Phase 2 (review), Phase 4 (auto count)

### Context Files to Read
1. `plans/18-UI-OVERHAUL.md` — Phase D section
2. `plans/18B-UI-OVERHAUL-PHASE-CONTEXTS.md` — Phase D context
3. `plans/08-AI-TAKEOFF-GENERATION.md` — AI takeoff generation spec
4. `backend/app/services/ai_takeoff.py` — Current AI service
5. `backend/app/workers/takeoff_tasks.py` — Current takeoff task

### Tasks

#### 6.1 AutoTab — AI-suggested next measurement
- After user completes a measurement, AI predicts the next likely measurement
- Show as "ghost" dashed shapes on canvas that user can accept (Tab) or dismiss (Esc)
- Implementation: after each measurement saved, send context (condition type, last measurement, page image region) to LLM for next suggestion

#### 6.2 Batch AI inline
- "Run AI" button per sheet (in SheetTree context menu or TopToolbar)
- Runs AI takeoff for current sheet with existing conditions as context
- Results appear as unverified measurements on canvas (dashed outlines, lower opacity)
- User reviews inline (approve/reject using Phase 2's review mode)

#### 6.3 AI confidence visualization
- Color-code measurement overlays by AI confidence:
  - Green (>90%): high confidence
  - Yellow (70-90%): medium
  - Red (<70%): low
- Toggle confidence coloring on/off in toolbar

### Tests to Write
- Frontend: `AIAssistLayer.test.tsx` — ghost rendering, accept/dismiss
- Integration: verify AI suggestions appear after measurement completion

---

## Phase 7: UI Phase E — Export & Reporting in Workspace
**Effort:** 1-2 days | **Priority:** MEDIUM
**Depends on:** Phase 3 (assembly system for cost columns in exports)

### Context Files to Read
1. `plans/18-UI-OVERHAUL.md` — Phase E section
2. `plans/10-EXPORT-SYSTEM.md` — Export spec
3. `backend/app/api/routes/exports.py` — Existing export API (fully implemented)
4. `docs/api/EXPORTS_API.md` — Export API docs

### Tasks

#### 7.1 Export dropdown in workspace
- Add export button to `TopToolbar.tsx`
- Dropdown with format options: Excel, CSV, PDF Report, OST XML
- Each option opens a config dialog (which conditions to include, options)
- On submit: calls `POST /projects/{project_id}/export` and polls task status
- Show progress in BottomStatusBar
- On completion: auto-download via presigned URL

#### 7.2 Export options dialog
- Condition filter checkboxes (select which conditions to export)
- Format-specific options (per plan spec):
  - Excel: include/exclude cost columns, summary sheet toggle
  - CSV: delimiter option
  - PDF: include page images toggle
  - OST: version selection

#### 7.3 Update exporters for assembly costs
- Modify `excel_exporter.py` to include assembly cost columns when assemblies exist
- Modify `pdf_exporter.py` to include cost summary section
- Add `assembly` join to `fetch_export_data` queries

### Tests to Write
- Frontend: `ExportDialog.test.tsx` — form submission, polling, download trigger
- Backend: update export tests to verify assembly cost columns

---

## Phase 8: Plan Overlay / Version Comparison
**Effort:** 2-3 days | **Priority:** LOW (post-MVP)
**Depends on:** Phase 1 (canvas)

### Context Files to Read
1. `plans/17-KREO-ARCHITECTURE-PREP.md` — Plan Overlay section
2. `backend/app/models/document.py` — Revision fields already present

### Tasks

#### 8.1 Backend: Revision linking API
- `PUT /documents/{id}/revision` — set revision_number, revision_label, link to supersedes_document_id
- `GET /projects/{id}/revisions` — list document revision chains
- `GET /documents/{id}/compare/{other_id}` — return matched page pairs

#### 8.2 Frontend: Overlay viewer
- Side-by-side or overlay view with opacity slider
- Page matching by sheet_number
- Highlight changed regions (diff overlay)

---

## Phase 9: Housekeeping & Quality
**Effort:** 1-2 days | **Priority:** HIGH (do alongside or after Phase 1)

### Tasks

#### 9.1 Update STATUS.md
- Rewrite to reflect current state (post-branch-merge)
- Document all new endpoints, models, and frontend components

#### 9.2 Clean up dead .bak files
- Remove `Dashboard.ORIGINAL_BACKUP.tsx.bak`, `Dashboard.tsx.bak`, `DashboardRefactored.tsx.bak` from `frontend/src/pages/`

#### 9.3 Reconcile old viewer route with new workspace
- The old `TakeoffViewer.tsx` at `/documents/:documentId/pages/:pageId` still exists
- Decision needed: deprecate it or keep as a fallback
- If deprecating: add redirect to new workspace route
- If keeping: document when each route is used

#### 9.4 Database migration audit
- Verify all migrations run cleanly from scratch (`alembic downgrade base && alembic upgrade head`)
- Fix any broken migration chains (there are merge migrations suggesting potential issues)

#### 9.5 Alembic migration for new models
- Assembly, AssemblyItem, AssemblyTemplate, AssemblyTemplateItem tables
- MeasurementHistory table
- Verify foreign keys and cascade deletes

---

## Dependency Graph

```
Phase 1: Canvas Migration (CRITICAL — blocks most other phases)
    │
    ├──→ Phase 2: Enhanced Review Interface
    │        │
    │        └──→ Phase 3: Assembly System
    │                 │
    │                 └──→ Phase 7: Export UI (needs assembly for cost columns)
    │
    ├──→ Phase 4: Auto Count
    │
    ├──→ Phase 5: Quick Adjust Tools (needs Phase 2 for measurement selection)
    │
    └──→ Phase 6: AI Assist Layer (needs Phase 2 + Phase 4)

Phase 8: Plan Overlay (independent, post-MVP)
Phase 9: Housekeeping (can run anytime, ideally after Phase 1)
```

## Recommended Execution Order

| Order | Phase | Parallelizable With |
|-------|-------|---------------------|
| 1 | Phase 1: Canvas Migration | Phase 9: Housekeeping |
| 2 | Phase 2: Enhanced Review | Phase 3: Assembly (backend only, in parallel) |
| 3 | Phase 3: Assembly (frontend) | — |
| 4 | Phase 4: Auto Count | Phase 5: Quick Adjust |
| 5 | Phase 5: Quick Adjust | Phase 4: Auto Count |
| 6 | Phase 6: AI Assist Layer | — |
| 7 | Phase 7: Export UI | — |
| 8 | Phase 8: Plan Overlay | (post-MVP, optional) |

---

## Notes for LLM Sessions

### Architecture Rules (from UI Overhaul Audit)
- **State:** Zustand for UI state (`workspaceStore`), React Query for server data. Never mix.
- **Error handling:** No error loses user work. Toast + retry everywhere.
- **Focus system:** `FocusContext` with `focusRegion` for keyboard shortcut routing.
- **Constants:** All magic numbers in `frontend/src/lib/constants.ts`.
- **Feature flag:** `ENABLE_NEW_WORKSPACE` gates the new workspace route.

### Testing Requirements
- Backend: 85%+ coverage on new service code, 95%+ on critical modules (formula engine, geometry adjuster)
- Frontend: React Testing Library + Vitest. Test user interactions, not implementation details.
- Always run full regression before committing: `cd backend && pytest tests/ -v --tb=short`

### Key File Paths
```
# Backend
backend/app/models/          — SQLAlchemy models
backend/app/schemas/         — Pydantic schemas
backend/app/api/routes/      — FastAPI route handlers
backend/app/services/        — Business logic services
backend/app/workers/         — Celery task definitions
backend/app/utils/storage.py — MinIO/S3 storage abstraction
backend/alembic/versions/    — Database migrations

# Frontend
frontend/src/stores/         — Zustand stores
frontend/src/hooks/          — React hooks
frontend/src/components/workspace/ — New workspace components
frontend/src/components/sheets/    — Sheet tree, scale badge
frontend/src/components/conditions/ — Condition panel, quick create
frontend/src/components/viewer/    — OLD viewer (pre-overhaul)
frontend/src/contexts/       — FocusContext, NotificationContext
frontend/src/lib/constants.ts — Shared constants
frontend/src/api/            — API client functions
frontend/src/types/          — TypeScript type definitions

# Plans
plans/00-MASTER-IMPLEMENTATION-PLAN.md — Master roadmap
plans/13-ASSEMBLY-SYSTEM.md            — Assembly spec
plans/14-AUTO-COUNT.md                 — Auto count spec
plans/15-QUICK-ADJUST-TOOLS.md        — Quick adjust spec
plans/09-REVIEW-INTERFACE-ENHANCED.md  — Enhanced review spec
plans/18-UI-OVERHAUL.md               — UI overhaul full spec
plans/18A-UI-OVERHAUL-AUDIT.md        — Architecture decisions
plans/18B-UI-OVERHAUL-PHASE-CONTEXTS.md — Per-phase AI context
```
