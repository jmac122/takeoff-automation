# ForgeX UI/UX Overhaul Implementation Plan — Audit Report

> **Auditor:** Claude (Software Architect Review)
> **Date:** February 5, 2026
> **Source Plan:** `FORGEX_UI_OVERHAUL_IMPLEMENTATION_PLAN.md` v1.0
> **Spec Reference:** `forgex-ui-overhaul-spec.docx` v1.0

---

## Audit Summary

The implementation plan is a solid task breakdown that captures the **what** of each phase, but it has critical gaps in the **how** — specifically in the systems-level concerns that determine whether the code will hold together as AI-generated components are assembled. The plan will let you start coding, but you'll hit walls around **state management**, **data persistence flow**, **undo/redo ↔ backend sync**, and **focus/context management** — all areas where ambiguity causes expensive rework.

I identified **7 Critical gaps** (will block you), **9 Structural gaps** (will cause rework), and **12 Missing spec items** (features in the spec with no implementation task). Every finding is categorized, explained, and resolved below.

---

## PART 1: CRITICAL GAPS (Will Block Implementation)

These are architectural decisions that must be made before any code is written. If you start Phase A without resolving these, you'll be refactoring by Phase B.

---

### CRITICAL-1: No Global State Architecture Defined

**The Problem:** Task A.4 shows a `WorkspaceState` interface with 3 fields (`activeSheetId`, `activeConditionId`, `activeTool`). That's it. But the workspace has **at least 15 pieces of cross-cutting state** that multiple components need simultaneously. The plan says "Use React context or Zustand" — this is not a decision, it's a hedge. And the state shape isn't specified, which means every AI coding session will invent its own, and they won't compose.

**Why This Matters:** The canvas reads active condition color. The toolbar reads active tool. The status bar reads scale + cursor position + active tool + selection. The conditions panel reads active condition + measurements. The undo stack references measurement IDs. Without a single source of truth defined up front, components will drift.

**Resolution — Add as Task A.0 (Day 0, before anything else):**

```typescript
// FILE: frontend/src/stores/workspaceStore.ts
// DECISION: Zustand (not React Context). Reason: multiple independent
// slices, selectors for render optimization, no provider nesting.

import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';

// ─── CORE WORKSPACE STATE ───────────────────────────────────
interface WorkspaceStore {
  // ── Sheet Navigation ──
  projectId: string | null;
  activeSheetId: string | null;
  selectedSheetIds: Set<string>;    // multi-select for batch ops
  expandedGroups: Set<string>;      // tree collapse state

  // ── Conditions ──
  activeConditionId: string | null;
  conditionVisibility: Map<string, boolean>;  // id → visible

  // ── Drawing Tools ──
  activeTool: DrawingTool | null;   // 'line'|'polyline'|'polygon'|'rect'|'count'|null
  isDrawing: boolean;               // true while placing points
  currentPoints: Point[];           // in-progress drawing points

  // ── Selection (canvas measurements) ──
  selectedMeasurementIds: Set<string>;
  editingMeasurementId: string | null;  // vertex edit mode

  // ── Canvas Viewport ──
  zoom: number;
  panOffset: { x: number; y: number };
  cursorPosition: { x: number; y: number } | null;  // real-world coords

  // ── AI Assist ──
  autoTabEnabled: boolean;
  pendingPrediction: PredictedPoint | null;

  // ── UI State ──
  leftPanelCollapsed: boolean;
  rightPanelCollapsed: boolean;
  leftPanelWidth: number;
  rightPanelWidth: number;

  // ── Actions (non-exhaustive, expand per slice) ──
  setActiveSheet: (id: string) => void;
  setActiveCondition: (id: string | null) => void;
  setActiveTool: (tool: DrawingTool | null) => void;
  // ... (each slice gets its own actions)
}

// INVARIANT: activeConditionId must be set before activeTool can be
// anything other than null or 'count'. Drawing without a condition
// is an error state — the UI must prevent it.

// INVARIANT: isDrawing === true implies activeTool !== null.
// Escape always sets isDrawing = false AND activeTool = null.

// INVARIANT: selectedMeasurementIds is cleared when activeTool is set.
// You are either selecting or drawing, never both.
```

**Boundary Rule:** Server data (sheets, conditions, measurements) lives in **React Query cache**, not in Zustand. Zustand holds only **UI state** (what's selected, what's active, viewport position). This prevents duplication and stale data.

---

### CRITICAL-2: No Measurement Persistence Strategy (Auto-Save)

**The Problem:** The spec says `Ctrl+S` "auto-saves, but feels right." The plan has no task defining WHEN measurements hit the backend. Currently the MeasurementEngine creates measurements via `POST /conditions/{id}/measurements` — but when does that call fire in the new drawing-first workflow?

**Why This Matters:** This directly affects undo/redo design (CRITICAL-3). If you save on every point click, undo must DELETE from the server. If you save only on drawing completion, you lose data on browser crash.

**Resolution — Define the persistence model explicitly:**

```
PERSISTENCE RULES:
1. Measurement is CREATED on the server when the drawing is FINISHED
   (Enter/double-click for polyline, second click for line, mouse-up
   for rectangle). Not on each point placement.

2. While drawing (isDrawing === true), points live in Zustand only
   (currentPoints). No server calls.

3. On drawing finish:
   a. POST /conditions/{conditionId}/measurements with geometry_data
   b. On success: add to React Query cache, clear currentPoints
   c. On failure: show toast error, keep geometry in currentPoints
      so user can retry (do NOT lose their work)

4. Edits (move, vertex drag) are PATCH requests on blur/mouse-up.
   Debounced 500ms to batch rapid drags.

5. Deletes are immediate DELETEs with optimistic update in React Query.

6. Ctrl+S triggers a no-op toast "All changes saved automatically"
   (there is no unsaved state except in-progress drawings).
```

**Add as a section in the plan called "Data Persistence Strategy" — referenced by C.1 (Undo), C.5 (Edit/Move), and B.3 (Active Condition).**

---

### CRITICAL-3: Undo/Redo ↔ Backend Sync Undefined

**The Problem:** Task C.1 defines a clean `UndoManager` with `execute()`/`undo()`/`redo()` commands. But it's client-only. Measurements are server-persisted. The plan never specifies what happens server-side when you undo/redo.

**Why This Matters:** If you undo a `DrawMeasurement`, does it `DELETE` from the server? If you redo, does it `POST` again (new ID)? What if the server fails on the redo-POST? What about undoing an edit — does it `PATCH` back to the old geometry?

**Resolution — Specify each command's server behavior:**

```typescript
// Each command must define both optimistic UI + server effect

interface Command {
  execute(): Promise<void>;   // NOT void — must handle async server calls
  undo(): Promise<void>;
  redo(): Promise<void>;      // separate from execute — may differ (e.g., reuse ID)
  description: string;
  affectedMeasurementIds: string[];  // for cache invalidation
}

// COMMAND: DrawMeasurement
// execute(): POST to server, get ID, add to React Query cache
// undo(): DELETE from server (soft-delete or hard-delete? DECIDE: hard-delete)
// redo(): POST again (gets new server ID — update local references)

// COMMAND: DeleteMeasurement
// execute(): DELETE from server, remove from cache, STORE the full measurement data
// undo(): POST measurement data back (re-create), gets new ID
// redo(): DELETE again

// COMMAND: MoveMeasurement / EditMeasurement
// execute(): PATCH new geometry, store previous geometry
// undo(): PATCH back to previous geometry
// redo(): PATCH to new geometry again

// COMMAND: ChangeCondition (reassign measurement)
// execute(): PATCH measurement.condition_id, update both condition totals
// undo(): PATCH back to original condition_id
// redo(): PATCH to new condition_id again

// ERROR HANDLING INVARIANT:
// If a server call fails during undo/redo, show error toast and
// REMOVE that command from the stack (don't leave the stack in an
// inconsistent state). Log the failure for debugging.
```

**The UndoManager must be async-aware.** Change the interface in Task C.1 accordingly. The plan's current synchronous `execute(): void` signature will not work.

---

### CRITICAL-4: No Focus Management / Keyboard Context System

**The Problem:** The plan has an extensive keyboard shortcut appendix with a "Context" column (`Canvas focused`, `Always`, `While drawing`, etc.). But there is zero implementation for how context is determined. When is the canvas "focused"? What happens if the user is typing in the sheet search box and presses "L"? Does it activate the Line tool or type the letter L?

**Why This Matters:** Without a focus management system, keyboard shortcuts will fight with text inputs, causing either shortcuts that don't work (frustrating) or shortcuts that fire when you're typing (destructive).

**Resolution — Define a FocusContext system:**

```typescript
// FILE: frontend/src/lib/FocusContext.ts

// RULE: Keyboard shortcuts only fire when their context is active.
// Context is determined by which region has focus.

type FocusRegion = 
  | 'canvas'        // center canvas area
  | 'sheet-tree'    // left sidebar tree
  | 'conditions'    // right panel
  | 'search'        // any text input
  | 'dialog'        // modal dialog open
  | 'global';       // fallback

// ROUTING RULES:
// 1. Single-key shortcuts (L, P, A, R, C, M, V, 1-9, Esc)
//    → ONLY fire when focusRegion is 'canvas' or 'global'
//    → NEVER fire when 'search' or 'dialog'
//
// 2. Ctrl+Key shortcuts (Ctrl+Z, Ctrl+S, Ctrl+N, etc.)
//    → Fire in ALL contexts EXCEPT 'dialog'
//    → Special case: Ctrl+Z in 'search' should undo text, not canvas
//
// 3. 'Always' shortcuts (Page Up/Down, Escape)
//    → Fire everywhere, Escape also closes dialogs/menus first

// IMPLEMENTATION: Use a FocusContext provider that tracks the active
// region via onFocus/onBlur on wrapper divs. The hotkey hook checks
// context before dispatching.

// Add as Task A.0.2 (part of workspace foundation, before shortcuts)
```

**This must be built in Phase A, not Phase C.** The plan currently adds shortcuts in C.2 without this foundation.

---

### CRITICAL-5: No "Drawing Without Condition" Behavior Defined

**The Problem:** The plan says clicking a condition makes it active, and drawing creates measurements under the active condition. But it never defines what happens when:
- No condition exists yet (empty project, first use)
- No condition is selected (user pressed Escape)
- User presses a tool key (L) with no active condition

**Why This Matters:** This is the #1 edge case new users will hit. If the tool silently does nothing, they'll think it's broken.

**Resolution — Define the invariant and the UI response:**

```
INVARIANT: A drawing tool CANNOT be activated without an active condition.
Exception: 'M' (standalone measurement tool) works without a condition.

BEHAVIOR WHEN USER ACTIVATES TOOL WITHOUT CONDITION:
1. Show toast: "Select a condition first" (with link/button to conditions panel)
2. Do NOT activate the tool
3. Highlight the conditions panel briefly (pulse animation)

BEHAVIOR ON FIRST USE (no conditions exist):
1. When workspace loads with 0 conditions, auto-open the Quick-Create bar
2. Show helper tooltip: "Create your first condition to start measuring"

BEHAVIOR WHEN ACTIVE CONDITION IS DELETED:
1. Set activeConditionId = null
2. Set activeTool = null
3. If isDrawing === true, cancel the current drawing (same as Escape)
```

**Add to Task B.3 (Active Condition State) and cross-reference in C.2 (Tool Shortcuts).**

---

### CRITICAL-6: No Canvas ↔ React State Synchronization Strategy

**The Problem:** Konva.js has its own internal object model (shapes, layers, groups). React has its own state (Zustand + React Query). The plan treats MeasurementLayer as a straightforward React component, but Konva shapes are mutable objects that can be manipulated directly (drag events update Konva's internal position, not React state). Without a defined sync strategy, the canvas and state will drift.

**Resolution — Define the data flow direction:**

```
DATA FLOW RULES:
1. React → Konva (ONE-WAY for rendering):
   - Measurements from React Query are rendered as Konva shapes
   - Shape positions/geometry come from measurement.geometry_data
   - Condition colors come from React Query condition cache

2. Konva → React (EVENTS ONLY):
   - User interactions (click, drag, draw) fire React callbacks
   - Callbacks update React state (Zustand + server)
   - React state change triggers re-render → Konva shapes update

3. NEVER read Konva's internal state as source of truth.
   After a drag, read the new position from the Konva event,
   then UPDATE React state, then let React re-render Konva.
   Do not trust shape.x() / shape.y() as the canonical position.

4. Exception: In-progress drawing points (currentPoints in Zustand)
   are rendered directly by a separate DrawingPreview layer that
   IS driven by Konva mouse events for performance (60fps tracking).
   These are ephemeral and not persisted until drawing completes.
```

**Add as a preamble to Phase C, referenced by C.1, C.3, C.4, C.5.**

---

### CRITICAL-7: No Migration/Transition Strategy

**The Problem:** The plan says "Replace DocumentPages with SheetTree" and "Remove PageBrowser." But it doesn't specify how the transition works. Do both UIs exist simultaneously? Is there a feature flag? What about existing projects with data — do they work in the new UI?

**Resolution:**

```
TRANSITION STRATEGY:
1. The new TakeoffWorkspace is a NEW route: /projects/:id
   The OLD routes (/documents/:id, /review/:id, etc.) continue to work
   during development. This is NOT a migration — it's a parallel build.

2. Feature flag: ENABLE_NEW_WORKSPACE (default false during dev)
   When true, /projects/:id routes to TakeoffWorkspace.
   When false, /projects/:id routes to existing UI.

3. Data compatibility: NO data migration needed. The new UI reads the
   same pages, conditions, and measurements tables. New fields
   (display_name, display_order, etc.) have sensible defaults.

4. Cutover: When all phases complete and QA passes, set flag to true.
   Old routes can be removed in a cleanup pass after.
```

**Add as Section 2.4 in the plan.**

---

## PART 2: STRUCTURAL GAPS (Will Cause Rework)

---

### STRUCT-1: No Error Handling Strategy

The plan mentions "Error state if image fails to load" in A.4, but has no systematic error handling approach. Every async operation (API calls, image loads, export jobs, AI predictions) needs error boundaries and recovery.

**Resolution — Add to Section 2:**

```
ERROR HANDLING PATTERNS:
- API failures: Toast notification + retry button. Never silent failures.
- Image load failures: Show placeholder with "Retry" link in canvas.
- Export failures: Toast with error detail + "Try Again" button.
- AI prediction failures: Silently degrade (no ghost point shown). Never block drawing.
- WebSocket/polling failures: Banner at top "Connection lost, reconnecting..."
- Canvas crashes: React Error Boundary around CenterCanvas that shows "Reload" option.

RULE: No error should ever lose user work. In-progress drawings survive
API failures. Completed measurements are in server + React Query cache.
```

---

### STRUCT-2: Missing `GET /projects/{id}/sheets` Backend Task

Section 8.2 lists `GET /projects/{id}/sheets` as a new endpoint ("Aggregated sheet tree data"), but there is no implementation task for it. Task A.10 only covers the page display fields. This endpoint is what the SheetTree actually needs.

**Resolution — Add Task A.2.5:**
```
Task A.2.5: Build GET /projects/{id}/sheets endpoint
- Returns all pages for a project with classification, scale, and
  display fields pre-joined
- Grouped by discipline (or group_name override)
- Sorted by display_order (or sheet_number fallback)
- Includes measurement counts per page (for progress indicators)
- Single query, no N+1
- Files: backend/app/api/routes/sheets.py
- Priority: P0 (SheetTree depends on this)
```

---

### STRUCT-3: Copy/Paste Has Shortcuts But No Task

`Ctrl+C` / `Ctrl+V` are in the keyboard shortcut appendix (Section 12.3) but there is no implementation task anywhere in the plan. Copy/paste is non-trivial — it needs to handle coordinate translation (pasting on a different sheet), condition assignment, and server creation of the new measurement.

**Resolution — Add Task C.6.5:**
```
Task C.6.5: Implement Copy/Paste for Measurements
- Ctrl+C: Store selected measurement geometry + condition in clipboard state
- Ctrl+V: Create new measurement at cursor position with copied geometry
  - If same sheet: offset by 20px to avoid overlap
  - If different sheet: center on viewport
  - Always creates under active condition (not original condition)
- Support multi-select copy (Ctrl+C with multiple selected)
- Priority: P1
- Effort: 1 day
- Depends on: C.5, C.6
```

---

### STRUCT-4: Missing Measurement Hover Tooltip Task

The spec explicitly says: "Hover tooltip: Show condition name, quantity, and measurement type on hover." No task exists for this.

**Resolution — Add to Task C.5 acceptance criteria:**
```
- [ ] Hover over measurement shows tooltip with:
      condition name, quantity + unit, measurement type
- [ ] Tooltip disappears on mouse leave
- [ ] Tooltip does not appear while drawing (isDrawing === true)
```

---

### STRUCT-5: Missing Z-Ordering for Measurement Layers

The spec says: "Z-ordering: Areas below lines below points. Selected measurement always on top." No task addresses this.

**Resolution — Add to Task C.5 technical details:**
```
Z-ORDER RULES (enforced in MeasurementLayer render order):
1. Area measurements (polygons, rectangles) — bottom
2. Linear measurements (lines, polylines) — middle
3. Count measurements (points) — top
4. Selected measurement(s) — always topmost, regardless of type
5. In-progress drawing — above everything
6. AI ghost/draft measurements — above plan image, below user measurements

Implementation: Sort measurements by type before rendering. Move
selected to end of render array. Use separate Konva Layer for
draft/ghost measurements.
```

---

### STRUCT-6: Missing Fill Patterns for Area Measurements

The spec says: "Use hatching patterns for different concrete types." No task.

**Resolution — Add Task C.10.5 (P2, can defer):**
```
Task C.10.5: Area Measurement Fill Patterns
- Semi-transparent fill with condition color (default: 0.2 opacity)
- Optional hatching overlay per condition type:
  - Slab: diagonal lines
  - Foundation: cross-hatch
  - Sidewalk: dots
- Configurable in condition properties (line style section)
- Priority: P2
- Effort: 0.5 days
```

---

### STRUCT-7: Missing Selected State Visual Specification

The spec defines selection appearance: "Blue handles at vertices, dashed boundary, slightly thicker stroke." The plan's Task C.5 says "show handles" but doesn't specify these visual constants.

**Resolution — Add to Task C.5 technical details:**
```
SELECTION VISUAL CONSTANTS:
- Handle size: 8px screen-space (inverse-scaled with zoom)
- Handle color: #3B82F6 (blue-500)
- Handle shape: square for corner vertices, circle for midpoints
- Selected stroke: 2x normal width, dashed (dashArray: [8, 4])
- Selected fill: original fill + 0.1 opacity boost
- Multi-select: same treatment, all selected measurements get handles
```

---

### STRUCT-8: Missing Drag-to-Reorder in Sheet Tree

Spec section 3.2.2 says: "Drag: Reorder within group or move between groups." The plan's SheetTree tasks (A.2, A.3) only cover click, keyboard, and right-click — no drag-and-drop.

**Resolution — Add Task A.2.5 (can be P2):**
```
Task A.2.5: Sheet Tree Drag-and-Drop Reorder
- Drag sheet within group to reorder (updates display_order)
- Drag sheet between groups to move (updates group_name)
- Uses existing @dnd-kit/core library
- Optimistic update + PUT /pages/{id}/display on drop
- Priority: P2
- Effort: 1 day
```

---

### STRUCT-9: Missing OCR Text Highlight on Canvas for Search Results

Spec says text search "Results show which sheets contain the text and highlight the regions on the canvas." Task A.7 only covers sheet filtering — no canvas overlay.

**Resolution — Add Task A.7.5 (P2):**
```
Task A.7.5: Text Search Canvas Highlights
- When text search returns results, highlight matching OCR regions on the active sheet
- Use a temporary overlay layer with semi-transparent yellow rectangles
- OCR text positions already stored from ingestion pipeline
- Highlights clear when search is cleared
- Priority: P2
- Effort: 1 day
- Depends on: A.7 (search) + A.4 (canvas load)
```

---

## PART 3: SPEC ITEMS WITH NO IMPLEMENTATION TASK

These are features explicitly described in the spec that have no corresponding task in the plan. For each, I've noted whether it needs a task or can be absorbed into an existing one.

| # | Spec Feature | Spec Section | Resolution |
|---|---|---|---|
| 1 | Zoom to selection (draw zoom rectangle) | 5.1.1 | Add to C.8 or new C.8.5 (P2) |
| 2 | Condition Groups filter/group-by dropdown | 4.3 | Add Task B.6.5 (P2, basic dropdown) |
| 3 | Recently used templates as chips | 4.1.1 | Absorb into B.2 — store in localStorage |
| 4 | Measurement "Copy to Another Sheet" | 5.3 | Absorb into C.7 context menu (needs cross-sheet POST logic) |
| 5 | Condition color swatch click-to-change | 4.1.2 | Absorb into B.1 (row component) |
| 6 | ClassificationBadges moved into tree nodes | 3.6 | Absorb into A.2 (SheetTreeNode) |
| 7 | Calibration triggered from status bar click | 5.6 | Absorb into C.8 (status bar) |
| 8 | Snap Level 2: Grid snap | 5.1.3 | Add Task C.4.5 (P2, future) |
| 9 | `measurement_history` table (spec 9.1) | 9.1 | Already exists from Phase 4B — verify compatibility |
| 10 | Condition `scope`/`category` fields for grouping | 4.3 | Already on model — wire into B.6.5 |
| 11 | Custom report templates (column selection, header/footer) | 7.2 | Explicitly mark as "Future" — not in scope |
| 12 | `ScaleCalibration` trigger from context menu | 3.6 | Absorb into A.9 "Set Scale" menu item |

---

## PART 4: PLAN IMPROVEMENTS (Systems Thinking)

### 4.1 Add Section 2.5: Component Communication Rules

```
WHO TALKS TO WHOM:
- SheetTree → WorkspaceStore (setActiveSheet)
- ConditionsPanel → WorkspaceStore (setActiveCondition)
- TopToolbar → WorkspaceStore (setActiveTool)
- CenterCanvas ← WorkspaceStore (reads everything via selectors)
- CenterCanvas → WorkspaceStore (selection, cursor position, drawing events)
- StatusBar ← WorkspaceStore (read-only, never writes)
- Any component → React Query (data fetching, mutations)

NO component directly talks to another component. Everything goes
through either WorkspaceStore (UI state) or React Query (server state).

EXCEPTION: The UndoManager is a singleton accessed by CenterCanvas
and TopToolbar (undo/redo buttons). It can also be accessed via
WorkspaceStore actions for convenience.
```

### 4.2 Add Section 2.6: Constants & Defaults

```typescript
// FILE: frontend/src/lib/constants.ts

// Canvas
export const DEFAULT_ZOOM = 1;
export const MIN_ZOOM = 0.1;
export const MAX_ZOOM = 10;
export const ZOOM_STEP = 0.1;

// Snap
export const SNAP_THRESHOLD_PX = 10;  // screen pixels
export const ANGLE_SNAP_DEGREES = 45;

// Undo
export const UNDO_STACK_DEPTH = 100;  // spec says 50 minimum

// Panels
export const LEFT_PANEL_DEFAULT_WIDTH = 280;
export const LEFT_PANEL_MIN_WIDTH = 200;
export const LEFT_PANEL_MAX_WIDTH = 400;
export const RIGHT_PANEL_DEFAULT_WIDTH = 340;
export const RIGHT_PANEL_MIN_WIDTH = 260;
export const RIGHT_PANEL_MAX_WIDTH = 500;
export const TOP_TOOLBAR_HEIGHT = 48;
export const BOTTOM_STATUS_BAR_HEIGHT = 32;

// Drawing
export const DEFAULT_STROKE_WIDTH = 2;
export const SELECTED_STROKE_MULTIPLIER = 2;
export const SELECTION_HANDLE_SIZE = 8;
export const SELECTION_HANDLE_COLOR = '#3B82F6';
export const DEFAULT_FILL_OPACITY = 0.2;
export const GHOST_POINT_OPACITY = 0.5;

// AI
export const AUTOTAB_DEBOUNCE_MS = 200;
export const AUTOTAB_TIMEOUT_MS = 2000;
export const AUTOTAB_MIN_POINTS = 2;
export const AUTOTAB_MIN_CONFIDENCE = 0.5;

// Persistence
export const EDIT_DEBOUNCE_MS = 500;
export const EXPORT_POLL_INTERVAL_MS = 2000;

// Scale
export const SCALE_CONFIDENCE_HIGH = 0.85;
export const SCALE_CONFIDENCE_LOW = 0.50;
```

### 4.3 Revised Task Dependency Graph

The plan has implicit dependencies that aren't called out. Here's the actual critical path:

```
A.0  State Architecture (NEW — must be first)
 ├── A.1  Workspace Layout
 │    ├── A.2  SheetTree
 │    │    ├── A.3  Keyboard Nav
 │    │    ├── A.5  Scale Indicators
 │    │    ├── A.7  Sheet Search
 │    │    └── A.8  Thumbnails
 │    └── A.4  Sheet → Canvas Load
 │         └── A.9  Context Menu
 │              └── A.10 Backend Fields
 │
 ├── B.1  Conditions Layout
 │    ├── B.2  Template Dropdown
 │    ├── B.3  Active Condition State ← CRITICAL (gates ALL of Phase C)
 │    │    └── B.7  Canvas Color Wiring
 │    ├── B.4  Visibility Toggle
 │    └── B.5  Number Keys
 │
 └── C.1  Undo/Redo ← Depends on persistence strategy (CRITICAL-2)
      ├── C.2  Tool Shortcuts ← Depends on focus system (CRITICAL-4)
      ├── C.3  Measurement Preview
      ├── C.4  Snap Engine
      └── C.5  Select/Edit/Move
           ├── C.6  Multi-Select
           ├── C.7  Context Menu
           └── D.1+ AI features
```

### 4.4 Add Stabilization Buffer Between Phases

The plan has no integration testing between phases. Add 2-3 days after each phase:

```
Phase A: 2-3 weeks + 2 days stabilization
Phase B: 2 weeks + 2 days stabilization
Phase C: 3-4 weeks + 3 days stabilization (most complex)
Phase D: 2-3 weeks + 2 days stabilization
Phase E: 1-2 weeks + 1 day stabilization

Total: 12-16 weeks (was 10-14, underestimated by ~2 weeks)
```

---

## PART 5: UPDATED TASK LIST (Additions Only)

These are new tasks to add to the plan. Existing tasks remain unchanged unless noted in Parts 1-3 above.

| Task | Phase | Priority | Effort | Description |
|------|-------|----------|--------|-------------|
| A.0 | A | P0 | 1 day | Define Zustand store architecture + constants file |
| A.0.2 | A | P0 | 0.5 days | Build FocusContext system for keyboard shortcut routing |
| A.2.5 | A | P2 | 1 day | Sheet tree drag-and-drop reorder |
| A.7.5 | A | P2 | 1 day | Text search canvas highlights (OCR regions) |
| B.6.5 | B | P2 | 0.5 days | Condition group-by dropdown filter |
| C.1* | C | P0 | 3 days | Undo/Redo system (REVISED: async commands + server sync, was 2 days) |
| C.5* | C | P0 | 2 days | Select/Edit/Move (REVISED: add hover tooltip + z-order + selection visuals, was 1.5 days) |
| C.6.5 | C | P1 | 1 day | Copy/Paste measurements |
| C.8.5 | C | P2 | 0.5 days | Zoom to selection rectangle |
| C.10.5 | C | P2 | 0.5 days | Area fill patterns (hatching) |

**Net addition: ~5.5 days of new tasks + ~2.5 days of revised estimates = ~8 extra days, mostly absorbed by the stabilization buffers.**

---

## PART 6: RECOMMENDED READING ORDER FOR AI CODING SESSIONS

When feeding this to an AI assistant for implementation, provide these in order:

1. **Before Phase A:** This audit (Part 1 critical gaps), then the state architecture from CRITICAL-1
2. **Phase A tasks:** Plan section 3, plus A.0 and A.0.2 from this audit
3. **Before Phase B:** Persistence strategy (CRITICAL-2), "no condition" behavior (CRITICAL-5)
4. **Phase B tasks:** Plan section 4
5. **Before Phase C:** Undo/redo sync model (CRITICAL-3), Canvas ↔ React sync (CRITICAL-6), constants file (4.2)
6. **Phase C tasks:** Plan section 5 + revised tasks from Part 5
7. **Phase D/E:** Plan sections 6-7 as written (minimal gaps)

---

*End of Audit. The implementation plan is strong on task decomposition. The gaps are almost entirely in the connective tissue — the state contracts, data flow rules, and invariants that keep independently-built components composing correctly. Fix these before writing code, and the implementation will be dramatically smoother.*
