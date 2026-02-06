# Migrate Remaining Celery Tasks to Unified TaskTracker

## Context

We just implemented the Unified Task API (Phase 2.5) and completed a bug-fix pass on the initial PR. The infrastructure is in place and the patterns have been refined:

- `backend/app/models/task.py` — TaskRecord model (with TaskStatus enum for type safety)
- `backend/app/services/task_tracker.py` — TaskTracker with `register_async()`, `mark_started_sync()`, `update_progress_sync()`, `mark_completed_sync()`, `mark_failed_sync()`
- `backend/app/api/routes/tasks.py` — Unified `/api/v1/tasks/` router (tracebacks NOT exposed in API responses)
- `frontend/src/hooks/useTaskPolling.ts` — Frontend polling hook

**Only `generate_ai_takeoff_task` in `takeoff_tasks.py` is wired up.** The other 4 task modules still fire-and-forget with no TaskTracker integration. This means the unified task list (`GET /tasks/project/{project_id}`) only shows AI takeoff tasks — document processing, OCR, classification, and scale detection are invisible.

## ⚠️ CRITICAL: Read the Current Code First

Before making any changes, **read the current implementation** of `generate_ai_takeoff_task` in `backend/app/workers/takeoff_tasks.py` and its route in `backend/app/api/routes/takeoff.py`. These were updated during the bug-fix pass and represent the CORRECT pattern. The sections below describe the pattern conceptually, but **the actual code is the source of truth**.

Also read:
- `backend/app/services/task_tracker.py` — to see the exact method signatures and how they handle sessions
- `backend/app/models/task.py` — to see the TaskStatus enum and field types

## Reference Pattern (Post-Bug-Fix)

### Route Side: Register BEFORE Enqueueing

The old pattern was `task = something.delay(...)` then `register_async(task_id=task.id)`. This had a race condition where the worker could start before the DB record existed.

**New pattern — pre-generate the task ID, register first, then enqueue:**

```python
import uuid
from app.services.task_tracker import TaskTracker

# 1. Generate task ID up front
task_id = str(uuid.uuid4())

# 2. Register in DB FIRST (record exists before worker starts)
await TaskTracker.register_async(
    db,
    task_id=task_id,
    task_type="document_processing",
    task_name=f"Processing {filename}",
    project_id=str(project_id),
    metadata={"document_id": str(document_id)},
)

# 3. Enqueue with the pre-generated ID
some_task.apply_async(
    args=[str(document_id), str(project_id)],
    task_id=task_id,
)
```

**Important:** Use `.apply_async(args=[...], task_id=task_id)` instead of `.delay(...)` to pass the pre-generated task ID.

### Worker Side: TaskTracker Calls

Look at the CURRENT `generate_ai_takeoff_task` to see the exact pattern, but conceptually:

```python
# At task start (inside SyncSession):
TaskTracker.mark_started_sync(db, self.request.id)

# During processing — update both Celery state AND DB:
self.update_state(state="PROGRESS", meta={"percent": 30, "step": "Running AI analysis"})
TaskTracker.update_progress_sync(db, self.request.id, 30, "Running AI analysis")

# On success:
TaskTracker.mark_completed_sync(db, self.request.id, result_summary)

# On failure (final, no retry):
TaskTracker.mark_failed_sync(db, self.request.id, str(e), tb_module.format_exc())
```

### ⚠️ Critical Bug Fixes to Follow

These bugs were caught and fixed in the initial PR. Follow the SAME fixes in all new task integrations:

1. **`update_progress_sync` and session commits**: Check how `update_progress_sync` handles `db.commit()` / `db.flush()` in the current code. The original bug was that `update_progress_sync` called `db.commit()` which prematurely committed pending domain objects (measurements, etc.) in the same session. Follow whatever approach the fixed code uses — it may use `db.flush()`, a separate session, or another strategy.

2. **Don't mark FAILURE before retry**: If a task has `max_retries > 0` and calls `self.retry()`, do NOT call `mark_failed_sync` before the retry — it incorrectly shows FAILURE status during the retry countdown. Only call `mark_failed_sync` in the FINAL failure handler (when retries are exhausted). Check how `generate_ai_takeoff_task` handles this.

3. **Use `db.get(TaskRecord, task_id)` in TaskTracker methods**: The sync methods use modern SQLAlchemy 2.0 `db.get()` instead of legacy `db.query().filter()`. You don't need to change TaskTracker itself (it's already fixed), but be aware this is the pattern if you need to query TaskRecord anywhere.

## What to Implement

### 1. `backend/app/workers/document_tasks.py` — `process_document_task`

**Task type:** `"document_processing"`
**Progress steps:**
- 10% — "Downloading file"
- 40% — "Extracting pages" (after `processor.process_document()` returns)
- 70% — "Saving page records" (after creating Page objects)
- 90% — "Queueing OCR"
- 100% — complete

**Result summary:** `{"document_id": ..., "page_count": ...}`

**Notes:**
- The task uses `bind=True` already, so `self.request.id` is available
- Import `TaskTracker` and `traceback as tb_module`
- Add `mark_started_sync` right after opening the session
- This task has `max_retries=3` — follow the retry-aware pattern from `generate_ai_takeoff_task`. Only call `mark_failed_sync` when retries are truly exhausted.
- The `except Exception` block opens a second `SyncSession` for error handling — call `mark_failed_sync` in that same second session (only if not retrying)

**Route registration:** Update `backend/app/api/routes/documents.py` where `process_document_task.delay()` is called. Replace with pre-generate + register + `apply_async` pattern:
```python
import uuid
from app.services.task_tracker import TaskTracker

# Generate task ID
task_id = str(uuid.uuid4())

# Register FIRST
await TaskTracker.register_async(
    db,
    task_id=task_id,
    task_type="document_processing",
    task_name=f"Processing {file.filename}",
    project_id=str(project_id),
    metadata={"document_id": str(document_id), "filename": file.filename},
)

# THEN enqueue
process_document_task.apply_async(
    args=[str(document_id), str(project_id)],
    task_id=task_id,
)
```
Import `TaskTracker` and `uuid` at the top of the file.

### 2. `backend/app/workers/ocr_tasks.py` — `process_page_ocr_task`

**Task type:** `"ocr_processing"`
**Progress steps:**
- 10% — "Downloading page image"
- 40% — "Running OCR"
- 70% — "Parsing title block"
- 90% — "Saving results"
- 100% — complete

**Result summary:** `{"page_id": ..., "text_length": ..., "sheet_number": ..., "title": ...}`

**Notes:**
- Import `TaskTracker` and `traceback as tb_module`
- Add progress calls at the appropriate points in the existing flow
- Follow the retry-aware pattern — this task likely has retries
- In the `except` block, only call `mark_failed_sync` when retries exhausted
- **Do NOT modify** `process_document_ocr_task` (the batch orchestrator) — it just queues individual page tasks
- **Do NOT modify** `process_page_title_block_ocr_task` or `process_document_title_block_task` — those are secondary tasks not worth tracking individually for now

**Route registration:** Update `backend/app/api/routes/pages.py` where `process_page_ocr_task.delay()` is called for the reprocess-OCR endpoint. Replace with pre-generate + register + `apply_async`:
```python
import uuid
from app.services.task_tracker import TaskTracker

task_id = str(uuid.uuid4())

# Need to get the project_id for task registration
page_doc = await db.execute(
    select(Document.project_id).where(Document.id == page.document_id)
)
project_id = page_doc.scalar_one()

await TaskTracker.register_async(
    db,
    task_id=task_id,
    task_type="ocr_processing",
    task_name=f"OCR for page {page.sheet_number or page.page_number}",
    project_id=str(project_id),
    metadata={"page_id": str(page_id)},
)

process_page_ocr_task.apply_async(args=[str(page_id)], task_id=task_id)
```
**Note:** The automatic OCR triggered by `process_document_task` (which calls `process_document_ocr_task.delay()`) happens inside a Celery worker, not a route. Don't try to register those — only register user-initiated OCR reprocessing from the route.

### 3. `backend/app/workers/classification_tasks.py` — `classify_page_task`

**Task type:** `"page_classification"`
**Progress steps:**
- 10% — "Loading page data"
- 30% — "Running OCR classification" (if OCR path) or "Running vision classification" (if vision path)
- 70% — "Updating page record"
- 90% — "Saving classification history"
- 100% — complete

**Result summary:** `{"page_id": ..., "discipline": ..., "page_type": ..., "concrete_relevance": ..., "provider": ...}`

**Notes:**
- Import `TaskTracker` and `traceback as tb_module`
- The task already has `bind=True` so `self.request.id` is available
- The task has `max_retries=0` — so `mark_failed_sync` can be called directly in the `except` block (no retry concern)
- **Do NOT modify** `classify_document_pages` (batch orchestrator)

**Route registration:** Update `backend/app/api/routes/pages.py` where `classify_page_task.delay()` is called:
```python
import uuid
from app.services.task_tracker import TaskTracker

task_id = str(uuid.uuid4())

# Get project_id for registration
page_result = await db.execute(
    select(Page.document_id).where(Page.id == page_id)
)
doc_id = page_result.scalar_one()
doc_result = await db.execute(
    select(Document.project_id).where(Document.id == doc_id)
)
project_id = doc_result.scalar_one()

await TaskTracker.register_async(
    db,
    task_id=task_id,
    task_type="page_classification",
    task_name=f"Classifying page {page_id}",
    project_id=str(project_id),
    metadata={"page_id": str(page_id), "provider": provider, "use_vision": use_vision},
)

classify_page_task.apply_async(
    args=[str(page_id)],
    kwargs={"provider": provider, "use_vision": use_vision},
    task_id=task_id,
)
```

### 4. `backend/app/workers/scale_tasks.py` — `detect_page_scale_task`

**Task type:** `"scale_detection"`
**Progress steps:**
- 10% — "Loading page data"
- 30% — "Downloading image"
- 60% — "Detecting scale"
- 90% — "Saving results"
- 100% — complete

**Result summary:** `{"page_id": ..., "scale_text": ..., "scale_value": ..., "calibrated": ...}`

**Notes:**
- Import `TaskTracker` and `traceback as tb_module`
- `bind=True` is already set, so `self.request.id` is available
- This task likely has retries — follow the retry-aware pattern. Do NOT call `mark_failed_sync` before `self.retry()`. Only call it when retries are exhausted.
- **Do NOT modify** `detect_document_scales_task` (batch orchestrator) or `calibrate_page_scale_task` (manual calibration — synchronous result is fine)

**Route registration:** Update `backend/app/api/routes/pages.py` where `detect_page_scale_task.delay()` is called:
```python
import uuid
from app.services.task_tracker import TaskTracker

task_id = str(uuid.uuid4())

# Get project_id
page_result = await db.execute(
    select(Page.document_id).where(Page.id == page_id)
)
doc_id = page_result.scalar_one()
doc_result = await db.execute(
    select(Document.project_id).where(Document.id == doc_id)
)
project_id = doc_result.scalar_one()

await TaskTracker.register_async(
    db,
    task_id=task_id,
    task_type="scale_detection",
    task_name=f"Scale detection for page {page_id}",
    project_id=str(project_id),
    metadata={"page_id": str(page_id)},
)

detect_page_scale_task.apply_async(args=[str(page_id)], task_id=task_id)
```

**Important:** The detect-scale endpoint may not inject `db`. Check the current endpoint signature — if `db: Annotated[AsyncSession, Depends(get_db)]` is missing, you'll need to add it.

### 5. Remaining Tasks in `takeoff_tasks.py`

These three tasks in `takeoff_tasks.py` were NOT instrumented in the initial implementation. Add TaskTracker calls to all three, following the exact same patterns as `generate_ai_takeoff_task` (which is already correct).

**`autonomous_ai_takeoff_task`:**
- Check if `bind=True` is set (add it if not)
- task_type: `"autonomous_ai_takeoff"`
- Progress: 10% Loading → 30% AI analysis → 70% Creating measurements → 90% Updating conditions → complete
- Add `mark_started_sync`, `update_progress_sync`, `mark_completed_sync`, `mark_failed_sync` (retry-aware)
- Update route in `takeoff.py`: pre-generate ID → `register_async` → `apply_async`

**`compare_providers_task`:**
- task_type: `"provider_comparison"`
- Progress: 10% Loading → 20-80% per provider → 90% Compiling results → complete
- Same pattern
- Update route in `takeoff.py`: pre-generate ID → `register_async` → `apply_async`

**`batch_ai_takeoff_task`:**
- task_type: `"batch_ai_takeoff"`
- Simple: 10% start → progress per page queued → complete
- Same pattern
- Update route in `takeoff.py`: pre-generate ID → `register_async` → `apply_async`

## Files Modified (Summary)

| File | Changes |
|------|---------|
| `backend/app/workers/document_tasks.py` | Add TaskTracker to `process_document_task` |
| `backend/app/workers/ocr_tasks.py` | Add TaskTracker to `process_page_ocr_task` |
| `backend/app/workers/classification_tasks.py` | Add TaskTracker to `classify_page_task` |
| `backend/app/workers/scale_tasks.py` | Add TaskTracker to `detect_page_scale_task` |
| `backend/app/workers/takeoff_tasks.py` | Add TaskTracker to `autonomous_ai_takeoff_task`, `compare_providers_task`, `batch_ai_takeoff_task` |
| `backend/app/api/routes/documents.py` | Register `process_document_task` — pre-generate ID pattern |
| `backend/app/api/routes/pages.py` | Register OCR, classification, and scale tasks — pre-generate ID pattern |
| `backend/app/api/routes/takeoff.py` | Register autonomous, compare, and batch tasks — pre-generate ID pattern |

## What NOT to Do

- Do NOT modify TaskRecord model, TaskTracker service, or tasks router — those are done and bug-fixed
- Do NOT create new Alembic migrations — no schema changes needed
- Do NOT modify `process_document_ocr_task`, `process_document_title_block_task`, `process_page_title_block_ocr_task`, `detect_document_scales_task`, or `classify_document_pages` — these are batch orchestrators that fan out to individual tasks
- Do NOT change the existing `generate_ai_takeoff_task` TaskTracker integration — it's the reference and is already correct
- Do NOT try to register tasks that are queued from inside other Celery workers (e.g., OCR auto-queued from document processing) — only register tasks triggered from API routes
- Do NOT use `.delay()` for task enqueueing — use `.apply_async(args=[...], task_id=task_id)` to pass pre-generated IDs
- Do NOT call `mark_failed_sync` before `self.retry()` in tasks with retries — only mark failure when retries are exhausted

## Verification

After implementation:
1. Upload a document → `GET /tasks/project/{project_id}` shows a `document_processing` task with progress
2. Trigger OCR reprocessing → task list shows an `ocr_processing` task
3. Classify a page → task list shows a `page_classification` task
4. Detect scale → task list shows a `scale_detection` task
5. Run autonomous takeoff → task list shows an `autonomous_ai_takeoff` task
6. Run provider comparison → task list shows a `provider_comparison` task
7. Run batch takeoff → task list shows a `batch_ai_takeoff` task
8. All existing functionality continues to work — no regressions
9. Progress updates appear during task execution (not just start/complete)
10. Tasks with retries show correct status during retry countdown (not FAILURE)
11. No premature session commits from progress updates
