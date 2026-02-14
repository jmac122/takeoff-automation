# Phase 5: Quick Adjust Tools — Task Completion List

**Status**: COMPLETE
**Branch**: `claude/create-phase-1-tasks-OBEE7`

## Summary

Phase 5 implements keyboard-driven precision geometry editing tools for measurements. Users can nudge, snap-to-grid, extend, trim, offset, split, and join measurement geometry directly from the canvas using keyboard shortcuts or a floating toolbar. A visual grid overlay system assists with alignment.

---

## Tasks

### QA-001: Create Backend Geometry Adjuster Service ✅
**Files**: `backend/app/services/geometry_adjuster.py`

Pure geometry helper functions:
- `_translate_point()`, `_snap_point()`, `_distance()`
- `_project_point_on_segment()` — point-to-segment projection clamped to [0,1]
- `_line_line_intersection()` — segment or infinite line intersection
- `_perpendicular()` — left-perpendicular unit normal

7 geometry operations (pure functions on geometry_data dicts):
- `nudge_geometry()` — move all vertices by dx/dy for direction (up/down/left/right)
- `snap_geometry_to_grid()` — snap all vertices to nearest grid intersection
- `extend_geometry()` — extend line/polyline endpoints along their direction
- `trim_geometry()` — project trim_point onto line, keep longer side
- `offset_geometry()` — parallel offset for polygons/rectangles (miter or bevel corners)
- `split_geometry()` — split line/polyline at a point into two geometries
- `join_geometries()` — join two line/polyline geometries at touching endpoints

`GeometryAdjusterService` async class:
- `adjust_measurement()` — dispatches action, persists to DB, recalculates quantities
- Stores `original_geometry` / `original_quantity` on first modification for undo
- `_recalculate()` — delegates to MeasurementEngine for quantity recalculation
- `_update_condition_totals()` — updates denormalized condition sums
- Singleton via `get_geometry_adjuster()`

### QA-002: Create Geometry Adjust Schemas ✅
**Files**: `backend/app/schemas/geometry_adjust.py`

- `AdjustPoint` — x, y
- `GeometryAdjustRequest` — action (Literal union of 7 actions) + params dict, with model_validator ensuring required params per action
- `GeometryAdjustResponse` — status, action, measurement_id, new_geometry_type, new_geometry_data, new_quantity, new_unit, created_measurement_id (for split)

### QA-003: Add Adjust API Endpoint ✅
**Files**: `backend/app/api/routes/measurements.py` (modified)

- `PUT /measurements/{id}/adjust` — accepts `GeometryAdjustRequest`, returns `GeometryAdjustResponse`
- Handles split action by querying for newly created measurement
- 400 on ValueError, 422 on validation errors

### QA-004: Add Frontend Types ✅
**Files**: `frontend/src/types/index.ts` (modified)

- `GeometryAdjustAction` — 7-member string literal union
- `GeometryAdjustRequest` — action + params
- `GeometryAdjustResponse` — full response type with optional created_measurement_id

### QA-005: Add Frontend API Client ✅
**Files**: `frontend/src/api/measurements.ts` (modified)

- `adjustMeasurement(measurementId, data)` → `GeometryAdjustResponse`

### QA-006: Create useQuickAdjust Hook ✅
**Files**: `frontend/src/hooks/useQuickAdjust.ts`

- `useAdjustMeasurement()` — React Query mutation with cache invalidation (measurements + conditions)
- `useQuickAdjustKeyboard()` — keyboard event listener:
  - Arrow keys: nudge 1px (Shift: 10px)
  - G: toggle snap mode, Shift+G: snap selection to grid
  - X: extend end, Shift+X: extend start
  - Only active when focusRegion is 'canvas' and measurements are selected
  - Ignores events when typing in inputs/textareas

### QA-007: Add Snap/Grid State to workspaceStore ✅
**Files**: `frontend/src/stores/workspaceStore.ts` (modified)

State:
- `snapToGrid: boolean` (default false)
- `gridSize: number` (default 10px)
- `showGrid: boolean` (default false)

Actions:
- `toggleSnapToGrid()`
- `setGridSize(size)` — clamps to min 1
- `toggleShowGrid()`

Selectors:
- `selectSnapToGrid`, `selectGridSize`, `selectShowGrid`

### QA-008: Create QuickAdjustToolbar Component ✅
**Files**: `frontend/src/components/workspace/QuickAdjustToolbar.tsx`

- Floating toolbar, only renders when measurements are selected
- Buttons: 4 nudge arrows, Snap to Grid, Extend, Trim, Offset, Split, Join
- Join button disabled when < 2 measurements selected
- Shows keyboard shortcut tooltips
- Pending indicator during mutations

### QA-009: Create GridOverlay Component ✅
**Files**: `frontend/src/components/workspace/GridOverlay.tsx`

- SVG overlay rendering grid lines across the canvas
- Grid lines in image-pixel space, transformed by viewport zoom/pan
- Performance guard: hides when scaled grid < 4px
- Subtle white lines at 8% opacity
- Hidden when `showGrid` is false

### QA-010: Integrate with TopToolbar ✅
**Files**: `frontend/src/components/workspace/TopToolbar.tsx` (modified)

- Added `Grid3X3` icon import
- Added grid toggle button between Undo/Redo and spacer
- Blue highlight when grid is active
- Reads `showGrid` / `toggleShowGrid` from workspace store

### QA-011: Write Backend Unit Tests ✅
**Files**: `backend/tests/unit/test_geometry_adjuster.py`

Helper tests:
- translate_point, snap_point, distance, project_point_on_segment
- line_line_intersection: crossing, parallel, no segment overlap, unclamped

Nudge tests (9):
- All directions for line, polyline, polygon, rectangle, circle, point
- Zero distance, unknown type passthrough, extra field preservation

Snap tests (7):
- Line, polyline, rectangle, circle, point
- Zero/negative grid returns unchanged

Extend tests (8):
- Line end/start/both, diagonal line direction
- Polyline end/start
- Zero-length line, polygon returns unchanged

Trim tests (4):
- Line trim keeps longer side (both directions)
- Polyline trim
- Polygon returns unchanged

Offset tests (7):
- Rectangle outward/inward, clamps minimum dimension
- Polygon miter/bevel, too-few-points edge case
- Line returns unchanged

Split tests (6):
- Line split at midpoint, near-start/near-end returns None
- Polyline split
- Polygon returns None, single-point polyline returns None

Join tests (5):
- End-to-start, end-to-end connections
- Not within tolerance returns None
- Polyline-to-line join
- Custom tolerance thresholds

### QA-012: Write Integration Tests ✅
**Files**: `backend/tests/integration/test_geometry_adjust_api.py`

API endpoint tests:
- 200 responses for all 7 actions (nudge, snap, extend, trim, offset, split, join)
- 400 when measurement not found (ValueError from service)
- 422 for invalid action
- 422 for missing required params (nudge/direction, trim/trim_point, split/split_point, join/other_measurement_id)

---

## Key Design Decisions

1. **Pure functions + async service** — Geometry operations are pure functions for testability; the `GeometryAdjusterService` wraps them with DB persistence
2. **Single endpoint** — `PUT /measurements/{id}/adjust` with action dispatch rather than separate endpoints per operation
3. **Original geometry preservation** — First modification stores `original_geometry` and `original_quantity` for undo reference
4. **Split creates second measurement** — Split operation creates a new Measurement in the same condition, linked by notes
5. **Join deletes second measurement** — Join merges into the first measurement and deletes the other
6. **Keyboard shortcuts respect focus** — Only fire when `focusRegion === 'canvas'` and not in an input
7. **Grid overlay as SVG** — Lightweight SVG lines rather than canvas rendering, with performance guard at small grid sizes
8. **Workspace store for grid state** — `snapToGrid`, `gridSize`, `showGrid` in Zustand for cross-component access
