# Phase 4: Auto Count Feature — Task Completion List

**Status**: COMPLETE
**Branch**: `claude/create-phase-1-tasks-OBEE7`

## Summary

Phase 4 implements a hybrid Auto Count feature that combines OpenCV template matching with LLM vision-based detection to automatically find and count repeated elements (symbols, fixtures, etc.) on plan pages. Users select a template region, the system finds all similar instances, and users can review/confirm/reject detections before converting them into measurements.

---

## Tasks

### AC-001: Create AutoCountSession + AutoCountDetection Models & Migration ✅
**Files**: `backend/app/models/auto_count.py`, `backend/app/models/__init__.py`, `backend/app/main.py`, `backend/alembic/versions/q5r6s7t8u9v0_add_auto_count.py`

- `AutoCountSession` — tracks a detection run: page_id, condition_id, template_bbox (JSONB), confidence_threshold, scale/rotation tolerances, detection_method (template/llm/hybrid), status, result counts, processing_time_ms
- `AutoCountDetection` — individual detection: session_id, measurement_id (nullable, set on confirm), bbox (JSONB), center_x/y, confidence, detection_source, status (pending/confirmed/rejected), is_auto_confirmed
- Both use `UUIDMixin` + `TimestampMixin`, cascade deletes from session
- Migration creates `auto_count_sessions` and `auto_count_detections` tables with indexes
- Down revision: `p4q5r6s7t8u9` (Phase 3)

### AC-002: Create Template Matching Service (OpenCV) ✅
**Files**: `backend/app/services/auto_count/__init__.py`, `backend/app/services/auto_count/template_matcher.py`

- `MatchResult` dataclass with x, y, w, h, center_x, center_y, confidence
- `TemplateMatchingService` — configurable thresholds for confidence, scale, rotation, NMS overlap
- `find_matches()` — multi-scale (±20%) and multi-rotation (±15°) template matching using `cv2.matchTemplate(TM_CCOEFF_NORMED)`
- `_transform_template()` — applies rotation and scale transforms
- `_match_single_variant()` — runs template matching for one scale/rotation variant
- `_non_maximum_suppression()` — greedy NMS deduplication by IoU
- `_compute_iou()` — intersection-over-union calculation
- `_exclude_template_region()` — removes detections overlapping the original template
- Graceful degradation when OpenCV is not installed (returns empty list with warning)

### AC-003: Create LLM Similarity Service ✅
**Files**: `backend/app/services/auto_count/llm_similarity.py`

- `LLMSimilarityService` — vision-based detection using LLM
- `find_similar()` — sends highlighted page image to vision LLM with structured JSON prompt
- `_highlight_template()` — draws red bounding box on page image to indicate template region
- Scales coordinates from LLM image space back to original dimensions
- Uses `get_llm_client(provider, task="auto_count")`
- Returns list of `MatchResult` with bounding boxes and confidence scores

### AC-004: Create Auto Count Orchestrator ✅
**Files**: `backend/app/services/auto_count/orchestrator.py`

- `AutoCountService` — combines template matching and LLM detection
- Session CRUD: `create_session()`, `get_session()`, `list_sessions()`
- `run_detection()` — core pipeline: template match → LLM detect → merge → store detections
- `_merge_detections()` — deduplicates overlapping detections from both sources using IoU > 0.30 threshold, keeping higher confidence
- Detection review: `confirm_detection()`, `reject_detection()`, `bulk_confirm_above_threshold()`
- `create_measurements_from_confirmed()` — creates point measurements (geometry_type="point", quantity=1.0, unit="EA") and updates condition total_quantity
- Singleton: `get_auto_count_service()`

### AC-005: Create Schemas and API Endpoints ✅
**Files**: `backend/app/schemas/auto_count.py`, `backend/app/api/routes/auto_count.py`, `backend/app/main.py`

Schemas:
- `BBox` — x, y, w, h with positive value validators
- `AutoCountCreateRequest` — condition_id, template_bbox, thresholds, detection_method
- `BulkConfirmRequest` — threshold float
- `DetectionResponse`, `SessionResponse`, `SessionDetailResponse`
- `AutoCountStartResponse` — session_id + task_id for async tracking

7 API endpoints:
- `POST /pages/{page_id}/auto-count` — 202 ACCEPTED, creates session + dispatches Celery task
- `GET /auto-count-sessions/{session_id}` — session with detections
- `GET /pages/{page_id}/auto-count-sessions` — list sessions for a page
- `POST /auto-count-detections/{detection_id}/confirm` — confirm single detection
- `POST /auto-count-detections/{detection_id}/reject` — reject single detection
- `POST /auto-count-sessions/{session_id}/bulk-confirm` — bulk confirm above threshold
- `POST /auto-count-sessions/{session_id}/create-measurements` — convert confirmed detections to measurements

Router registered in `main.py` with prefix `/api/v1`, tag `Auto Count`.

### AC-006: Create Celery Task for Background Processing ✅
**Files**: `backend/app/workers/auto_count_tasks.py`

- `auto_count_task` — Celery task with `bind=True, max_retries=3`
- Uses sync SQLAlchemy (psycopg2), not asyncpg
- Progress reporting via TaskTracker: 5% → 10% → 20% → 50% → 75% → 100%
- Downloads page image from storage service
- Runs template matching (OpenCV)
- Wraps async LLM call in `asyncio.new_event_loop()` for sync Celery context
- Merges detections, stores in DB, updates session summary
- Error handling: ValueError fails immediately, other exceptions retry with 60s countdown (max 3 retries)
- Helper functions: `_fail_session()`, `_get_image_dimensions()`, `_merge_detections()`

### AC-007: Create Frontend Types, API Client & Hooks ✅
**Files**: `frontend/src/types/index.ts`, `frontend/src/api/autoCount.ts`, `frontend/src/hooks/useAutoCount.ts`

Types:
- `BBox`, `AutoCountDetection`, `AutoCountSession`, `AutoCountSessionDetail`, `AutoCountStartResponse`

API client functions:
- `startAutoCount()`, `getAutoCountSession()`, `listPageAutoCountSessions()`
- `confirmDetection()`, `rejectDetection()`, `bulkConfirmDetections()`
- `createMeasurementsFromDetections()`

React Query hooks with cache invalidation:
- `useAutoCountSession()` — with polling (refetchInterval 2000ms while pending/processing)
- `usePageAutoCountSessions()`, `useStartAutoCount()`
- `useConfirmDetection()`, `useRejectDetection()`, `useBulkConfirmDetections()`
- `useCreateMeasurementsFromDetections()` — invalidates conditions cache on success

### AC-008: Create AutoCountTool + AutoCountOverlay Components ✅
**Files**: `frontend/src/components/auto-count/AutoCountTool.tsx`, `frontend/src/components/auto-count/AutoCountOverlay.tsx`, `frontend/src/components/workspace/TopToolbar.tsx`

`AutoCountTool` — 4-state workflow:
- **Idle**: confidence threshold slider + detection method selector + "Select Template Region" button
- **Selecting**: instruction overlay to draw bbox on canvas
- **Processing**: spinner with session status polling and progress display
- **Reviewing**: stats summary, threshold slider for bulk confirm, per-detection confirm/reject list, create measurements button
- Color-coded confidence: ≥90% green, ≥70% yellow, <70% red

`AutoCountOverlay` — SVG overlay:
- Renders detection bounding boxes with zoom/pan transforms from viewport
- Color by status: confirmed=green, rejected=red, pending=confidence-based
- Dashed stroke for pending, solid for confirmed
- Center point markers and confidence labels

`TopToolbar` — Added "Auto Count" button with cyan accent color and ScanSearch icon.

### AC-009: Write Unit and Integration Tests ✅
**Files**: `backend/tests/unit/test_template_matcher.py`, `backend/tests/unit/test_auto_count_orchestrator.py`, `backend/tests/integration/test_auto_count_api.py`

Template matcher tests:
- IoU calculation: identical boxes (1.0), no overlap (0.0), partial overlap, contained box
- NMS: no overlap keeps all, overlapping keeps highest confidence, empty/single input
- Template exclusion: excludes overlapping region, keeps non-overlapping
- find_matches: returns list, invalid bbox returns empty

Orchestrator tests:
- Merge detections: non-overlapping merges all, overlapping keeps higher confidence (both directions), empty inputs
- Session creation: missing page raises ValueError, missing condition raises ValueError
- Detection review: missing detection raises ValueError for both confirm and reject

API integration tests (mock-based):
- GET session: 200 with data, 404 not found
- GET list sessions: 200 with empty list
- POST confirm detection: 200 with confirmed status
- POST reject detection: 200 with rejected status
- POST bulk confirm: 200 with confirmed count
- POST create measurements: 200 with measurements count

---

## Key Design Decisions

1. **Hybrid detection approach** — Combines fast OpenCV template matching (good for identical symbols) with LLM vision detection (handles variations, rotations, scale differences)
2. **Async via Celery** — Detection runs as background Celery task, frontend polls for status with 2s interval
3. **Celery sync/async bridge** — LLM service is async but Celery workers are sync; wrapped with `asyncio.new_event_loop()` + `run_until_complete()`
4. **Two-phase workflow** — First detect (automated), then review (human-in-the-loop), then create measurements
5. **NMS deduplication** — IoU > 0.30 threshold prevents duplicate detections from overlapping matches
6. **Template region exclusion** — Original template region is excluded from results to avoid self-matching
7. **OpenCV optional** — Template matcher gracefully returns empty list when cv2 not installed
8. **Coordinate scaling for LLM** — LLM may resize images internally; coordinates scaled back to original dimensions
9. **Point measurements** — Confirmed detections create point measurements (geometry_type="point", quantity=1.0, unit="EA")
