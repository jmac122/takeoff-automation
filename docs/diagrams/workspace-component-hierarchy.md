# Workspace Component Hierarchy

## Overview

Visual diagram of the workspace component tree showing how React components compose to form the three-panel workspace layout.

## Full Component Tree

```
App (React Router)
└── /projects/:id/workspace
    └── TakeoffWorkspace
        │
        ├── FocusProvider (Context)
        │
        ├── TopToolbar
        │   ├── Drawing tool buttons (Select, Line, Polyline, Polygon, Rectangle, Circle, Measure)
        │   ├── Undo / Redo buttons
        │   ├── Zoom controls (Zoom In, Zoom Out, percentage)
        │   ├── AI Assist toggle
        │   └── Panel collapse toggles (Left, Right)
        │
        ├── Panel Group (react-resizable-panels, horizontal)
        │   │
        │   ├── Left Panel (20% default, 15-35%, collapsible)
        │   │   └── SheetTree
        │   │       ├── Search input
        │   │       ├── View mode toggle (Tree | Thumbnails)
        │   │       ├── Sheet groups (expandable)
        │   │       │   └── Sheet rows
        │   │       │       ├── Sheet number + title
        │   │       │       ├── ScaleBadge
        │   │       │       └── Measurement count
        │   │       ├── ThumbnailStrip (alternate view)
        │   │       └── SheetContextMenu (on right-click)
        │   │
        │   ├── Separator (draggable, blue on hover)
        │   │
        │   ├── Center Panel (min 30%)
        │   │   └── CenterCanvas
        │   │       ├── Sheet image display
        │   │       ├── Measurement overlays (Konva)
        │   │       ├── Drawing cursor
        │   │       └── Loading spinner
        │   │
        │   ├── Separator (draggable, blue on hover)
        │   │
        │   └── Right Panel (25% default, 18-40%, collapsible)
        │       └── RightPanel
        │           └── ConditionPanel
        │               ├── QuickCreateBar
        │               │   ├── "Add Condition" button
        │               │   └── Template dropdown
        │               │       └── Category groups
        │               │           └── Template items
        │               │
        │               ├── ConditionList
        │               │   └── Condition rows (scrollable)
        │               │       ├── Color dot
        │               │       ├── Name + measurement count
        │               │       ├── Total quantity + unit
        │               │       ├── Visibility toggle (Eye/EyeOff)
        │               │       └── Shortcut number (1-9)
        │               │
        │               ├── PropertiesInspector
        │               │   ├── Condition header (name, edit, delete)
        │               │   ├── Properties grid
        │               │   │   ├── Type
        │               │   │   ├── Unit
        │               │   │   ├── Depth / Thickness
        │               │   │   ├── Total quantity
        │               │   │   ├── Measurement count
        │               │   │   ├── Line width
        │               │   │   └── Fill opacity
        │               │   └── Per-sheet breakdown (expandable)
        │               │
        │               ├── ConditionContextMenu (on right-click)
        │               │   ├── Edit
        │               │   ├── Duplicate
        │               │   ├── Delete
        │               │   ├── Move Up / Move Down
        │               │   └── Toggle Visibility
        │               │
        │               └── Delete confirmation dialog (modal)
        │
        ├── BottomStatusBar
        │   ├── Sheet info
        │   ├── Scale display
        │   ├── Zoom percentage
        │   ├── Active tool
        │   └── Measurement count
        │
        └── Tool rejection toast (amber, bottom-center, auto-dismiss 3s)
```

## State Flow

```
                  ┌─────────────────────────┐
                  │    workspaceStore        │
                  │    (Zustand)             │
                  ├─────────────────────────┤
                  │ activeSheetId           │◄──── SheetTree click
                  │ activeConditionId       │◄──── ConditionList click / number keys
                  │ activeTool              │◄──── TopToolbar click
                  │ isDrawing               │◄──── CenterCanvas interaction
                  │ viewport                │◄──── CenterCanvas zoom/pan
                  │ focusRegion             │◄──── Panel focus events
                  │ leftPanelCollapsed      │◄──── TopToolbar toggle
                  │ rightPanelCollapsed     │◄──── TopToolbar toggle
                  │ toolRejectionMessage    │◄──── setActiveTool validation
                  └──────────┬──────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
         SheetTree    CenterCanvas   ConditionPanel
         reads:        reads:         reads:
         - activeSheet - activeSheet  - activeCondition
         - viewMode    - viewport     - conditions
         - expanded    - activeTool   - activeTool
         - search      - isDrawing
```

## Data Flow

```
                  ┌─────────────────────────┐
                  │    React Query           │
                  │    (Server State)        │
                  ├─────────────────────────┤
                  │ ['project', id]         │──── projectsApi.get()
                  │ ['project-sheets', id]  │──── getProjectSheets()
                  │ ['conditions', id]      │──── listProjectConditions()
                  │ ['condition-templates'] │──── listConditionTemplates()
                  └──────────┬──────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
         SheetTree    TakeoffWorkspace  ConditionPanel
         uses:         uses:             uses:
         - sheetsData  - project         - conditions
                       - activeSheet     - templates
```
