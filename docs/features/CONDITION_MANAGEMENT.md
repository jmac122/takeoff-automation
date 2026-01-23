# Condition Management (Phase 3B)

Condition management organizes takeoff line items, their measurement types, and the
visual styling used in the viewer. Phase 3B adds templates, filtering, duplication,
and drag-and-drop ordering with an upgraded UI for faster takeoff setup.

## Goals
- Provide reusable condition templates for common concrete scopes
- Allow users to create, edit, duplicate, and reorder conditions
- Show grouped condition totals and measurement counts in the viewer
- Keep condition data consistent across backend and frontend types

## Core Data
Conditions track:
- Name, scope, category, measurement type, and unit
- Visual styling (color, line width, fill opacity)
- Optional depth or thickness for volume estimation
- Sort order for display sequencing

Templates define the same fields with defaults for line width and fill opacity.

## Backend API

### Endpoints
- `GET /condition-templates`  
  List available templates. Optional query params: `scope`, `category`.
- `GET /projects/{project_id}/conditions`  
  List project conditions. Optional query params: `scope`, `category`.
- `POST /projects/{project_id}/conditions`  
  Create a custom condition; sort order auto-increments.
- `POST /projects/{project_id}/conditions/from-template`  
  Create a condition from a template (`template_name` query param).
- `GET /conditions/{condition_id}`  
  Returns condition details with measurement summaries.
- `PUT /conditions/{condition_id}`  
  Update a condition.
- `DELETE /conditions/{condition_id}`  
  Delete a condition.
- `POST /conditions/{condition_id}/duplicate`  
  Duplicate a condition (measurements excluded).
- `PUT /projects/{project_id}/conditions/reorder`  
  Persist a new sort order (ordered list of IDs).

### Implementation Notes
- Sort order is assigned with `max(sort_order) + 1` per project.
- Reorder validates all IDs belong to the project.
- Condition detail includes measurement summaries for quick UI display.

## Frontend UX

### Conditions Panel
Located in the viewer overlay:
- Grouped by category with collapsible sections
- Drag-and-drop ordering (Dnd Kit)
- Context menu actions: Edit, Duplicate, Delete
- Totals by unit and measurement counts

### Modals
- Create Condition (template + custom tabs)
- Edit Condition (pre-filled values)

### Hooks and Types
- `useConditions` exposes list/mutations and invalidates caches on success.
- Shared type contracts in `frontend/src/types/index.ts` keep API and UI aligned.

## Templates
Concrete templates are provided across categories:
- Foundations (strip footing, spread footing, foundation wall, grade beam)
- Slabs (SOG, sidewalk)
- Paving (concrete paving, curb & gutter)
- Vertical (columns, walls)
- Miscellaneous (piers, catch basins)

## Testing
- Backend: `backend/tests/test_condition_templates.py`
- Frontend: `docker compose exec frontend npm run lint`

## Manual Verification
1. Create a project and open a page in the viewer.
2. Open Conditions panel; create from template and custom.
3. Drag to reorder and refresh to confirm persistence.
4. Duplicate and delete to verify updates and totals.
