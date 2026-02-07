# Condition Panel (Phase B)

## Overview

The Condition Panel is the right-side panel in the workspace layout. It provides a three-section interface for creating, managing, and inspecting takeoff conditions. Conditions are the line items of a construction takeoff — each represents a material or work item (e.g., "4\" SOG", "Strip Footing") with associated measurements.

## Architecture

The panel follows a three-section layout:

```
┌─────────────────────────────────┐
│  Quick Create Bar               │
│  [+ Add Condition ▼]            │
├─────────────────────────────────┤
│  Condition List (scrollable)    │
│                                 │
│  ● 4" SOG          2.5k SF 👁 1│
│  ● Strip Footing    320 LF 👁 2│
│  ● Spread Footing     8 EA 👁 3│
│                                 │
├─────────────────────────────────┤
│  Properties Inspector           │
│                                 │
│  ● 4" SOG           [✏] [🗑]   │
│  Type:         Area             │
│  Unit:         Square Feet      │
│  Depth:        4"               │
│  Total:        2,450.0 SF       │
│  Measurements: 5                │
│  Line Width:   2px              │
│  Fill Opacity: 30%              │
│                                 │
│  ▸ Per-sheet breakdown          │
└─────────────────────────────────┘
```

## Components

### QuickCreateBar
**File**: `frontend/src/components/conditions/QuickCreateBar.tsx`

Provides a button to create new conditions from predefined templates. Clicking opens a dropdown grouped by category.

**Props**:
```typescript
interface QuickCreateBarProps {
  projectId: string;
  onCreated?: (conditionId: string) => void;
}
```

**Template Categories**: Foundations, Slabs, Paving, Vertical, Miscellaneous

### ConditionList
**File**: `frontend/src/components/conditions/ConditionList.tsx`

Renders a scrollable list of all conditions for the project. Each row shows:
- Color dot (matching the condition's drawing color)
- Name and measurement count
- Total quantity with unit abbreviation
- Visibility toggle (Eye/EyeOff icons)
- Keyboard shortcut number (1-9)

**Props**:
```typescript
interface ConditionListProps {
  conditions: Condition[];
  projectId: string;
  onContextMenu?: (e: React.MouseEvent, condition: Condition) => void;
}
```

**Quantity Formatting**:
| Value | Display |
|---|---|
| 0 | `0` |
| 1-99.9 | `XX.X` (one decimal) |
| 100-999 | `XXX` (no decimal) |
| 1000+ | `X.Xk` (thousands) |

**States**:
- Active condition: Blue left border, blue background tint
- Hidden condition: 50% opacity
- Empty state: "No conditions yet" placeholder

### PropertiesInspector
**File**: `frontend/src/components/conditions/PropertiesInspector.tsx`

Shows detailed properties for the active (selected) condition. Displays nothing meaningful when no condition is selected.

**Properties Shown**:
- Type (Linear, Area, Volume, Count)
- Unit (Linear Feet, Square Feet, Cubic Yards, Each)
- Depth (if applicable)
- Thickness (if applicable)
- Total quantity with unit
- Measurement count
- Line width (px)
- Fill opacity (%)
- Per-sheet breakdown (expandable, placeholder)

### ConditionContextMenu
**File**: `frontend/src/components/conditions/ConditionContextMenu.tsx`

Right-click context menu for condition rows with these actions:

| Action | Icon | Description |
|---|---|---|
| Edit | Pencil | Open edit modal (placeholder) |
| Duplicate | Copy | Create copy with "Copy of" prefix |
| Delete | Trash2 | Delete with confirmation dialog |
| Move Up | ArrowUp | Move earlier in sort order |
| Move Down | ArrowDown | Move later in sort order |
| Toggle Visibility | Eye/EyeOff | Show/hide condition measurements |

### ConditionPanel (Orchestrator)
**File**: `frontend/src/components/conditions/ConditionPanel.tsx`

Ties all sub-components together and manages:
- Active condition selection/deselection
- Keyboard shortcuts
- Context menu state
- Delete confirmation dialog
- Condition reordering
- Visibility toggling

## Keyboard Shortcuts

| Key | Requires | Action |
|---|---|---|
| `1`-`9` | Any | Select condition by list position |
| `V` | Active condition | Toggle visibility of active condition |
| `Ctrl+D` / `Cmd+D` | Active condition | Duplicate active condition |
| `Delete` | Active condition | Open delete confirmation |

Shortcuts are disabled when `focusRegion` is `'dialog'` or `'search'`.

## Visibility Toggle

The `is_visible` field on conditions controls whether their measurements are drawn on the canvas:

- **Backend**: `is_visible` column on `conditions` table, default `true`
- **API**: Updated via `PUT /conditions/{id}` with `{ is_visible: false }`
- **Frontend**: Eye/EyeOff icon toggles, 50% opacity on hidden conditions
- **Canvas**: (Wired in Phase C) Hidden conditions' measurements are not rendered

### Migration
Added via Alembic migration `n2o3p4q5r6s7_add_is_visible_to_conditions.py`:
```python
op.add_column('conditions', sa.Column('is_visible', sa.Boolean(), server_default='true', nullable=False))
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/condition-templates` | List predefined templates |
| `GET` | `/projects/{id}/conditions` | List project conditions |
| `POST` | `/projects/{id}/conditions` | Create new condition |
| `POST` | `/projects/{id}/conditions/from-template` | Create from template |
| `GET` | `/conditions/{id}` | Get condition with measurements |
| `PUT` | `/conditions/{id}` | Update condition (including `is_visible`) |
| `DELETE` | `/conditions/{id}` | Delete condition + measurements |
| `POST` | `/conditions/{id}/duplicate` | Duplicate without measurements |
| `PUT` | `/projects/{id}/conditions/reorder` | Reorder by ID list |

See [CONDITIONS_API.md](../api/CONDITIONS_API.md) for full API reference.

## Concrete Templates

16+ predefined templates across 5 categories:

| Category | Templates | Type | Unit |
|---|---|---|---|
| Foundations | Strip Footing, Spread Footing, Foundation Wall, Grade Beam, Pier/Caisson | Linear/Count/Area | LF/EA/SF |
| Slabs | 4" SOG, 6" SOG, Elevated Slab, SOG Thickened Edge | Area/Linear | SF/LF |
| Paving | Sidewalk, Curb & Gutter, Asphalt Paving | Area/Linear | SF/LF |
| Vertical | CMU Wall, Tilt-Up Panel, Cast-in-Place Wall | Area | SF |
| Misc | Rebar, Misc Concrete | Area/Volume | SF/CY |

Each template includes: scope, category, measurement_type, unit, color, line_width, fill_opacity, depth/thickness.

## Testing

### Frontend Tests (`ConditionPanel.test.tsx`)
13 tests covering:
- Three-section layout rendering
- Condition list rendering with data
- Empty state display
- Click to select/deselect conditions
- Properties inspector display
- Visibility toggle rendering
- Shortcut number display
- Number key condition selection
- Delete key confirmation dialog
- Right-click context menu
- Template dropdown opening
- Quantity display formatting

### Backend Tests (`test_condition_visibility.py`)
7 tests covering:
- Model `is_visible` field existence
- Response schema includes `is_visible`
- Default value is `true`
- Update endpoint sets `is_visible`
- Update endpoint treats `is_visible` as optional
- Update preserves other fields when toggling visibility

## Key Files

| File | Purpose |
|---|---|
| `frontend/src/components/conditions/ConditionPanel.tsx` | Main orchestrator |
| `frontend/src/components/conditions/QuickCreateBar.tsx` | Template creation |
| `frontend/src/components/conditions/ConditionList.tsx` | Condition list |
| `frontend/src/components/conditions/PropertiesInspector.tsx` | Property display |
| `frontend/src/components/conditions/ConditionContextMenu.tsx` | Right-click menu |
| `frontend/src/hooks/useConditions.ts` | React Query hooks |
| `frontend/src/api/conditions.ts` | API client |
| `backend/app/api/routes/conditions.py` | API routes |
| `backend/app/models/condition.py` | Database model |
| `backend/app/schemas/condition.py` | Request/response schemas |
