# Frontend Architecture

## Overview

The frontend is a React 18 + TypeScript single-page application built with Vite. It implements a three-panel workspace layout for construction takeoff estimation, with a canvas-based drawing engine for measurements.

## Directory Structure

```
frontend/src/
├── api/                    # REST API client modules
│   ├── client.ts           # Axios instance with base config
│   ├── projects.ts         # Project CRUD
│   ├── documents.ts        # Document upload and management
│   ├── pages.ts            # Page operations
│   ├── conditions.ts       # Condition CRUD, templates, reorder
│   ├── measurements.ts     # Measurement CRUD
│   ├── sheets.ts           # Sheet tree data fetching
│   ├── classification.ts   # Page classification triggers
│   ├── scale.ts            # Scale detection and calibration
│   ├── takeoff.ts          # AI takeoff generation
│   └── tasks.ts            # Background task polling
│
├── components/
│   ├── common/             # Shared reusable components
│   ├── conditions/         # Condition panel components
│   │   ├── ConditionPanel.tsx
│   │   ├── ConditionList.tsx
│   │   ├── ConditionContextMenu.tsx
│   │   ├── PropertiesInspector.tsx
│   │   └── QuickCreateBar.tsx
│   ├── dashboard/          # Dashboard widgets
│   ├── document/           # Document upload and browsing
│   ├── layout/             # App shell (Header, Breadcrumbs)
│   ├── project/            # Project cards and modals
│   ├── sheets/             # Sheet tree and navigation
│   │   ├── SheetTree.tsx
│   │   ├── ThumbnailStrip.tsx
│   │   ├── ScaleBadge.tsx
│   │   └── SheetContextMenu.tsx
│   ├── takeoff/            # AI takeoff dialogs
│   ├── ui/                 # shadcn/ui primitives (50+)
│   ├── viewer/             # Takeoff viewer and canvas
│   └── workspace/          # Workspace layout orchestration
│       ├── TakeoffWorkspace.tsx   # Main 3-panel layout
│       ├── TopToolbar.tsx
│       ├── BottomStatusBar.tsx
│       ├── CenterCanvas.tsx
│       └── RightPanel.tsx
│
├── contexts/               # React contexts (FocusContext)
├── hooks/                  # Custom hooks
│   ├── useConditions.ts    # Condition CRUD hooks (React Query)
│   ├── useKeyboardShortcuts.ts
│   ├── useMeasurements.ts
│   ├── usePageImage.ts
│   ├── useScaleCalibration.ts
│   ├── useScaleDetection.ts
│   ├── useCanvasControls.ts
│   ├── useCanvasEvents.ts
│   ├── useDrawingState.ts
│   ├── useTaskPolling.ts
│   ├── useNotifications.ts
│   └── useUndoRedo.ts
│
├── lib/                    # Utility functions and constants
│   └── constants.ts        # Panel sizes, zoom limits, feature flags
│
├── pages/                  # Route-level page components
│   ├── Projects.tsx
│   ├── ProjectDetail.tsx
│   ├── DocumentDetail.tsx
│   ├── TakeoffViewer.tsx
│   ├── AIEvaluation.tsx
│   └── Testing.tsx
│
├── stores/                 # Zustand state stores
│   └── workspaceStore.ts   # Main workspace state
│
└── types/                  # Shared TypeScript types
    └── index.ts
```

## State Management

### Two-Layer Pattern

The frontend uses a two-layer state management approach:

```
┌──────────────────────────────────────┐
│        Zustand (Client State)         │
│  UI state, active selections,         │
│  viewport, drawing mode, focus        │
│  region, panel collapse state         │
└──────────────┬───────────────────────┘
               │  Components read from both
┌──────────────┴───────────────────────┐
│      React Query (Server State)       │
│  Conditions, sheets, measurements,    │
│  project data — cached with           │
│  automatic invalidation on mutation   │
└──────────────────────────────────────┘
```

### Workspace Store (Zustand)

The workspace store is the single source of truth for all UI state. Key state slices:

#### Sheet Navigation
```typescript
activeSheetId: string | null       // Currently viewed sheet
selectedSheetIds: string[]         // Multi-select for batch ops
highlightedSheetId: string | null  // Hover highlight
sheetViewMode: 'tree' | 'thumbnails'
expandedGroups: Record<string, boolean>
sheetSearchQuery: string
```

#### Conditions & Drawing
```typescript
activeConditionId: string | null   // Selected condition for drawing
activeTool: DrawingTool            // 'select' | 'line' | 'polyline' | 'polygon' | ...
isDrawing: boolean                 // Currently in a draw operation
currentPoints: Point[]             // Points for current drawing
```

#### Viewport
```typescript
viewport: {
  zoom: number    // Clamped to MIN_ZOOM..MAX_ZOOM
  panX: number
  panY: number
}
```

#### UI Chrome
```typescript
leftPanelWidth: number             // Clamped to min/max
rightPanelWidth: number
leftPanelCollapsed: boolean
rightPanelCollapsed: boolean
focusRegion: FocusRegion           // 'canvas' | 'sheet-tree' | 'conditions' | ...
```

#### AI Assist
```typescript
autoTabEnabled: boolean
pendingPrediction: boolean
```

#### Transient Feedback
```typescript
toolRejectionMessage: string | null  // Cleared on next action
```

### Critical Invariant

**Drawing tools require an active condition.** The `setActiveTool()` action enforces this:
- Tools `'select'` and `'measure'` work without a condition
- All other tools (`'line'`, `'polyline'`, `'polygon'`, `'rectangle'`, `'circle'`) require `activeConditionId` to be non-null
- If violated, the tool is not set and `toolRejectionMessage` is populated for toast display

### React Query Integration

All server data is fetched and mutated through React Query hooks:

```typescript
// Fetching — auto-cached by query key
const { data } = useQuery({
  queryKey: ['conditions', projectId],
  queryFn: () => listProjectConditions(projectId),
});

// Mutations — invalidate cache on success
const updateCondition = useMutation({
  mutationFn: ({ conditionId, data }) => updateCondition(conditionId, data),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['conditions', projectId] });
  },
});
```

Custom hooks in `/hooks/useConditions.ts` wrap all condition operations with proper cache invalidation.

## Component Architecture

### Workspace Layout

```
TakeoffWorkspace
├── TopToolbar
├── Panel Group (horizontal, resizable)
│   ├── Left Panel (15-35%, collapsible)
│   │   └── SheetTree
│   │       ├── Search input
│   │       ├── View mode toggle (tree / thumbnails)
│   │       └── Grouped sheet list with expand/collapse
│   ├── Separator
│   ├── Center Panel (min 30%)
│   │   └── CenterCanvas (Konva)
│   ├── Separator
│   └── Right Panel (18-40%, collapsible)
│       └── RightPanel
│           └── ConditionPanel
│               ├── QuickCreateBar (template dropdown)
│               ├── ConditionList (scrollable, selectable)
│               └── PropertiesInspector (active condition details)
└── BottomStatusBar
```

### ConditionPanel Component Hierarchy

```
ConditionPanel (orchestrator)
├── QuickCreateBar
│   ├── "Add Condition" button
│   └── Template dropdown (grouped by category)
├── ConditionList
│   └── Per-condition row:
│       ├── Color dot
│       ├── Name + measurement count
│       ├── Total quantity + unit
│       ├── Visibility toggle (Eye/EyeOff)
│       └── Shortcut number (1-9)
├── PropertiesInspector
│   ├── Condition name + edit/delete buttons
│   ├── Properties grid (type, unit, depth, thickness, total, etc.)
│   └── Per-sheet breakdown toggle
├── ConditionContextMenu (right-click)
│   └── Edit, Duplicate, Delete, Move Up/Down, Toggle Visibility
└── Delete confirmation dialog
```

### SheetTree Component

The SheetTree manages its own expanded-group state in localStorage, keyed per project to prevent state leaks:

```typescript
const LS_KEY = `sheet-tree-state-${projectId}`;
// Loads persisted state OR initializes from sheetsData on first mount
```

Features:
- Groups sheets by discipline/group_name
- Natural sort within groups (display_order → sheet_number → page_number)
- Search filtering by sheet name
- Scale status badges (color-coded by confidence)
- Right-click context menu per sheet

## Keyboard Shortcuts

| Key | Context | Action |
|---|---|---|
| `1`-`9` | Condition panel | Select condition by position |
| `V` | Active condition | Toggle visibility |
| `Ctrl+D` | Active condition | Duplicate condition |
| `Delete` | Active condition | Delete (with confirmation) |
| `Escape` | Global | Reset drawing state, clear selection |

## Routing

```
/                              → Projects list
/projects/:id                  → Project detail (legacy)
/projects/:id/workspace        → TakeoffWorkspace (new, behind feature flag)
/projects/:id/documents/:docId → Document detail
/projects/:id/viewer           → Takeoff viewer (legacy)
```

The new workspace is gated behind `ENABLE_NEW_WORKSPACE` feature flag. When disabled, `/projects/:id/workspace` redirects to `/projects/:id`.

## Testing

- **Framework**: Vitest + React Testing Library
- **Strategy**: Component tests with mocked hooks and lucide-react icons
- **Conventions**: Each component directory has a `__tests__/` subdirectory
- **Key test files**:
  - `ConditionPanel.test.tsx` — 13 tests covering rendering, selection, keyboard shortcuts, context menu
  - `TakeoffWorkspace.test.tsx` — 4 tests covering layout, loading, error states
  - `SheetTree.test.tsx` — 10 tests covering grouping, search, keyboard nav, persistence
  - `workspaceStore.test.ts` — 12 tests covering state actions and invariants
