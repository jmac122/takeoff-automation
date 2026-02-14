# Workspace Layout (Phase A)

## Overview

The workspace layout is a three-panel resizable interface designed for construction takeoff estimation. It replaces the legacy project detail page with a purpose-built workspace that mirrors professional estimating tools like Bluebeam Revu and PlanSwift.

## Layout Structure

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Top Toolbar                                │
│  [Tools] [Undo/Redo] [Zoom] [Scale] [TitleBlock] [AI] [Export] [Panels] │
├───────────────┬─────────────────────────────┬───────────────────────┤
│               │                             │                       │
│  Sheet Tree   │      Center Canvas          │   Condition Panel     │
│  (Left Panel) │      (Konva.js)             │   (Right Panel)       │
│               │                             │                       │
│  - Search     │  - Sheet image display      │   - Quick Create      │
│  - Groups     │  - Drawing tools            │   - Condition List    │
│  - Sheets     │  - Measurement overlay      │   - Properties        │
│  - Thumbnails │  - Zoom/pan                 │   - Cost Tab          │
│               │  - Scale overlays           │   - Revisions Tab     │
│               │  - Calibration overlay      │                       │
│               │  - Title block overlay      │                       │
│               │  - Measurements panel       │                       │
│               │                             │                       │
│  15-35%       │      min 30%                │   18-40%              │
│  default: 20% │                             │   default: 25%        │
├───────────────┴─────────────────────────────┴───────────────────────┤
│                        Bottom Status Bar                            │
│  [Sheet info] [Scale] [Zoom %] [Active tool] [Measurements count]   │
└─────────────────────────────────────────────────────────────────────┘
```

## Panel Behavior

### Left Panel (Sheet Tree)
- **Default width**: 20%
- **Min/Max**: 15% - 35%
- **Collapsible**: Yes, via toolbar toggle
- **Contents**: `SheetTree` component
- **Persistence**: Expanded groups stored in localStorage per project

### Center Canvas
- **Minimum size**: 30% (always visible)
- **Contents**: Active sheet image with measurement overlays
- **Image loading**: Preloads images with stale-flag pattern to prevent race conditions
- **Zoom/Pan**: Stored in `viewport` state, clamped to `MIN_ZOOM..MAX_ZOOM`

### Toolbar Sections

The `TopToolbar` organizes controls into logical groups:

| Section | Controls |
|---------|----------|
| Drawing Tools | Select, Line, Polyline, Polygon, Rectangle, Circle, Point, Measure |
| Undo/Redo | Undo (Ctrl+Z), Redo (Ctrl+Shift+Z) — wired to canvas action stack |
| Zoom | Zoom In, Zoom Out, Zoom percentage display |
| Scale | Set Scale (manual calibration), Auto Detect (AI), Show Location (MapPin toggle) |
| Title Block | Toggle title block drawing mode, Show/hide existing region |
| Grid | Toggle snap-to-grid, Toggle grid visibility, Grid size |
| AI Assist | Batch AI takeoff, AI confidence overlay toggle |
| Review | Review mode toggle, confidence filter |
| Export | Export dropdown (Excel, CSV, PDF, OST) |
| Panels | Toggle left panel, Toggle right panel |

### Context Menu (Right-Click on Measurement)

| Action | Description |
|--------|-------------|
| Duplicate | Creates a copy offset by 12px |
| Show/Hide | Toggles local visibility of the measurement |
| Bring to Front | Moves measurement to top of z-order |
| Send to Back | Moves measurement to bottom of z-order |
| Delete | Removes measurement (with undo support) |

### Canvas Overlays

| Overlay | Trigger | Description |
|---------|---------|-------------|
| Scale Warning Banner | Sheet not calibrated | Amber bar at top of canvas warning about missing scale |
| Scale Detection Banner | After auto-detect | Green bar showing detected scale with dismiss button |
| Calibration Overlay | "Set Scale" clicked | Dashed amber line while user draws calibration line |
| Title Block Overlay | Title block mode active | Blue dashed rectangle for drawing title block region |
| Title Block Region | "Show Region" toggled | Green filled rectangle showing saved title block |
| Scale Location | "Show Location" toggled | Green highlight on detected scale bbox |
| Measurements Panel | Measurements exist | Bottom-right floating panel listing measurements per sheet |
| Calibration Mode Banner | Calibrating | Blue banner at top: "CALIBRATION MODE — Draw a line..." |
| Title Block Mode Banner | Drawing title block | Purple banner at top: "TITLE BLOCK MODE — Click and drag..." |

### Right Panel (Conditions)
- **Default width**: 25%
- **Min/Max**: 18% - 40%
- **Collapsible**: Yes, via toolbar toggle
- **Contents**: `ConditionPanel` component

### Resizing
Panels use `react-resizable-panels` with draggable separators. Separators highlight blue on hover for visual affordance.

## Feature Flag

The workspace is gated behind `ENABLE_NEW_WORKSPACE` in `/lib/constants.ts`. When disabled:
- `/projects/:id/workspace` redirects to `/projects/:id`
- Legacy project detail page is served

## Data Flow

```
1. TakeoffWorkspace mounts with projectId from route params
2. React Query fetches:
   a. Project data: GET /projects/{id}
   b. Sheet tree:   GET /projects/{id}/sheets
   c. Page data:    GET /pages/{activeSheetId} (scale_calibration_data, title_block_region)
3. SheetTree renders grouped sheets from SheetsResponse
4. User clicks sheet → setActiveSheet(sheetId)
5. TakeoffWorkspace finds active sheet in sheetsData
6. Image URL triggers preload, sets loading state
7. CenterCanvas displays sheet image when loaded
8. RightPanel renders ConditionPanel with projectId
```

## Error Handling

| Scenario | Behavior |
|---|---|
| Project not found | Shows "Project not found" message with explanation |
| Project loading | Shows centered spinner (Loader2) |
| Missing projectId | Shows "Project ID missing" message |
| Sheet image fails to load | Loading state clears, canvas shows placeholder |
| Tool rejected (no condition) | Amber toast appears bottom-center, auto-dismisses in 3s |

## Keyboard Shortcuts

| Key | Action |
|---|---|
| `Escape` | Reset drawing state, clear selection, cancel calibration/title block mode |
| `1`-`9` | Select condition by position (from ConditionPanel) |
| `V` | Select tool |
| `L` | Line tool |
| `P` | Polyline tool |
| `A` | Polygon (area) tool |
| `R` | Rectangle tool |
| `C` | Circle tool |
| `M` | Measure tool (no condition required) |
| `Ctrl+Z` | Undo last action |
| `Ctrl+Shift+Z` | Redo last action |
| `Delete`/`Backspace` | Delete selected measurement(s) |
| `G` | Toggle snap-to-grid |

## Key Files

| File | Purpose |
|---|---|
| `frontend/src/components/workspace/TakeoffWorkspace.tsx` | Main layout orchestrator, scale/calibration/title block state |
| `frontend/src/components/workspace/TopToolbar.tsx` | Drawing tools, zoom, scale, title block, grid, AI, export, review |
| `frontend/src/components/workspace/BottomStatusBar.tsx` | Status information, review stats |
| `frontend/src/components/workspace/CenterCanvas.tsx` | Konva canvas with all overlay layers and measurement interaction |
| `frontend/src/components/workspace/RightPanel.tsx` | Condition panel, cost tab, revisions tab |
| `frontend/src/components/workspace/MeasurementContextMenu.tsx` | Right-click context menu for measurements |
| `frontend/src/stores/workspaceStore.ts` | All workspace UI state (Zustand) |
| `frontend/src/lib/constants.ts` | Panel size limits, zoom bounds, feature flags, timeouts |
| `frontend/src/contexts/FocusContext.tsx` | Focus region tracking for keyboard shortcuts |
| `frontend/src/hooks/useScaleCalibration.ts` | Scale calibration line drawing workflow |
| `frontend/src/hooks/useScaleDetection.ts` | Auto scale detection with polling |
| `frontend/src/hooks/useUndoRedo.ts` | Undo/redo action stack |

## Backend Support

The workspace relies on these backend endpoints:

| Endpoint | Purpose |
|---|---|
| `GET /projects/{id}` | Project metadata |
| `GET /projects/{id}/sheets` | Sheet tree with groups, scale, measurement counts |
| `PUT /pages/{id}/display` | Update sheet display name, order, group |
| `PUT /pages/{id}/relevance` | Include/exclude sheets from tree |
| `POST /pages/batch-scale` | Apply scale to multiple sheets |

## Testing

### Frontend Tests
- `TakeoffWorkspace.test.tsx` — 4 tests: layout rendering, loading state, error state, prop passing
- `workspaceStore.test.ts` — 12 tests: all state actions and invariants

### Backend Tests
- Sheet tree endpoint tested via integration tests
- Natural sort ordering verified
- Measurement count subquery tested
