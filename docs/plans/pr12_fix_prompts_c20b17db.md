---
name: PR12 Fix Prompts
overview: "Create 3 optimized LLM prompts to resolve all 13 unique PR review comments from PR #12, grouped by file locality and domain context for minimal token cost and maximal fix accuracy."
todos:
  - id: prompt-1
    content: "Prompt 1: Fix 5 issues in backend API routes (takeoff.py, documents.py, measurements.py, assemblies.py)"
    status: pending
  - id: prompt-2
    content: "Prompt 2: Fix 5 issues in backend services + migration (assembly_service.py, ai_predict_point.py, orchestrator.py, assembly migration, assembly model)"
    status: pending
  - id: prompt-3
    content: "Prompt 3: Fix 3 issues in review stats, STATUS.md documentation, and frontend console.log cleanup"
    status: pending
isProject: false
---

# PR #12 Comment Resolution: 3 Optimized LLM Prompts

## Comment Inventory (13 unique issues after dedup)

After analyzing all 17 raw comments (10 Gemini, 7 Cursor Bugbot) and deduplicating overlaps:

**HIGH severity (3):**

- C1: `metadata` reserved keyword in assembly migration (3 tables)
- C2: AutoTab endpoint uses non-existent Page model attributes + filesystem access instead of MinIO + sync I/O in async function
- C3: N+1 revision chain queries (while loops instead of CTE)

**MEDIUM severity (9):**

- C4: Brittle split measurement lookup via notes string
- C5: FormulaContext hardcodes count/perimeter/height/width/length to zero
- C6: Boolean `== True` idiom in assemblies.py
- C7: STATUS.md API route documentation has multiple discrepancies
- C8: Debug console.log in DrawingPreviewLayer.tsx
- C9: Point normalization zeroes coordinates in ai_predict_point.py
- C10: Auto count skips measurement_count update on condition
- C11: Revision chain crashes when multiple docs supersede same parent
- C12: Review stats approved count overlaps with modified count

**LOW severity (1):**

- C13: Hybrid detection source labels all matches identically

---

## Prompt Grouping Strategy

Comments are grouped by **file locality** and **shared domain context** to minimize redundant file reads and maximize the ratio of fixes per token spent.

- **Prompt 1** (5 issues) -- **Claude Opus 4 (thinking)**: All API route-layer files. Needs Opus-level reasoning for the recursive CTE refactor and multi-attribute AutoTab endpoint rewrite spanning 4 files. Thinking mode essential for correct SQL construction.
- **Prompt 2** (5 issues) -- **Claude Sonnet 4 (thinking)**: All service-layer + migration files. Each fix is well-scoped with explicit before/after code, but source labeling touches multiple methods and migration renames need careful ORM cross-referencing. Thinking mode ensures aggregate pattern is applied correctly without Opus cost.
- **Prompt 3** (3 issues) -- **Claude Sonnet 4 (non-thinking)**: Review stats + STATUS.md + frontend cleanup. Single SQL tweak, mechanical doc table updates, and trivial console.log removal. No deep reasoning needed -- speed and cost efficiency prioritized.

---

## Prompt 1: Backend API Routes (5 issues) -- Claude Opus 4 (thinking)

**Target files to modify:**

- `backend/app/api/routes/takeoff.py` (C2)
- `backend/app/api/routes/documents.py` (C3, C11)
- `backend/app/api/routes/measurements.py` (C4)
- `backend/app/api/routes/assemblies.py` (C6)

**Context files to read (do not modify):**

- `backend/app/models/page.py` -- Page model has `image_key` (not `image_path`), `width`/`height` (not `image_width`/`image_height`)
- `backend/app/models/document.py` -- Document model `supersedes_document_id` FK, no unique constraint
- `backend/app/workers/auto_count_tasks.py` lines 82-90 -- example of `get_storage_service().download_file(page.image_key)` pattern
- `backend/app/services/geometry_adjuster.py` -- `adjust_measurement` service that should return split measurement ID

### Prompt text:

SYSTEM: You are a senior Python backend engineer. Apply exactly the fixes described below. Read each target file fully before editing. Do NOT modify files not listed. After all edits, verify no import errors or linter issues.

### TASK: Fix 5 PR review comments in backend API route files for a FastAPI + SQLAlchemy async application.

READ FIRST (context, do not modify):

- backend/app/models/page.py — Page model. Key fields: `image_key: Mapped[str]` (MinIO storage key), `width: Mapped[int]`, `height: Mapped[int]`. NOTE: There is NO `image_path`, `image_width`, or `image_height` attribute.
- backend/app/models/document.py — Document model. `supersedes_document_id` is a nullable FK to documents.id with NO unique constraint. Multiple documents can supersede the same parent.
- backend/app/workers/auto_count_tasks.py lines 82-90 — Reference pattern for MinIO image download: `storage = get_storage_service(); page_image_bytes = storage.download_file(page.image_key)`
- backend/app/services/geometry_adjuster.py — Contains `adjust_measurement()` method

### FIX 1 — backend/app/api/routes/takeoff.py (predict_next_point endpoint, ~line 465-506):

The `predict_next_point` endpoint has 3 compounding bugs:
(a) References `page_data.page.image_path` — does not exist. Correct attribute: `page_data.page.image_key`
(b) References `page_data.page.image_width` and `page_data.page.image_height` — do not exist. Correct attributes: `page_data.page.width` and `page_data.page.height`
(c) Reads image via `pathlib.Path(...).read_bytes()` — images are in MinIO, not local filesystem. Must use `get_storage_service().download_file(image_key)`.
(d) The sync file I/O would block the asyncio event loop even if paths were correct.

Required change: Replace the image loading block (lines ~480-490) with:

```python
from app.services.storage import get_storage_service
image_key = page_data.page.image_key
if not image_key:
    return PredictNextPointResponse(
        prediction=None,
        latency_ms=round((time.monotonic() - start) * 1000, 1),
    )
storage = get_storage_service()
image_bytes = storage.download_file(image_key)
```

Also fix `image_width=page_data.page.width or 1` and `image_height=page_data.page.height or 1`.
Remove the `import pathlib` line.

### FIX 2 — backend/app/api/routes/documents.py (get_revision_chain endpoint, ~line 380-430):

Replace the two while-loop N+1 queries (backward walk + forward walk) with a single recursive CTE query. The CTE should:

1. Anchor: select the document with id = document_id
2. Recurse backward: join on Document.supersedes_document_id = cte.c.id
3. Recurse forward: join on Document.id where supersedes_document_id = cte.c.id
4. Return all chain documents ordered by created_at ASC

If a full recursive CTE is complex, an acceptable alternative: keep the while loops but add `.limit(1)` or use `scalars().first()` instead of `scalar_one_or_none()` for the forward walk query.

### FIX 3 — backend/app/api/routes/documents.py (same function, forward walk ~line 410):

The forward walk uses `scalar_one_or_none()`. Since `supersedes_document_id` has no unique constraint, multiple documents can supersede the same parent. `scalar_one_or_none()` raises `MultipleResultsFound` in this case, causing an unhandled 500.
Change `result.scalar_one_or_none()` to `result.scalars().first()` in the forward walk.
NOTE: If you implemented the CTE in Fix 2, this is already resolved.

### FIX 4 — backend/app/api/routes/measurements.py (~line 272-286):

The split action finds the new measurement by querying `Measurement.notes == f"Split from {measurement_id}"`. This is brittle.
Change: Make `adjust_measurement` return a tuple or dict that includes the new measurement ID for split operations. Update the route to extract `created_id` from the service response instead of querying by notes.
If modifying the service interface is too invasive, an acceptable minimal fix: after the split, query by `condition_id`, `created_at DESC`, and `notes LIKE 'Split from%'` with proper ordering, but document the fragility with a TODO comment.

### FIX 5 — backend/app/api/routes/assemblies.py (line 54):

Change `AssemblyTemplate.is_active == True` to `AssemblyTemplate.is_active.is_(True)`.
Remove the `# noqa: E712` comment on that line since `is_(True)` is PEP 8 compliant.

COMMIT: After all fixes, stage and commit with message "fix: resolve PR #12 review comments — API routes layer"

---

## Prompt 2: Backend Services + Migration (5 issues) -- Claude Sonnet 4 (thinking)

**Target files to modify:**

- `backend/alembic/versions/p4q5r6s7t8u9_add_assembly_system.py` (C1)
- `backend/app/models/assembly.py` (C1 -- verify ORM mappings)
- `backend/app/services/assembly_service.py` (C5)
- `backend/app/services/ai_predict_point.py` (C9)
- `backend/app/services/auto_count/orchestrator.py` (C10, C13)

**Context files to read (do not modify):**

- `backend/app/models/condition.py` -- Condition model: has `total_quantity`, `measurement_count`, `depth`, `thickness`. No `perimeter`, `height`, `width`, `length` fields.
- `backend/app/services/geometry_adjuster.py` lines 673-690 -- Reference `_update_condition_totals` pattern: SQL aggregate query updating both `total_quantity` and `measurement_count`
- `backend/app/data/assembly_templates.py` lines 275-285 -- Templates using `{count}` and `{perimeter}` in formulas

### Prompt text:

SYSTEM: You are a senior Python backend engineer. Apply exactly the fixes described below. Read each target file fully before editing. Do NOT modify files not listed unless explicitly instructed.

### TASK: Fix 5 PR review comments in backend service/migration files for a FastAPI + SQLAlchemy async application.

READ FIRST (context, do not modify):

- backend/app/models/condition.py — Condition model fields: `total_quantity: Float`, `measurement_count: Integer`, `depth: Float`, `thickness: Float`. NOTE: No `perimeter`, `height`, `width`, or `length` attributes exist.
- backend/app/services/geometry_adjuster.py lines 673-690 — Canonical `_update_condition_totals`

pattern:

```python
result = await session.execute(
    select(func.sum(Measurement.quantity), func.count(Measurement.id))
    .where(Measurement.condition_id == condition.id, Measurement.is_rejected == False)
)
row = result.one()
condition.total_quantity = row[0] or 0.0
condition.measurement_count = row[1] or 0
```

- backend/app/data/assembly_templates.py — Some templates use `{count}` (spread footings, columns: 10 formulas) and `{perimeter}` (sidewalk: 1 formula) in quantity formulas.

#### FIX 1 — backend/alembic/versions/p4q5r6s7t8u9_add_assembly_system.py:

The column name `metadata` is a reserved keyword in SQLAlchemy. Rename all 3 occurrences of `sa.Column("metadata", postgresql.JSONB, nullable=True)` to `sa.Column("extra_data", postgresql.JSONB, nullable=True)`.
Locations: line 87 (cost_items table), line 141 (assemblies table), line 191 (assembly_components table).
THEN verify backend/app/models/assembly.py — if the ORM models use `mapped_column("metadata", JSONB, ...)`, update them to `mapped_column("extra_data", JSONB, ...)` or simply `mapped_column(JSONB, ...)` with the Python attribute named `extra_data`. The current code has `extra_data: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)` — change the explicit column name from `"metadata"` to `"extra_data"` to match the migration change. Do this for ALL models in the file that have this pattern (Assembly, AssemblyComponent, CostItem, AssemblyTemplate).

#### FIX 2 — backend/app/services/assembly_service.py (build_formula_context method, ~line 406-417):

The `FormulaContext` hardcodes `count=0`, `perimeter=0.0`, `height=0.0`, `width=0.0`, `length=0.0`. The `count` variable is used in 10+ template formulas and should come from `condition.measurement_count`. The others have no source on the Condition model yet.

Required change:

- Set `count=condition.measurement_count or 0` instead of `count=0`
- For `perimeter`, `height`, `width`, `length`: keep them at 0 but update the comment to clearly document they are placeholders, and add a TODO with the specific fields that need to be added to the Condition model to support them.

#### FIX 3 — backend/app/services/ai_predict_point.py (~line 152-155):

The point normalization code has a logic bug:

```python
if "x" not in geometry_data:
    geometry_data = {"x": geometry_data.get("x", 0), "y": geometry_data.get("y", 0)}
```

When `"x"` is not in `geometry_data`, calling `geometry_data.get("x", 0)` always returns 0. This zeroes out coordinates instead of extracting them from an alternative format.

Required change: Check if the LLM returned coordinates in alternative formats (e.g., `{"lat": ..., "lng": ...}`, `{"col": ..., "row": ...}`, `[x, y]` list, or `{"point": {"x": ..., "y": ...}}`). Extract coordinates from these alternative formats, or if no recognizable format exists, return None instead of silently zeroing coordinates:

```python
if "x" not in geometry_data:
    # Try alternative coordinate formats from LLM
    if "point" in geometry_data and isinstance(geometry_data["point"], dict):
        geometry_data = {"x": geometry_data["point"].get("x", 0), "y": geometry_data["point"].get("y", 0)}
    elif isinstance(geometry_data, list) and len(geometry_data) >= 2:
        geometry_data = {"x": geometry_data[0], "y": geometry_data[1]}
    else:
        logger.warning("Unrecognized point format from LLM", data=geometry_data)
        return None
```

#### FIX 4 — backend/app/services/auto_count/orchestrator.py (create_measurements_from_confirmed, ~line 379-384):

After creating measurements, the function manually adds `count` to `condition.total_quantity` but never updates `condition.measurement_count`. Every other code path uses a SQL aggregate query to properly recalculate both fields.

Required change: Replace the manual increment block:

```python
if count > 0:
    condition = await db.get(Condition, session.condition_id)
    if condition is not None:
        condition.total_quantity = (condition.total_quantity or 0) + count
```

With the canonical `_update_condition_totals` pattern (SQL aggregate):

```python
if count > 0:
    condition = await db.get(Condition, session.condition_id)
    if condition is not None:
        from sqlalchemy import func, select
        result = await db.execute(
            select(func.sum(Measurement.quantity), func.count(Measurement.id))
            .where(Measurement.condition_id == condition.id, Measurement.is_rejected == False)
        )
        row = result.one()
        condition.total_quantity = row[0] or 0.0
        condition.measurement_count = row[1] or 0
```

#### FIX 5 — backend/app/services/auto_count/orchestrator.py (determine_source, ~line 269-281):

The function ignores the individual `match` parameter and only checks global `template_count`/`llm_count` totals. In hybrid mode, every detection is labeled `"both"` even if it only came from one source.

Required change: Add per-match source tracking. When merging in `_merge_matches`, tag each `MatchResult` with a `source` field ("template" or "llm"). For matches that overlap and are merged, tag as "both". Then `_determine_source` should read the tag from the individual match instead of using global counts:

```python
def _determine_source(self, match: MatchResult, template_count: int, llm_count: int) -> str:
    if hasattr(match, 'source') and match.source:
        return match.source
    if template_count > 0 and llm_count > 0:
        return "both"
    elif template_count > 0:
        return "template"
    return "llm"
```

COMMIT: After all fixes, stage and commit with message "fix: resolve PR #12 review comments — services and migration layer"

---

## Prompt 3: Review Stats + Documentation + Frontend (3 issues) -- Claude Sonnet 4 (non-thinking)

**Target files to modify:**

- `backend/app/services/review_service.py` (C12)
- `STATUS.md` (C7)
- `frontend/src/components/viewer/DrawingPreviewLayer.tsx` (C8)

**Context files to read (do not modify):**

- `backend/app/api/routes/review.py` -- Actual review route definitions
- `backend/app/api/routes/assemblies.py` -- Actual assembly route definitions
- `backend/app/api/routes/auto_count.py` -- Actual auto count route definitions
- `backend/app/api/routes/measurements.py` -- Actual measurement route definitions

### Prompt text:

SYSTEM: You are a senior full-stack engineer. Apply exactly the fixes described below. Read each target file fully before editing.

### TASK: Fix 3 PR review comments: review statistics overlap bug, STATUS.md API documentation inaccuracies, and debug console.log removal.

#### FIX 1 — backend/app/services/review_service.py (get_review_stats method, ~line 331-476):

The `approved` count query counts ALL verified-and-not-rejected measurements (including modified ones). The `modified` count is a subset of `approved`. This means `approved + rejected + modified + pending != total` — modified is double-counted.

In the SQL case expression for `approved` (~line 371-380), add an exclusion for modified measurements:

```python
func.sum(
    case(
        (
            and_(
                Measurement.is_verified == True,
                Measurement.is_rejected == False,
                Measurement.is_modified == False,  # Exclude modified from approved
            ),
            1,
        ),
        else_=0,
    )
).label("approved"),
```

This makes approved, rejected, modified, and pending mutually exclusive categories that sum to total.

#### FIX 2 — STATUS.md (API Endpoints section, ~lines 179-239):

The API documentation has multiple discrepancies with actual route implementations. Read the actual route files first, then fix:

Measurements section (lines 179-189) — fix these rows:

- `PUT /measurements/{id}/verify` -> `POST /measurements/{id}/approve` with description "Approve measurement"
- `DELETE /measurements/{id}/reject` -> `POST /measurements/{id}/reject` with description "Reject measurement"
- `PUT /measurements/{id}/geometry` -> `POST /measurements/{id}/modify` with description "Modify measurement"

Review section (lines 200-205) — add missing routes:

- POST `/measurements/{id}/approve` — Approve measurement
- POST `/measurements/{id}/reject` — Reject measurement
- POST `/measurements/{id}/modify` — Modify measurement
- GET `/measurements/{id}/history` — Measurement history

NOTE: The approve/reject/modify routes appear in both the Measurements table AND the Review table since they are measurement operations that are part of the review workflow. Keep them in Measurements with correct methods, and also add them to Review for discoverability. Or move them entirely to Review and remove from Measurements — either approach is acceptable, just be consistent.

Assemblies section (lines 212-223) — fix these rows:

- Remove `POST /conditions/{id}/assembly/from-template` (does not exist; template creation is handled by `POST /conditions/{id}/assembly`)
- `POST /assemblies/{id}/items` -> `POST /assemblies/{id}/components` with description "Add component"
- `PUT /assembly-items/{id}` -> `PUT /components/{id}` with description "Update component"
- `DELETE /assembly-items/{id}` -> `DELETE /components/{id}` with description "Remove component"
- Add missing routes: `DELETE /assemblies/{id}`, `POST /assemblies/{id}/calculate`, `POST /assemblies/{id}/lock`, `POST /assemblies/{id}/unlock`, `GET /assembly-templates/{id}`, `PUT /assemblies/{id}/components/reorder`, `POST /formulas/validate`, `GET /formulas/presets`, `GET /formulas/help`

Auto Count section (lines 207-210) — add missing routes:

- GET `/auto-count/sessions/{id}` — Get session details
- GET `/pages/{id}/auto-count/sessions` — List page sessions
- POST `/auto-count/detections/{id}/confirm` — Confirm detection
- POST `/auto-count/detections/{id}/reject` — Reject detection
- POST `/auto-count/sessions/{id}/bulk-confirm` — Bulk confirm
- POST `/auto-count/sessions/{id}/create-measurements` — Create measurements

#### FIX 3 — frontend/src/components/viewer/DrawingPreviewLayer.tsx:

Remove any `console.log` statements in this file. Search the entire file for `console.log` and remove all instances. These are debug statements that should not be in production.

COMMIT: After all fixes, stage and commit with message "fix: resolve PR #12 review comments — review stats, docs, and frontend cleanup"

```

---

## Token Cost and Model Estimates

| Prompt | Model | Est. Input | Rationale |
|--------|-------|-----------|-----------|
| 1 | Opus 4 (thinking) | ~30k tokens | CTE construction + multi-file coordination demands highest reasoning |
| 2 | Sonnet 4 (thinking) | ~25k tokens | Well-defined fixes benefit from reasoning at lower cost than Opus |
| 3 | Sonnet 4 (non-thinking) | ~20k tokens | Mechanical edits, speed > reasoning |

**Total: ~75k tokens across 3 conversations.** This is ~50% cheaper than a single-conversation approach (~150k+ with all files loaded) and ~60% cheaper than per-issue conversations (~200k+ with redundant file reads).

**Execution order:** Run Prompt 1 first (highest severity, most complex). Then Prompt 2. Then Prompt 3. No cross-prompt dependencies -- all 3 could theoretically run in parallel if using separate branches.
```
