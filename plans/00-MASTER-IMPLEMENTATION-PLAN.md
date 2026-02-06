# AI-Powered Construction Takeoff Platform
## Master Implementation Plan

> **Purpose**: This document serves as the **single authoritative roadmap** for building an AI-powered construction takeoff automation platform. It is designed to be used with an LLM coding assistant (Claude in Cursor) to incrementally build the system.
>
> **Version**: 4.0 (Consolidated)
> **Last Updated**: February 2026
> **Total Duration**: ~38 weeks to MVP + post-MVP phases
> **Supersedes**: `00-MASTER-IMPLEMENTATION-PLAN-MERGED.md`, `00-MASTER-IMPLEMENTATION-PLAN-UPDATED-v3.md`

---

## Project Overview

### What We're Building
An application that automates construction takeoff by:
1. Accepting PDF/TIFF plan sets
2. Using AI vision models to identify concrete and related scopes
3. Detecting and calibrating to drawing scales
4. Generating draft takeoffs with visual measurement overlays
5. Allowing human review and refinement
6. Exporting to Excel and On Screen Takeoff-compatible formats

### Target Accuracy
- **75% automated accuracy** with human review for the remaining 25%
- The system creates a "rough draft" that estimators refine

### Technology Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | React 18, TypeScript, Vite, TailwindCSS, Konva.js, PDF.js |
| **Backend** | Python 3.11+, FastAPI, Celery, SQLAlchemy |
| **Database** | PostgreSQL 15+, Redis 7+ |
| **AI/ML** | Claude 3.5 Sonnet, GPT-4o, Gemini 1.5/2.5, Grok — multi-provider, LLM-agnostic |
| **Storage** | MinIO (S3-compatible) |
| **Infrastructure** | Docker, Docker Compose, Nginx, GCP |

### Cumulative Feature Set

| Version | Added Features |
|---------|---------------|
| **v1** (Original) | Document ingestion, OCR, classification, scale detection, measurement engine, conditions, AI takeoff, review, export |
| **v2** (Kreo-Enhanced) | Assembly system, auto count, enhanced review with keyboard shortcuts, quick adjust tools |
| **v3** (Architecture Prep) | Unified task API, plan overlay prep, vector PDF detection, natural language query stub |
| **v4** (This Document) | UI overhaul parallel track, consolidated roadmap, completion status tracking |

### Kreo-Enhanced Features (v2)

Based on competitive analysis of Kreo.net, this platform includes professional-grade features:

| Feature | Original | Kreo-Enhanced |
|---------|----------|---------------|
| Conditions | Flat name/unit/depth model | Full assembly breakdown with formulas, costs, waste factors |
| Review | Manual approve/reject only | Auto-accept, keyboard shortcuts, confidence filtering, bulk ops |
| Counting | Manual click each item | Select one → find all similar automatically |
| Geometry editing | Mouse-only dragging | Keyboard nudge, snap, extend, trim, offset, split |

---

## Phase Overview

```
Phase 1: Project Setup (Weeks 1-3)
    ↓
Phase 2: Document Ingestion (Weeks 4-6)
    ↓                         ┌─────────────────────────────────┐
Phase 3A: OCR & Text          │ Phase 2.5: Unified Task API     │
  Extraction (Weeks 7-9)      │ (Weeks 5-6, parallel with       │
    ↓                         │  document ingestion)             │
Phase 3B: Page Classification  │ Spec: 16-UNIFIED-TASK-API.md   │
  (Weeks 10-12)               └─────────────────────────────────┘
    ↓
Phase 3C: Scale Detection (Weeks 13-15)
    ↓
Phase 4A: Measurement Engine (Weeks 16-17)
    ↓
Phase 4B: Condition Management (Weeks 18-19)
    ↓
Phase 4C: Assembly System (Weeks 20-22)
    ↓
Phase 5A: AI Takeoff Generation (Weeks 23-25)
    ↓
Phase 5B: Auto Count Feature (Weeks 26-27)
    ↓
Phase 6: Review Interface Enhanced (Weeks 28-30)
    ↓
Phase 7A: Export System (Weeks 31-32)
    ↓
Phase 7B: Plan Overlay / Version Comparison (Weeks 33-34)
    ↓
Phase 8: Testing & Deployment (Weeks 35-38)
    ↓
─── MVP COMPLETE ─── POST-MVP BELOW ───
    ↓
Phase 9: Vector PDF Extraction (Post-MVP)
    ↓
Phase 10: Natural Language Query / AI Assistant (Post-MVP)

─── PARALLEL FRONTEND TRACK (runs alongside backend phases) ───

UI Phase A: Sheet Manager & Navigation (2-3 weeks)
    ↓
UI Phase B: Conditions Panel Overhaul (2 weeks)
    ↓
UI Phase C: Plan Viewer & Drawing Tools (3-4 weeks)
    ↓
UI Phase D: AI Assist Layer (2-3 weeks)
    ↓
UI Phase E: Export & Reporting (1-2 weeks)
    Documents: 18-UI-OVERHAUL.md, 18A-UI-OVERHAUL-AUDIT.md, 18B-UI-OVERHAUL-PHASE-CONTEXTS.md
```

---

## Document Index

### Phase Documents

| Document | Phase | Status | Description |
|----------|-------|--------|-------------|
| `01-PROJECT-SETUP.md` | 1 | Original | Repository structure, dev environment, CI/CD |
| `02-DOCUMENT-INGESTION.md` | 2 | Original + v3 additions | PDF/TIFF upload, processing, storage |
| `03-OCR-TEXT-EXTRACTION.md` | 3A | Original | Text extraction, title block parsing |
| `04-PAGE-CLASSIFICATION.md` | 3B | Original | LLM vision for page type identification |
| `05-SCALE-DETECTION.md` | 3C | Original | Scale detection and calibration system |
| `06-MEASUREMENT-ENGINE.md` | 4A | Original | Core measurement tools and geometry |
| `06B-MANUAL-DRAWING-TOOLS.md` | 3A+ | Original | Manual drawing tools |
| `07-CONDITION-MANAGEMENT.md` | 4B | Original | Takeoff conditions data model and UI |
| `08-AI-TAKEOFF-GENERATION.md` | 5A | Original | Automated element detection and measurement |
| `09-REVIEW-INTERFACE-ENHANCED.md` | 6 | **Enhanced** | Human review with keyboard shortcuts, auto-accept |
| `10-EXPORT-SYSTEM.md` | 7A | Original | Excel and OST export functionality |
| `11-TESTING-QA.md` | 8 | Original | Testing strategy and quality assurance |
| `12-DEPLOYMENT.md` | 8 | Original | Production deployment and monitoring |
| `13-ASSEMBLY-SYSTEM.md` | 4C | **v2 NEW** | Assembly/cost system with formulas |
| `14-AUTO-COUNT.md` | 5B | **v2 NEW** | Template matching & LLM similarity detection |
| `15-QUICK-ADJUST-TOOLS.md` | 6 | **v2 NEW** | Precision geometry editing tools |
| `16-UNIFIED-TASK-API.md` | 2.5 | **v3 NEW** | Unified async task polling API |
| `17-KREO-ARCHITECTURE-PREP.md` | 7B, 9, 10 | **v3 NEW** | Schema prep for future features |
| `18-UI-OVERHAUL.md` | UI A-E | **v3 NEW** | Frontend rewrite spec (Phases A-E) |
| `18A-UI-OVERHAUL-AUDIT.md` | UI A-E | **v3 NEW** | Architecture decisions & gap analysis |
| `18B-UI-OVERHAUL-PHASE-CONTEXTS.md` | UI A-E | **v3 NEW** | Per-phase AI context files |

### How to Use These Documents

1. **Start each phase** by providing the relevant document to Cursor/Claude
2. **Include context** from previous phases as needed (the LLM will reference completed work)
3. **Task lists** in each document are designed to be worked through sequentially
4. **Code examples** show expected patterns—the LLM should follow these conventions

### Document Dependencies

```
01-PROJECT-SETUP.md
    └── 02-DOCUMENT-INGESTION.md
        ├── 16-UNIFIED-TASK-API.md (parallel)
        └── 03-OCR-TEXT-EXTRACTION.md
            └── 04-PAGE-CLASSIFICATION.md
                └── 05-SCALE-DETECTION.md
                    └── 06-MEASUREMENT-ENGINE.md
                        └── 07-CONDITION-MANAGEMENT.md
                            └── 13-ASSEMBLY-SYSTEM.md
                                └── 08-AI-TAKEOFF-GENERATION.md
                                    └── 14-AUTO-COUNT.md
                                        └── 09-REVIEW-INTERFACE-ENHANCED.md
                                            └── 15-QUICK-ADJUST-TOOLS.md
                                                └── 10-EXPORT-SYSTEM.md
                                                    └── 17-KREO-ARCHITECTURE-PREP.md
                                                        └── Plan Overlay (7B)
                                                            └── 11-TESTING-QA.md
                                                                └── 12-DEPLOYMENT.md
                                                                    ── MVP ──
                                                                    └── Vector PDF (Phase 9)
                                                                    └── NL Query (Phase 10)
```

---

## Detailed Phase Schedule

### Phase 1: Project Setup
**Duration**: Weeks 1-3
**Document**: `01-PROJECT-SETUP.md`

- [ ] Repository structure
- [ ] Development environment (Docker, PostgreSQL, Redis)
- [ ] FastAPI backend scaffold
- [ ] React + TypeScript frontend scaffold
- [ ] CI/CD pipeline

### Phase 2: Document Ingestion
**Duration**: Weeks 4-6
**Document**: `02-DOCUMENT-INGESTION.md`

- [ ] PDF upload and storage
- [ ] TIFF support
- [ ] Page extraction (fixed 1568px resolution)
- [ ] Thumbnail generation
- [ ] Document status tracking
- [ ] Capture `is_vector_pdf` and `has_extractable_geometry` metadata flags during ingestion (architecture prep for Phase 9)
- [ ] Store document revision metadata (`revision_number`, `revision_date`, `supersedes_document_id`) for Phase 7B

### Phase 2.5: Unified Async Task API
**Duration**: Weeks 5-6 (parallel with Phase 2)
**Document**: `16-UNIFIED-TASK-API.md`

- [ ] Refactor `GET /tasks/{task_id}/status` from takeoff router to shared router
- [ ] Add `POST /tasks/{task_id}/cancel` endpoint
- [ ] Add `GET /projects/{id}/tasks` for project-level task listing
- [ ] Create shared `TaskResponse` schema used by all async operations
- [ ] Add progress reporting (percent complete, current step)
- [ ] WebSocket upgrade path for push-based status (stub only)
- [ ] Frontend `useTaskPolling` hook
- [ ] Ensure all Celery tasks return consistent result shapes

### Phase 3A: OCR & Text Extraction
**Duration**: Weeks 7-9
**Document**: `03-OCR-TEXT-EXTRACTION.md`

- [ ] Tesseract OCR integration
- [ ] Text region detection
- [ ] Scale text extraction
- [ ] Dimension parsing

### Phase 3B: Page Classification
**Duration**: Weeks 10-12
**Document**: `04-PAGE-CLASSIFICATION.md`

- [ ] Multi-provider LLM integration (Claude, GPT-4o, Gemini, Grok)
- [ ] Plan type detection (foundation, slab, site, detail)
- [ ] Confidence scoring
- [ ] Classification review UI

### Phase 3C: Scale Detection
**Duration**: Weeks 13-15
**Document**: `05-SCALE-DETECTION.md`

- [ ] Scale bar detection via LLM
- [ ] Written scale parsing ("1/4" = 1'-0"")
- [ ] Manual calibration tool
- [ ] pixels_per_foot calculation

### Phase 4A: Measurement Engine
**Duration**: Weeks 16-17
**Document**: `06-MEASUREMENT-ENGINE.md`

- [ ] Geometry primitives (polygon, polyline, point, rectangle)
- [ ] Area calculation (Shoelace formula)
- [ ] Linear measurement
- [ ] Volume calculation (area × depth)
- [ ] Unit conversions

### Phase 4B: Condition Management
**Duration**: Weeks 18-19
**Document**: `07-CONDITION-MANAGEMENT.md`

- [ ] Condition CRUD API
- [ ] Condition templates (concrete types)
- [ ] Measurement grouping
- [ ] Condition totals

### Phase 4C: Assembly System
**Duration**: Weeks 20-22
**Document**: `13-ASSEMBLY-SYSTEM.md`

- [ ] Assembly model with components
- [ ] Formula engine for quantity calculations
- [ ] Component types (material, labor, equipment, subcontract)
- [ ] Assembly templates for concrete work
- [ ] Cost database integration
- [ ] Waste factors and productivity rates
- [ ] Markup and pricing calculations
- [ ] Assembly builder UI

### Phase 5A: AI Takeoff Generation
**Duration**: Weeks 23-25
**Document**: `08-AI-TAKEOFF-GENERATION.md`

- [ ] LLM-based element detection
- [ ] Multi-provider support with fallback
- [ ] Confidence scoring
- [ ] Boundary extraction
- [ ] Measurement generation

### Phase 5B: Auto Count Feature
**Duration**: Weeks 26-27
**Document**: `14-AUTO-COUNT.md`

- [ ] Template matching (OpenCV)
- [ ] LLM similarity detection
- [ ] Hybrid detection combining both methods
- [ ] User template selection
- [ ] Match review workflow
- [ ] Bulk measurement creation

### Phase 6: Review Interface Enhanced
**Duration**: Weeks 28-30
**Document**: `09-REVIEW-INTERFACE-ENHANCED.md`

- [ ] Review queue with confidence sorting
- [ ] Keyboard shortcuts (A/R/E/N/P)
- [ ] Auto-accept threshold feature
- [ ] Bulk operations
- [ ] Measurement history/audit trail
- [ ] AI vs Modified overlay
- [ ] Statistics dashboard
- [ ] Quick adjust tools (`15-QUICK-ADJUST-TOOLS.md`)

### Phase 7A: Export System
**Duration**: Weeks 31-32
**Document**: `10-EXPORT-SYSTEM.md`

- [ ] Excel export (detailed + summary)
- [ ] OST XML format
- [ ] CSV export
- [ ] PDF report generation

### Phase 7B: Plan Overlay / Version Comparison
**Duration**: Weeks 33-34
**Document**: `17-KREO-ARCHITECTURE-PREP.md` (architecture) → Full spec TBD

- [ ] Document revision linking (which doc supersedes which)
- [ ] Page-level matching across revisions (by page number, title block)
- [ ] Side-by-side overlay view (opacity slider, split view)
- [ ] Difference highlighting (new elements, removed elements, changed areas)
- [ ] Measurement delta report (what quantities changed between revisions)

### Phase 8: Testing & Deployment
**Duration**: Weeks 35-38
**Document**: `11-TESTING-QA.md`, `12-DEPLOYMENT.md`

- [ ] Unit tests (95% coverage for geometry)
- [ ] Integration tests
- [ ] E2E tests with Playwright
- [ ] AI accuracy benchmarking
- [ ] GCP deployment
- [ ] Monitoring setup

---

## Post-MVP Phases

These phases are architecturally prepared for (schema decisions, metadata flags, interface stubs) but not built until after MVP ships.

### Phase 9: Vector PDF Extraction (Post-MVP)
**Document**: `17-KREO-ARCHITECTURE-PREP.md` (architecture) → Full spec TBD
**Prerequisites**: Document ingestion captures vector metadata

- [ ] PDF path/object extraction using PyMuPDF or pdfplumber
- [ ] Vector geometry → measurement conversion
- [ ] Hybrid pipeline: vector extraction for CAD PDFs, raster for scanned
- [ ] Accuracy comparison: vector vs raster measurements
- [ ] Fallback to raster when vector extraction fails

### Phase 10: Natural Language Query / AI Assistant (Post-MVP)
**Document**: `17-KREO-ARCHITECTURE-PREP.md` (architecture) → Full spec TBD
**Prerequisites**: Measurements, conditions, and assemblies populated

- [ ] RAG pipeline over project data (measurements, conditions, assemblies, OCR text)
- [ ] Conversational interface ("What's the total slab area?", "How many piers on S1.01?")
- [ ] Query-to-SQL translation for structured data
- [ ] Multi-turn context (follow-up questions about same project)
- [ ] "Ask AI" button in project toolbar (stub added in Phase 6)

---

## UI/UX Overhaul (Parallel Frontend Track)

The UI overhaul (`18-UI-OVERHAUL.md`) represents a fundamental shift from "batch AI processing pipeline" to "estimator-first takeoff tool with AI assist." It runs as a **parallel frontend track** alongside the backend phases.

| UI Phase | Maps To Backend Phase | Scope |
|----------|----------------------|-------|
| **Phase A**: Sheet Manager & Navigation | Phase 2 (Ingestion), 3B (Classification) | Sheet tree, workspace layout, batch ops |
| **Phase B**: Conditions Panel Overhaul | Phase 4B (Conditions) | Quick-create bar, properties inspector |
| **Phase C**: Plan Viewer & Drawing Tools | Phase 4A (Measurement), 6 (Review) | Undo/redo, snap, drawing tools, selection |
| **Phase D**: AI Assist Layer | Phase 5A (AI Takeoff) | AutoTab, ghost points, batch AI inline |
| **Phase E**: Export & Reporting | Phase 7A (Export) | Export dropdown, format options |

The audit (`18A-UI-OVERHAUL-AUDIT.md`) resolved 7 critical architectural gaps including global state architecture (Zustand for UI state, React Query for server data), undo/redo with server sync, and persistence rules. These decisions apply to ALL frontend work.

The phase contexts (`18B-UI-OVERHAUL-PHASE-CONTEXTS.md`) provide focused AI context files for each phase — copy into Cursor rules when working on that phase.

---

## Architecture Decisions

### Decision 1: Unified Task API (Phase 2.5)
**Status**: Build now
**Rationale**: Currently `GET /tasks/{task_id}/status` exists only in the takeoff router. Document processing, OCR, classification, and scale tasks each have ad-hoc status checking. Unifying this into a shared `/api/tasks/` router prevents five different polling implementations and gives the frontend a single `useTaskPolling()` hook.

### Decision 2: Document Revision Metadata (Phase 2)
**Status**: Add schema now, build overlay UI in Phase 7B
**Rationale**: Adding `revision_number`, `revision_date`, and `supersedes_document_id` to the document model costs nothing but prevents a painful migration later. The plan overlay UI depends on being able to link documents across revisions.

### Decision 3: Vector PDF Detection (Phase 2)
**Status**: Add detection now, build extraction post-MVP
**Rationale**: During PDF ingestion, detecting whether a PDF contains extractable vector geometry (`is_vector_pdf` flag) is trivial with PyMuPDF. This metadata enables Phase 9 to selectively process vector PDFs without re-scanning the document library.

### Decision 4: AI Assistant Stub (Phase 6)
**Status**: Add UI placeholder now, build post-MVP
**Rationale**: Adding a disabled "Ask AI" button in the review interface costs nothing and signals the feature direction. The actual RAG pipeline depends on having real project data flowing through the system.

### Decision 5: Multi-Provider LLM Architecture
**Status**: Active throughout
**Rationale**: The system supports Claude, GPT-4o, Gemini, and Grok to avoid vendor lock-in and enable empirical comparison across tasks (classification, scale detection, element detection). Each task can use a different optimal provider.

### Decision 6: Fixed Resolution Image Processing
**Status**: Active
**Rationale**: All page images processed at max 1568px dimension. This eliminates coordinate translation bugs from on-the-fly compression and scale factor tracking. Pixel-based coordinates used throughout.

---

## Complete File Structure

```
takeoff-platform/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       ├── deploy-staging.yml
│       └── deploy-prod.yml
├── docker/
│   ├── Dockerfile.api
│   ├── Dockerfile.worker
│   ├── Dockerfile.frontend
│   └── docker-compose.yml
├── backend/
│   ├── alembic/
│   │   ├── versions/
│   │   └── env.py
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── dependencies.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── routes/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── projects.py
│   │   │   │   ├── documents.py
│   │   │   │   ├── pages.py
│   │   │   │   ├── conditions.py
│   │   │   │   ├── measurements.py
│   │   │   │   ├── tasks.py                 # v3: Unified task API
│   │   │   │   ├── assemblies.py            # v2: Assembly system
│   │   │   │   ├── auto_count.py            # v2: Auto count
│   │   │   │   ├── review.py               # v2: Enhanced review
│   │   │   │   ├── exports.py
│   │   │   │   └── health.py
│   │   │   └── deps.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── project.py
│   │   │   ├── document.py
│   │   │   ├── page.py
│   │   │   ├── condition.py
│   │   │   ├── measurement.py
│   │   │   ├── task_record.py               # v3: Unified task tracking
│   │   │   ├── assembly.py                  # v2: Assembly system
│   │   │   ├── auto_count.py                # v2: Auto count
│   │   │   └── export.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── project.py
│   │   │   ├── document.py
│   │   │   ├── page.py
│   │   │   ├── condition.py
│   │   │   ├── measurement.py
│   │   │   ├── task.py                      # v3: TaskResponse, TaskListResponse
│   │   │   ├── assembly.py                  # v2
│   │   │   ├── auto_count.py                # v2
│   │   │   ├── review.py                    # v2
│   │   │   └── export.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── document_processor.py
│   │   │   ├── ocr_service.py
│   │   │   ├── page_classifier.py
│   │   │   ├── scale_detector.py
│   │   │   ├── measurement_engine.py
│   │   │   ├── ai_takeoff.py
│   │   │   ├── task_tracker.py              # v3: TaskTracker helper
│   │   │   ├── assembly_service.py          # v2
│   │   │   ├── formula_engine.py            # v2
│   │   │   ├── auto_count_service.py        # v2
│   │   │   ├── template_matching.py         # v2
│   │   │   ├── llm_similarity.py            # v2
│   │   │   ├── review_service.py            # v2
│   │   │   ├── export_service.py
│   │   │   └── llm_client.py
│   │   ├── workers/
│   │   │   ├── __init__.py
│   │   │   ├── celery_app.py
│   │   │   ├── document_tasks.py
│   │   │   ├── ocr_tasks.py
│   │   │   ├── classification_tasks.py
│   │   │   ├── scale_tasks.py
│   │   │   ├── takeoff_tasks.py
│   │   │   ├── auto_count_tasks.py          # v2
│   │   │   └── export_tasks.py              # v2
│   │   ├── data/
│   │   │   ├── __init__.py
│   │   │   ├── assembly_templates.py        # v2
│   │   │   └── formula_presets.py           # v2
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── geometry.py
│   │       ├── image_processing.py
│   │       ├── pdf_utils.py
│   │       └── storage.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── factories/
│   │   ├── fixtures/
│   │   ├── test_api/
│   │   ├── test_services/
│   │   └── test_workers/
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── alembic.ini
│   └── pyproject.toml
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── vite-env.d.ts
│   │   ├── api/
│   │   │   ├── client.ts
│   │   │   ├── projects.ts
│   │   │   ├── documents.ts
│   │   │   ├── pages.ts
│   │   │   ├── conditions.ts
│   │   │   ├── measurements.ts
│   │   │   ├── tasks.ts                     # v3: Unified task polling
│   │   │   ├── assemblies.ts                # v2
│   │   │   ├── autoCount.ts                 # v2
│   │   │   ├── review.ts                    # v2
│   │   │   └── exports.ts
│   │   ├── components/
│   │   │   ├── ui/
│   │   │   │   └── [shadcn components]
│   │   │   ├── layout/
│   │   │   │   ├── Header.tsx
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   └── Layout.tsx
│   │   │   ├── project/
│   │   │   │   ├── ProjectList.tsx
│   │   │   │   ├── ProjectCard.tsx
│   │   │   │   └── CreateProjectModal.tsx
│   │   │   ├── document/
│   │   │   │   ├── DocumentUploader.tsx
│   │   │   │   ├── DocumentList.tsx
│   │   │   │   └── PageThumbnails.tsx
│   │   │   ├── viewer/
│   │   │   │   ├── PlanViewer.tsx
│   │   │   │   ├── ViewerToolbar.tsx
│   │   │   │   ├── MeasurementLayer.tsx
│   │   │   │   ├── ConditionLayer.tsx
│   │   │   │   └── ScaleCalibration.tsx
│   │   │   ├── takeoff/
│   │   │   │   ├── ConditionPanel.tsx
│   │   │   │   ├── ConditionList.tsx
│   │   │   │   ├── MeasurementTools.tsx
│   │   │   │   └── TakeoffSummary.tsx
│   │   │   ├── assembly/                    # v2
│   │   │   │   ├── AssemblyPanel.tsx
│   │   │   │   ├── AssemblyTemplateSelector.tsx
│   │   │   │   ├── ComponentEditor.tsx
│   │   │   │   └── FormulaBuilder.tsx
│   │   │   ├── autocount/                   # v2
│   │   │   │   ├── AutoCountTool.tsx
│   │   │   │   ├── AutoCountOverlay.tsx
│   │   │   │   └── DetectionReviewDialog.tsx
│   │   │   ├── review/                      # v2
│   │   │   │   ├── ReviewPanel.tsx
│   │   │   │   ├── StatisticsPanel.tsx
│   │   │   │   ├── QuickAdjustToolbar.tsx
│   │   │   │   └── MeasurementHistory.tsx
│   │   │   └── export/
│   │   │       ├── ExportModal.tsx
│   │   │       └── ExportPreview.tsx
│   │   ├── hooks/
│   │   │   ├── useProjects.ts
│   │   │   ├── useDocuments.ts
│   │   │   ├── usePages.ts
│   │   │   ├── useConditions.ts
│   │   │   ├── useMeasurements.ts
│   │   │   ├── useTaskPolling.ts            # v3: Unified task hook
│   │   │   ├── useViewer.ts
│   │   │   ├── useKeyboardShortcuts.ts
│   │   │   └── useQuickAdjust.ts            # v2
│   │   ├── services/
│   │   │   └── geometry-adjustment.ts       # v2
│   │   ├── stores/
│   │   │   ├── projectStore.ts
│   │   │   ├── viewerStore.ts
│   │   │   ├── workspaceStore.ts            # v3 UI: Zustand workspace state
│   │   │   ├── takeoffStore.ts
│   │   │   └── uiStore.ts
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── ProjectDetail.tsx
│   │   │   ├── TakeoffWorkspace.tsx
│   │   │   ├── ReviewWorkspace.tsx          # v2
│   │   │   └── Settings.tsx
│   │   ├── lib/
│   │   │   ├── utils.ts
│   │   │   ├── constants.ts                 # v3 UI: All magic numbers
│   │   │   ├── geometry.ts
│   │   │   ├── pdfRenderer.ts
│   │   │   └── exportHelpers.ts
│   │   ├── types/
│   │   │   ├── index.ts
│   │   │   ├── project.ts
│   │   │   ├── document.ts
│   │   │   ├── page.ts
│   │   │   ├── condition.ts
│   │   │   ├── measurement.ts
│   │   │   ├── assembly.ts                  # v2
│   │   │   ├── autoCount.ts                 # v2
│   │   │   └── geometry.ts                  # v2
│   │   └── styles/
│   │       └── globals.css
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── postcss.config.js
├── plans/
│   ├── arch/
│   ├── prompts/
│   │   ├── branch-a-task-migration.md
│   │   ├── branch-b-export-system.md
│   │   ├── branch-c-ui-overhaul-phase-a.md
│   │   ├── migrate-tasks-to-tracker-prompt-v2.md
│   │   └── unified-task-api-prompt.md
│   ├── 00-MASTER-IMPLEMENTATION-PLAN.md     ← THIS FILE (canonical)
│   ├── 01-PROJECT-SETUP.md
│   ├── 02-DOCUMENT-INGESTION.md
│   │   ... (all phase documents)
│   ├── 18-UI-OVERHAUL.md
│   ├── 18A-UI-OVERHAUL-AUDIT.md
│   └── 18B-UI-OVERHAUL-PHASE-CONTEXTS.md
├── scripts/
│   ├── setup-dev.sh
│   ├── seed-db.py
│   ├── seed-assembly-templates.py           # v2
│   └── generate-test-data.py
├── docs/
│   ├── api/
│   ├── architecture/
│   └── user-guide/
├── .env.example
├── .gitignore
├── README.md
└── Makefile
```

---

## Database Schema Overview

### Core Data Model

```
Project (1) ──< Document (many) ──< Page (many)
    │                                    │
    ├──< TaskRecord (many)               ▼
    │                            Measurement (many)
    ▼                                    ▲
Condition (many) ────────────────────────┘
    │
    ▼
Assembly (1:1) ──< AssemblyComponent (many)
```

### Key Relationships
- **Project** has many **Documents** (plan sets)
- **Document** has many **Pages** (individual sheets)
- **Project** has many **Conditions** (takeoff line items)
- **Condition** has many **Measurements** (geometric shapes on pages)
- **Measurement** belongs to one **Page** and one **Condition**
- **Project** has many **TaskRecords** (async operation tracking)
- **Condition** has one **Assembly** (cost breakdown)
- **Assembly** has many **AssemblyComponents** (material, labor, equipment)

### Extended Entities (v2+)

```
┌─────────────┐     ┌───────────────────┐
│  Condition  │────<│     Assembly      │
└─────────────┘     └───────────────────┘
                            │
                            ▼
                    ┌───────────────────┐
                    │ AssemblyComponent │
                    └───────────────────┘

┌─────────────┐     ┌───────────────────┐     ┌───────────────────┐
│    Page     │────<│ AutoCountSession  │────<│ AutoCountDetection│
└─────────────┘     └───────────────────┘     └───────────────────┘

┌─────────────┐     ┌───────────────────┐
│ Measurement │────<│ MeasurementHistory│
└─────────────┘     └───────────────────┘

┌─────────────┐     ┌───────────────────┐
│   Project   │────<│   TaskRecord      │  (v3: Unified task tracking)
└─────────────┘     └───────────────────┘
```

### Database Tables Detail

```sql
-- v3: Unified Task Tracking
task_records
├── id (UUID PK), task_id (Celery task ID, unique, indexed)
├── project_id (FK → projects), task_type, task_name
├── status (PENDING/STARTED/PROGRESS/SUCCESS/FAILURE/REVOKED)
├── progress_percent (0-100), current_step
├── result (JSON), error_message, traceback
├── created_at, updated_at, started_at, completed_at
└── celery_task_id, worker_hostname

-- v2: Assembly System
assemblies
├── id, condition_id (1:1)
├── name, csi_code
├── default_waste_percent, productivity_rate, crew_size
├── material_cost, labor_cost, equipment_cost, subcontract_cost
├── total_cost, unit_cost
├── overhead_percent, profit_percent, sell_price
└── is_locked

assembly_components
├── id, assembly_id
├── name, component_type (material/labor/equipment/subcontract/other)
├── quantity_formula, unit, unit_cost
├── waste_percent, calculated_quantity, quantity_with_waste
├── extended_cost, labor_hours
└── sort_order, is_included, is_optional

assembly_templates
├── id, name, scope (system/organization/project)
├── category, csi_code
├── measurement_type, expected_unit
├── component_definitions (JSON)
└── is_system, version

cost_items
├── id, code, name
├── item_type, category
├── unit, unit_cost
├── labor_rate, hourly_rate, daily_rate
└── vendor, effective_date, region

-- v2: Auto Count
auto_count_sessions
├── id, page_id, condition_id
├── template_center_x/y, template_width/height, template_image_data
├── detection_method (template_match/llm_embedding/hybrid)
├── similarity_threshold, scale_tolerance, rotation_tolerance
├── search_scope (page/document/selected_pages)
├── total_detections, confirmed_count, rejected_count, pending_count
└── status, processing_time_ms

auto_count_detections
├── id, session_id, page_id
├── center_x/y, width, height, rotation, bounding_box
├── similarity_score, template_match_score, llm_embedding_score
├── detected_by, review_status (pending/confirmed/rejected)
├── rank
└── measurement_id (nullable, set after creation)

-- v2: Review System
measurement_history
├── id, measurement_id
├── action (created/approved/rejected/modified/verified/flagged)
├── actor, actor_type (user/system/auto_accept)
├── previous_status, new_status
├── previous_geometry, new_geometry, previous_quantity, new_quantity
├── change_description, change_reason
└── session_id, ip_address

review_sessions
├── id, reviewer, project_id
├── started_at, ended_at
├── measurements_reviewed/approved/rejected/modified/flagged
├── auto_accepted_count, auto_accept_threshold
├── total_review_time_seconds, avg_time_per_measurement_seconds
└── settings (JSON)
```

---

## API Endpoints Overview

### Projects
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/projects` | List all projects |
| POST | `/api/v1/projects` | Create new project |
| GET | `/api/v1/projects/{id}` | Get project details |
| PUT | `/api/v1/projects/{id}` | Update project |
| DELETE | `/api/v1/projects/{id}` | Delete project |

### Documents
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/projects/{id}/documents` | Upload document |
| GET | `/api/v1/documents/{id}` | Get document details |
| GET | `/api/v1/documents/{id}/status` | Get processing status |
| DELETE | `/api/v1/documents/{id}` | Delete document |

### Pages
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/documents/{id}/pages` | List document pages |
| GET | `/api/v1/pages/{id}` | Get page details |
| PUT | `/api/v1/pages/{id}/scale` | Set/update page scale |
| GET | `/api/v1/pages/{id}/image` | Get page image |
| GET | `/api/v1/projects/{id}/sheets` | List all project sheets (UI overhaul) |

### Conditions
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/projects/{id}/conditions` | List project conditions |
| POST | `/api/v1/projects/{id}/conditions` | Create condition |
| PUT | `/api/v1/conditions/{id}` | Update condition |
| DELETE | `/api/v1/conditions/{id}` | Delete condition |

### Measurements
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/conditions/{id}/measurements` | List measurements |
| POST | `/api/v1/conditions/{id}/measurements` | Create measurement |
| PUT | `/api/v1/measurements/{id}` | Update measurement |
| DELETE | `/api/v1/measurements/{id}` | Delete measurement |
| POST | `/api/v1/pages/{id}/ai-takeoff` | Trigger AI takeoff |

### Tasks (v3: Unified API)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/tasks/{task_id}` | Unified task status |
| POST | `/api/v1/tasks/{task_id}/cancel` | Cancel running task |
| GET | `/api/v1/tasks/project/{project_id}` | List project tasks |

### Exports
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/projects/{id}/export` | Generate export |
| GET | `/api/v1/exports/{id}` | Get export status/download |

### Assemblies (v2)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/assembly-templates` | List assembly templates |
| POST | `/api/v1/conditions/{id}/assembly` | Create assembly from template |
| GET | `/api/v1/assemblies/{id}` | Get assembly with components |
| PUT | `/api/v1/assemblies/{id}` | Update assembly settings |
| POST | `/api/v1/assemblies/{id}/calculate` | Recalculate quantities/costs |
| POST | `/api/v1/assemblies/{id}/lock` | Lock assembly |
| POST | `/api/v1/assemblies/{id}/components` | Add component |
| PUT | `/api/v1/components/{id}` | Update component |
| DELETE | `/api/v1/components/{id}` | Remove component |
| GET | `/api/v1/cost-items` | List cost database items |
| POST | `/api/v1/formulas/validate` | Validate formula |
| GET | `/api/v1/formulas/presets` | Get formula presets |

### Auto Count (v2)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/pages/{id}/auto-count` | Start auto count session |
| GET | `/api/v1/auto-count/{id}` | Get session with detections |
| GET | `/api/v1/auto-count/{id}/detections` | List detections with filters |
| POST | `/api/v1/auto-count/detections/{id}/confirm` | Confirm single detection |
| POST | `/api/v1/auto-count/detections/{id}/reject` | Reject detection |
| POST | `/api/v1/auto-count/{id}/bulk-confirm` | Bulk confirm above threshold |
| POST | `/api/v1/auto-count/{id}/create-measurements` | Create measurements from confirmed |
| DELETE | `/api/v1/auto-count/{id}` | Delete session |

### Review (v2)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/projects/{id}/review-queue` | Get filtered review queue |
| POST | `/api/v1/measurements/{id}/approve` | Approve measurement |
| POST | `/api/v1/measurements/{id}/reject` | Reject measurement |
| POST | `/api/v1/measurements/{id}/modify` | Modify measurement geometry |
| POST | `/api/v1/measurements/{id}/verify` | Second-level verification |
| POST | `/api/v1/measurements/{id}/flag` | Flag for additional review |
| POST | `/api/v1/projects/{id}/review/bulk-approve` | Bulk approve |
| POST | `/api/v1/projects/{id}/review/bulk-reject` | Bulk reject |
| POST | `/api/v1/projects/{id}/review/auto-accept` | Auto-accept high confidence |
| GET | `/api/v1/projects/{id}/review/statistics` | Get review statistics |
| GET | `/api/v1/measurements/{id}/history` | Get measurement audit trail |

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| AI detection accuracy | 75%+ | Approved without changes / Total AI |
| Review throughput | 3x baseline | Measurements reviewed per hour |
| Auto count recall | 90%+ | Found / Actual instances |
| Auto count precision | 85%+ | True positives / Total detections |
| Assembly completeness | 95%+ | Components with formulas |
| Export accuracy | 100% | Quantity match original |
| Task status reliability | 100% | All async ops trackable via unified API |
| Revision tracking | 100% | All revisions linked to predecessors |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Assembly formula complexity | Pre-built templates for common concrete work |
| Auto count false positives | Confidence threshold + manual review |
| Review speed regression | Keyboard shortcuts + auto-accept |
| Feature creep | Phase gates with verification checklists |
| Task API migration | Backward-compatible; old endpoints redirect to new |
| Plan overlay complexity | Start with simple opacity overlay, add diff later |
| Vector PDF edge cases | Always fall back to raster pipeline |
| LLM vendor changes | Multi-provider architecture, no single-vendor dependency |

---

## Important Conventions

### Code Style
- **Python**: Follow PEP 8, use type hints, async/await for I/O
- **TypeScript**: Strict mode, explicit return types, functional components
- **Naming**: snake_case (Python), camelCase (TypeScript), PascalCase (components/classes)

### Git Workflow
- `main` — production-ready code
- `develop` — integration branch
- `feature/*` — new features
- `fix/*` — bug fixes

### Testing Standards
- **Coverage targets**: 80%+ overall, 85%+ for core business logic, 95%+ for geometry calculations
- **Test types**: Unit, integration, E2E (Playwright), AI accuracy benchmarks
- **Test-first methodology**: Write tests in the same commit as feature code
- **Required for every PR**: All tests pass, zero session warnings, coverage maintained

### Environment Variables
All configuration via environment variables. Never commit secrets.

---

## Getting Started

1. **Begin with `01-PROJECT-SETUP.md`** to establish your repository and development environment
2. **Follow the task lists** in sequential order within each phase document
3. **Provide context to the LLM** by including relevant completed code when starting new phases
4. **Run tests continuously** as specified in each phase
5. **Reference this master plan** when you need the full picture of how phases connect

---

## Next Step

→ **Open `01-PROJECT-SETUP.md`** and provide it to your LLM assistant to begin.
