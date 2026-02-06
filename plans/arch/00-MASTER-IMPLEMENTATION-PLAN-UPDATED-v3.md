# Master Implementation Plan (Updated v3)
## AI-Powered Construction Takeoff Platform

> **Last Updated**: February 2026
> **Version**: 3.0 (Kreo-Enhanced + Architecture Prep)
> **Total Duration**: ~38 weeks

---

## Executive Summary

This plan builds on v2.0 (Kreo-Enhanced) with four additional capabilities identified from competitive analysis. These are tiered by implementation urgency:

| Enhancement | Tier | When | Business Value |
|-------------|------|------|----------------|
| **Unified Async Task API** | Build Now | Integrated into current phases | Single polling pattern for all async ops; cleaner frontend |
| **Plan Overlay / Version Comparison** | Architect Now, Build Post-MVP | Phase 7B | Revision tracking for addenda — critical for real estimating |
| **Vector PDF Extraction** | Architect Now, Build Post-MVP | Phase 9 | Higher accuracy on CAD-exported PDFs |
| **Natural Language Query (AI Assistant)** | Stub Now, Build Post-MVP | Phase 10 | Conversational interface over project data |

### Cumulative Feature Set (v1 → v2 → v3)

| Version | Added Features |
|---------|---------------|
| **v1** (Original) | Document ingestion, OCR, classification, scale detection, measurement engine, conditions, AI takeoff, review, export |
| **v2** (Kreo-Enhanced) | Assembly system, auto count, enhanced review with keyboard shortcuts, quick adjust tools |
| **v3** (This Update) | Unified task API, plan overlay, vector PDF extraction, natural language query |

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
Phase 7B: Plan Overlay / Version Comparison ← NEW (Weeks 33-34)
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
- [ ] **NEW**: Capture `is_vector_pdf` and `has_extractable_geometry` metadata flags during ingestion (architecture prep for Phase 9)
- [ ] **NEW**: Store document revision metadata (`revision_number`, `revision_date`, `supersedes_document_id`) for Phase 7B

### Phase 2.5: Unified Async Task API ← **NEW — BUILD NOW**
**Duration**: Weeks 5-6 (parallel with Phase 2)
**Document**: `16-UNIFIED-TASK-API.md`

- [ ] Refactor `GET /tasks/{task_id}/status` from takeoff router to shared router
- [ ] Add `POST /tasks/{task_id}/cancel` endpoint
- [ ] Add `GET /projects/{id}/tasks` for project-level task listing
- [ ] Create shared `TaskResponse` schema used by all async operations
- [ ] Add progress reporting (percent complete, current step)
- [ ] WebSocket upgrade path for push-based status (stub only)
- [ ] Frontend `useTaskPolling` hook
- [ ] Ensure all Celery tasks (document, OCR, classification, scale, takeoff, auto count, export) return consistent result shapes

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

### Phase 7B: Plan Overlay / Version Comparison ← **NEW**
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

## Document Index

| Document | Phase | Status |
|----------|-------|--------|
| `01-PROJECT-SETUP.md` | 1 | Original |
| `02-DOCUMENT-INGESTION.md` | 2 | Original (needs revision metadata addition) |
| `03-OCR-TEXT-EXTRACTION.md` | 3A | Original |
| `04-PAGE-CLASSIFICATION.md` | 3B | Original |
| `05-SCALE-DETECTION.md` | 3C | Original |
| `06-MEASUREMENT-ENGINE.md` | 4A | Original |
| `07-CONDITION-MANAGEMENT.md` | 4B | Original |
| `08-AI-TAKEOFF-GENERATION.md` | 5A | Original |
| `09-REVIEW-INTERFACE-ENHANCED.md` | 6 | Enhanced |
| `10-EXPORT-SYSTEM.md` | 7A | Original |
| `11-TESTING-QA.md` | 8 | Original |
| `12-DEPLOYMENT.md` | 8 | Original |
| `13-ASSEMBLY-SYSTEM.md` | 4C | **v2 NEW** |
| `14-AUTO-COUNT.md` | 5B | **v2 NEW** |
| `15-QUICK-ADJUST-TOOLS.md` | 6 | **v2 NEW** |
| `16-UNIFIED-TASK-API.md` | 2.5 | **v3 NEW** |
| `17-KREO-ARCHITECTURE-PREP.md` | 7B, 9, 10 | **v3 NEW** |
| `18-UI-OVERHAUL.md` | A-E (parallel) | **v3 NEW** — Frontend rewrite spec (Phases A-E) |
| `18A-UI-OVERHAUL-AUDIT.md` | A-E (parallel) | **v3 NEW** — Architecture decisions & gap analysis |
| `18B-UI-OVERHAUL-PHASE-CONTEXTS.md` | A-E (parallel) | **v3 NEW** — Per-phase AI context files |

---

## UI/UX Overhaul (Parallel Frontend Track)

The UI overhaul (`18-UI-OVERHAUL.md`) represents a fundamental shift from "batch AI processing pipeline" to "estimator-first takeoff tool with AI assist." It runs as a **parallel frontend track** alongside the backend phases and touches:

| UI Phase | Maps To Backend Phase | Scope |
|----------|----------------------|-------|
| **Phase A**: Sheet Manager & Navigation | Phase 2 (Ingestion), 3B (Classification) | Sheet tree, workspace layout, batch ops |
| **Phase B**: Conditions Panel Overhaul | Phase 4B (Conditions) | Quick-create bar, properties inspector |
| **Phase C**: Plan Viewer & Drawing Tools | Phase 4A (Measurement), 6 (Review) | Undo/redo, snap, drawing tools, selection |
| **Phase D**: AI Assist Layer | Phase 5A (AI Takeoff) | AutoTab, ghost points, batch AI inline |
| **Phase E**: Export & Reporting | Phase 7A (Export) | Export dropdown, format options |

The audit (`18A-UI-OVERHAUL-AUDIT.md`) resolved 7 critical architectural gaps including global state architecture (Zustand), undo/redo with server sync, and persistence rules. These decisions apply to ALL frontend work.

The phase contexts (`18B-UI-OVERHAUL-PHASE-CONTEXTS.md`) provide focused AI context files for each phase — copy into Cursor rules when working on that phase.

---

## Architecture Decisions Made in v3

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

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| AI detection accuracy | 75%+ | Approved without changes / Total AI |
| Review throughput | 3x baseline | Measurements reviewed per hour |
| Auto count recall | 90%+ | Found / Actual instances |
| Assembly completeness | 95%+ | Components with formulas |
| Export accuracy | 100% | Quantity match original |
| Task status reliability | 100% | All async ops trackable via unified API |
| Revision tracking | 100% | All revisions linked to predecessors |

---

## Document Dependencies

```
01-PROJECT-SETUP.md
    └── 02-DOCUMENT-INGESTION.md
        ├── 16-UNIFIED-TASK-API.md ← NEW (parallel)
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
