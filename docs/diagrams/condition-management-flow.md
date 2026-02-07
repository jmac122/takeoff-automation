# Condition Management Flow

## Overview

Diagrams showing the condition lifecycle from creation through measurement to export, including the data flow between frontend components, hooks, and backend APIs.

## Condition Lifecycle

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   Template   │      │   Create     │      │   Active     │      │   Export     │
│   Selection  │─────►│   Condition  │─────►│   Use        │─────►│   / Report   │
└──────────────┘      └──────────────┘      └──────────────┘      └──────────────┘
                                                   │
                                            ┌──────┴──────┐
                                            ▼             ▼
                                      ┌──────────┐ ┌──────────┐
                                      │  Draw    │ │  Toggle  │
                                      │ Measure- │ │ Visibility│
                                      │  ments   │ │  / Edit  │
                                      └──────────┘ └──────────┘
```

## Create from Template Flow

```
User clicks "Add Condition"
     │
     ▼
QuickCreateBar opens dropdown
     │
     ▼
Template list loaded via useConditionTemplates()
  → GET /condition-templates
     │
     ▼
User clicks a template (e.g., "4\" SOG")
     │
     ▼
useCreateConditionFromTemplate.mutate(templateName)
  → POST /projects/{id}/conditions/from-template
     │
     ▼
Backend creates condition with template values
  - Locks project row (prevents sort_order race)
  - Assigns sort_order = max + 1
  - Returns ConditionResponse
     │
     ▼
React Query invalidates ['conditions', projectId]
     │
     ▼
ConditionList re-renders with new condition
     │
     ▼
onCreated callback sets new condition as active
  → workspaceStore.setActiveCondition(conditionId)
```

## Selection and Drawing Flow

```
ConditionList                    workspaceStore              CenterCanvas
     │                               │                           │
     │  Click condition row          │                           │
     │──────────────────────────────►│                           │
     │  setActiveCondition(id)       │                           │
     │                               │                           │
     │  User selects drawing tool    │                           │
     │  (e.g., polygon)             │                           │
     │──────────────────────────────►│                           │
     │  setActiveTool('polygon')     │                           │
     │                               │                           │
     │  VALIDATION CHECK:            │                           │
     │  activeConditionId != null?   │                           │
     │  ├── YES: tool is set         │                           │
     │  └── NO: toolRejectionMessage │                           │
     │          = "Select a          │                           │
     │           condition first"    │                           │
     │                               │                           │
     │                               │  User draws on canvas     │
     │                               │──────────────────────────►│
     │                               │  addCurrentPoint(x,y)     │
     │                               │  isDrawing = true         │
     │                               │                           │
     │                               │  Drawing completed        │
     │                               │◄──────────────────────────│
     │                               │                           │
     │  Measurement created:         │                           │
     │  POST /measurements           │                           │
     │  { condition_id, page_id,     │                           │
     │    geometry_type, geometry_data│                           │
     │    quantity, unit }           │                           │
     │                               │                           │
```

## Keyboard Shortcut Flow

```
Window keydown event
     │
     ├── Key '1'-'9' (no modifiers)
     │   └── Select condition at index (key-1)
     │       → setActiveCondition(conditions[index].id)
     │
     ├── Key 'V' (no modifiers, active condition)
     │   └── Toggle visibility
     │       → useUpdateCondition.mutate({
     │           conditionId, data: { is_visible: !current }
     │         })
     │       → Invalidates ['conditions'] cache
     │
     ├── Ctrl/Cmd + 'D' (active condition)
     │   └── Duplicate condition
     │       → useDuplicateCondition.mutate(conditionId)
     │       → POST /conditions/{id}/duplicate
     │       → Creates "Copy of {name}" with new sort_order
     │
     ├── 'Delete' (active condition)
     │   └── Show delete confirmation dialog
     │       → User clicks "Delete" button
     │       → useDeleteCondition.mutate(conditionId)
     │       → DELETE /conditions/{id}
     │       → Cascades: deletes all measurements
     │       → setActiveCondition(null)
     │       → setActiveTool('select')
     │
     └── 'Escape'
         └── Reset all drawing state
             → escapeAll()
```

## Reorder Flow

```
Context Menu: "Move Up" / "Move Down"
     │
     ▼
handleMoveUp(condition) / handleMoveDown(condition)
     │
     ▼
Swap adjacent IDs in local array
  [A, B, C] → [B, A, C]  (move A down)
     │
     ▼
useReorderConditions.mutate(newIdOrder)
  → PUT /projects/{id}/conditions/reorder
    { condition_ids: ["B", "A", "C"] }
     │
     ▼
Backend validates:
  ├── All IDs present? (no partial reorders)
  ├── No duplicate IDs?
  └── Locks project row
     │
     ▼
Assigns sort_order: B=0, A=1, C=2
     │
     ▼
React Query invalidates ['conditions']
     │
     ▼
ConditionList re-renders in new order
```

## Visibility Toggle Flow

```
ConditionList: Click Eye icon
     │
     ▼
handleToggleVisibility(condition)
     │
     ▼
useUpdateCondition.mutate({
  conditionId: condition.id,
  data: { is_visible: !condition.is_visible }
})
     │
     ▼
PUT /conditions/{id}
{ is_visible: false }
     │
     ▼
Backend updates condition row
     │
     ▼
React Query invalidates ['conditions']
     │
     ▼
ConditionList re-renders:
  - Hidden condition: 50% opacity
  - EyeOff icon instead of Eye
     │
     ▼
Canvas (Phase C wiring):
  - Hidden conditions' measurements not rendered
```

## Data Flow: React Query + Zustand

```
┌─────────────────────────────────────────────────────────────┐
│                     React Query Cache                        │
│                                                             │
│  ['conditions', projectId] ──► { conditions: [...], total } │
│  ['condition-templates']   ──► [...]                        │
│                                                             │
│  Mutations invalidate cache on success:                     │
│  - useCreateCondition       → invalidates ['conditions']    │
│  - useCreateFromTemplate    → invalidates ['conditions']    │
│  - useUpdateCondition       → invalidates ['conditions']    │
│  - useDeleteCondition       → invalidates ['conditions']    │
│  - useDuplicateCondition    → invalidates ['conditions']    │
│  - useReorderConditions     → invalidates ['conditions']    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼ Components read server data
┌─────────────────────────────────────────────────────────────┐
│                   Zustand Store                              │
│                                                             │
│  activeConditionId ──► Which condition is selected           │
│  activeTool        ──► What drawing tool is active           │
│  focusRegion       ──► Keyboard shortcut scoping             │
│                                                             │
│  These are purely UI state — not duplicated server data     │
└─────────────────────────────────────────────────────────────┘
```
