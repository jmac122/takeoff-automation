# ForgeX UI/UX Overhaul Implementation Plan

> **Document Version:** 1.0
> **Created:** February 2026
> **Based on:** ForgeX UI/UX Overhaul Specification v1.0
> **Target Completion:** 12 weeks from start

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture Overview](#2-architecture-overview)
3. [Phase A: Sheet Manager & Navigation](#3-phase-a-sheet-manager--navigation)
4. [Phase B: Conditions Panel Overhaul](#4-phase-b-conditions-panel-overhaul)
5. [Phase C: Plan Viewer & Drawing Tools](#5-phase-c-plan-viewer--drawing-tools)
6. [Phase D: AI Assist Layer](#6-phase-d-ai-assist-layer)
7. [Phase E: Export & Reporting](#7-phase-e-export--reporting)
8. [Database & API Changes](#8-database--api-changes)
9. [Dependencies & Prerequisites](#9-dependencies--prerequisites)
10. [Risk Assessment](#10-risk-assessment)
11. [Success Criteria](#11-success-criteria)
12. [Appendix: Complete Keyboard Shortcut Map](#12-appendix-complete-keyboard-shortcut-map)

---

## 1. Executive Summary

### 1.1 Philosophy Shift

ForgeX Takeoffs is transitioning from a **batch AI processing pipeline** to an **estimator-first takeoff tool** with intelligent AI assistance.

| Aspect | Old Model | New Model |
|--------|-----------|-----------|
| Control | AI-driven with human review | Human-driven with AI assist |
| Workflow | Upload → AI process → Review → Approve | Upload → Auto-organize → Manual takeoff with AI assists |
| User Mental Model | "AI processes everything" | "AI is my copilot" |
| Similar To | Batch processing tool | Bluebeam, PlanSwift, On Screen Takeoff |

### 1.2 What We Keep

The existing backend is solid and maps directly to the new model:

| Component | Status | Action Required |
|-----------|--------|-----------------|
| Document Ingestion Pipeline | **Keep** | No changes needed |
| OCR / Google Cloud Vision | **Keep** | Powers SheetScan + search |
| Page Classification (LLM) | **Keep** | Auto-tags sheets on upload |
| Scale Detection + Calibration | **Keep** | Powers auto-scale in SheetScan |
| Measurement Engine (geometry) | **Keep** | Core drawing tool math |
| Condition Management | **Refactor** | New docked panel UI |
| AI Takeoff Generation | **Refactor** | Becomes on-demand AI assists |
| Review Interface | **Rebuild** | Replaced by inline editing |
| Konva.js Canvas + Drawing | **Refactor** | Enhanced with snap/undo/keyboard |
| Export System | **Keep** | Add report templates later |

### 1.3 Implementation Timeline

| Phase | Scope | Estimated Effort | Dependencies |
|-------|-------|------------------|--------------|
| **Phase A** | Sheet Manager & Navigation | 2-3 weeks | None (start here) |
| **Phase B** | Conditions Panel Overhaul | 2 weeks | Phase A |
| **Phase C** | Plan Viewer & Drawing Tools | 3-4 weeks | Phase A + B |
| **Phase D** | AI Assist Layer | 2-3 weeks | Phase C |
| **Phase E** | Export & Reporting | 1-2 weeks | Phase B |

**Total Timeline:** 10-14 weeks

---

## 2. Architecture Overview

### 2.1 New Application Layout

The workspace transitions from multi-page navigation to a **single integrated workspace**:

```
┌─────────────────────────────────────────────────────────────────────────┐
│ TOP TOOLBAR (48px)                                                       │
│ [Drawing Tools] [Zoom Controls] [Undo/Redo] [AI Assist] [Search]        │
├──────────────┬────────────────────────────────────┬─────────────────────┤
│ LEFT SIDEBAR │        CENTER CANVAS               │    RIGHT PANEL      │
│ (260-300px)  │        (Flexible)                  │    (320-360px)      │
│              │                                    │                     │
│ Sheet Tree   │   Plan Viewer (Konva.js)           │ Conditions Panel    │
│ Navigator    │   Measurement Layer                │ Properties Panel    │
│              │   AI Overlay Layer                 │ Measurement Details │
│ Thumbnails   │   Calibration Overlay              │                     │
│              │                                    │                     │
│ Sheet Search │                                    │                     │
├──────────────┴────────────────────────────────────┴─────────────────────┤
│ BOTTOM STATUS BAR (32px)                                                 │
│ [Scale Indicator] [Cursor Coordinates] [Active Tool] [Selection Info]   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 New Route Structure

```
/                              → Project list (dashboard)
/projects/:id                  → Takeoff Workspace (main app)
/projects/:id/settings         → Project settings
/projects/:id/export           → Export/reports view
```

### 2.3 Component Hierarchy

```
TakeoffWorkspace
├── TopToolbar
│   ├── DrawingTools (line, polyline, polygon, rect, count)
│   ├── ZoomControls
│   ├── UndoRedoButtons
│   ├── AIAssistToggle
│   └── SearchBar
├── LeftSidebar
│   ├── SheetTree
│   ├── SheetThumbnails
│   └── SheetSearch
├── CenterCanvas
│   ├── PlanViewer (Konva.js stage)
│   ├── MeasurementLayer
│   ├── AIOverlayLayer
│   └── CalibrationOverlay
├── RightPanel
│   ├── ConditionsPanel
│   ├── PropertiesPanel
│   └── MeasurementDetails
└── BottomStatusBar
    ├── ScaleIndicator
    ├── CursorCoordinates
    └── ActiveToolInfo
```

---

## 3. Phase A: Sheet Manager & Navigation

**Duration:** 2-3 weeks
**Dependencies:** None
**Goal:** Replace flat document list with organized, navigable sheet tree

### 3.1 Week 1: Layout + Sheet Tree

#### Task A.1: Create TakeoffWorkspace Layout Component
- **Priority:** P0 (Critical)
- **Estimated Effort:** 1 day
- **Description:** Create three-panel split layout with resizable panels
- **Technical Details:**
  - Use `react-resizable-panels` library for panel management
  - CSS Grid or flexbox for primary layout
  - Collapsible left and right panels
  - Persist panel sizes in localStorage
- **Files to Create:**
  - `frontend/src/pages/TakeoffWorkspace.tsx`
  - `frontend/src/components/workspace/WorkspaceLayout.tsx`
- **Files to Modify:**
  - `frontend/src/App.tsx` (add route)
- **Acceptance Criteria:**
  - [ ] Three-panel layout renders correctly
  - [ ] Panels are resizable via drag handles
  - [ ] Panel sizes persist across page refreshes
  - [ ] Panels collapse/expand with toggle buttons

#### Task A.2: Create SheetTree Component
- **Priority:** P0 (Critical)
- **Estimated Effort:** 2 days
- **Description:** Hierarchical tree with auto-grouping by discipline
- **Technical Details:**
  - Wire to existing `GET /documents/{id}/pages` endpoint
  - Auto-group by `discipline` field from classification
  - Sort within groups by `sheet_number`
  - Use accessible tree pattern (aria-tree)
- **Files to Create:**
  - `frontend/src/components/workspace/SheetTree.tsx`
  - `frontend/src/components/workspace/SheetTreeNode.tsx`
  - `frontend/src/hooks/useSheetTree.ts`
- **API Integration:**
  ```typescript
  // Existing endpoint - no backend changes needed
  GET /documents/{documentId}/pages?include=classification,scale
  ```
- **Tree Structure Example:**
  ```
  Project: 123 Main Street
    [v] Structural (12 sheets)
        S-101  Foundation Plan          [calibrated]
        S-102  Foundation Plan North    [calibrated]
        ...
    [v] Civil (6 sheets)
        C-001  Site Plan                [calibrated]
        ...
    [>] Architectural (18 sheets)
    [>] Unclassified (2 sheets)
  ```
- **Acceptance Criteria:**
  - [ ] Tree displays all pages grouped by discipline
  - [ ] Groups expand/collapse on click
  - [ ] Sheet number and name displayed for each node
  - [ ] Loading state while fetching data

#### Task A.3: Add Keyboard Navigation to SheetTree
- **Priority:** P1 (High)
- **Estimated Effort:** 1 day
- **Description:** Full keyboard support for tree navigation
- **Keyboard Shortcuts:**
  - `↑/↓` - Navigate between nodes
  - `←/→` - Collapse/expand groups
  - `Enter` - Load selected sheet
  - `Space` - Toggle group expand/collapse
  - `Home/End` - Jump to first/last node
- **Technical Details:**
  - Implement roving tabindex pattern
  - ARIA tree role with proper states
- **Acceptance Criteria:**
  - [ ] All shortcuts function correctly
  - [ ] Focus management works properly
  - [ ] Screen reader announces node states

#### Task A.4: Implement Sheet Selection → Canvas Load
- **Priority:** P0 (Critical)
- **Estimated Effort:** 1 day
- **Description:** Clicking a sheet loads the plan image in center canvas
- **Technical Details:**
  - Use React context or Zustand for active sheet state
  - Integrate with existing `usePageImage` hook
  - Show loading state during image fetch
- **Files to Modify:**
  - `frontend/src/components/viewer/PlanViewer.tsx`
  - `frontend/src/hooks/usePageImage.ts`
- **State Management:**
  ```typescript
  interface WorkspaceState {
    activeSheetId: string | null;
    activeConditionId: string | null;
    activeTool: DrawingTool | null;
  }
  ```
- **Acceptance Criteria:**
  - [ ] Single click selects sheet and loads in canvas
  - [ ] Double click zooms to fit
  - [ ] Loading spinner shown during image load
  - [ ] Error state if image fails to load

### 3.2 Week 2: Scale Status + Search

#### Task A.5: Add Scale Status Indicators
- **Priority:** P1 (High)
- **Estimated Effort:** 0.5 days
- **Description:** Visual indicators for calibration state on each tree node
- **Indicator Types:**
  - 🟢 Green checkmark: Auto-calibrated (confidence ≥ 85%)
  - 🟡 Yellow warning: Low confidence detection
  - 🔴 Red X: No scale detected
  - 🔵 Blue ruler: Manually calibrated
- **Files to Modify:**
  - `frontend/src/components/workspace/SheetTreeNode.tsx`
- **Acceptance Criteria:**
  - [ ] Correct indicator shown for each scale state
  - [ ] Tooltip explains each indicator on hover
  - [ ] Icons are accessible (aria-label)

#### Task A.6: Implement Batch Scale Operations
- **Priority:** P1 (High)
- **Estimated Effort:** 1 day
- **Description:** Multi-select sheets and apply/copy scale
- **Operations:**
  - Apply Scale to Selected: Set same scale on all selected
  - Copy Scale from Sheet: Pick calibrated sheet, copy to selected
  - Auto-Detect All: Re-run detection on selected
- **Technical Details:**
  - Use Ctrl+click for multi-select
  - Use Shift+click for range select
  - Show selection count in toolbar
- **API Endpoints (existing):**
  ```
  POST /pages/{id}/scale/copy-from/{sourceId}
  POST /pages/{id}/scale/detect
  PUT /pages/{id}/scale
  ```
- **Acceptance Criteria:**
  - [ ] Multi-select works with Ctrl/Shift+click
  - [ ] Batch apply scale completes successfully
  - [ ] Progress indicator for batch operations
  - [ ] Error handling for partial failures

#### Task A.7: Add Sheet Search
- **Priority:** P1 (High)
- **Estimated Effort:** 1 day
- **Description:** Combined sheet name filter + full-text OCR search
- **Two Search Modes:**
  1. **Sheet search**: Client-side filter by sheet number/name (instant)
  2. **Text search**: Server-side OCR text search (uses existing endpoint)
- **API Endpoint (existing):**
  ```
  GET /projects/{id}/search?q={query}
  ```
- **Files to Create:**
  - `frontend/src/components/workspace/SheetSearch.tsx`
- **Acceptance Criteria:**
  - [ ] Instant filtering as user types
  - [ ] Toggle between sheet/text search modes
  - [ ] Text search shows matching sheets with highlights
  - [ ] Clear button resets search

#### Task A.8: Add Thumbnail Strip View
- **Priority:** P2 (Medium)
- **Estimated Effort:** 0.5 days
- **Description:** Alternative view showing page thumbnails
- **Technical Details:**
  - Lazy-load thumbnails with IntersectionObserver
  - Thumbnails already generated in ingestion pipeline
  - Active thumbnail gets colored border (condition color)
- **Files to Create:**
  - `frontend/src/components/workspace/ThumbnailStrip.tsx`
- **Acceptance Criteria:**
  - [ ] Thumbnails lazy-load as scrolled into view
  - [ ] Click thumbnail loads page
  - [ ] Active page thumbnail highlighted
  - [ ] Toggle between tree/thumbnail views

### 3.3 Week 3: Polish + Context Menus

#### Task A.9: Sheet Context Menu
- **Priority:** P1 (High)
- **Estimated Effort:** 1 day
- **Description:** Right-click menu for sheet operations
- **Menu Items:**
  - Set Scale
  - Copy Scale To...
  - Rename
  - Move to Group
  - Mark as Not Relevant
- **Files to Create:**
  - `frontend/src/components/workspace/SheetContextMenu.tsx`
- **Acceptance Criteria:**
  - [ ] Context menu appears on right-click
  - [ ] All operations function correctly
  - [ ] Keyboard shortcut hints shown in menu
  - [ ] Menu closes on action or click-away

#### Task A.10: Backend - Add Display Fields to Pages Model
- **Priority:** P1 (High)
- **Estimated Effort:** 0.5 days
- **Description:** Add user-editable display fields
- **New Fields:**
  ```sql
  ALTER TABLE pages ADD COLUMN display_name VARCHAR(200);
  ALTER TABLE pages ADD COLUMN display_order INTEGER;
  ALTER TABLE pages ADD COLUMN group_name VARCHAR(100);
  ALTER TABLE pages ADD COLUMN is_relevant BOOLEAN DEFAULT true;
  ```
- **Files to Modify:**
  - `backend/app/models/page.py`
  - `backend/alembic/versions/xxx_add_page_display_fields.py`
- **API Endpoints to Add:**
  ```
  PUT /pages/{id}/display
  PUT /pages/{id}/relevance
  ```
- **Acceptance Criteria:**
  - [ ] Migration runs without errors
  - [ ] API endpoints return updated data
  - [ ] Existing pages have sensible defaults

#### Task A.11: Persist Tree State
- **Priority:** P2 (Medium)
- **Estimated Effort:** 0.5 days
- **Description:** Remember expanded/collapsed groups per project
- **Technical Details:**
  - Store in localStorage keyed by project ID
  - Restore on project load
- **Acceptance Criteria:**
  - [ ] Expand/collapse state persists
  - [ ] State isolated per project
  - [ ] Graceful handling of stale data

#### Task A.12: Page Up/Down Navigation
- **Priority:** P2 (Medium)
- **Estimated Effort:** 0.5 days
- **Description:** Global keyboard shortcuts for sheet navigation
- **Shortcuts:**
  - `Page Up` - Previous sheet
  - `Page Down` - Next sheet
  - `Ctrl+G` - Go to sheet (opens search)
- **Acceptance Criteria:**
  - [ ] Shortcuts work when canvas focused
  - [ ] Visual feedback on sheet change
  - [ ] Wraps at start/end of list

### Phase A Deliverables Summary

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| A.1 TakeoffWorkspace layout | P0 | 1 day | ⬜ |
| A.2 SheetTree component | P0 | 2 days | ⬜ |
| A.3 Keyboard navigation | P1 | 1 day | ⬜ |
| A.4 Sheet → Canvas load | P0 | 1 day | ⬜ |
| A.5 Scale status indicators | P1 | 0.5 days | ⬜ |
| A.6 Batch scale operations | P1 | 1 day | ⬜ |
| A.7 Sheet search | P1 | 1 day | ⬜ |
| A.8 Thumbnail strip | P2 | 0.5 days | ⬜ |
| A.9 Context menu | P1 | 1 day | ⬜ |
| A.10 Backend display fields | P1 | 0.5 days | ⬜ |
| A.11 Persist tree state | P2 | 0.5 days | ⬜ |
| A.12 Page navigation | P2 | 0.5 days | ⬜ |

**Total Phase A Effort:** ~11 days (2-3 weeks with buffer)

---

## 4. Phase B: Conditions Panel Overhaul

**Duration:** 2 weeks
**Dependencies:** Phase A
**Goal:** Transform conditions panel into primary takeoff control center

### 4.1 Weeks 3-4: Panel Redesign

#### Task B.1: Refactor ConditionPanel Layout
- **Priority:** P0 (Critical)
- **Estimated Effort:** 1.5 days
- **Description:** Three-section vertical layout
- **Panel Sections:**
  ```
  ┌─────────────────────────────┐
  │ QUICK-CREATE BAR            │  ← Template dropdown + Custom button
  ├─────────────────────────────┤
  │ ACTIVE CONDITIONS LIST      │  ← Scrollable list with totals
  │ [Color] Name        Total   │
  │ [●] 4" Slab        2,450 SF │
  │ [●] Foundation     1,200 LF │
  │ ...                         │
  ├─────────────────────────────┤
  │ PROPERTIES INSPECTOR        │  ← Selected condition details
  │ Type: Area (SF)             │
  │ Depth: 4 inches             │
  │ Per-sheet breakdown...      │
  └─────────────────────────────┘
  ```
- **Files to Modify:**
  - `frontend/src/components/conditions/ConditionPanel.tsx`
- **Files to Create:**
  - `frontend/src/components/conditions/QuickCreateBar.tsx`
  - `frontend/src/components/conditions/ConditionList.tsx`
  - `frontend/src/components/conditions/PropertiesInspector.tsx`
- **Acceptance Criteria:**
  - [ ] Three-section layout renders correctly
  - [ ] Sections resize appropriately
  - [ ] Properties section collapses when no selection

#### Task B.2: Wire Template Dropdown
- **Priority:** P0 (Critical)
- **Estimated Effort:** 0.5 days
- **Description:** Quick-create from condition templates
- **Template Categories:**
  - Flatwork: 4" Slab, 6" Slab, Sidewalk
  - Foundations: Foundation Wall, Footing, Grade Beam
  - Vertical: Column, Wall
  - Linear: Curb & Gutter, Edge Form
- **API Endpoint (existing):**
  ```
  GET /conditions/templates
  ```
- **Acceptance Criteria:**
  - [ ] Templates load from API
  - [ ] One-click creates condition
  - [ ] Recently used templates shown as chips

#### Task B.3: Condition Selection → Active Drawing State
- **Priority:** P0 (Critical)
- **Estimated Effort:** 1 day
- **Description:** Selected condition becomes active for drawing
- **Technical Details:**
  - Clicking condition row sets it as active
  - Canvas cursor color matches condition color
  - All new measurements attach to active condition
- **State Changes:**
  ```typescript
  // Add to workspace state
  activeConditionId: string | null;
  ```
- **Acceptance Criteria:**
  - [ ] Click sets active condition
  - [ ] Active condition highlighted in list
  - [ ] Canvas reflects active condition color
  - [ ] Measurements created under active condition

#### Task B.4: Add Visibility Toggle
- **Priority:** P1 (High)
- **Estimated Effort:** 0.5 days
- **Description:** Eye icon to show/hide condition measurements
- **Technical Details:**
  - Toggle icon in condition row
  - Updates canvas MeasurementLayer visibility
  - Backend: add `is_visible` field to conditions
- **Database Change:**
  ```sql
  ALTER TABLE conditions ADD COLUMN is_visible BOOLEAN DEFAULT true;
  ```
- **Acceptance Criteria:**
  - [ ] Eye icon toggles visibility
  - [ ] Canvas hides/shows measurements immediately
  - [ ] Visibility state persists

#### Task B.5: Number Key Shortcuts (1-9)
- **Priority:** P1 (High)
- **Estimated Effort:** 0.5 days
- **Description:** Quick condition selection via keyboard
- **Shortcuts:**
  - `1-9` - Select condition by list position
  - `Ctrl+N` - Create new condition
  - `Ctrl+D` - Duplicate selected condition
  - `Delete` - Delete selected condition (with confirm)
  - `V` - Toggle visibility
  - `Ctrl+Shift+V` - Toggle ALL visibility
- **Acceptance Criteria:**
  - [ ] All shortcuts function correctly
  - [ ] Visual feedback on selection change
  - [ ] Delete requires confirmation

### 4.2 Week 5: Properties + Integration

#### Task B.6: Build Properties Inspector
- **Priority:** P1 (High)
- **Estimated Effort:** 1 day
- **Description:** Detailed view for selected condition
- **Displayed Fields:**
  - Measurement Type (Linear/Area/Volume/Count)
  - Depth/Thickness (for volume calculations)
  - Line Style (width, opacity, fill pattern)
  - Per-Sheet Breakdown (collapsible)
  - Edit/Delete buttons
- **Files to Create:**
  - `frontend/src/components/conditions/PropertiesInspector.tsx`
  - `frontend/src/components/conditions/PerSheetBreakdown.tsx`
- **Acceptance Criteria:**
  - [ ] All properties displayed correctly
  - [ ] Editable fields save on blur
  - [ ] Per-sheet breakdown shows correct totals

#### Task B.7: Wire Canvas Colors to Active Condition
- **Priority:** P0 (Critical)
- **Estimated Effort:** 0.5 days
- **Description:** Drawing tools use active condition color
- **Technical Details:**
  - Get color from active condition
  - Apply to cursor, drawing preview, measurement stroke
  - Fall back to default if no condition selected
- **Files to Modify:**
  - `frontend/src/hooks/useDrawingTool.ts`
  - `frontend/src/components/viewer/MeasurementLayer.tsx`
- **Acceptance Criteria:**
  - [ ] Cursor shows condition color
  - [ ] New measurements use condition color
  - [ ] Existing measurements maintain their colors

#### Task B.8: Condition Context Menu
- **Priority:** P1 (High)
- **Estimated Effort:** 0.5 days
- **Description:** Right-click menu for condition operations
- **Menu Items:**
  - Duplicate
  - Edit
  - Change Color
  - Move Up/Down
  - View Measurements
  - Delete
- **Acceptance Criteria:**
  - [ ] Menu appears on right-click
  - [ ] All operations work correctly
  - [ ] Optimistic updates for reorder

### Phase B Deliverables Summary

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| B.1 Panel layout refactor | P0 | 1.5 days | ⬜ |
| B.2 Template dropdown | P0 | 0.5 days | ⬜ |
| B.3 Active condition state | P0 | 1 day | ⬜ |
| B.4 Visibility toggle | P1 | 0.5 days | ⬜ |
| B.5 Number key shortcuts | P1 | 0.5 days | ⬜ |
| B.6 Properties inspector | P1 | 1 day | ⬜ |
| B.7 Canvas color wiring | P0 | 0.5 days | ⬜ |
| B.8 Context menu | P1 | 0.5 days | ⬜ |

**Total Phase B Effort:** ~6 days (2 weeks with buffer)

---

## 5. Phase C: Plan Viewer & Drawing Tools

**Duration:** 3-4 weeks
**Dependencies:** Phase A + B
**Goal:** Professional-grade drawing experience with undo/redo

### 5.1 Weeks 5-6: Core Enhancements

#### Task C.1: Implement Undo/Redo System
- **Priority:** P0 (Critical)
- **Estimated Effort:** 2 days
- **Description:** Command pattern for all canvas actions
- **Command Types:**
  - `DrawMeasurement`
  - `DeleteMeasurement`
  - `MoveMeasurement`
  - `EditMeasurement`
  - `ChangeCondition`
- **Technical Details:**
  - Stack depth: minimum 50 actions
  - Keyboard: `Ctrl+Z` undo, `Ctrl+Shift+Z` redo
  - Show toast notification on undo/redo
- **Files to Create:**
  - `frontend/src/lib/UndoManager.ts`
  - `frontend/src/hooks/useUndoRedo.ts`
- **UndoManager Interface:**
  ```typescript
  interface Command {
    execute(): void;
    undo(): void;
    description: string;
  }

  class UndoManager {
    execute(command: Command): void;
    undo(): Command | null;
    redo(): Command | null;
    canUndo(): boolean;
    canRedo(): boolean;
  }
  ```
- **Acceptance Criteria:**
  - [ ] All measurement operations are undoable
  - [ ] Stack maintains 50+ actions
  - [ ] Keyboard shortcuts work globally
  - [ ] Toast shows what was undone

#### Task C.2: Keyboard Shortcuts for Drawing Tools
- **Priority:** P0 (Critical)
- **Estimated Effort:** 1 day
- **Description:** Single-key activation for all tools
- **Shortcuts:**
  | Key | Tool |
  |-----|------|
  | `L` | Line (two-point) |
  | `P` | Polyline (multi-point) |
  | `A` | Polygon / Area |
  | `R` | Rectangle |
  | `C` | Count / Point |
  | `M` | Standalone measurement |
  | `Esc` | Cancel / deselect |
  | `Enter` | Finish polyline/polygon |
  | `Backspace` | Remove last point |
- **Files to Modify:**
  - `frontend/src/hooks/useDrawingTool.ts`
  - `frontend/src/components/workspace/TopToolbar.tsx`
- **Acceptance Criteria:**
  - [ ] All shortcuts activate correct tool
  - [ ] Visual feedback on tool activation
  - [ ] Esc properly cancels in-progress drawing

#### Task C.3: Real-Time Measurement Preview
- **Priority:** P0 (Critical)
- **Estimated Effort:** 1.5 days
- **Description:** Live measurements during drawing
- **Display Requirements:**
  - **Line/Polyline:** Running total length, segment lengths on lines
  - **Polygon/Rectangle:** Area (SF) and perimeter, dimensions on edges
  - **Count:** Incrementing count near cursor
- **Format:** Feet-inches (e.g., `14'-6"`)
- **Files to Modify:**
  - `frontend/src/components/viewer/DrawingPreview.tsx`
- **Acceptance Criteria:**
  - [ ] Live measurement updates as cursor moves
  - [ ] Correct unit formatting (ft-in)
  - [ ] Labels readable at all zoom levels

#### Task C.4: Snap-to-Endpoint System (Level 1)
- **Priority:** P0 (Critical)
- **Estimated Effort:** 1 day
- **Description:** Snap to existing measurement endpoints
- **Behavior:**
  - When drawing near an existing point, snap to it
  - Visual indicator: circle highlight when snapping
  - Snap threshold: configurable (default 10px screen space)
- **Files to Create:**
  - `frontend/src/lib/SnapEngine.ts`
  - `frontend/src/hooks/useSnap.ts`
- **Acceptance Criteria:**
  - [ ] Snaps to existing measurement points
  - [ ] Visual indicator shows when snapping
  - [ ] No gaps between adjacent measurements

### 5.2 Week 7: Measurement Interaction

#### Task C.5: Click-to-Select, Double-Click-to-Edit, Drag-to-Move
- **Priority:** P0 (Critical)
- **Estimated Effort:** 1.5 days
- **Description:** Full interaction model for existing measurements
- **Interactions:**
  - **Single click:** Select measurement, show handles
  - **Double click:** Enter edit mode with draggable vertices
  - **Drag:** Move entire measurement
- **Technical Details:**
  - Use Konva hit detection
  - Show selection handles at vertices
  - Show properties in right panel when selected
- **Files to Modify:**
  - `frontend/src/components/viewer/MeasurementShape.tsx`
  - `frontend/src/components/viewer/MeasurementLayer.tsx`
- **Acceptance Criteria:**
  - [ ] Click selects measurement
  - [ ] Double-click enters vertex edit mode
  - [ ] Drag moves entire measurement
  - [ ] Selection updates properties panel

#### Task C.6: Multi-Select
- **Priority:** P1 (High)
- **Estimated Effort:** 1 day
- **Description:** Select multiple measurements at once
- **Methods:**
  - `Ctrl+click` - Add/remove from selection
  - Drag rectangle - Area select
  - `Ctrl+A` - Select all on page
- **Operations on Multi-Select:**
  - Bulk delete
  - Bulk condition change
  - Move together
- **Files to Create:**
  - `frontend/src/components/viewer/SelectionRectangle.tsx`
- **Acceptance Criteria:**
  - [ ] Ctrl+click toggles selection
  - [ ] Drag rectangle selects enclosed items
  - [ ] Ctrl+A selects all
  - [ ] Bulk operations work on selection

#### Task C.7: Measurement Context Menu
- **Priority:** P1 (High)
- **Estimated Effort:** 0.5 days
- **Description:** Right-click menu for measurement operations
- **Menu Items:**
  - Edit
  - Delete
  - Change Condition
  - Duplicate
  - Copy to Another Sheet
- **Acceptance Criteria:**
  - [ ] Menu appears on right-click
  - [ ] All operations function correctly
  - [ ] Works for single and multi-select

#### Task C.8: Bottom Status Bar
- **Priority:** P1 (High)
- **Estimated Effort:** 1 day
- **Description:** Persistent context information
- **Components:**
  - **Scale indicator:** Shows current page scale (e.g., `1/4" = 1'-0" | 48 px/ft`)
    - Click to recalibrate
    - Red text if uncalibrated
  - **Cursor coordinates:** Real-world X,Y in feet
    - Only shows when calibrated
  - **Active tool:** Current tool name and modifier state
  - **Selection info:** Count and total quantity when selected
- **Files to Create:**
  - `frontend/src/components/workspace/StatusBar.tsx`
- **Acceptance Criteria:**
  - [ ] All information displays correctly
  - [ ] Scale click opens calibration
  - [ ] Coordinates update as cursor moves

### 5.3 Week 8: Polish

#### Task C.9: Cursor Changes Based on Context
- **Priority:** P2 (Medium)
- **Estimated Effort:** 0.5 days
- **Description:** Context-aware cursor styles
- **Cursor States:**
  - Default (no tool): Grab hand for panning
  - Drawing tool active: Crosshair in condition color
  - Hovering measurement: Pointer with highlight
  - Calibrating: Crosshair with ruler icon
- **Acceptance Criteria:**
  - [ ] Cursor changes appropriately
  - [ ] Condition color reflected in crosshair

#### Task C.10: Label Scaling
- **Priority:** P2 (Medium)
- **Estimated Effort:** 0.5 days
- **Description:** Text labels remain readable at all zoom levels
- **Technical Details:**
  - Scale text inversely to canvas zoom
  - Minimum/maximum font size bounds
  - Labels should not overlap at low zoom
- **Acceptance Criteria:**
  - [ ] Labels readable at any zoom level
  - [ ] No text overlap issues
  - [ ] Performance remains good

#### Task C.11: Shift-to-Constrain Angles
- **Priority:** P2 (Medium)
- **Estimated Effort:** 0.5 days
- **Description:** Hold Shift to constrain to 45/90-degree angles
- **Behavior:**
  - While drawing, hold Shift
  - Snaps to nearest 0°, 45°, 90°, 135°, 180°, etc.
  - Shows constraint indicator
- **Acceptance Criteria:**
  - [ ] Shift constrains angles correctly
  - [ ] Visual feedback when constrained
  - [ ] Works with all line-based tools

#### Task C.12: Complete Remaining Drawing Tools
- **Priority:** P1 (High)
- **Estimated Effort:** 1 day
- **Description:** Ensure all geometry tools are fully implemented
- **Tools to Verify/Complete:**
  - Line (two-point)
  - Polyline (multi-point linear)
  - Polygon (closed area)
  - Rectangle (quick area)
  - Circle (optional, lower priority)
- **Acceptance Criteria:**
  - [ ] All tools create correct geometry
  - [ ] Measurements calculate correctly
  - [ ] All tools support undo/redo

### Phase C Deliverables Summary

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| C.1 Undo/Redo system | P0 | 2 days | ⬜ |
| C.2 Tool keyboard shortcuts | P0 | 1 day | ⬜ |
| C.3 Live measurement preview | P0 | 1.5 days | ⬜ |
| C.4 Snap-to-endpoint | P0 | 1 day | ⬜ |
| C.5 Select/Edit/Move | P0 | 1.5 days | ⬜ |
| C.6 Multi-select | P1 | 1 day | ⬜ |
| C.7 Measurement context menu | P1 | 0.5 days | ⬜ |
| C.8 Status bar | P1 | 1 day | ⬜ |
| C.9 Cursor changes | P2 | 0.5 days | ⬜ |
| C.10 Label scaling | P2 | 0.5 days | ⬜ |
| C.11 Shift-constrain | P2 | 0.5 days | ⬜ |
| C.12 Complete drawing tools | P1 | 1 day | ⬜ |

**Total Phase C Effort:** ~12 days (3-4 weeks with buffer)

---

## 6. Phase D: AI Assist Layer

**Duration:** 2-3 weeks
**Dependencies:** Phase C
**Goal:** AI-powered assists that feel like superpowers, not a separate workflow

### 6.1 AI Features Priority

| Feature | Complexity | Backend Exists? | Priority |
|---------|------------|-----------------|----------|
| SheetScan (auto setup) | Low | Yes - fully built | P0 (Phase A) |
| Auto-Scale (detection) | Low | Yes - fully built | P0 (Phase A) |
| AutoTab (endpoint prediction) | High | Partially (AI takeoff) | P1 (Phase D) |
| QuickDraw (dimension assist) | Medium | Partially (OCR + class.) | P2 (Phase D) |
| AutoCount (find similar) | High | Not built | P3 (future) |
| Full AI Takeoff (batch) | High | Yes - fully built | P4 (power feature) |

### 6.2 Task D.1: AutoTab Backend Endpoint
- **Priority:** P1 (High)
- **Estimated Effort:** 2 days
- **Description:** Real-time endpoint prediction service
- **New API Endpoint:**
  ```
  POST /api/v1/ai/predict-next-point
  ```
- **Request Body:**
  ```json
  {
    "page_id": "uuid",
    "current_points": [{"x": 100, "y": 200}, {"x": 300, "y": 200}],
    "condition_type": "slab",
    "viewport": {"x": 0, "y": 0, "width": 1000, "height": 800},
    "scale_pixels_per_foot": 48.0
  }
  ```
- **Response:**
  ```json
  {
    "predicted_point": {"x": 500, "y": 200},
    "confidence": 0.85,
    "reasoning": "Following wall line detected in image"
  }
  ```
- **Technical Details:**
  - Crop plan image around expected area
  - Send to Gemini 2.5 Flash for speed
  - Target latency: < 500ms
- **Files to Create:**
  - `backend/app/services/ai_predict.py`
  - `backend/app/api/routes/ai_predict.py`
- **Acceptance Criteria:**
  - [ ] Endpoint returns predictions
  - [ ] Latency under 800ms consistently
  - [ ] Handles edge cases gracefully

### 6.3 Task D.2: AutoTab Frontend UX
- **Priority:** P1 (High)
- **Estimated Effort:** 2 days
- **Description:** Ghost point and Tab/Escape accept/reject
- **Workflow:**
  1. User places 2+ points on polyline/polygon
  2. System fires prediction request
  3. Ghost point appears at predicted location
  4. Press `Tab` to accept → point added, next prediction triggered
  5. Press `Escape` to dismiss → continue manually
  6. Click elsewhere → overrides prediction
- **Visual Elements:**
  - Semi-transparent circle at predicted location
  - Dashed line from last point to ghost point
  - Pulsing indicator while loading
- **Files to Create:**
  - `frontend/src/components/viewer/GhostPoint.tsx`
  - `frontend/src/hooks/useAutoTab.ts`
- **Latency Budget:**
  - Image crop + encode: < 50ms
  - API round-trip: < 100ms
  - LLM inference: < 500ms
  - Response + render: < 50ms
  - **Total: < 800ms**
- **Acceptance Criteria:**
  - [ ] Ghost point appears within 1 second
  - [ ] Tab accepts and chains predictions
  - [ ] Escape dismisses cleanly
  - [ ] Manual click overrides prediction

### 6.4 Task D.3: Refactor Batch AI Takeoff
- **Priority:** P1 (High)
- **Estimated Effort:** 1.5 days
- **Description:** Full AI takeoff as inline canvas overlay
- **New Workflow:**
  1. Estimator clicks "AI Auto-Takeoff" button
  2. AI generates draft measurements for current sheet
  3. Results display on canvas in distinct style (dashed, ghost fill)
  4. Click measurement to accept (converts to solid)
  5. Press Delete to reject
- **Technical Details:**
  - Use existing AI takeoff backend
  - Display results as "draft" measurements
  - No separate review page needed
- **Files to Modify:**
  - `frontend/src/components/viewer/MeasurementLayer.tsx`
  - `frontend/src/components/workspace/TopToolbar.tsx`
- **Files to Create:**
  - `frontend/src/components/viewer/DraftMeasurementLayer.tsx`
- **Acceptance Criteria:**
  - [ ] AI takeoff runs on current sheet
  - [ ] Results display as distinct draft style
  - [ ] Accept/reject works inline
  - [ ] Accepted measurements become permanent

### 6.5 Task D.4: QuickDraw Prototype (Optional)
- **Priority:** P2 (Medium)
- **Estimated Effort:** 1.5 days
- **Description:** AI-assisted dimension detection on Q-hold
- **Behavior:**
  1. Hold `Q` key
  2. AI scans visible area for dimension callouts
  3. Clickable suggestions appear near detected elements
  4. Click suggestion to create measurement
- **Detection Types:**
  - Dimension callouts (e.g., "14'-6"" near wall)
  - Area labels (e.g., "SLAB ON GRADE")
  - Part labels (e.g., "4" CONC. SLAB")
- **Technical Details:**
  - Leverage existing OCR text blocks with positions
  - AI identifies which text is a dimension vs label
- **Acceptance Criteria:**
  - [ ] Q-hold shows overlay
  - [ ] Detected dimensions are clickable
  - [ ] Clicking creates measurement

### Phase D Deliverables Summary

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| D.1 AutoTab backend | P1 | 2 days | ⬜ |
| D.2 AutoTab frontend | P1 | 2 days | ⬜ |
| D.3 Batch AI inline | P1 | 1.5 days | ⬜ |
| D.4 QuickDraw (optional) | P2 | 1.5 days | ⬜ |

**Total Phase D Effort:** ~7 days (2-3 weeks with buffer)

---

## 7. Phase E: Export & Reporting

**Duration:** 1-2 weeks
**Dependencies:** Phase B
**Goal:** Quick export to standard formats

### 7.1 Task E.1: Export Button with Format Dropdown
- **Priority:** P0 (Critical)
- **Estimated Effort:** 0.5 days
- **Description:** Toolbar export button with format options
- **Export Formats:**
  - Export to Excel (.xlsx)
  - Export to OST (On Screen Takeoff XML)
  - Export to CSV
  - Export to PDF
- **Files to Modify:**
  - `frontend/src/components/workspace/TopToolbar.tsx`
- **Files to Create:**
  - `frontend/src/components/export/ExportDropdown.tsx`
- **Acceptance Criteria:**
  - [ ] Dropdown shows all format options
  - [ ] Each option triggers correct export
  - [ ] Loading state during export generation

### 7.2 Task E.2: Wire to Existing Export Backend
- **Priority:** P0 (Critical)
- **Estimated Effort:** 0.5 days
- **Description:** Connect UI to existing export endpoints
- **Existing Endpoints:**
  ```
  POST /projects/{id}/export/excel
  POST /projects/{id}/export/ost
  POST /projects/{id}/export/csv
  POST /projects/{id}/export/pdf
  ```
- **Acceptance Criteria:**
  - [ ] All exports trigger correct endpoint
  - [ ] Error handling for failed exports
  - [ ] Success notification with download link

### 7.3 Task E.3: Export Options Dialog
- **Priority:** P1 (High)
- **Estimated Effort:** 1 day
- **Description:** Configure export before generating
- **Options:**
  - Select sheets to include (all / specific)
  - Select conditions to include
  - Format-specific options (e.g., include thumbnails for PDF)
- **Files to Create:**
  - `frontend/src/components/export/ExportOptionsDialog.tsx`
- **Acceptance Criteria:**
  - [ ] Dialog shows relevant options
  - [ ] Options passed to export endpoint
  - [ ] Remembers last-used settings

### 7.4 Task E.4: Download Handling
- **Priority:** P0 (Critical)
- **Estimated Effort:** 0.5 days
- **Description:** Handle async export job → download
- **Workflow:**
  1. Trigger export (returns job ID)
  2. Poll for status
  3. When complete, show download link/button
  4. Auto-download or click to download
- **Technical Details:**
  - Use existing Celery job infrastructure
  - Poll status endpoint every 2 seconds
  - Show progress indicator
- **Acceptance Criteria:**
  - [ ] Export jobs tracked correctly
  - [ ] Progress shown during generation
  - [ ] Download initiates when ready

### Phase E Deliverables Summary

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| E.1 Export dropdown | P0 | 0.5 days | ⬜ |
| E.2 Wire to backend | P0 | 0.5 days | ⬜ |
| E.3 Options dialog | P1 | 1 day | ⬜ |
| E.4 Download handling | P0 | 0.5 days | ⬜ |

**Total Phase E Effort:** ~2.5 days (1-2 weeks with buffer)

---

## 8. Database & API Changes

### 8.1 New Database Fields

#### Pages Table
```sql
ALTER TABLE pages ADD COLUMN display_name VARCHAR(200);
ALTER TABLE pages ADD COLUMN display_order INTEGER;
ALTER TABLE pages ADD COLUMN group_name VARCHAR(100);
ALTER TABLE pages ADD COLUMN is_relevant BOOLEAN DEFAULT true;
```

#### Conditions Table
```sql
ALTER TABLE conditions ADD COLUMN is_visible BOOLEAN DEFAULT true;
```

### 8.2 New API Endpoints

| Method | Endpoint | Purpose | Phase |
|--------|----------|---------|-------|
| PUT | `/pages/{id}/display` | Update display_name, display_order, group | A |
| PUT | `/pages/{id}/relevance` | Toggle is_relevant | A |
| POST | `/ai/predict-next-point` | AutoTab prediction | D |
| GET | `/projects/{id}/sheets` | Aggregated sheet tree data | A |

### 8.3 API Modifications

| Endpoint | Change |
|----------|--------|
| `GET /documents/{id}/pages` | Add `?include=classification,scale` query param |
| `PUT /conditions/{id}` | Add `is_visible` to schema |

---

## 9. Dependencies & Prerequisites

### 9.1 New NPM Packages

| Package | Purpose | Priority |
|---------|---------|----------|
| `react-resizable-panels` | Resizable three-panel layout | Required |
| `zustand` | Global state management | Recommended |
| `react-hotkeys-hook` | Keyboard shortcut management | Already installed |
| `@dnd-kit/core` | Drag-and-drop for reorder | Already installed |
| `cmdk` | Command palette (optional) | Nice-to-have |
| `react-virtualized` | Virtualized lists for large sheet sets | If > 100 sheets |

### 9.2 Backend Prerequisites

- [ ] Google Cloud Vision API configured (existing)
- [ ] Gemini 2.5 Flash API access for AutoTab
- [ ] Celery workers running for export jobs

### 9.3 Existing Components to Refactor

| Component | Current State | Refactor Needed |
|-----------|--------------|-----------------|
| `DocumentPages` | Flat page list | Replace with SheetTree |
| `PageBrowser` | Separate page view | Remove, merge into workspace |
| `ConditionPanel` | Basic list | Three-section layout |
| `PlanViewer` | Basic Konva setup | Add snap, undo, cursors |
| `MeasurementLayer` | Renders measurements | Add selection, edit modes |
| `useDrawingTool` | Basic drawing | Add command pattern, shortcuts |

---

## 10. Risk Assessment

### 10.1 Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Undo/Redo complexity | Medium | High | Start simple, iterate. Focus on core operations first. |
| AutoTab latency | Medium | High | Pre-fetch predictions, use fastest LLM model, degrade gracefully. |
| Konva performance with many measurements | Low | Medium | Use virtualization, limit visible elements, optimize hit detection. |
| State management complexity | Medium | Medium | Use Zustand with clear separation. Document state shape. |

### 10.2 Timeline Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Phase A takes longer due to layout complexity | Medium | Medium | Start with simple layout, add resizing later if needed. |
| AutoTab backend requires more tuning | High | Medium | Treat as P1, not blocking Phase C completion. |
| Integration issues between phases | Medium | Medium | Ensure each phase has clear API contracts. |

### 10.3 UX Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Keyboard shortcuts conflict with browser | Low | Low | Test thoroughly, use standard patterns. |
| Learning curve for new UI | Medium | Medium | Provide keyboard shortcut help (? key), maintain familiar patterns. |
| AutoTab predictions annoy more than help | Medium | High | Make opt-in, easy to dismiss, configurable sensitivity. |

---

## 11. Success Criteria

### 11.1 Phase A: Sheet Manager

- [ ] Estimator can upload 50-page plan set and see organized sheets within 60 seconds
- [ ] Estimator can navigate between sheets using keyboard only
- [ ] Batch scale apply works on multi-selected sheets
- [ ] Sheet search finds text across all pages

### 11.2 Phase B: Conditions

- [ ] Estimator can create condition from template in under 3 seconds (two clicks)
- [ ] Switching conditions via number keys feels instant
- [ ] Running totals update in real-time as measurements are added

### 11.3 Phase C: Drawing

- [ ] Undo/redo works reliably for at least 50 actions
- [ ] Snap-to-endpoint prevents gaps between adjacent measurements
- [ ] Real-time measurement preview shows accurate feet-inches during drawing
- [ ] An estimator familiar with PlanSwift/Bluebeam finds the tool intuitive

### 11.4 Phase D: AI Assists

- [ ] AutoTab prediction appears in under 1 second
- [ ] Tab-Tab-Tab chaining works to traverse a straight wall in seconds
- [ ] AI suggestions are visually distinct from user-placed measurements
- [ ] No AI suggestion is ever applied without explicit human action

### 11.5 Phase E: Export

- [ ] One-click export to Excel works correctly
- [ ] Export options dialog allows sheet/condition selection
- [ ] Download initiates automatically when export completes

### 11.6 Overall

- [ ] Estimator can complete takeoff for simple slab project (10 sheets) in under 30 minutes
- [ ] Tool feels faster than On Screen Takeoff for repetitive concrete measurements
- [ ] Zero data loss: all measurements persist correctly, undo/redo is reliable

---

## 12. Appendix: Complete Keyboard Shortcut Map

### 12.1 Drawing Tools

| Key | Action | Context |
|-----|--------|---------|
| `L` | Line tool | Canvas focused |
| `P` | Polyline tool | Canvas focused |
| `A` | Polygon / Area tool | Canvas focused |
| `R` | Rectangle tool | Canvas focused |
| `C` | Count / Point tool | Canvas focused |
| `M` | Measurement tool (no condition) | Canvas focused |
| `Escape` | Cancel / deselect tool | Always |
| `Enter` | Finish polyline/polygon | While drawing |
| `Double-click` | Finish polyline/polygon | While drawing |
| `Backspace` | Remove last point | While drawing |
| `Tab` | Accept AI prediction (AutoTab) | During AI-assisted draw |

### 12.2 Navigation

| Key | Action | Context |
|-----|--------|---------|
| `Scroll wheel` | Zoom in/out | Canvas focused |
| `Middle-click drag` | Pan | Canvas focused |
| `Right-click drag` | Pan (alternative) | Canvas focused |
| `Home` | Zoom to fit page | Canvas focused |
| `Ctrl+0` | Zoom to 100% | Canvas focused |
| `Page Up` | Previous sheet | Always |
| `Page Down` | Next sheet | Always |
| `Ctrl+G` | Go to sheet (opens search) | Always |

### 12.3 Editing

| Key | Action | Context |
|-----|--------|---------|
| `Ctrl+Z` | Undo | Always |
| `Ctrl+Shift+Z` / `Ctrl+Y` | Redo | Always |
| `Delete` / `Backspace` | Delete selected measurement(s) | Measurement selected |
| `Ctrl+C` | Copy measurement | Measurement selected |
| `Ctrl+V` | Paste measurement | After copy |
| `Ctrl+A` | Select all measurements on page | Canvas focused |

### 12.4 Conditions

| Key | Action | Context |
|-----|--------|---------|
| `1-9` | Select condition by position | Always |
| `Ctrl+N` | New condition | Always |
| `Ctrl+D` | Duplicate selected condition | Condition selected |
| `V` | Toggle condition visibility | Condition selected |
| `Ctrl+Shift+V` | Toggle ALL conditions visibility | Always |

### 12.5 General

| Key | Action | Context |
|-----|--------|---------|
| `Ctrl+S` | Save (auto-saves, but feels right) | Always |
| `Ctrl+E` | Export dialog | Always |
| `Ctrl+F` | Search sheets / text | Always |
| `?` | Show keyboard shortcuts help | Always |
| `Q` (hold) | QuickDraw AI overlay | Canvas focused |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | February 2026 | Claude | Initial implementation plan based on spec |

---

*This implementation plan is designed to be executed sequentially through the phases, with each phase building upon the previous. Adjust timelines and priorities based on team capacity and emerging requirements.*
