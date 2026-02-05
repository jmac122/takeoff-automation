# Implement Unified Task API + Architecture Prep + Update Project Docs

## Context — Read These First

Before writing ANY code, read these files to understand the full picture:

1. `plans/00-MASTER-IMPLEMENTATION-PLAN-UPDATED-v3.md` — **Master roadmap**. Shows how the Unified Task API (Phase 2.5) and architecture prep schema additions fit into the overall project. Pay attention to the Document Index table and the phase overview diagram.
2. `plans/16-UNIFIED-TASK-API.md` — **Full spec** for the Unified Async Task API (database model, schemas, router, service, frontend hook, migration path).
3. `plans/17-KREO-ARCHITECTURE-PREP.md` — **Schema additions** for future features (plan overlay, vector PDF, NL query). Only columns — no features to build.
4. `.cursor/claude.md` — **Current cursor rules**. This file is STALE and needs updating (see Part 4 below).
5. `.cursor/rules/documentation.mdc` — **Documentation index**. Also STALE — missing plans 13-18.

Also skim these for awareness of the full plan set (do NOT implement these, just know they exist):
- `plans/13-ASSEMBLY-SYSTEM.md`
- `plans/14-AUTO-COUNT.md`
- `plans/15-QUICK-ADJUST-TOOLS.md`
- `plans/18-UI-OVERHAUL.md`
- `plans/18A-UI-OVERHAUL-AUDIT.md`
- `plans/18B-UI-OVERHAUL-PHASE-CONTEXTS.md`

## Existing Codebase Patterns

- All models: `backend/app/models/`, inherit `Base, UUIDMixin, TimestampMixin` from `backend/app/models/base.py`
  - **Exception:** TaskRecord uses Celery's string task_id as PK — only needs `Base, TimestampMixin` (no UUIDMixin)
- All models registered in `backend/app/models/__init__.py`
- Schemas: Pydantic v2 in `backend/app/schemas/`
- Routes: `backend/app/api/routes/`, registered in `backend/app/main.py`
- All routes use prefix `/api/v1/` (the spec says `/api/tasks/` — adjust to `/api/v1/tasks/`)
- Async routes use `AsyncSession` from `app.api.deps.get_db`
- Celery workers use SYNC SQLAlchemy (psycopg2) — see `backend/app/workers/takeoff_tasks.py` for pattern
- Celery app: `backend/app/workers/celery_app.py` with `task_track_started=True`
- Frontend uses React Query + Zustand (see `.cursor/claude.md` and `.cursor/rules/forgex-rules.md`)

---

## PART 1: Unified Task API (Phase 2.5)

Full spec: `plans/16-UNIFIED-TASK-API.md`

### Files to Create

1. **`backend/app/models/task.py`** — TaskRecord model (spec Task 16.1)
   - Primary key: `task_id: Mapped[str] = mapped_column(String(255), primary_key=True)` (Celery task ID)
   - DO NOT use UUIDMixin
   - Include: project_id FK, task_type, task_name, status enum, progress_percent, progress_step, started_at, completed_at, result_summary, error_message, error_traceback, task_metadata (JSON)
   - Indexes on (project_id, status) and (project_id, task_type)

2. **`backend/app/schemas/task.py`** — Pydantic schemas (spec Task 16.2)
   - TaskProgress, TaskResponse, TaskListResponse, StartTaskResponse, CancelTaskResponse

3. **`backend/app/api/routes/tasks.py`** — Unified router (spec Task 16.3)
   - `GET /tasks/{task_id}` — Get any task status (merge Celery state + DB record)
   - `POST /tasks/{task_id}/cancel` — Cancel running task via `celery_app.control.revoke(task_id, terminate=True, signal='SIGTERM')`
   - `GET /tasks/project/{project_id}` — List project tasks with optional `status` and `task_type` query params
   - Router: `prefix="/tasks"`, tags=`["Tasks"]`

4. **`backend/app/services/task_tracker.py`** — TaskTracker class (spec Task 16.4)
   - `register_async(db: AsyncSession, ...)` — called from FastAPI routes after `.delay()`
   - `update_progress_sync(db: Session, ...)` — called from Celery workers
   - `mark_started_sync()`, `mark_completed_sync()`, `mark_failed_sync()` — Celery workers
   - Async methods use `sqlalchemy.ext.asyncio.AsyncSession`, sync methods use `sqlalchemy.orm.Session`

### Files to Modify

5. **`backend/app/models/__init__.py`** — Add `TaskRecord` import and to `__all__`

6. **`backend/app/main.py`** — Register the tasks router:
   ```python
   from app.api.routes import tasks
   app.include_router(tasks.router, prefix="/api/v1", tags=["Tasks"])
   ```

7. **`backend/app/api/routes/takeoff.py`** — Two changes:
   a. Add backward-compatible redirect: the old `GET /takeoff/tasks/{task_id}/status` should redirect (301) to `GET /api/v1/tasks/{task_id}`. Set `include_in_schema=False`.
   b. Update `generate_ai_takeoff` endpoint to return `StartTaskResponse` and register the task via `TaskTracker.register_async()` after calling `.delay()`. Keep ALL existing validation logic intact.

8. **`backend/app/workers/takeoff_tasks.py`** — Add TaskTracker calls to `generate_ai_takeoff_task` ONLY (reference implementation, spec Task 16.5):
   - `mark_started_sync` at task start
   - `update_progress_sync` at key steps: 10% "Loading page data", 30% "Running AI analysis", 70% "Creating measurements", 90% "Finalizing"
   - Also call `self.update_state(state="PROGRESS", meta={"percent": N, "step": "..."})` alongside each progress update
   - `mark_completed_sync` on success with result summary (measurement count, etc.)
   - `mark_failed_sync` on error with traceback
   - **Leave all other task functions unchanged** — they'll be migrated later per the spec's migration path

### Alembic Migration

9. Create migration: `alembic revision --autogenerate -m "add_task_records_and_architecture_prep"`
   - This single migration should cover BOTH the TaskRecord table AND the Part 2 schema additions below
   - Include the composite indexes from the spec

---

## PART 2: Architecture Prep Schema Additions

Full spec: `plans/17-KREO-ARCHITECTURE-PREP.md`

These are lightweight nullable columns on existing models. No new features — just future-proofing the schema.

### Document Model (`backend/app/models/document.py`)

Add these columns (add `Date`, `Boolean` to imports, add `from datetime import date`):
```python
# Revision tracking (for future Plan Overlay — Phase 7B)
revision_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
revision_date: Mapped[date | None] = mapped_column(Date, nullable=True)
revision_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
supersedes_document_id: Mapped[uuid.UUID | None] = mapped_column(
    UUID(as_uuid=True),
    ForeignKey("documents.id", ondelete="SET NULL"),
    nullable=True,
)
is_latest_revision: Mapped[bool] = mapped_column(Boolean, default=True)
```

Add self-referential relationship:
```python
supersedes: Mapped["Document | None"] = relationship(
    "Document",
    remote_side="Document.id",
    foreign_keys=[supersedes_document_id],
)
```

### Page Model (`backend/app/models/page.py`)

**IMPORTANT:** `sheet_number` already exists on this model — do NOT duplicate it. Only add:
```python
# Title block info (sheet_number already exists)
sheet_title: Mapped[str | None] = mapped_column(String(255), nullable=True)

# Vector PDF detection (for future Vector PDF Extraction — Phase 9)
is_vector: Mapped[bool] = mapped_column(Boolean, default=False)
has_extractable_geometry: Mapped[bool] = mapped_column(Boolean, default=False)
vector_path_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
vector_text_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
pdf_origin: Mapped[str | None] = mapped_column(String(50), nullable=True)  # autocad, revit, bluebeam, scanned, unknown
```

### Condition Model (`backend/app/models/condition.py`)

Add spatial grouping columns:
```python
# Spatial grouping (for future NL Query — Phase 10)
building: Mapped[str | None] = mapped_column(String(100), nullable=True)
area: Mapped[str | None] = mapped_column(String(100), nullable=True)
elevation: Mapped[str | None] = mapped_column(String(50), nullable=True)
```

### Single Migration

All Part 1 + Part 2 schema changes should go in ONE Alembic migration:
```bash
alembic revision --autogenerate -m "add_task_records_and_architecture_prep"
alembic upgrade head
```

---

## PART 3: Frontend Task Polling Hook

Create **`frontend/src/hooks/useTaskPolling.ts`** per spec Task 16.8.

Check if `@tanstack/react-query` is already in `frontend/package.json`. It should be (the project uses React Query). If not, install it.

The hook should:
- Accept `taskId`, `onSuccess`, `onError`, `invalidateKeys` params
- Poll `GET /api/v1/tasks/{taskId}` every 2000ms using `useQuery` with `refetchInterval`
- Stop polling when status is terminal (`completed`, `failed`, `cancelled`)
- Fire `onSuccess`/`onError` callbacks on terminal states
- Invalidate specified React Query keys on success via `queryClient.invalidateQueries()`
- Provide a `cancel()` function that calls `POST /api/v1/tasks/{taskId}/cancel`
- Return: `{ taskStatus, isPolling, progress, isSuccess, isError, cancel }`

Also create a **`frontend/src/components/ui/TaskProgressBar.tsx`** component:
- Shows spinner when running, checkmark when complete, error icon when failed
- Progress bar with percentage
- Current step name display
- Cancel button for running tasks

---

## PART 4: Update Project Documentation

### 4A. Update `.cursor/claude.md`

The current file is stale. Make these specific updates:

**Implementation Phases table** — Replace the current phase table with this expanded version:
```
| Phase | Document | Description |
|-------|----------|-------------|
| 0 | `01-PROJECT-SETUP.md` | Repo structure, dev environment |
| 1A | `02-DOCUMENT-INGESTION.md` | PDF/TIFF upload, processing |
| 1B | `03-OCR-TEXT-EXTRACTION.md` | Text extraction, title blocks |
| 2A | `04-PAGE-CLASSIFICATION.md` | LLM page type identification |
| 2B | `05-SCALE-DETECTION.md` | Scale detection/calibration |
| 2.5 | `16-UNIFIED-TASK-API.md` | Unified async task polling API |
| 3A | `06-MEASUREMENT-ENGINE.md` | Core measurement tools |
| 3A+ | `06B-MANUAL-DRAWING-TOOLS.md` | Manual drawing tools |
| 3B | `07-CONDITION-MANAGEMENT.md` | Conditions data model/UI |
| 4A | `08-AI-TAKEOFF-GENERATION.md` | Automated element detection |
| 4B | `09-REVIEW-INTERFACE.md` | Human review UI |
| 5A | `10-EXPORT-SYSTEM.md` | Excel/OST export |
| 5B | `11-TESTING-QA.md` | Testing strategy |
| 6 | `12-DEPLOYMENT.md` | Production deployment |
| 6+ | `13-ASSEMBLY-SYSTEM.md` | Assembly/grouped takeoffs |
| 6+ | `14-AUTO-COUNT.md` | Automatic counting |
| 6+ | `15-QUICK-ADJUST-TOOLS.md` | Quick adjust tools |
| 7B | `17-KREO-ARCHITECTURE-PREP.md` | Schema prep for future features |
| **UI** | `18-UI-OVERHAUL.md` | Workspace UI overhaul (Phases A-E) |
| **UI** | `18A-UI-OVERHAUL-AUDIT.md` | UI architecture audit |
| **UI** | `18B-UI-OVERHAUL-PHASE-CONTEXTS.md` | Per-phase AI context files |
| **Master** | `00-MASTER-IMPLEMENTATION-PLAN-UPDATED-v3.md` | Current master roadmap |
```

**Core Data Model** — Add TaskRecord to the diagram:
```
Project (1) ──< Document (many) ──< Page (many)
    │                                    │
    ├──< TaskRecord (many)               ▼
    │                            Measurement (many)
    ▼                                    ▲
Condition (many) ────────────────────────┘
```

**API Endpoints** — Add to the Core section:
```
### Tasks (new)
GET    /tasks/{task_id}              # Unified task status
POST   /tasks/{task_id}/cancel       # Cancel running task
GET    /tasks/project/{project_id}   # List project tasks
```

**Note about master plan:** Add a note after the phase table:
```
**Master Plan:** `plans/00-MASTER-IMPLEMENTATION-PLAN-UPDATED-v3.md` is the canonical roadmap.
The `-v3` version includes Kreo-inspired enhancements (Unified Task API, Plan Overlay prep,
Vector PDF prep, NL Query prep) and the UI Overhaul parallel track.
```

### 4B. Update `.cursor/rules/documentation.mdc`

In the `## Plans` section, add the missing plan files:
```
- `plans/00-MASTER-IMPLEMENTATION-PLAN-UPDATED-v3.md` (CURRENT master roadmap)
- `plans/13-ASSEMBLY-SYSTEM.md`
- `plans/14-AUTO-COUNT.md`
- `plans/15-QUICK-ADJUST-TOOLS.md`
- `plans/16-UNIFIED-TASK-API.md`
- `plans/17-KREO-ARCHITECTURE-PREP.md`
- `plans/18-UI-OVERHAUL.md`
- `plans/18A-UI-OVERHAUL-AUDIT.md`
- `plans/18B-UI-OVERHAUL-PHASE-CONTEXTS.md`
```

Also add entries for the `-UPDATED` variants of existing plans that exist in the directory:
```
- `plans/07-CONDITION-MANAGEMENT-UPDATED.md`
- `plans/08-AI-TAKEOFF-GENERATION-UPDATED.md`
- `plans/10-EXPORT-SYSTEM-UPDATED.md`
- `plans/11-TESTING-QA-UPDATED.md`
- `plans/12-DEPLOYMENT-UPDATED.md`
- `plans/00-APPLICATION-INTERFACE-UPDATED.md`
```

---

## Verification Steps

After ALL implementation, verify:

1. `alembic upgrade head` applies cleanly
2. New `task_records` table exists with correct columns and indexes
3. New columns appear on `documents`, `pages`, and `conditions` tables
4. `GET /api/v1/tasks/{any-celery-task-id}` returns a TaskResponse
5. `POST /api/v1/tasks/{task-id}/cancel` sends revoke signal
6. `GET /api/v1/tasks/project/{project-id}` returns TaskListResponse with filters
7. Legacy `GET /api/v1/takeoff/tasks/{task-id}/status` redirects (301) to new endpoint
8. Starting an AI takeoff creates a TaskRecord in the database
9. TaskRecord shows progress updates (10%, 30%, 70%, 90%) during execution
10. All existing endpoints still work — no regressions
11. `.cursor/claude.md` reflects new phases, models, endpoints, and master plan reference
12. `.cursor/rules/documentation.mdc` lists all plan files 13-18

## What NOT to Do

- Do NOT modify any Celery tasks other than `generate_ai_takeoff_task`
- Do NOT build any UI for plan overlay, vector PDF, or NL query — only add schema columns
- Do NOT remove the old task status endpoint — keep as redirect for backward compat
- Do NOT rename or move any existing plan files
- Do NOT touch `.cursor/rules/forgex-rules.md` or `scale-detection-accuracy.mdc` — those are fine as-is
- Do NOT implement anything from plans 13, 14, 15, or 18 — those are future phases
