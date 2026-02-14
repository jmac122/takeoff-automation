# Phase 1: Canvas Migration Task List

## Konva.js in New Workspace

**Objective:** Replace the placeholder `CenterCanvas.tsx` shell (currently an `<img>` tag) with a fully functional Konva.js canvas supporting image rendering, pan/zoom, drawing tools, measurement overlays, undo/redo with server sync, and per-sheet viewport persistence.

**Deliverable:** Users can view sheet images on a Konva canvas, draw measurements with all 7 tools, see existing measurements as color-coded overlays, select/edit/move/delete measurements, undo/redo actions with server persistence, and retain viewport state when switching sheets.

**Priority:** CRITICAL — blocks all subsequent phases (Review, Assembly, Auto Count, AI Assist, Export UI)

**Source:** `docs/plans/0226-forgex-remaining-work-prompts.md` Phase 1

---

## Task Overview

| Category | Task Count | Priority |
|----------|------------|----------|
| 1. Konva Stage & Image Loading | 6 tasks | Critical |
| 2. Viewport Controls (Pan, Zoom, Fit) | 6 tasks | Critical |
| 3. Drawing Tool Integration | 8 tasks | Critical |
| 4. Measurement Overlay Rendering | 5 tasks | High |
| 5. Measurement Interaction (Select, Edit, Move, Delete) | 5 tasks | High |
| 6. Undo/Redo System with Server Sync | 5 tasks | High |
| 7. Viewport Persistence (Per-Sheet State) | 4 tasks | Medium |
| 8. Testing & Verification | 6 tasks | High |

**Total: 45 tasks**

---

## 1. Konva Stage & Image Loading

### 1.1 Core Stage Setup

- [x] **CM-001**: Replace CenterCanvas HTML shell with Konva Stage container
  - **File:** `frontend/src/components/workspace/CenterCanvas.tsx`
  - Remove the `<img>` tag and `<div>` overflow container
  - Add a `<div id="workspace-canvas-container">` wrapper that fills parent via `h-full w-full`
  - Import `Stage` from `react-konva` and render `<Stage>` inside the wrapper
  - Preserve existing props interface (`CenterCanvasProps`) but add `pageId?: string`
  - Preserve `data-focus-region="canvas"`, `tabIndex={0}`, and `onFocus` handler
  - Keep the "No sheet selected", "Loading sheet...", and "Sheet image not available" placeholder states
  - **Ref pattern:** Use `useRef<Konva.Stage>(null)` and attach via `ref`

- [x] **CM-002**: Add ResizeObserver-based stage sizing hook
  - **File (new):** `frontend/src/hooks/useStageSize.ts`
  - Accept a container `ref` or `id` string
  - Return `{ width: number, height: number }` tracking the container's client dimensions
  - Use `ResizeObserver` (with window `resize` fallback) — pattern from existing `useCanvasControls.ts` lines 48-83
  - Debounce to avoid layout thrashing during panel resizing (`react-resizable-panels` triggers frequent events)
  - Set `<Stage width={stageSize.width} height={stageSize.height}>` in CM-001

- [x] **CM-003**: Load sheet image as Konva.Image on a base layer
  - **File:** `frontend/src/components/workspace/CenterCanvas.tsx`
  - Reuse existing `usePageImage` hook from `frontend/src/hooks/usePageImage.ts`
  - Pass `sheetImageUrl` to get an `HTMLImageElement`
  - Render `<Layer><KonvaImage image={image} /></Layer>` as the bottom layer
  - Guard on `image && image.complete && image.width > 0 && image.height > 0`

- [x] **CM-004**: Implement multi-layer Konva architecture with Z-ordering
  - **File:** `frontend/src/components/workspace/CenterCanvas.tsx`
  - Create layers in order (bottom to top), matching `Z_ORDER` from `frontend/src/lib/constants.ts`:
    - Layer 0: Background image (KonvaImage)
    - Layer 1: MeasurementLayer (areas first, then lines, then points — sorted by type)
    - Layer 2: Selected measurement highlight (Z_ORDER.SELECTED)
    - Layer 3: Drawing preview / in-progress (Z_ORDER.PREVIEW)
  - Z-ordering within measurement layer handled by render order (areas → lines → points)

- [x] **CM-005**: Wire CenterCanvas props through TakeoffWorkspace
  - **File:** `frontend/src/components/workspace/TakeoffWorkspace.tsx`
  - Pass `pageId` (derived from `activeSheet.id`) to `CenterCanvas`
  - Pass full `activeSheet` object (or needed fields) so CenterCanvas can access scale data for distance labels
  - `activeSheet` already has `image_url`, `width`, `height`, `scale_value`, `scale_unit`, `scale_calibrated`

- [x] **CM-006**: Implement cursor management for canvas modes
  - **File:** `frontend/src/components/workspace/CenterCanvas.tsx`
  - Set `cursor` style on canvas container `div` based on state:
    - `activeTool === 'select'` and not panning: `default`
    - `activeTool === 'select'` and panning: `grabbing`
    - Any drawing tool active: `crosshair`
    - Hovering a measurement in select mode: `pointer`
  - Read `activeTool` from `useWorkspaceStore`
  - Pattern reference: `frontend/src/pages/TakeoffViewer.tsx` lines 1010-1016

---

## 2. Viewport Controls (Pan, Zoom, Fit)

- [x] **CM-007**: Create workspace-aware canvas controls hook
  - **File (new):** `frontend/src/hooks/useWorkspaceCanvasControls.ts`
  - Replaces old `useCanvasControls.ts` (which uses local `useState`) with one that reads/writes viewport from `workspaceStore`
  - Read `viewport` (`zoom`, `panX`, `panY`) from `useWorkspaceStore`
  - Write via `setViewport()` and `setZoom()` actions
  - Port `handleFitToScreen`: needs image dimensions + stage size; computes `Math.min(scaleX, scaleY) * 0.95`
  - Port `handleActualSize`: sets zoom=1, pan=(0,0)
  - Port `handleZoomIn` / `handleZoomOut`: multiply/divide by 1.2, clamped to `MIN_ZOOM`..`MAX_ZOOM` from constants
  - Remove debug `fetch()` calls present in old hook

- [x] **CM-008**: Implement scroll-wheel zoom with pointer-anchoring
  - **File:** `frontend/src/hooks/useWorkspaceCanvasControls.ts`
  - Port `handleWheel` from existing `useCanvasControls.ts` lines 109-126
  - Scale factor: `1.1` per wheel event
  - Anchor zoom around pointer position so point under cursor stays fixed:
    ```ts
    const imageX = (pointerPos.x - panX) / oldZoom;
    const imageY = (pointerPos.y - panY) / oldZoom;
    const newPanX = pointerPos.x - imageX * newZoom;
    const newPanY = pointerPos.y - imageY * newZoom;
    ```
  - Wire to `<Stage onWheel={...}>` via Konva event adapter

- [x] **CM-009**: Implement mouse-drag panning
  - **File (new):** `frontend/src/hooks/useWorkspaceCanvasEvents.ts`
  - Port panning logic from existing `useCanvasEvents.ts`
  - Pan triggers: right-click drag, middle-click drag, or left-click drag when `activeTool === 'select'` and clicking empty stage
  - Track `isPanning`, `panStart`, `panStartPos` in local state (transient, not store)
  - On mouse move while panning: compute delta and update `setViewport({ panX, panY })`
  - Global `window.addEventListener('mouseup')` to prevent stuck panning state

- [x] **CM-010**: Wire TopToolbar zoom buttons to workspace canvas controls
  - **File:** `frontend/src/components/workspace/TopToolbar.tsx`
  - Currently zoom buttons call `setZoom(viewport.zoom + 0.1)` — replace with proper `handleZoomIn()` / `handleZoomOut()` from new hook
  - Add `zoomIn()`, `zoomOut()` actions to `workspaceStore` that apply the 1.2x multiplier with clamping
  - Add `fitToScreen` action (requires image dimensions — store in workspace store or use a ref)

- [x] **CM-011**: Implement fit-to-page on first sheet load
  - **File:** `frontend/src/components/workspace/CenterCanvas.tsx`
  - When `image` loads and stage size is known, auto-compute fit-to-page zoom
  - Only trigger on initial load — use a `hasInitialFit` ref per sheet
  - Reset `hasInitialFit` when `activeSheetId` changes
  - Formula: `zoom = Math.min(stageWidth / imageWidth, stageHeight / imageHeight) * 0.95`
  - Center the image: `panX = (stageWidth - imageWidth * zoom) / 2`, `panY = ...`

- [x] **CM-012**: Apply viewport transform to Konva Stage
  - **File:** `frontend/src/components/workspace/CenterCanvas.tsx`
  - Set Stage props: `scaleX={viewport.zoom}`, `scaleY={viewport.zoom}`, `x={viewport.panX}`, `y={viewport.panY}`
  - Set `draggable={false}` (panning is manual, not Konva's built-in drag)
  - Set `pixelRatio={1}` for consistent rendering

---

## 3. Drawing Tool Integration

- [x] **CM-013**: Create workspace-aware drawing state hook
  - **File (new):** `frontend/src/hooks/useWorkspaceDrawingState.ts`
  - Bridge between `workspaceStore` (which has `activeTool`, `isDrawing`, `currentPoints`) and drawing preview logic from `useDrawingState.ts`
  - Read `activeTool`, `isDrawing`, `currentPoints` from store
  - Write via `setIsDrawing()`, `setCurrentPoints()`, `addCurrentPoint()`
  - Port `previewShape` generation logic (lines 65-119 of `useDrawingState.ts`) as derived state
  - Port `startDrawing()`, `addPoint()`, `updatePreview()`, `finishDrawing()`, `cancelDrawing()`
  - Port per-point undo/redo during drawing

- [x] **CM-014**: Implement click-click drawing event handler for line, polyline, polygon
  - **File:** `frontend/src/hooks/useWorkspaceCanvasEvents.ts`
  - On left-click with drawing tool active (not `select`):
    - Convert screen coords to image coords via `stage.getRelativePointerPosition()`
    - **Point tool:** Immediate creation — call `onMeasurementCreate` directly
    - **Line tool:** First click starts drawing, second click finishes and auto-creates
    - **Polyline/Polygon:** First click starts, subsequent clicks add points, double-click finishes
    - **Polygon close detection:** When within `SNAP_THRESHOLD_PX` of first point, show "Click to close" hint and snap
  - On mouse-move with drawing active: call `updatePreview(mousePos)` to update live preview
  - Enforce condition requirement: check `activeConditionId` is set before starting (except `measure` tool); show toast via `toolRejectionMessage` if not

- [x] **CM-015**: Implement click-drag-release drawing for rectangle and circle
  - **File:** `frontend/src/hooks/useWorkspaceCanvasEvents.ts`
  - **Rectangle:** mouse-down starts, mouse-move updates preview, mouse-up finishes
  - **Circle:** mouse-down sets center, mouse-move computes radius from distance, mouse-up finishes
  - Minimum size check: reject shapes smaller than 5px (pattern from `useCanvasEvents.ts` lines 243-254)

- [x] **CM-016**: Implement double-click finish for polyline and polygon
  - **File:** `frontend/src/hooks/useWorkspaceCanvasEvents.ts`
  - Port `handleStageDoubleClick` from existing `useCanvasEvents.ts` lines 279-318
  - Polyline: finish if at least 2 points; add final point if not near last point
  - Polygon: finish if at least 3 points; snap to start if close, otherwise add final point
  - Prevent double-click from also triggering single-click point add (filter `e.evt.detail > 1`)

- [x] **CM-017**: Create measurement on drawing completion
  - **File:** `frontend/src/components/workspace/CenterCanvas.tsx` (callback)
  - Convert result to API geometry format using `createMeasurementGeometry()` from `frontend/src/utils/measurementUtils.ts`
  - Call `createMeasurementAsync()` from `useMeasurements` hook with:
    - `conditionId`: from `workspaceStore.activeConditionId`
    - `pageId`: from active sheet ID
    - `geometryType` and `geometryData`: from `createMeasurementGeometry()` output
  - On success: reset drawing state, invalidate measurements query
  - On error: show error toast, do NOT lose drawing data

- [x] **CM-018**: Render DrawingPreviewLayer for in-progress shapes
  - **File:** `frontend/src/components/workspace/CenterCanvas.tsx`
  - **Reuse** existing `DrawingPreviewLayer` component from `frontend/src/components/viewer/DrawingPreviewLayer.tsx` as-is
  - Pass: `previewShape`, `points`, `isDrawing`, `color` (from active condition), `scale`, `isCloseToStart`, `pixelsPerUnit`, `unitLabel`
  - Place as the topmost layer in the Stage

- [x] **CM-019**: Wire keyboard shortcuts for tool selection via FocusContext
  - **File:** `frontend/src/components/workspace/CenterCanvas.tsx` or dedicated hook
  - Use `useFocusContext().shouldFireShortcut(e)` to gate single-key shortcuts
  - Map keys to `setActiveTool()`: V→select, L→line, P→polyline, A→polygon, R→rectangle, C→circle, M→measure
  - `Escape` → `escapeAll()` (verify it cancels in-progress drawing)
  - `Delete`/`Backspace` → delete selected measurement(s)
  - Register on `window.addEventListener('keydown')` with cleanup

- [x] **CM-020**: Display DrawingInstructions overlay for active tool
  - **File:** `frontend/src/components/workspace/CenterCanvas.tsx`
  - **Reuse or adapt** `DrawingInstructions` from `frontend/src/components/viewer/DrawingInstructions.tsx`
  - Show contextual instructions when drawing tool is active and condition is selected
  - Pass `tool`, `conditionName`, `isDrawing`, `isCloseToStart`

---

## 4. Measurement Overlay Rendering

- [x] **CM-021**: Fetch page measurements via React Query
  - **File:** `frontend/src/components/workspace/CenterCanvas.tsx`
  - Use `useQuery` with key `['measurements', activeSheetId]` and fetcher `listPageMeasurements(activeSheetId)`
  - API function exists at `frontend/src/api/measurements.ts` — `GET /pages/{page_id}/measurements`
  - Only enable when `activeSheetId` is set
  - Returns `{ measurements: Measurement[], total: number }`

- [x] **CM-022**: Fetch project conditions for color-coding
  - **File:** `frontend/src/components/workspace/CenterCanvas.tsx`
  - Use `useConditions(projectId)` hook from `frontend/src/hooks/useConditions.ts`
  - Build a `Map<string, Condition>` for fast lookup by ID
  - Filter measurements by condition `is_visible` flag — skip rendering measurements whose condition has `is_visible === false`

- [x] **CM-023**: Render MeasurementLayer with all measurements for active sheet
  - **File:** `frontend/src/components/workspace/CenterCanvas.tsx`
  - **Reuse** existing `MeasurementLayer` from `frontend/src/components/viewer/MeasurementLayer.tsx`
  - Pass: `measurements` (filtered list), `conditions` (Map), `selectedMeasurementId`, `onMeasurementSelect`, `onMeasurementUpdate`, `onMeasurementContextMenu`, `isEditing`, `scale`
  - Wire `selectedMeasurementId` to `workspaceStore.selectedMeasurementIds[0]` (single selection initially)
  - Wire `onMeasurementSelect` to `setSelectedMeasurements([id])` and `setActiveCondition(measurement.condition_id)`

- [x] **CM-024**: Verify quantity labels display on measurements
  - Already handled by `MeasurementShape.tsx` — renders `${measurement.quantity.toFixed(1)} ${measurement.unit}` as Konva `Text`
  - **File:** `frontend/src/components/viewer/MeasurementShape.tsx`
  - Verify labels are readable at different zoom levels (fontSize is `12/scale` or `14/scale`)
  - No code changes expected — verify in integration

- [x] **CM-025**: Color-code measurements by condition and enforce visibility
  - Already handled by `MeasurementShape.tsx` which uses `condition.color` for stroke and fill
  - **File:** `frontend/src/components/workspace/CenterCanvas.tsx`
  - When rendering, filter by `condition.is_visible`:
    ```ts
    const visibleMeasurements = measurements.filter(m => {
      const condition = conditionsMap.get(m.condition_id);
      return condition?.is_visible !== false;
    });
    ```
  - `ConditionPanel` already has visibility toggles that set `is_visible`

---

## 5. Measurement Interaction (Select, Edit, Move, Delete)

- [x] **CM-026**: Implement measurement selection on click
  - **File:** `frontend/src/components/workspace/CenterCanvas.tsx`
  - When `activeTool === 'select'` and user clicks a measurement shape, `MeasurementShape` fires `onSelect`
  - Wire to: `setSelectedMeasurements([measurement.id])`, `setActiveCondition(measurement.condition_id)`
  - Clicking empty stage (target === stage): `clearSelection()`
  - Selection updates RightPanel to show the selected condition's properties

- [x] **CM-027**: Implement measurement drag-to-move
  - Already handled by `MeasurementShape.tsx` `commonGroupProps.draggable` (enabled when `isSelected && isEditing`)
  - `isEditing` should be `true` when `activeTool === 'select'` and measurement is selected
  - On drag end: calls `onUpdate(newGeometry, previousGeometry)` which triggers `PUT /measurements/{id}`
  - **File:** `frontend/src/components/workspace/CenterCanvas.tsx`
  - Wire `onMeasurementUpdate` callback to call `updateMeasurementAsync()` and push to undo stack

- [x] **CM-028**: Implement vertex editing for polyline and polygon
  - Already handled by `MeasurementShape.tsx` vertex handles (lines 276-319)
  - When `isSelected && isEditing` and geometry is polyline/polygon, draggable vertex circles appear
  - Each vertex drag fires `onUpdate` with modified geometry
  - Verify works correctly with workspace store state

- [x] **CM-029**: Implement shape transformer for rectangle and circle resize
  - Already handled by `ShapeTransformer.tsx` from `frontend/src/components/viewer/ShapeTransformer.tsx`
  - `MeasurementShape.tsx` renders `<ShapeTransformer>` for rectangle/circle when `isSelected && isEditing`
  - On transform end: computes new geometry from Konva node's scale/position and fires `onUpdate`
  - Verify integration

- [x] **CM-030**: Implement right-click context menu on measurements
  - **File (new):** `frontend/src/components/workspace/MeasurementContextMenu.tsx`
  - **Reuse or adapt** `ShapeContextMenu` from `frontend/src/components/viewer/ShapeContextMenu.tsx`
  - Options: Edit, Duplicate, Delete, Bring to Front, Send to Back
  - Wire `onContextMenu` from `MeasurementShape` → open menu at click position
  - Render as absolutely positioned HTML div (not Konva)
  - Close on click-away or Escape

---

## 6. Undo/Redo System with Server Sync

- [x] **CM-031**: Create workspace undo/redo manager
  - **File (new):** `frontend/src/hooks/useWorkspaceUndoRedo.ts`
  - **Adapt** existing `useUndoRedo.ts` from `frontend/src/hooks/useUndoRedo.ts`
  - Existing hook already supports async `undo()` / `redo()` functions
  - Add `UNDO_STACK_DEPTH` limit (100) from constants
  - When pushing new action, trim history to stack depth
  - Expose `canUndo`, `canRedo`, `push`, `undo`, `redo`, `clear`

- [x] **CM-032**: Push create-measurement actions to undo stack
  - **File:** `frontend/src/components/workspace/CenterCanvas.tsx`
  - After successful `createMeasurementAsync()`, push to undo stack:
    - `undo`: call `deleteMeasurementAsync(createdId)`, clear selection
    - `redo`: call `createMeasurementAsync(sameParams)`, update selection to new ID
  - Pattern reference: `TakeoffViewer.tsx` `handleMeasurementCreate` lines 150-218

- [x] **CM-033**: Push delete-measurement actions to undo stack
  - **File:** `frontend/src/components/workspace/CenterCanvas.tsx`
  - Before deleting, capture measurement's full data (`condition_id`, `geometry_type`, `geometry_data`)
  - After successful `deleteMeasurementAsync()`, push:
    - `undo`: `createMeasurementAsync(captured data)`, restore selection
    - `redo`: `deleteMeasurementAsync(recreatedId)`
  - Pattern reference: `TakeoffViewer.tsx` `handleDeleteMeasurement` lines 315-373

- [x] **CM-034**: Push update-measurement (move/edit) actions to undo stack
  - **File:** `frontend/src/components/workspace/CenterCanvas.tsx`
  - `onMeasurementUpdate(id, newGeometry, previousGeometry)` handler
  - After successful `updateMeasurementAsync()`, push:
    - `undo`: `updateMeasurementAsync(id, previousGeometry)`
    - `redo`: `updateMeasurementAsync(id, newGeometry)`

- [x] **CM-035**: Wire undo/redo to TopToolbar buttons and keyboard shortcuts
  - **File:** `frontend/src/components/workspace/TopToolbar.tsx`
  - Currently undo/redo buttons are `disabled` — remove `disabled` and wire `onClick`
  - Pass `canUndo`, `canRedo` as props (or read from shared hook/store)
  - Keyboard: `Ctrl+Z` → undo, `Ctrl+Shift+Z` → redo
  - During active drawing: `Ctrl+Z` removes last point (per-point undo), not stack undo
  - Use `useFocusContext().shouldFireShortcut(e)` to gate

---

## 7. Viewport Persistence (Per-Sheet State)

- [x] **CM-036**: Add per-sheet viewport map to workspaceStore
  - **File:** `frontend/src/stores/workspaceStore.ts`
  - Add new state field: `sheetViewports: Record<string, ViewportState>`
  - Default: `{}`

- [x] **CM-037**: Save viewport state when leaving a sheet
  - **File:** `frontend/src/stores/workspaceStore.ts`
  - Modify `setActiveSheet` to save current viewport before switching:
    ```ts
    setActiveSheet: (sheetId) => {
      const { activeSheetId, viewport, sheetViewports } = get();
      if (activeSheetId) {
        set({ sheetViewports: { ...sheetViewports, [activeSheetId]: viewport } });
      }
      set({ activeSheetId: sheetId });
    }
    ```

- [x] **CM-038**: Restore viewport state when switching to a sheet
  - **File:** `frontend/src/components/workspace/CenterCanvas.tsx`
  - On `activeSheetId` change, check `sheetViewports[activeSheetId]`
  - If saved viewport exists: restore via `setViewport(savedViewport)`
  - If no saved viewport (first visit): trigger fit-to-page (CM-011)

- [x] **CM-039**: Clear undo stack on sheet switch
  - **File:** `frontend/src/components/workspace/CenterCanvas.tsx`
  - When `activeSheetId` changes, call `undoRedo.clear()`
  - Undo history is per-sheet and lost on switch (intentional — server is source of truth)
  - Also reset drawing state: `resetDrawingState()`

---

## 8. Testing & Verification

- [x] **CM-040**: Create CenterCanvas.test.tsx — Stage rendering and image loading
  - **File (new):** `frontend/src/components/workspace/__tests__/CenterCanvas.test.tsx`
  - Test: renders "No sheet selected" when `activeSheetId` is null
  - Test: renders loading state when `isLoadingSheet` is true
  - Test: renders "Sheet image not available" when no `sheetImageUrl`
  - Test: Stage component renders when sheet is active
  - Test: `data-focus-region="canvas"` is present
  - Mock `react-konva` Stage/Layer components

- [x] **CM-041**: Create useWorkspaceCanvasControls.test.ts — zoom/pan behavior
  - **File (new):** `frontend/src/hooks/__tests__/useWorkspaceCanvasControls.test.ts`
  - Test: `handleZoomIn` multiplies zoom by 1.2
  - Test: `handleZoomOut` divides zoom by 1.2
  - Test: zoom respects `MIN_ZOOM` and `MAX_ZOOM` bounds
  - Test: `handleWheel` anchors zoom around pointer position
  - Test: `handleFitToScreen` computes correct zoom for given image and stage dimensions

- [x] **CM-042**: Create useWorkspaceDrawingState.test.ts — drawing tool completion
  - **File (new):** `frontend/src/hooks/__tests__/useWorkspaceDrawingState.test.ts`
  - Test: `startDrawing` sets `isDrawing=true` and records first point
  - Test: `addPoint` appends to `currentPoints`
  - Test: `finishDrawing` returns tool, points, and previewShape; resets state
  - Test: `cancelDrawing` resets all state without creating measurement
  - Test: per-point undo/redo works correctly
  - Test: line tool auto-finishes after 2 points

- [x] **CM-043**: Create MeasurementOverlay.test.tsx — renders correct shapes from data
  - **File (new):** `frontend/src/components/workspace/__tests__/MeasurementOverlay.test.tsx`
  - Test: renders shapes for each geometry type (line, polygon, rectangle, circle, point)
  - Test: applies condition color to shapes
  - Test: filters out measurements for conditions with `is_visible: false`

- [x] **CM-044**: Create useWorkspaceUndoRedo.test.ts — undo/redo stack behavior
  - **File (new):** `frontend/src/hooks/__tests__/useWorkspaceUndoRedo.test.ts`
  - Test: `push` adds action, `canUndo` becomes true
  - Test: `undo` calls action's undo function, `canRedo` becomes true
  - Test: `redo` calls action's redo function
  - Test: pushing after undo discards redo history
  - Test: stack respects `UNDO_STACK_DEPTH` limit (100)
  - Test: `clear` empties the stack

- [x] **CM-045**: End-to-end verification gate
  - Run full verification suite:
    ```bash
    cd frontend && npx tsc --noEmit && npm run lint && npm test -- --run
    ```
  - Manual smoke test checklist:
    - [x]Sheet image loads on Konva canvas
    - [x]Pan with right-click drag works
    - [x]Scroll-wheel zoom with pointer anchoring works
    - [x]Fit-to-page on first sheet load
    - [x]Draw a line measurement (2 clicks)
    - [x]Draw a polygon measurement (multi-click + double-click)
    - [x]Draw a rectangle (click-drag-release)
    - [x]Existing measurements render with correct colors
    - [x]Click measurement to select, see properties in RightPanel
    - [x]Drag selected measurement to move
    - [x]Undo (Ctrl+Z) after creating a measurement
    - [x]Redo (Ctrl+Shift+Z) restores the measurement
    - [x]Switch sheets and back; viewport is restored

---

## Dependency Graph

```
CM-001 (Stage shell)
  ├── CM-002 (ResizeObserver hook)
  ├── CM-003 (Image loading) ──→ CM-011 (Fit-to-page on load)
  ├── CM-004 (Multi-layer architecture)
  ├── CM-005 (Wire props through TakeoffWorkspace)
  └── CM-006 (Cursor management)
         ↓
CM-007 (Canvas controls hook) ──→ CM-008 (Wheel zoom)
         │                    ──→ CM-009 (Drag panning)
         │                    ──→ CM-010 (Toolbar zoom wiring)
         ↓
CM-012 (Stage transform) ─────→ requires CM-007
         ↓
CM-013 (Drawing state hook)
  ├── CM-014 (Click-click drawing)
  ├── CM-015 (Click-drag drawing)
  ├── CM-016 (Double-click finish)
  ├── CM-017 (Create on completion) ──→ requires CM-021 (fetch measurements)
  ├── CM-018 (Preview layer)
  ├── CM-019 (Keyboard shortcuts)
  └── CM-020 (Drawing instructions)
         ↓
CM-021 (Fetch measurements) ──→ CM-022 (Fetch conditions)
         │                  ──→ CM-023 (MeasurementLayer)
         │                  ──→ CM-024 (Labels - verify)
         │                  ──→ CM-025 (Color/visibility)
         ↓
CM-026 (Selection) ──→ CM-027 (Drag move) ──→ CM-028 (Vertex edit)
                   ──→ CM-029 (Shape transformer)
                   ──→ CM-030 (Context menu)
         ↓
CM-031 (Undo manager)
  ├── CM-032 (Create undo)
  ├── CM-033 (Delete undo)
  ├── CM-034 (Update undo)
  └── CM-035 (Wire to UI)
         ↓
CM-036 (Viewport map) ──→ CM-037 (Save on leave) ──→ CM-038 (Restore)
                       ──→ CM-039 (Clear undo on switch)
         ↓
CM-040..CM-045 (Tests)
```

---

## Implementation Order (Suggested Days)

### Day 1: Foundation — Stage, Image, Viewport (CM-001 through CM-012)
- Set up Konva Stage in CenterCanvas
- Image loading and rendering
- Pan, zoom, fit-to-page
- Wire toolbar zoom buttons
- **Goal:** User can see sheet image on Konva canvas, pan/zoom with mouse

### Day 2: Drawing Tools (CM-013 through CM-020)
- Drawing state management hook
- All 7 tool event handlers (select, line, polyline, polygon, rectangle, circle, point)
- Drawing preview layer
- Measurement creation on drawing completion
- Keyboard shortcuts
- **Goal:** User can draw measurements with all tools; measurements saved to backend

### Day 3: Measurement Overlay & Interaction (CM-021 through CM-030)
- Fetch and render existing measurements
- Color-coding by condition
- Select, move, edit vertices, resize, delete
- Context menu
- **Goal:** All existing measurements visible and interactive on canvas

### Day 4: Undo/Redo, Persistence, Testing (CM-031 through CM-045)
- Undo/redo stack with server sync
- Viewport persistence per sheet
- Write all test files
- Run verification gate
- **Goal:** Robust undo/redo, viewport memory, all tests passing

---

## Definition of Done

Each task is considered complete when:

1. **Code compiles** with no TypeScript errors (`npx tsc --noEmit`)
2. **Lint passes** with no warnings (`npm run lint`)
3. **Unit tests pass** for the affected module
4. **Existing tests still pass** (no regressions)
5. **No debug fetch() calls** introduced (remove `#region agent log` patterns found in old viewer code)
6. **State architecture rules** followed: Zustand for UI state, React Query for server data
7. **FocusContext** routing respected for keyboard shortcuts

---

## Phase 1 Acceptance Criteria

Phase 1 is complete when a user can:

1. Open a project workspace and see the active sheet rendered on a Konva canvas (not an `<img>` tag)
2. Pan the canvas with right-click drag or middle-click drag
3. Zoom with scroll wheel (anchored to pointer position) and toolbar buttons
4. See the canvas auto-fit to the sheet on first load
5. Select any drawing tool (V/L/P/A/R/C/M) from toolbar or keyboard shortcut
6. Draw a measurement of any type (line, polyline, polygon, rectangle, circle, point)
7. See the measurement saved to backend and appear as a colored overlay
8. See all existing measurements for the active sheet with correct condition colors
9. Click a measurement to select it; see it highlighted and condition focused in RightPanel
10. Drag a selected measurement to move it; edit vertices; resize rectangle/circle
11. Delete a selected measurement with Delete/Backspace key
12. Undo the last action with Ctrl+Z (measurement removed from server)
13. Redo with Ctrl+Shift+Z (measurement recreated on server)
14. Switch to another sheet and back; viewport position/zoom is restored
15. All automated tests pass: `cd frontend && npm run type-check && npm run lint && npm test -- --run`

---

## Technical Notes

### Canvas Coordinate System
- Konva Stage applies `scaleX/scaleY` and `x/y` transforms for zoom/pan
- `stage.getRelativePointerPosition()` returns coords in image space (accounting for zoom/pan)
- All geometry data stored in **pixel coordinates** (image space) — backend handles real-world unit conversion via page scale value
- Drawing tools must convert screen coords to image coords before recording points

### Performance Considerations
- Construction plan images can be very large (10,800 x 14,400 px at 300 DPI for E-size)
- `pixelRatio={1}` on Stage prevents doubling canvas resolution on HiDPI displays
- `listening={false}` on non-interactive layers (image, preview) improves hit-testing
- Consider `perfectDrawEnabled={false}` on Line shapes with many points

### Reuse Strategy
- **Direct reuse (no changes):** `DrawingPreviewLayer.tsx`, `MeasurementLayer.tsx`, `MeasurementShape.tsx`, `ShapeTransformer.tsx`, `measurementUtils.ts`, `usePageImage.ts`
- **Adapt (refactor for workspace store):** `useCanvasControls.ts` → `useWorkspaceCanvasControls.ts`, `useDrawingState.ts` → `useWorkspaceDrawingState.ts`, `useCanvasEvents.ts` → `useWorkspaceCanvasEvents.ts`
- **Extend:** `workspaceStore.ts` (add sheetViewports map), `TopToolbar.tsx` (wire undo/redo/zoom)
- **Keep as-is:** `FocusContext.tsx`, `constants.ts`

### Debug Logging Cleanup
- Several existing files contain `#region agent log` blocks that POST debug data to `http://127.0.0.1:7244`. Remove from any files modified during this phase. Affected: `useCanvasControls.ts`, `usePageImage.ts`, `MeasurementShape.tsx`, `TakeoffViewer.tsx`.

### Backend API Quick Reference

| Action | Method | Endpoint | Notes |
|--------|--------|----------|-------|
| List measurements for page | GET | `/pages/{page_id}/measurements` | Returns `{ measurements, total }` |
| Create measurement | POST | `/conditions/{condition_id}/measurements` | Body: `{ page_id, geometry_type, geometry_data }` |
| Update measurement | PUT | `/measurements/{measurement_id}` | Body: `{ geometry_data }` |
| Delete measurement | DELETE | `/measurements/{measurement_id}` | Returns 204 |
| Recalculate measurement | POST | `/measurements/{measurement_id}/recalculate` | After scale change |

### Geometry Data Structures

| Type | Structure |
|------|-----------|
| Line | `{ start: {x,y}, end: {x,y} }` |
| Polyline | `{ points: [{x,y}, ...] }` |
| Polygon | `{ points: [{x,y}, ...] }` |
| Rectangle | `{ x, y, width, height, rotation? }` |
| Circle | `{ center: {x,y}, radius }` |
| Point | `{ x, y }` |

### Critical Files

| File | Action |
|------|--------|
| `frontend/src/components/workspace/CenterCanvas.tsx` | **Transform**: replace img shell with full Konva Stage + layers + events |
| `frontend/src/stores/workspaceStore.ts` | **Extend**: add sheetViewports map and viewport persistence actions |
| `frontend/src/components/workspace/TopToolbar.tsx` | **Wire**: undo/redo buttons, zoom buttons |
| `frontend/src/components/workspace/TakeoffWorkspace.tsx` | **Wire**: pass pageId and sheet data to CenterCanvas |
| `frontend/src/pages/TakeoffViewer.tsx` | **Reference**: contains the complete working pattern to port from |
| `frontend/src/hooks/useCanvasEvents.ts` | **Adapt**: existing event routing into workspace-aware version |
| `frontend/src/components/viewer/MeasurementShape.tsx` | **Reuse**: renders shapes with selection, editing, dragging |
| `frontend/src/components/viewer/DrawingPreviewLayer.tsx` | **Reuse**: real-time drawing preview |
| `frontend/src/components/viewer/MeasurementLayer.tsx` | **Reuse**: renders all measurements for a page |
| `frontend/src/utils/measurementUtils.ts` | **Reuse**: geometry creation and offset utilities |
| `frontend/src/api/measurements.ts` | **Reuse**: measurement API client functions |

---

## Completion Status

**All 45 tasks completed.** Phase 1 Canvas Migration is fully implemented.

- Canvas migration: February 2026
- 10-feature migration (scale calibration, scale detection, scale warning, measurement duplication, visibility toggle, z-ordering, undo/redo wiring, title block mode, scale location display, measurements panel): February 12, 2026
