# Conditions API Reference

## Overview

The Conditions API manages takeoff conditions (line items) for a project. Each condition represents a material or work item (e.g., "4\" SOG", "Strip Footing") with associated color, measurement type, unit, and styling. Conditions group measurements and track aggregate quantities.

## Endpoints

### List Condition Templates

```
GET /condition-templates
```

Returns predefined condition templates that can be used to quickly create new conditions.

**Query Parameters**:
| Parameter | Type | Required | Description |
|---|---|---|---|
| `scope` | string | No | Filter by scope (e.g., `"concrete"`) |
| `category` | string | No | Filter by category (e.g., `"slabs"`) |

**Response** `200 OK`:
```json
[
  {
    "name": "4\" SOG",
    "scope": "concrete",
    "category": "slabs",
    "measurement_type": "area",
    "unit": "SF",
    "color": "#22C55E",
    "line_width": 2,
    "fill_opacity": 0.3,
    "depth": 4,
    "thickness": null
  }
]
```

**Available Templates** (16+):

| Category | Name | Type | Unit | Color |
|---|---|---|---|---|
| Foundations | Strip Footing | linear | LF | #EF4444 |
| Foundations | Spread Footing | count | EA | #F97316 |
| Foundations | Foundation Wall | area | SF | #F59E0B |
| Foundations | Grade Beam | linear | LF | #F97316 |
| Foundations | Pier/Caisson | count | EA | #A855F7 |
| Slabs | 4" SOG | area | SF | #22C55E |
| Slabs | 6" SOG | area | SF | #16A34A |
| Slabs | Elevated Slab | area | SF | #0EA5E9 |
| Slabs | SOG Thickened Edge | linear | LF | #84CC16 |
| Paving | Sidewalk | area | SF | #D4D4D4 |
| Paving | Curb & Gutter | linear | LF | #0EA5E9 |
| Paving | Asphalt Paving | area | SF | #737373 |
| Vertical | CMU Wall | area | SF | #F59E0B |
| Vertical | Tilt-Up Panel | area | SF | #6366F1 |
| Vertical | Cast-in-Place Wall | area | SF | #EC4899 |
| Misc | Rebar | area | SF | #EF4444 |
| Misc | Misc Concrete | volume | CY | #A3A3A3 |

---

### List Project Conditions

```
GET /projects/{project_id}/conditions
```

**Query Parameters**:
| Parameter | Type | Required | Description |
|---|---|---|---|
| `scope` | string | No | Filter by scope |
| `category` | string | No | Filter by category |

**Response** `200 OK`:
```json
{
  "conditions": [
    {
      "id": "uuid",
      "project_id": "uuid",
      "name": "4\" SOG",
      "description": null,
      "scope": "concrete",
      "category": "slabs",
      "measurement_type": "area",
      "color": "#22C55E",
      "line_width": 2,
      "fill_opacity": 0.3,
      "unit": "SF",
      "depth": 4,
      "thickness": null,
      "total_quantity": 2450.0,
      "measurement_count": 5,
      "sort_order": 0,
      "is_ai_generated": false,
      "is_visible": true,
      "extra_metadata": null,
      "created_at": "2026-01-15T10:00:00Z",
      "updated_at": "2026-01-15T10:00:00Z"
    }
  ],
  "total": 1
}
```

**Notes**:
- Ordered by `sort_order ASC`, then `name ASC`

---

### Create Condition

```
POST /projects/{project_id}/conditions
```

**Status**: `201 Created`

**Request Body**:
```json
{
  "name": "4\" SOG",
  "scope": "concrete",
  "category": "slabs",
  "measurement_type": "area",
  "color": "#22C55E",
  "line_width": 2,
  "fill_opacity": 0.3,
  "unit": "SF",
  "depth": 4
}
```

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `name` | string | Yes | — | Condition name |
| `description` | string? | No | null | Optional description |
| `scope` | string | No | `"concrete"` | Scope category |
| `category` | string? | No | null | Sub-category |
| `measurement_type` | string | Yes | — | `"linear"`, `"area"`, `"volume"`, `"count"` |
| `color` | string | No | auto | Hex color code |
| `line_width` | int | No | 2 | Drawing line width (px) |
| `fill_opacity` | float | No | 0.3 | Fill opacity (0-1) |
| `unit` | string | No | auto | `"LF"`, `"SF"`, `"CY"`, `"EA"` |
| `depth` | float? | No | null | Depth in inches |
| `thickness` | float? | No | null | Thickness in inches |
| `sort_order` | int | No | auto | Position in list |
| `extra_metadata` | object? | No | null | Custom metadata |

**Notes**:
- `sort_order` is auto-assigned as `max(sort_order) + 1` if not provided
- Project row is locked during creation to prevent sort_order races

---

### Create Condition from Template

```
POST /projects/{project_id}/conditions/from-template
```

**Status**: `201 Created`

**Request Body**:
```json
{
  "template_name": "4\" SOG"
}
```

**Notes**:
- Copies all template fields (scope, category, type, unit, color, depth, thickness, etc.)
- Auto-assigns sort_order

---

### Get Condition

```
GET /projects/{project_id}/conditions/{condition_id}
```

Returns a condition with all its measurements pre-loaded. Scoped to the project to prevent IDOR access.

**Response** `200 OK`:
```json
{
  "id": "uuid",
  "name": "4\" SOG",
  "measurements": [
    {
      "id": "uuid",
      "page_id": "uuid",
      "geometry_type": "polygon",
      "geometry_data": { "points": [...] },
      "quantity": 450.0,
      "unit": "SF"
    }
  ],
  ...
}
```

---

### Update Condition

```
PUT /projects/{project_id}/conditions/{condition_id}
```

Update any condition field. All fields are optional — only provided fields are modified. Scoped to the project to prevent IDOR access.

**Request Body**:
```json
{
  "name": "Updated Name",
  "color": "#FF0000",
  "is_visible": false
}
```

| Field | Type | Description |
|---|---|---|
| `name` | string | Condition name |
| `description` | string? | Description |
| `scope` | string | Scope |
| `category` | string? | Category |
| `measurement_type` | string | Measurement type |
| `color` | string | Hex color |
| `line_width` | int | Line width (px) |
| `fill_opacity` | float | Fill opacity (0-1) |
| `unit` | string | Unit |
| `depth` | float? | Depth (inches) |
| `thickness` | float? | Thickness (inches) |
| `is_visible` | bool | Whether measurements are shown on canvas |
| `extra_metadata` | object? | Custom metadata |

**Notes**:
- `is_visible` controls whether the condition's measurements are rendered on the canvas
- Default value for `is_visible` is `true`

---

### Delete Condition

```
DELETE /projects/{project_id}/conditions/{condition_id}
```

**Status**: `204 No Content`

**Notes**:
- Cascades to delete all associated measurements
- Irreversible operation

---

### Duplicate Condition

```
POST /projects/{project_id}/conditions/{condition_id}/duplicate
```

**Status**: `201 Created`

Creates a copy of the condition **without** its measurements.

**Notes**:
- New name is prefixed with "Copy of "
- New sort_order is assigned as max + 1
- All other fields are copied from the original, including `is_visible`

---

### Reorder Conditions

```
PUT /projects/{project_id}/conditions/reorder
```

Set the order of all conditions in a project.

**Request Body**:
```json
{
  "condition_ids": ["uuid-3", "uuid-1", "uuid-2"]
}
```

**Notes**:
- **All** condition IDs must be provided (no partial reorders)
- Duplicate IDs are rejected with `422`
- Missing IDs are rejected with `400`
- Project row is locked to prevent concurrent reorder races
- `sort_order` is assigned sequentially (0, 1, 2, ...)

**Error Responses**:
| Status | Description |
|---|---|
| `400` | Missing condition IDs in the list |
| `404` | Project not found |
| `422` | Duplicate IDs in the list |

## Condition Response Schema

| Field | Type | Description |
|---|---|---|
| `id` | UUID | Condition ID |
| `project_id` | UUID | Parent project ID |
| `name` | string | Display name |
| `description` | string? | Optional description |
| `scope` | string | Scope (e.g., "concrete") |
| `category` | string? | Category (e.g., "slabs") |
| `measurement_type` | string | `"linear"`, `"area"`, `"volume"`, `"count"` |
| `color` | string | Hex color code |
| `line_width` | int | Drawing line width in pixels |
| `fill_opacity` | float | Fill opacity (0.0 - 1.0) |
| `unit` | string | Unit abbreviation (`LF`, `SF`, `CY`, `EA`) |
| `depth` | float? | Depth in inches |
| `thickness` | float? | Thickness in inches |
| `total_quantity` | float | Aggregate quantity across measurements |
| `measurement_count` | int | Number of measurements |
| `sort_order` | int | Position in condition list |
| `is_ai_generated` | bool | Whether created by AI takeoff |
| `is_visible` | bool | Whether measurements are shown on canvas |
| `extra_metadata` | object? | Custom metadata JSON |
| `created_at` | datetime | Creation timestamp |
| `updated_at` | datetime | Last update timestamp |
