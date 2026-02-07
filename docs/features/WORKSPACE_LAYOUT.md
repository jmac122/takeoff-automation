# Workspace Layout (Phase A)

## Overview

The workspace layout is a three-panel resizable interface designed for construction takeoff estimation. It replaces the legacy project detail page with a purpose-built workspace that mirrors professional estimating tools like Bluebeam Revu and PlanSwift.

## Layout Structure

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Top Toolbar                                │
│  [Tools] [Undo/Redo] [Zoom Controls] [AI Assist] [Panel Toggles]   │
├───────────────┬─────────────────────────────┬───────────────────────┤
│               │                             │                       │
│  Sheet Tree   │      Center Canvas          │   Condition Panel     │
│  (Left Panel) │      (Konva.js)             │   (Right Panel)       │
│               │                             │                       │
│  - Search     │  - Sheet image display      │   - Quick Create      │
│  - Groups     │  - Drawing tools            │   - Condition List    │
│  - Sheets     │  - Measurement overlay      │   - Properties        │
│  - Thumbnails │  - Zoom/pan                 │                       │
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
| `Escape` | Reset drawing state, clear selection |
| `1`-`9` | Select condition by position (from ConditionPanel) |

## Key Files

| File | Purpose |
|---|---|
| `frontend/src/components/workspace/TakeoffWorkspace.tsx` | Main layout orchestrator |
| `frontend/src/components/workspace/TopToolbar.tsx` | Drawing tools, zoom, toggles |
| `frontend/src/components/workspace/BottomStatusBar.tsx` | Status information |
| `frontend/src/components/workspace/CenterCanvas.tsx` | Canvas rendering |
| `frontend/src/components/workspace/RightPanel.tsx` | Condition panel wrapper |
| `frontend/src/stores/workspaceStore.ts` | All workspace UI state |
| `frontend/src/lib/constants.ts` | Panel size limits, feature flags |
| `frontend/src/contexts/FocusContext.tsx` | Focus region tracking |

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
