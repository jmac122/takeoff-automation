# 20 — Vector PDF Extraction (Master Plan Phase 9)

> **Status:** Scoping / dev handoff
> **Priority:** HIGH — the deferred post-MVP phase with the largest accuracy payoff
> **Effort estimate:** 4–6 days
> **Depends on:** Nothing hard; pairs well with 22-ISOLATED-PDF-PARSING.md (run extraction in the isolated child)
> **Design reference (no code ported):** OpenConstructionERP `backend/app/modules/takeoff/recognize.py` — AGPL-3.0, reference for approach and threshold starting points only; our implementation is original code

---

## 1. Problem Statement

The entire measurement pipeline today is raster-based: pages are rendered to images (max 1568px), and geometry comes from either manual drawing or AI vision. But a large share of construction PDFs are CAD-generated and still carry their **vector drawing layer** — exact lines, rectangles, and closed polygons in PDF coordinate space. For those pages, reading the vectors directly yields measurements that are *exact* rather than ~75% AI-accurate, at near-zero inference cost.

The master plan reserved this as Phase 9 (post-MVP) and the schema prep was done in `17-KREO-ARCHITECTURE-PREP.md`: `Page` already has `is_vector`, `has_extractable_geometry`, `vector_path_count`, `vector_text_count` (see `backend/app/models/page.py` lines ~92–95). **Nothing currently writes these fields** — verified by grep: no references in `services/` or `workers/`. PyMuPDF is already a dependency (`pymupdf==1.23.18`) and is already imported in `backend/app/utils/pdf_utils.py`.

## 2. Feature Overview

Two deliverables:

**A. Vector detection at ingestion** — while processing an uploaded PDF, inspect each page's vector content and populate the four existing `Page` flags. Cheap (one `page.get_drawings()` + `page.get_text("words")` count per page), runs inside the existing document-processing Celery task.

**B. Vector extraction service** — an on-demand, deterministic candidate generator: given a vector-capable page and a target condition, read the drawing layer and propose candidate measurements the estimator confirms or rejects using the **existing review workflow** (draft styling, approve/reject shortcuts, MeasurementHistory audit trail). No AI call involved.

Guiding principle (same one the reference implementation follows, and the same one our review interface embodies): the system proposes with an honest confidence and a human confirms. Never auto-create verified measurements from vector extraction.

## 3. Detailed Requirements

### 3.1 Ingestion detection (deliverable A)

- Extend the document processing flow (`backend/app/services/document_processor.py` / `workers/document_tasks.py`) to compute per page:
  - `vector_path_count` = number of drawing paths from `page.get_drawings()`
  - `vector_text_count` = number of native text words/spans
  - `is_vector` = `vector_path_count >= PATH_THRESHOLD` (config, start at 50 — scanned rasters have ~0; CAD exports have hundreds to tens of thousands)
  - `has_extractable_geometry` = `is_vector` AND path count below a sanity ceiling (config, start at 50,000 — beyond that the sheet is hatch-dense and extraction quality collapses; still vector, but flag extraction off by default)
- Constants live in backend config/settings, not inline.
- Backfill: management command or one-off script to compute flags for already-ingested documents (`python -m scripts.backfill_vector_flags`).

### 3.2 Extraction service (deliverable B)

New module `backend/app/services/vector_extractor.py` — **pure and DB-free** at its core (mirrors the structure of `formula_engine.py`/`geometry_adjuster.py`): a function that consumes already-extracted PDF primitives and returns candidates, so unit tests run without a PDF or DB. A thin wrapper handles fitz I/O.

Candidate rules (starting thresholds; all configurable and expressed in PDF points):

| Rule | Produces | Notes |
|---|---|---|
| Closed loop / rectangle with area ≥ ~600 pt² | `area` candidate | Filters glyph outlines and tiny symbols |
| Straight stroke ≥ ~18 pt long | `linear` candidate | Filters hatching, leader ticks, noise |
| Cluster of ≥ 3 near-identical small closed shapes (bbox diagonal ≤ ~46 pt) | `count` candidate (one point per instance) | Repeated symbols: piers, footings, fixtures |
| Global cap | max ~40 candidates/page | Keeps review workload sane; keep highest-confidence |

Each candidate carries: `geometry_type`, points (in **page-image pixel space**, see 3.3), `confidence` (heuristic: how clean the loop is, how isolated the stroke is, cluster tightness), and a human-readable `reason` string ("closed rectangle, 4 segments, area 2,340 pt²") surfaced in the review UI.

### 3.3 Coordinate transform — the critical correctness detail

`get_drawings()` returns PDF-point coordinates. Measurements are stored in the pixel space of the rendered page image (max-1568px convention, master plan Decision 6). The extraction wrapper must apply the same scale factor used when the page image was rendered (`rendered_width / page.rect.width`) to every point, and account for any rotation applied at render time (`page.rotation`). Add an explicit unit test asserting a known PDF rectangle lands on the correct image pixels — a mismatch here silently corrupts every quantity via `pixels_per_foot`.

### 3.4 Task + API

- Celery task `vector_extract_task(page_id, condition_id, options)` in `workers/` registered through the TaskTracker register-before-enqueue pattern (as all tasks are post-`16-UNIFIED-TASK-API`).
- `POST /api/v1/pages/{page_id}/vector-extract` — body `{ condition_id, options? }`, returns `task_id`; 409/422 when `has_extractable_geometry` is false.
- On completion the task creates measurements with `is_verified=False` and AI-draft styling semantics (`is_ai_generated`-equivalent provenance recorded — add `source: "vector_extract"` to measurement extra metadata so exports and stats can distinguish vector-derived from LLM-derived drafts), logs `MeasurementHistory` entries with actor_type `system`.
- Quantities computed through the existing measurement engine using the page's calibrated scale — vector extraction does not bypass scale calibration (pair with `21-DETERMINISTIC-SCALE-DETECTION.md`, which makes calibration itself cheaper on vector pages).

### 3.5 Frontend

- In `TopToolbar.tsx` (or SheetTree context menu), a "Vector Extract" action visible only when the active sheet's `has_extractable_geometry` is true (expose the flags through the sheets endpoint / `DocumentResponse`).
- Runs via `useTaskPolling`; results land as draft measurements on the canvas; estimator reviews with the existing review mode (A/R/S keys). The candidate `reason` shows in the review details panel.
- Sheet tree: small "vector" badge on vector-capable sheets (pattern: `ScaleBadge.tsx`).

## 4. Out of Scope

- Vector text extraction for OCR replacement (covered separately by 21's use of the text layer).
- DWG/DXF/RVT/IFC ingestion (potential future feature via DDC cad2data converters; different pipeline entirely).
- Auto-matching extracted geometry to conditions (candidates always go to the explicitly selected condition).
- Diffing vector layers between revisions (interesting future extension of Plan Overlay).

## 5. Acceptance Criteria

1. Uploading a CAD-generated PDF sets `is_vector=true` with plausible path counts; uploading a scanned TIFF/PDF leaves flags false. Backfill script fills flags for existing documents.
2. On a calibrated vector page, vector extract produces candidate drafts whose quantities for clean rectangles match hand-drawn equivalents within 1% (exactness bounded only by scale calibration).
3. Coordinate-transform unit test passes for both unrotated and 90°-rotated pages.
4. All candidates arrive unverified, reviewable with existing keyboard workflow, with history entries; rejecting all candidates leaves no orphan data.
5. Raster/AI paths are untouched — full existing backend + frontend test suites pass.
6. A hatch-dense page (> ceiling path count) refuses extraction gracefully with a clear API error surfaced as a toast.

## 6. Testing Requirements

- Unit: pure candidate-generation tests feeding synthetic primitives (tuples, no fitz objects) — loop detection, stroke filtering, cluster detection, cap enforcement, confidence ordering.
- Unit: coordinate transform (programmatically generated one-page PDF fixtures via PyMuPDF in-test).
- Integration: endpoint flow (flag gating, task registration, draft measurement creation, history logging).
- Frontend: button gating on the flag; polling → drafts appear (mock task API per existing patterns).

## 7. Risks

- **Hatching/detail noise** is the classic failure mode — thresholds will need tuning against real plan sets; keep them in config and log per-rule rejection counts to ease tuning.
- **Large drawings**: `get_drawings()` on 50k-path sheets is memory-heavy — run extraction inside the isolated parser child from `22-ISOLATED-PDF-PARSING.md` once that lands.
- **User trust:** exact-looking vector drafts may tempt blind bulk-accept; keep them visually distinct as drafts and let review stats count them separately (the `source` provenance field enables this).
