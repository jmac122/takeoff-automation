# Phase 2: Enhanced Review Interface Task List

## Context

**Why this change is needed:** The ForgeX takeoff system generates AI measurements with confidence scores, but there is no workflow for humans to review, approve, reject, or modify these measurements. Without a review interface, AI-generated measurements go unverified, making the system unsuitable for production use where accuracy is critical for construction cost estimation.

**What prompted it:** Phase 2 from `docs/plans/0226-forgex-remaining-work-prompts.md` and `plans/09-REVIEW-INTERFACE-ENHANCED.md`. Phase 1 (Canvas Migration) provides the Konva canvas that this phase depends on for measurement highlighting.

**Intended outcome:** Users can toggle review mode in the workspace, navigate through unreviewed measurements with keyboard shortcuts (A/R/S/E), see confidence-based color coding on the canvas, auto-accept high-confidence measurements in batch, view review statistics, and access a full audit trail for any measurement.

---

## What Already Exists

**Backend (ready to extend):**
- `Measurement` model with `is_verified`, `ai_confidence`, `ai_model`, `is_ai_generated`, `is_modified` fields
- `MeasurementEngine` with `_update_condition_totals()` (line 296-311 in `measurement_engine.py`) — needs filter for rejected
- `ClassificationHistory` model — provides the audit trail pattern to follow
- All measurement CRUD routes and schemas
- Base model mixins: `UUIDMixin`, `TimestampMixin`
- Latest Alembic migration head: `n2o3p4q5r6s7`

**Frontend (ready to extend):**
- `Measurement` TS type already has `is_verified`, `ai_confidence`, `is_ai_generated`, `is_modified`
- `workspaceStore` with state management (activeTool, selectedMeasurementIds, focusRegion, etc.)
- `FocusContext` with `shouldFireShortcut()` for keyboard routing
- `TopToolbar` with tool buttons, zoom, AI Assist button
- `BottomStatusBar` showing zoom/tool/sheet/selection
- `RightPanel` wrapping `ConditionPanel`
- Toast + NotificationContext systems
- `useMeasurements` hook and `api/measurements.ts` client

**What does NOT exist (confirmed by glob — zero matches):**
- `backend/app/models/measurement_history.py`
- `backend/app/services/review_service.py`
- `backend/app/api/routes/review.py`
- `backend/app/schemas/review.py`
- Any frontend review components, hooks, or API client

---

## Design Decisions

1. **Review status: Boolean approach** — Keep existing `is_verified` boolean, add `is_rejected` boolean. Status derived: pending (both false), approved (verified=true), rejected (is_rejected=true). Preserves backward compatibility.

2. **Rejection: Soft-delete** — Set `is_rejected=True`, keep measurement in DB for audit trail. Exclude from canvas rendering and condition totals.

3. **Review mode: In-workspace toggle** — Not a separate page. Toggle in TopToolbar activates review mode within existing TakeoffWorkspace.

4. **Condition totals: Must exclude rejected** — `_update_condition_totals()` in `measurement_engine.py:302-306` currently sums ALL measurements. Must add `.where(Measurement.is_rejected == False)` filter.

---

## Task Overview

| Category | Task Count | Priority |
|----------|------------|----------|
| 1. Backend: MeasurementHistory Model & Migration | 4 | Critical |
| 2. Backend: Measurement Model Extensions | 3 | Critical |
| 3. Backend: Review Schemas | 4 | High |
| 4. Backend: Review Service | 7 | Critical |
| 5. Backend: Review API Routes | 4 | High |
| 6. Frontend: Workspace Store Extensions | 4 | Critical |
| 7. Frontend: Review API Client & Hooks | 4 | High |
| 8. Frontend: Review Mode UI | 6 | High |
| 9. Frontend: Review Statistics | 2 | Medium |
| 10. Frontend: Canvas Review Overlays | 3 | High |
| 11. Testing & Verification | 5 | High |

**Total: 46 tasks**

---

## 1. Backend: MeasurementHistory Model & Migration

- [x] **RI-001**: Create `MeasurementHistory` model
  - **File (new):** `backend/app/models/measurement_history.py`
  - `MeasurementHistory(Base, UUIDMixin, TimestampMixin)`, `__tablename__ = "measurement_history"`
  - Fields: `measurement_id` (UUID FK to `measurements.id`, CASCADE, indexed), `action` (String(50), not null — values: created/approved/rejected/modified/auto_accepted), `actor` (String(255), not null), `actor_type` (String(50), default "user" — values: user/system/auto_accept), `previous_status` (String(50), nullable), `new_status` (String(50), nullable), `previous_geometry` (JSONB, nullable), `new_geometry` (JSONB, nullable), `previous_quantity` (Float, nullable), `new_quantity` (Float, nullable), `change_description` (Text, nullable), `notes` (Text, nullable)
  - Relationship: `measurement = relationship("Measurement", back_populates="history")`
  - Follow `ClassificationHistory` pattern from `backend/app/models/classification_history.py`

- [x] **RI-002**: Add `history` relationship to Measurement model
  - **File:** `backend/app/models/measurement.py`
  - Add: `history: Mapped[list["MeasurementHistory"]] = relationship("MeasurementHistory", back_populates="measurement", cascade="all, delete-orphan", order_by="MeasurementHistory.created_at.desc()")`

- [x] **RI-003**: Register MeasurementHistory in models `__init__.py`
  - **File:** `backend/app/models/__init__.py`
  - Add: `from app.models.measurement_history import MeasurementHistory`

- [x] **RI-004**: Create Alembic migration for all Phase 2 schema changes
  - **File (new):** `backend/alembic/versions/o3p4q5r6s7t8_add_review_fields_and_history.py`
  - `down_revision = 'n2o3p4q5r6s7'`
  - **Upgrade:** Create `measurement_history` table; Add to `measurements`: `is_rejected` (Boolean, default False), `rejection_reason` (Text, nullable), `review_notes` (Text, nullable), `reviewed_at` (DateTime(tz), nullable), `original_geometry` (JSONB, nullable), `original_quantity` (Float, nullable)
  - Add indexes: `ix_measurement_history_measurement_id`, `ix_measurements_is_rejected`
  - **Downgrade:** Drop table and columns

---

## 2. Backend: Measurement Model Extensions

- [x] **RI-005**: Add `is_rejected` and `rejection_reason` to Measurement model
  - **File:** `backend/app/models/measurement.py`
  - Add after `is_verified` field (line 67): `is_rejected: Mapped[bool] = mapped_column(Boolean, default=False)`, `rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)`

- [x] **RI-006**: Add review metadata fields to Measurement model
  - **File:** `backend/app/models/measurement.py`
  - Add: `review_notes` (Text, nullable), `reviewed_at` (DateTime(tz), nullable), `original_geometry` (JSONB, nullable), `original_quantity` (Float, nullable)

- [x] **RI-007**: Update `MeasurementResponse` schema with new fields
  - **File:** `backend/app/schemas/measurement.py`
  - Add to `MeasurementResponse`: `is_rejected: bool`, `rejection_reason: str | None`, `review_notes: str | None`, `reviewed_at: datetime | None`, `original_geometry: dict | None`, `original_quantity: float | None`

---

## 3. Backend: Review Schemas

- [x] **RI-008**: Create review request schemas
  - **File (new):** `backend/app/schemas/review.py`
  - `ApproveRequest`: `reviewer: str`, `notes: str | None`
  - `RejectRequest`: `reviewer: str`, `reason: str` (required)
  - `ModifyRequest`: `reviewer: str`, `geometry_data: dict[str, Any]`, `notes: str | None`
  - `AutoAcceptRequest`: `threshold: float` (default 0.90, range 0.5-1.0), `reviewer: str | None`

- [x] **RI-009**: Create review response schemas
  - **File:** `backend/app/schemas/review.py`
  - `ReviewActionResponse`: `status: str`, `measurement_id: uuid.UUID`, `new_quantity: float | None`
  - `AutoAcceptResponse`: `auto_accepted_count: int`, `threshold: float`
  - `NextUnreviewedResponse`: `measurement: MeasurementResponse | None`, `remaining_count: int`

- [x] **RI-010**: Create review statistics schema
  - **File:** `backend/app/schemas/review.py`
  - `ReviewStatisticsResponse`: `total`, `pending`, `approved`, `rejected`, `modified`, `ai_generated_count`, `ai_accuracy_percent`, `confidence_distribution: ConfidenceDistribution`
  - `ConfidenceDistribution`: `high` (>=0.9), `medium` (0.7-0.9), `low` (<0.7)

- [x] **RI-011**: Create measurement history response schema
  - **File:** `backend/app/schemas/review.py`
  - `MeasurementHistoryResponse`: all fields from model, `model_config = ConfigDict(from_attributes=True)`

---

## 4. Backend: Review Service

- [x] **RI-012**: Create ReviewService class skeleton
  - **File (new):** `backend/app/services/review_service.py`
  - Class with `structlog.get_logger()`, singleton pattern matching `measurement_engine.py:314-323`
  - Helper: `_derive_status(measurement) -> str` returns "pending"/"approved"/"rejected"/"modified"

- [x] **RI-013**: Implement `approve_measurement()`
  - **File:** `backend/app/services/review_service.py`
  - Sets `is_verified=True`, `is_rejected=False`, `reviewed_at=utcnow()`, `review_notes`
  - Creates `MeasurementHistory` record (action="approved", actor_type="user")
  - Guards: measurement exists, not already rejected

- [x] **RI-014**: Implement `reject_measurement()`
  - **File:** `backend/app/services/review_service.py`
  - Sets `is_rejected=True`, `is_verified=False`, `rejection_reason`, `reviewed_at`
  - Creates history record (action="rejected")
  - **Critical:** Calls `_update_condition_totals()` to exclude rejected measurement from condition totals
  - Must import and use `get_measurement_engine()` from `measurement_engine.py`

- [x] **RI-015**: Implement `modify_measurement()`
  - **File:** `backend/app/services/review_service.py`
  - Stores `original_geometry`/`original_quantity` on first modification only
  - Recalculates quantity via `MeasurementEngine._calculate_geometry()` and `_extract_quantity()`
  - Sets `is_modified=True`, `is_verified=True`
  - Creates history with previous/new geometry and quantity

- [x] **RI-016**: Implement `auto_accept_batch()`
  - **File:** `backend/app/services/review_service.py`
  - Query: measurements where `condition.project_id = project_id AND is_ai_generated=True AND ai_confidence >= threshold AND is_verified=False AND is_rejected=False`
  - Batch set `is_verified=True`, create history records with `actor_type="auto_accept"`
  - Single commit after loop
  - Returns count

- [x] **RI-017**: Implement `get_review_stats()`
  - **File:** `backend/app/services/review_service.py`
  - Counts via Condition join for `project_id`: total, pending, approved, rejected, modified
  - AI stats: accuracy % = (approved AI / total AI) * 100
  - Confidence distribution: high/medium/low counts

- [x] **RI-018**: Implement `get_next_unreviewed()`
  - **File:** `backend/app/services/review_service.py`
  - Query: `WHERE page_id AND is_verified=False AND is_rejected=False ORDER BY ai_confidence ASC NULLS LAST`
  - If `after_id` provided, skip past that measurement
  - Returns `(next_measurement | None, remaining_count)`

---

## 5. Backend: Review API Routes

- [x] **RI-019**: Create review router with approve/reject/modify endpoints
  - **File (new):** `backend/app/api/routes/review.py`
  - POST `/measurements/{measurement_id}/approve` — body: `ApproveRequest`
  - POST `/measurements/{measurement_id}/reject` — body: `RejectRequest`
  - POST `/measurements/{measurement_id}/modify` — body: `ModifyRequest`
  - Handle ValueError as 404/400 HTTPException

- [x] **RI-020**: Add auto-accept, stats, and next-unreviewed endpoints
  - **File:** `backend/app/api/routes/review.py`
  - POST `/projects/{project_id}/measurements/auto-accept` — body: `AutoAcceptRequest`
  - GET `/projects/{project_id}/review-stats`
  - GET `/pages/{page_id}/measurements/next-unreviewed?after={id}`

- [x] **RI-021**: Add measurement history endpoint
  - **File:** `backend/app/api/routes/review.py`
  - GET `/measurements/{measurement_id}/history` — returns `list[MeasurementHistoryResponse]`

- [x] **RI-022**: Register review router in application
  - **File:** `backend/app/main.py`
  - Add import: `from app.api.routes import review`
  - Add: `app.include_router(review.router, prefix="/api/v1", tags=["Review"])`
  - Add `MeasurementHistory` to model imports at top

---

## 6. Frontend: Workspace Store Extensions

- [x] **RI-023**: Add review mode state to workspaceStore
  - **File:** `frontend/src/stores/workspaceStore.ts`
  - Add to state: `reviewMode: boolean` (false), `reviewCurrentId: string | null`, `reviewConfidenceFilter: number` (0.0), `reviewAutoAdvance: boolean` (true)

- [x] **RI-024**: Add review mode actions to workspaceStore
  - **File:** `frontend/src/stores/workspaceStore.ts`
  - Actions: `toggleReviewMode()`, `setReviewMode(active)` (forces activeTool to 'select' on activate), `setReviewCurrentId(id)`, `setReviewConfidenceFilter(threshold)`, `advanceReview(nextId)` (sets reviewCurrentId + selectedMeasurementIds)

- [x] **RI-025**: Add review mode selectors
  - **File:** `frontend/src/stores/workspaceStore.ts`
  - `selectReviewMode`, `selectReviewCurrentId`, `selectReviewConfidenceFilter`, `selectReviewAutoAdvance`

- [x] **RI-026**: Update `escapeAll` to clear review state
  - **File:** `frontend/src/stores/workspaceStore.ts`
  - Modify `escapeAll` (line 301) to also set `reviewMode: false`, `reviewCurrentId: null`

---

## 7. Frontend: Review API Client & Hooks

- [x] **RI-027**: Create review API client functions
  - **File (new):** `frontend/src/api/review.ts`
  - Functions: `approveMeasurement()`, `rejectMeasurement()`, `modifyMeasurement()`, `autoAcceptMeasurements()`, `getReviewStats()`, `getNextUnreviewed()`, `getMeasurementHistory()`
  - Follow pattern from `frontend/src/api/measurements.ts`

- [x] **RI-028**: Add review types to frontend type definitions
  - **File:** `frontend/src/types/index.ts`
  - Extend `Measurement` interface: `is_rejected`, `rejection_reason`, `review_notes`, `reviewed_at`, `original_geometry`, `original_quantity`
  - Add: `ReviewActionResponse`, `ReviewStatistics`, `ConfidenceDistribution`

- [x] **RI-029**: Create `useReviewActions` React Query hook
  - **File (new):** `frontend/src/hooks/useReviewActions.ts`
  - Mutations for approve, reject, modify, autoAccept via `useMutation`
  - Invalidates: `['measurements', pageId]`, `['conditions', projectId]`, `['review-stats', projectId]`
  - On approve/reject success + autoAdvance: calls `getNextUnreviewed()` and `advanceReview(nextId)`

- [x] **RI-030**: Create `useReviewStats` React Query hook
  - **File (new):** `frontend/src/hooks/useReviewStats.ts`
  - `useQuery(['review-stats', projectId])` with `refetchInterval: 10000` (10s)
  - Enabled only when `projectId` defined AND `reviewMode` is true

---

## 8. Frontend: Review Mode UI

- [x] **RI-031**: Add review mode toggle button to TopToolbar
  - **File:** `frontend/src/components/workspace/TopToolbar.tsx`
  - `ClipboardCheck` icon after AI Assist button (line 134)
  - Green highlight when active (`bg-green-600 text-white`)
  - Reads/dispatches `reviewMode` from store

- [x] **RI-032**: Add confidence filter slider to TopToolbar (review mode only)
  - **File:** `frontend/src/components/workspace/TopToolbar.tsx`
  - Compact range slider (0-100), displays ">= X%"
  - Dispatches `setReviewConfidenceFilter(value / 100)`
  - Only visible when `reviewMode === true`

- [x] **RI-033**: Add auto-accept button to TopToolbar (review mode only)
  - **File:** `frontend/src/components/workspace/TopToolbar.tsx`
  - `Zap` icon, "Auto-Accept >= {threshold}%"
  - Calls `autoAcceptMutation.mutate()`, shows spinner while pending
  - Success notification via `useNotificationContext()`

- [x] **RI-034**: Create review keyboard shortcuts hook
  - **File (new):** `frontend/src/hooks/useReviewKeyboardShortcuts.ts`
  - Only active when `reviewMode === true`
  - Uses `shouldFireShortcut(e)` to gate
  - Keys: `A`=approve, `R`=reject (opens reason dialog), `S`/`N`/`ArrowRight`=skip, `ArrowLeft`/`P`=previous, `E`=edit, `Escape`=exit review
  - Review shortcuts override drawing tool shortcuts when reviewMode is active

- [x] **RI-035**: Create ReviewMeasurementPanel component
  - **File (new):** `frontend/src/components/workspace/ReviewMeasurementPanel.tsx`
  - Shows for `reviewCurrentId`: geometry type, quantity, unit, AI confidence badge (green/yellow/red), AI model, review status, notes textarea, Approve/Reject/Skip buttons, expandable history section

- [x] **RI-036**: Integrate ReviewMeasurementPanel into RightPanel with tabs
  - **File:** `frontend/src/components/workspace/RightPanel.tsx`
  - When `reviewMode === true`: show tab bar ("Conditions" | "Review"), auto-switch to Review tab
  - When `reviewMode === false`: show ConditionPanel only (current behavior)

---

## 9. Frontend: Review Statistics

- [x] **RI-037**: Add review statistics to BottomStatusBar
  - **File:** `frontend/src/components/workspace/BottomStatusBar.tsx`
  - When `reviewMode === true`: display "Review: X/Y approved | Z pending | W rejected"
  - Color-coded counts (green/yellow/red)
  - Add `projectId: string` prop, update `TakeoffWorkspace.tsx` to pass it

- [x] **RI-038**: Add review progress indicator to TopToolbar
  - **File:** `frontend/src/components/workspace/TopToolbar.tsx`
  - When `reviewMode === true`: show "14/32 reviewed" fraction
  - Calculated from stats: `reviewed = total - pending`

---

## 10. Frontend: Canvas Review Overlays

- [x] **RI-039**: Add confidence-based color coding to measurement overlays
  - **File:** `frontend/src/components/workspace/CenterCanvas.tsx`
  - When `reviewMode === true`: override condition colors with confidence colors
    - `ai_confidence >= 0.9` → green (`#22C55E`)
    - `0.7 <= ai_confidence < 0.9` → yellow (`#EAB308`)
    - `ai_confidence < 0.7` or null → red (`#EF4444`)
  - Apply confidence filter: hide measurements below `reviewConfidenceFilter`
  - Add constants to `frontend/src/lib/constants.ts`: `REVIEW_CONFIDENCE_HIGH`, `REVIEW_CONFIDENCE_MEDIUM`, `REVIEW_COLOR_HIGH/MEDIUM/LOW`

- [x] **RI-040**: Add pulsing highlight for currently reviewed measurement
  - **File:** `frontend/src/components/workspace/CenterCanvas.tsx`
  - When `reviewCurrentId` matches: render pulsing outline via Konva animation (strokeWidth 2-6px cycle)
  - Auto-center viewport on the measurement if off-screen

- [x] **RI-041**: Filter rejected measurements from canvas
  - **File:** `frontend/src/components/workspace/CenterCanvas.tsx`
  - Filter: `measurements.filter(m => !m.is_rejected)`
  - In review mode, also apply: `m.ai_confidence == null || m.ai_confidence >= reviewConfidenceFilter`

---

## 11. Testing & Verification

- [x] **RI-042**: Backend review service unit tests
  - **File (new):** `backend/tests/unit/test_review_service.py`
  - Tests: approve sets is_verified + creates history, reject sets is_rejected + stores reason, modify stores original_geometry on first edit, auto_accept skips verified/rejected, get_review_stats correct counts, get_next_unreviewed returns lowest confidence

- [x] **RI-043**: Backend review API integration tests
  - **File (new):** `backend/tests/integration/test_review_api.py`
  - Tests: all 7 endpoints return correct status codes and response shapes, 404 on non-existent ID, reject requires reason

- [x] **RI-044**: Frontend workspace store review mode tests
  - **File:** `frontend/src/components/workspace/__tests__/workspaceStore.test.ts` (extend)
  - Tests: toggle/set review mode, advanceReview updates both IDs, escapeAll clears review, setReviewMode(true) forces select tool

- [x] **RI-045**: Frontend ReviewMeasurementPanel tests
  - **File (new):** `frontend/src/components/workspace/__tests__/ReviewMeasurementPanel.test.tsx`
  - Tests: renders measurement details, confidence badge colors, approve/reject/skip button interactions

- [x] **RI-046**: End-to-end verification gate
  ```bash
  cd backend && pytest tests/ -v --tb=short
  cd frontend && npx tsc --noEmit && npm run lint && npm test -- --run
  ```

---

## Dependency Graph

```
RI-001..004 (Model + Migration)
  └── RI-005..007 (Measurement extensions + response schema)
         └── RI-008..011 (Review schemas)
                └── RI-012..018 (Review service)
                       └── RI-019..022 (API routes + registration)
                              ↓
RI-023..026 (Store extensions)
  └── RI-027..028 (API client + types)
         └── RI-029..030 (React Query hooks)
                ├── RI-031..033 (TopToolbar UI)
                ├── RI-034 (Keyboard shortcuts)
                ├── RI-035..036 (ReviewPanel + RightPanel tabs)
                ├── RI-037..038 (Statistics)
                └── RI-039..041 (Canvas overlays)
                       └── RI-042..046 (Tests)
```

---

## Implementation Order (Suggested Days)

### Day 1: Backend Models, Migration, Schemas (RI-001 → RI-011)
- MeasurementHistory model, relationship, registration
- Measurement model extensions (is_rejected, review fields)
- Alembic migration
- All Pydantic schemas
- **Goal:** Database schema complete, migration runs cleanly

### Day 2: Backend Service & API (RI-012 → RI-022)
- ReviewService with all 7 methods
- Review API routes with all endpoints
- Router registration
- Backend tests
- **Goal:** All review endpoints callable via curl/Swagger, backend tests pass

### Day 3: Frontend Store, API, Hooks (RI-023 → RI-030)
- workspaceStore review extensions
- Review API client
- Measurement type updates
- useReviewActions + useReviewStats hooks
- Store tests
- **Goal:** Frontend can call all review endpoints, store manages review state

### Day 4: Frontend UI & Canvas (RI-031 → RI-046)
- TopToolbar: review toggle, confidence slider, auto-accept, progress
- ReviewMeasurementPanel + RightPanel tabs
- Keyboard shortcuts hook
- BottomStatusBar review stats
- Canvas: confidence coloring, pulsing highlight, rejected filtering
- All remaining tests + verification gate
- **Goal:** Complete review workflow end-to-end with keyboard shortcuts

---

## Acceptance Criteria

Phase 2 is complete when a user can:

1. Toggle review mode via TopToolbar button
2. See measurements color-coded by AI confidence (green/yellow/red)
3. See currently reviewed measurement with pulsing outline
4. Press `A` to approve (sets is_verified, logs history, auto-advances)
5. Press `R` to reject (prompts for reason, soft-deletes, hides from canvas)
6. Press `S`/`N`/ArrowRight to skip to next unreviewed measurement
7. Press `E` to edit measurement geometry
8. Use confidence filter slider to hide low-confidence measurements
9. Click "Auto-Accept >= 90%" to batch-approve high-confidence AI measurements
10. See review statistics in BottomStatusBar
11. See review progress in TopToolbar
12. View Review tab in RightPanel with measurement details and action buttons
13. View full audit history for any measurement
14. Exit review mode with Escape, restoring normal coloring
15. All tests pass: backend `pytest` + frontend `tsc && lint && test`

---

## Technical Notes

### Review Status (Boolean Approach)
- **Pending:** `is_verified=False AND is_rejected=False`
- **Approved:** `is_verified=True AND is_rejected=False`
- **Rejected:** `is_rejected=True AND is_verified=False`
- **Modified:** `is_verified=True AND is_modified=True`
- Service enforces mutual exclusivity

### Keyboard Conflict Resolution
Review shortcuts (A, R, S, E) overlap with drawing tools (A=polygon, R=rectangle). When `reviewMode=true`, review shortcuts take precedence. `activeTool` is forced to `'select'` in review mode.

### Condition Totals Fix
`_update_condition_totals()` at `measurement_engine.py:302-306` must add `.where(Measurement.is_rejected == False)` so rejected measurements don't count toward condition totals.

### Critical Files Modified

| File | Action |
|------|--------|
| `backend/app/models/measurement.py` | Extended: is_rejected, review fields, history relationship |
| `backend/app/services/measurement_engine.py` | Fixed: _update_condition_totals excludes rejected |
| `backend/app/main.py` | Registered: review router + MeasurementHistory import |
| `backend/app/models/__init__.py` | Registered: MeasurementHistory |
| `backend/app/schemas/measurement.py` | Extended: MeasurementResponse with review fields |
| `frontend/src/stores/workspaceStore.ts` | Extended: review mode state/actions/selectors |
| `frontend/src/types/index.ts` | Extended: Measurement type + review types |
| `frontend/src/components/workspace/TopToolbar.tsx` | Added: review toggle, slider, auto-accept, progress |
| `frontend/src/components/workspace/RightPanel.tsx` | Added: tab switching for review panel |
| `frontend/src/components/workspace/BottomStatusBar.tsx` | Added: review stats display |
| `frontend/src/components/workspace/CenterCanvas.tsx` | Added: confidence coloring, pulsing, rejected filter |
| `frontend/src/components/workspace/TakeoffWorkspace.tsx` | Wired: review actions, keyboard shortcuts, props |
| `frontend/src/lib/constants.ts` | Added: review confidence thresholds and colors |

### New Files Created

| File | Purpose |
|------|---------|
| `backend/app/models/measurement_history.py` | MeasurementHistory model |
| `backend/app/services/review_service.py` | ReviewService (8 methods) |
| `backend/app/api/routes/review.py` | Review API routes (7 endpoints) |
| `backend/app/schemas/review.py` | All review schemas |
| `backend/alembic/versions/o3p4q5r6s7t8_*.py` | Migration |
| `frontend/src/api/review.ts` | Review API client |
| `frontend/src/hooks/useReviewActions.ts` | Review mutation hook |
| `frontend/src/hooks/useReviewStats.ts` | Review stats query hook |
| `frontend/src/hooks/useReviewKeyboardShortcuts.ts` | Keyboard shortcuts |
| `frontend/src/components/workspace/ReviewMeasurementPanel.tsx` | Review details panel |
| `backend/tests/unit/test_review_service.py` | Review service unit tests |
| `backend/tests/integration/test_review_api.py` | Review API integration tests |
