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
        │   ├── Drawing tool buttons (Select, Line, Polyline, Polygon, Rectangle, Circle, Point, Measure)
        │   ├── Undo / Redo buttons (wired to useUndoRedo)
        │   ├── Zoom controls (Zoom In, Zoom Out, percentage)
        │   ├── Scale section
        │   │   ├── Set Scale button (opens calibration mode)
        │   │   ├── Auto Detect button (triggers AI scale detection)
        │   │   └── Show Location toggle (MapPin, conditional on scale bbox)
        │   ├── Title Block section
        │   │   ├── Title Block mode toggle (Crop icon)
        │   │   └── Show Region toggle (Eye icon, conditional on saved region)
        │   ├── Grid section (snap toggle, show grid toggle)
        │   ├── AI Assist button (batch AI takeoff)
        │   ├── AI Confidence overlay toggle
        │   ├── Review mode toggle
        │   ├── ExportDropdown
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
        │   │       ├── Konva Stage
        │   │       │   ├── Layer: Sheet image (KonvaImage)
        │   │       │   ├── Layer: Measurement overlays (MeasurementLayer → MeasurementShape)
        │   │       │   ├── Layer: Drawing preview (DrawingPreviewLayer)
        │   │       │   ├── Layer: Calibration overlay (CalibrationOverlay — amber dashed line)
        │   │       │   ├── Layer: Title block region (green filled Rect)
        │   │       │   ├── Layer: Title block draft (blue dashed Rect)
        │   │       │   ├── Layer: Scale detection highlight (amber Rect)
        │   │       │   ├── Layer: Scale location overlay (green Rect)
        │   │       │   └── Layer: GhostPointLayer (AI prediction, cyan pulsing)
        │   │       ├── HTML Overlays
        │   │       │   ├── Scale warning banner (uncalibrated sheet)
        │   │       │   ├── ScaleDetectionBanner (post-detection result)
        │   │       │   ├── Calibration mode banner (blue)
        │   │       │   ├── Title block mode banner (purple)
        │   │       │   └── MeasurementsPanel (bottom-right floating)
        │   │       ├── MeasurementContextMenu (absolute positioned)
        │   │       │   ├── Duplicate
        │   │       │   ├── Show / Hide
        │   │       │   ├── Bring to Front / Send to Back
        │   │       │   └── Delete
        │   │       └── Loading spinner / placeholder states
        │   │
        │   ├── Separator (draggable, blue on hover)
        │   │
        │   └── Right Panel (25% default, 18-40%, collapsible)
        │       └── RightPanel (tabbed)
        │           ├── Conditions tab → ConditionPanel
        │           ├── Cost tab → Assembly cost breakdown
        │           └── Revisions tab → RevisionChainPanel
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
        │   ├── Measurement count
        │   └── Review stats (when review mode active)
        │
        ├── ScaleCalibrationDialog (modal, after calibration line drawn)
        │   ├── Pixel distance display
        │   ├── Real distance input
        │   ├── Unit selector (foot, inch, meter, etc.)
        │   └── Submit / Cancel buttons
        │
        ├── Title block save banner (fixed overlay, after title block drawn)
        │   ├── "Save Title Block Region?" prompt
        │   ├── Save button (re-runs OCR with new region)
        │   └── Reset button
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
                  │ reviewMode              │◄──── TopToolbar toggle
                  │ ghostPrediction         │◄──── AI AutoTab prediction
                  │ aiConfidenceOverlay     │◄──── TopToolbar toggle
                  │ batchAiTaskId           │◄──── AI Assist button
                  │ snapToGrid / showGrid   │◄──── TopToolbar toggles
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
                  │ ['page', sheetId]       │──── GET /pages/{id} (scale, title block)
                  │ ['measurements', sheetId]│──── listPageMeasurements()
                  └──────────┬──────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
         SheetTree    TakeoffWorkspace  ConditionPanel
         uses:         uses:             uses:
         - sheetsData  - project         - conditions
                       - activeSheet     - templates
```
