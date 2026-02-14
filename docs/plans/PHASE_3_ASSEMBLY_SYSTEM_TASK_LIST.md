# Phase 3: Assembly System — Task Completion List

**Status**: COMPLETE
**Branch**: `claude/create-phase-1-tasks-OBEE7`
**Commit**: `133cae3`

## Summary

Phase 3 implements a full-stack Assembly System that transforms conditions (takeoff line items with measurements) into cost assemblies with formula-driven component quantities, waste factors, markup calculations, and pre-built templates.

---

## Tasks

### AS-001: Create Assembly Models ✅
**Files**: `backend/app/models/assembly.py`

- `Assembly` — one-to-one with Condition, stores cost totals, markup, lock state
- `AssemblyComponent` — line items with formula, quantity, unit cost, waste
- `AssemblyTemplate` — reusable templates with JSONB component_definitions
- `CostItem` — reference cost items (table only, CRUD deferred)
- All use `UUIDMixin` + `TimestampMixin`, cost fields use `Numeric(12,2)`

### AS-002: Add Assembly Relationship to Condition ✅
**Files**: `backend/app/models/condition.py`

- Added `Assembly` import in `TYPE_CHECKING` block
- Added one-to-one `assembly` relationship with `uselist=False`, cascade delete

### AS-003: Register Models + Create Migration ✅
**Files**: `backend/app/models/__init__.py`, `backend/app/main.py`, `backend/alembic/versions/p4q5r6s7t8u9_add_assembly_system.py`

- Registered 4 new models in `__init__.py` and `__all__`
- Added model imports in `main.py`
- Alembic migration creates tables: `assembly_templates`, `cost_items`, `assemblies`, `assembly_components`
- Indexes on `condition_id` (unique), `assembly_id`, `code`
- Down revision: `o3p4q5r6s7t8`

### AS-004: Create FormulaEngine ✅
**Files**: `backend/app/services/formula_engine.py`

- `FormulaContext` dataclass with fields: qty, depth, thickness, perimeter, count, height, width, length
- Computed properties: `depth_ft`, `thickness_ft`, `volume_cf`, `volume_cy`
- `SafeEvaluator(ast.NodeVisitor)` — whitelists safe AST node types
- `FormulaEngine` — evaluate, validate, help methods
- 12 formula presets (concrete_cy_from_sf, rebar calculations, etc.)
- Allowed functions: ceil, floor, round, min, max, abs, sqrt, pow, pi

### AS-005: Create AssemblyService ✅
**Files**: `backend/app/services/assembly_service.py`

- Assembly CRUD: create (with optional template), get, update, delete
- Component CRUD: add, update, delete, reorder
- `calculate_assembly()` — evaluates formulas, applies waste, sums costs by type
- Lock/unlock assembly
- `duplicate_assembly()` — deep copy to new condition
- `get_project_cost_summary()` — aggregate costs across project
- Singleton pattern via `get_assembly_service()`

### AS-006: Create Pydantic Schemas ✅
**Files**: `backend/app/schemas/assembly.py`

- Component: Create, Update, Response
- Assembly: Create, Update, Response, DetailResponse (with nested components)
- Template: Response
- Formula: ValidateRequest, ValidateResponse
- Project: CostSummaryResponse
- All responses use `ConfigDict(from_attributes=True)`

### AS-007: Create Assembly API Routes ✅
**Files**: `backend/app/api/routes/assemblies.py`, `backend/app/main.py`

18 endpoints:
- `GET /assembly-templates` — list templates (filtered)
- `GET /assembly-templates/{id}` — get template
- `POST /conditions/{id}/assembly` — create assembly
- `GET /conditions/{id}/assembly` — get condition's assembly
- `GET /assemblies/{id}` — get assembly by ID
- `PUT /assemblies/{id}` — update assembly
- `DELETE /assemblies/{id}` — delete assembly
- `POST /assemblies/{id}/calculate` — recalculate costs
- `POST /assemblies/{id}/lock` — lock assembly
- `POST /assemblies/{id}/unlock` — unlock assembly
- `POST /assemblies/{id}/components` — add component
- `PUT /components/{id}` — update component
- `DELETE /components/{id}` — delete component
- `PUT /assemblies/{id}/components/reorder` — reorder
- `POST /formulas/validate` — validate formula
- `GET /formulas/presets` — list presets
- `GET /formulas/help` — formula documentation
- `GET /projects/{id}/cost-summary` — project cost summary

Router registered in `main.py` with prefix `/api/v1`, tag `Assemblies`.

### AS-008: Create Seed Data ✅
**Files**: `backend/app/data/__init__.py`, `backend/app/data/assembly_templates.py`, `backend/scripts/seed_assembly_templates.py`

10 concrete assembly templates across 4 categories:
- **Slabs**: 4" Slab (WWF), 4" Slab (Rebar), 6" Heavy Duty Slab
- **Foundations**: Strip Footing 24"x12", Spread Footing 3'x3', Foundation Wall 8"x8'
- **Paving**: 4" Sidewalk, Curb & Gutter
- **Vertical**: 16"x16" Column, 8" Wall

Seed script is idempotent (skips existing by name).

### AS-009: Create Frontend Types, API Client & Hooks ✅
**Files**: `frontend/src/types/index.ts`, `frontend/src/api/assemblies.ts`, `frontend/src/hooks/useAssemblies.ts`

Types:
- `Assembly`, `AssemblyComponent`, `AssemblyDetail`, `AssemblyTemplate`
- `ProjectCostSummary`, `FormulaValidateResponse`

API client functions:
- Assembly CRUD, calculate, lock/unlock
- Component CRUD, reorder
- Template list/get
- Formula validate/presets/help
- Project cost summary

React Query hooks:
- `useConditionAssembly`, `useCreateAssembly`, `useUpdateAssembly`, `useDeleteAssembly`
- `useCalculateAssembly`, `useLockAssembly`, `useUnlockAssembly`
- `useAddComponent`, `useUpdateComponent`, `useDeleteComponent`, `useReorderComponents`
- `useAssemblyTemplates`, `useProjectCostSummary`

### AS-010: Create AssemblyPanel & RightPanel Integration ✅
**Files**: `frontend/src/components/assembly/AssemblyPanel.tsx`, `frontend/src/components/assembly/AssemblyTemplateSelector.tsx`, `frontend/src/components/workspace/RightPanel.tsx`, `frontend/src/components/conditions/ConditionContextMenu.tsx`

- `AssemblyPanel` — full assembly view with cost summary grid, components grouped by type (material/labor/equipment/subcontract/other), collapsible groups, lock/unlock/calculate/delete controls
- `AssemblyTemplateSelector` — modal with search, category grouping, template metadata
- `RightPanel` — added "Cost" tab (amber accent, shown when condition selected)
- `ConditionContextMenu` — added "Create Assembly" menu item with Calculator icon

### AS-011: Unit & Integration Tests ✅
**Files**: `backend/tests/unit/test_formula_engine.py`, `backend/tests/unit/test_assembly_service.py`, `backend/tests/integration/test_assembly_api.py`

Formula engine tests (43 tests):
- Basic formulas, computed variables, functions (ceil/floor/round/min/max/sqrt/pow/pi)
- Safety: rejects import/exec/open/eval/unknown vars/attribute access/dunder
- Edge cases: division by zero, negative qty, zero qty, large numbers
- Validation, presets, singleton, help

Assembly service tests:
- FormulaContext building from condition
- Lock enforcement (update/delete/add_component blocked when locked)

Assembly API tests:
- CRUD: create 201, duplicate 400, get, get null, get by ID, not found 404
- Delete: 204 success, 400 locked
- Calculate, lock/unlock
- Component: add 201, update, delete 204
- Formula: validate valid/invalid/with test values, presets, help
- Project cost summary

---

## Key Design Decisions

1. **One-to-one Assembly↔Condition** — unique constraint on `condition_id` FK
2. **AST-based formula safety** — `ast.parse()` + `SafeEvaluator` validates before `eval()` with `{"__builtins__": {}}`
3. **Explicit calculation trigger** — `POST /calculate` instead of auto-calc on every change
4. **CostItem CRUD deferred** — table exists for FK references but no API endpoints
5. **Template seeding is idempotent** — checks by name before inserting
6. **Condition height/width default to 0.0** — fields don't exist on Condition model yet
