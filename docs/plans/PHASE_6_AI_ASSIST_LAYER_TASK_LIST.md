# Phase 6: AI Assist Layer — Task List

## Overview

Phase 6 implements three AI-powered features integrated directly into the Konva canvas workspace:

1. **AutoTab** — AI-suggested next measurement (ghost overlay, Tab to accept, Esc to dismiss)
2. **Batch AI Inline** — "AI Assist" button triggers autonomous AI takeoff for the current sheet
3. **AI Confidence Visualization** — Color-coded measurement overlays by AI confidence

## Tasks

### AI-001: Backend Predict-Next-Point Service + Endpoint
- **Status:** Complete
- **New file:** `backend/app/services/ai_predict_point.py`
  - `PredictNextPointService.predict_next()` — synchronous LLM call (NOT Celery)
  - Aggressive downscale to 768px for <800ms latency target
  - Silent failure: returns `None` on any error
  - Scales coordinates from LLM image space back to original
  - Helper functions: `_format_last_coords`, `_geometry_template`, `_scale_geometry`
  - Singleton factory: `get_predict_point_service()`
- **Modified file:** `backend/app/api/routes/takeoff.py`
  - Added `PredictNextPointRequest` and `PredictNextPointResponse` schemas
  - Added `POST /pages/{page_id}/predict-next-point` endpoint
  - Reuses `get_calibrated_page` dependency
  - Catches all exceptions → returns `{prediction: null}` (never 500)

### AI-002: Frontend AutoTab API + Hook + Store Additions
- **Status:** Complete
- **Modified file:** `frontend/src/api/takeoff.ts`
  - Added `PredictNextPointRequest`, `PredictNextPointPrediction`, `PredictNextPointResponse` types
  - Added `takeoffApi.predictNextPoint(pageId, data)` function
- **Modified file:** `frontend/src/stores/workspaceStore.ts`
  - Added state: `ghostPrediction`, `aiConfidenceOverlay`, `batchAiTaskId`
  - Added actions: `setGhostPrediction`, `clearGhostPrediction`, `toggleAiConfidenceOverlay`, `setBatchAiTaskId`, `clearBatchAiTaskId`
  - Added selectors: `selectGhostPrediction`, `selectAiConfidenceOverlay`, `selectBatchAiTaskId`
  - Updated `escapeAll()` to clear `ghostPrediction`
- **New file:** `frontend/src/hooks/useAutoTab.ts`
  - `useAutoTab(pageId, conditionId)` hook
  - `triggerPrediction()` with AbortController timeout
  - `acceptPrediction()` / `dismissPrediction()`
  - Uses `AUTOTAB_TIMEOUT_MS` from constants

### AI-003: GhostPointLayer Component + Canvas Integration + Keyboard
- **Status:** Complete
- **New file:** `frontend/src/components/viewer/GhostPointLayer.tsx`
  - Konva-based ghost shape overlay
  - Cyan dashed stroke (`#06B6D4`) to distinguish from real measurements
  - Pulsing opacity animation (0.3–0.7 over 1.5s)
  - "Tab to accept · Esc to dismiss" label
  - Renders all geometry types: line, polyline, polygon, rectangle, circle, point
- **Modified file:** `frontend/src/hooks/useKeyboardShortcuts.ts`
  - Tab key: accepts ghost prediction (when one exists)
  - Esc key: dismisses ghost prediction (before other escape handling)
  - Added `onAcceptGhost` and `onDismissGhost` callback props
- **Modified file:** `frontend/src/components/workspace/CenterCanvas.tsx`
  - Imported and rendered `<GhostPointLayer>` inside canvas area
  - Added `aiConfidenceOverlay` and `viewport` from store

### AI-004: Batch AI Inline (AI Assist Button + Draft Measurement Styling)
- **Status:** Complete
- **New file:** `frontend/src/hooks/useAiAssist.ts`
  - `useAiAssist(projectId, pageId)` hook
  - Uses `useTaskPolling` for async task tracking
  - `runBatchAi()` triggers `generateAutonomousTakeoff()`
  - Invalidates measurements cache on completion
- **Modified file:** `frontend/src/components/workspace/TopToolbar.tsx`
  - Wired "AI Assist" button with `onClick` → `runBatchAi()`
  - Purple highlight + loading spinner when batch task is running
  - Disabled while task is in progress
- **Modified file:** `frontend/src/components/workspace/TakeoffWorkspace.tsx`
  - Added `useAiAssist` hook integration
  - Passes `onRunBatchAi` and `isBatchAiRunning` to TopToolbar
- **Modified file:** `frontend/src/components/viewer/MeasurementShape.tsx`
  - Draft measurement styling: dashed stroke + 60% opacity for AI-generated unverified measurements
  - Added `aiConfidenceOverlay` prop
  - Added `effectiveColor` computed from `getReviewColor()` when overlay active
  - Added `groupOpacity` for draft vs. verified measurements

### AI-005: AI Confidence Overlay Toggle
- **Status:** Complete
- **Modified file:** `frontend/src/components/workspace/TopToolbar.tsx`
  - Added `Palette` icon import
  - Added confidence overlay toggle button (between AI Assist and Review Mode)
  - Blue highlight when active (same pattern as grid toggle)
  - Connected to `toggleAiConfidenceOverlay()` store action

### AI-006: Tests + Task List Doc + Commit + Push
- **Status:** Complete
- **New file:** `backend/tests/unit/test_ai_predict_point.py`
  - 14 unit tests covering helpers, service predictions, coordinate scaling, error handling, prompt content
- **New file:** `backend/tests/integration/test_predict_next_api.py`
  - 6 integration tests: 200 with prediction, null on error, null on missing image, 404, 400 uncalibrated, 422 invalid
- **New file:** `docs/plans/PHASE_6_AI_ASSIST_LAYER_TASK_LIST.md` (this document)

## Files Created (7)

| File | Purpose |
|------|---------|
| `backend/app/services/ai_predict_point.py` | Predict-next-point service |
| `frontend/src/hooks/useAutoTab.ts` | AutoTab prediction hook |
| `frontend/src/hooks/useAiAssist.ts` | Batch AI task management hook |
| `frontend/src/components/viewer/GhostPointLayer.tsx` | Ghost shape overlay |
| `backend/tests/unit/test_ai_predict_point.py` | Unit tests |
| `backend/tests/integration/test_predict_next_api.py` | API integration tests |
| `docs/plans/PHASE_6_AI_ASSIST_LAYER_TASK_LIST.md` | Task list document |

## Files Modified (7)

| File | Change |
|------|--------|
| `backend/app/api/routes/takeoff.py` | Predict-next-point schemas + endpoint |
| `frontend/src/api/takeoff.ts` | `predictNextPoint()` API function |
| `frontend/src/stores/workspaceStore.ts` | Ghost prediction, confidence overlay, batch AI state |
| `frontend/src/components/workspace/TopToolbar.tsx` | AI Assist button wired + confidence toggle |
| `frontend/src/components/workspace/TakeoffWorkspace.tsx` | `useAiAssist` integration |
| `frontend/src/components/viewer/MeasurementShape.tsx` | Draft styling + confidence color override |
| `frontend/src/hooks/useKeyboardShortcuts.ts` | Tab/Esc for ghost accept/dismiss |
| `frontend/src/components/workspace/CenterCanvas.tsx` | GhostPointLayer + aiConfidenceOverlay |

## Design Decisions

1. **AutoTab uses synchronous endpoint (NOT Celery)** — Target <800ms latency. Image downscaled to 768px, max_tokens=256.
2. **Silent failure for AutoTab** — Errors never block drawing. Returns null, no toasts.
3. **Batch AI reuses existing infrastructure** — No new backend endpoints for batch. Uses `autonomous_ai_takeoff_task` + `useTaskPolling`.
4. **Confidence colors reuse existing constants** — `REVIEW_CONFIDENCE_HIGH/MEDIUM` and `REVIEW_COLOR_*` from `constants.ts`.
5. **Draft measurement detection via `is_ai_generated` flag** — Measurements from AI already have this flag in DB.
6. **Ghost overlay uses Konva** — Renders as a `Group` with pulsing animation, not HTML overlay.
