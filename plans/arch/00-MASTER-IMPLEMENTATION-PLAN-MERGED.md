# AI-Powered Construction Takeoff Platform
## Master Implementation Plan

> **Purpose**: This document serves as the master guide for building an AI-powered construction takeoff automation platform. It is designed to be used with an LLM coding assistant (Claude Opus 4.5 in Cursor) to incrementally build the system.
> 
> **Version**: 2.0 (Kreo-Enhanced)
> **Last Updated**: January 2026

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

### Technology Stack Summary
| Layer | Technologies |
|-------|-------------|
| **Frontend** | React 18, TypeScript, Vite, TailwindCSS, Konva.js, PDF.js |
| **Backend** | Python 3.11+, FastAPI, Celery, SQLAlchemy |
| **Database** | PostgreSQL 15+, Redis 7+ |
| **AI/ML** | Claude 3.5 Sonnet API, OpenCV, PyTorch, YOLO, Google Cloud Vision |
| **Storage** | MinIO (S3-compatible) |
| **Infrastructure** | Docker, Docker Compose, Nginx |

---

## Kreo-Enhanced Features (v2.0)

Based on competitive analysis of Kreo.net, this update adds professional-grade features:

| Enhancement | Business Value |
|-------------|----------------|
| **Assembly System** | Real estimating workflow with material/labor/equipment breakdowns |
| **Auto Count** | 10x faster counting of repetitive elements (piers, columns, bolts) |
| **Enhanced Review** | 50% faster review with auto-accept and keyboard shortcuts |
| **Quick Adjust Tools** | Precision geometry editing without dialog boxes |

### Feature Comparison: Before vs After

| Feature | Original | Kreo-Enhanced |
|---------|----------|---------------|
| Conditions | Flat name/unit/depth model | Full assembly breakdown with formulas, costs, waste factors |
| Review | Manual approve/reject only | Auto-accept, keyboard shortcuts, confidence filtering, bulk ops |
| Counting | Manual click each item | Select one → find all similar automatically |
| Geometry editing | Mouse-only dragging | Keyboard nudge, snap, extend, trim, offset, split |

---

## Document Structure

This implementation plan is divided into **modular phase documents**. Feed each document to your LLM assistant as you begin that phase.

### Phase Documents

| Document | Phase | Duration | Description |
|----------|-------|----------|-------------|
| `01-PROJECT-SETUP.md` | 0 | Week 1 | Repository structure, dev environment, CI/CD |
| `02-DOCUMENT-INGESTION.md` | 1 | Weeks 2-5 | PDF/TIFF upload, processing, storage |
| `03-OCR-TEXT-EXTRACTION.md` | 1 | Weeks 4-6 | Text extraction, title block parsing |
| `04-PAGE-CLASSIFICATION.md` | 2 | Weeks 6-9 | LLM vision for page type identification |
| `05-SCALE-DETECTION.md` | 2 | Weeks 8-11 | Scale detection and calibration system |
| `06-MEASUREMENT-ENGINE.md` | 3 | Weeks 10-16 | Core measurement tools and geometry |
| `07-CONDITION-MANAGEMENT.md` | 3 | Weeks 14-18 | Takeoff conditions data model and UI |
| `08-AI-TAKEOFF-GENERATION.md` | 4 | Weeks 16-22 | Automated element detection and measurement |
| `09-REVIEW-INTERFACE-ENHANCED.md` | 4 | Weeks 20-26 | Human review and refinement UI (**ENHANCED**) |
| `10-EXPORT-SYSTEM.md` | 5 | Weeks 24-28 | Excel and OST export functionality |
| `11-TESTING-QA.md` | 5 | Weeks 26-32 | Testing strategy and quality assurance |
| `12-DEPLOYMENT.md` | 6 | Weeks 30-36 | Production deployment and monitoring |
| `13-ASSEMBLY-SYSTEM.md` | 3+ | Weeks 18-22 | Assembly/cost system with formulas (**NEW**) |
| `14-AUTO-COUNT.md` | 4+ | Weeks 22-25 | Template matching & LLM similarity detection (**NEW**) |
| `15-QUICK-ADJUST-TOOLS.md` | 4 | Weeks 20-26 | Precision geometry editing tools (**NEW**) |

### New Document Index (v2.0)

| Document | Status | Description |
|----------|--------|-------------|
| `13-ASSEMBLY-SYSTEM.md` | **NEW** | Full component breakdown with formulas, costs, waste factors |
| `14-AUTO-COUNT.md` | **NEW** | Select one object, find all similar automatically |
| `09-REVIEW-INTERFACE-ENHANCED.md` | **ENHANCED** | Keyboard shortcuts, auto-accept, confidence filtering |
| `15-QUICK-ADJUST-TOOLS.md` | **NEW** | Nudge, snap, extend, trim, offset, split tools |

### How to Use These Documents

1. **Start each phase** by providing the relevant document to Cursor/Opus
2. **Include context** from previous phases as needed (the LLM will reference completed work)
3. **Task lists** in each document are designed to be worked through sequentially
4. **Code examples** show expected patterns—the LLM should follow these conventions

### Document Dependencies

```
01-PROJECT-SETUP.md
    └── 02-DOCUMENT-INGESTION.md
        └── 03-OCR-TEXT-EXTRACTION.md
            └── 04-PAGE-CLASSIFICATION.md
                └── 05-SCALE-DETECTION.md
                    └── 06-MEASUREMENT-ENGINE.md
                        └── 07-CONDITION-MANAGEMENT.md
                            └── 13-ASSEMBLY-SYSTEM.md ← NEW
                                └── 08-AI-TAKEOFF-GENERATION.md
                                    └── 14-AUTO-COUNT.md ← NEW
                                        └── 09-REVIEW-INTERFACE-ENHANCED.md
                                            └── 15-QUICK-ADJUST-TOOLS.md ← NEW
                                                └── 10-EXPORT-SYSTEM.md
                                                    └── 11-TESTING-QA.md
                                                        └── 12-DEPLOYMENT.md
```

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
│   │   │   │   ├── assemblies.py          # NEW
│   │   │   │   ├── auto_count.py          # NEW
│   │   │   │   ├── review.py              # NEW
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
│   │   │   ├── assembly.py                # NEW
│   │   │   ├── auto_count.py              # NEW
│   │   │   └── export.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── project.py
│   │   │   ├── document.py
│   │   │   ├── page.py
│   │   │   ├── condition.py
│   │   │   ├── measurement.py
│   │   │   ├── assembly.py                # NEW
│   │   │   ├── auto_count.py              # NEW
│   │   │   ├── review.py                  # NEW
│   │   │   └── export.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── document_processor.py
│   │   │   ├── ocr_service.py
│   │   │   ├── page_classifier.py
│   │   │   ├── scale_detector.py
│   │   │   ├── measurement_engine.py
│   │   │   ├── ai_takeoff.py
│   │   │   ├── assembly_service.py        # NEW
│   │   │   ├── formula_engine.py          # NEW
│   │   │   ├── auto_count_service.py      # NEW
│   │   │   ├── template_matching.py       # NEW
│   │   │   ├── llm_similarity.py          # NEW
│   │   │   ├── review_service.py          # NEW
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
│   │   │   └── auto_count_tasks.py        # NEW
│   │   ├── data/
│   │   │   ├── __init__.py
│   │   │   ├── assembly_templates.py      # NEW
│   │   │   └── formula_presets.py         # NEW
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── geometry.py
│   │       ├── image_processing.py
│   │       ├── pdf_utils.py
│   │       └── storage.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
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
│   │   │   ├── assemblies.ts              # NEW
│   │   │   ├── autoCount.ts               # NEW
│   │   │   ├── review.ts                  # NEW
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
│   │   │   ├── assembly/                  # NEW
│   │   │   │   ├── AssemblyPanel.tsx
│   │   │   │   ├── AssemblyTemplateSelector.tsx
│   │   │   │   ├── ComponentEditor.tsx
│   │   │   │   └── FormulaBuilder.tsx
│   │   │   ├── autocount/                 # NEW
│   │   │   │   ├── AutoCountTool.tsx
│   │   │   │   ├── AutoCountOverlay.tsx
│   │   │   │   └── DetectionReviewDialog.tsx
│   │   │   ├── review/                    # NEW
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
│   │   │   ├── useViewer.ts
│   │   │   ├── useKeyboardShortcuts.ts
│   │   │   └── useQuickAdjust.ts          # NEW
│   │   ├── services/                      # NEW
│   │   │   └── geometry-adjustment.ts
│   │   ├── stores/
│   │   │   ├── projectStore.ts
│   │   │   ├── viewerStore.ts
│   │   │   ├── takeoffStore.ts
│   │   │   └── uiStore.ts
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── ProjectDetail.tsx
│   │   │   ├── TakeoffWorkspace.tsx
│   │   │   ├── ReviewWorkspace.tsx        # NEW
│   │   │   └── Settings.tsx
│   │   ├── lib/
│   │   │   ├── utils.ts
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
│   │   │   ├── assembly.ts                # NEW
│   │   │   ├── autoCount.ts               # NEW
│   │   │   └── geometry.ts                # NEW
│   │   └── styles/
│   │       └── globals.css
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── postcss.config.js
├── scripts/
│   ├── setup-dev.sh
│   ├── seed-db.py
│   ├── seed-assembly-templates.py         # NEW
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

### Core Entities (Original)

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Project   │────<│  Document   │────<│    Page     │
└─────────────┘     └─────────────┘     └─────────────┘
       │                                       │
       │                                       │
       ▼                                       ▼
┌─────────────┐                        ┌─────────────┐
│  Condition  │───────────────────────<│ Measurement │
└─────────────┘                        └─────────────┘
```

### Key Relationships
- **Project** has many **Documents** (plan sets)
- **Document** has many **Pages** (individual sheets)
- **Project** has many **Conditions** (takeoff line items)
- **Condition** has many **Measurements** (geometric shapes on pages)
- **Measurement** belongs to one **Page** and one **Condition**

### New Entities (v2.0)

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
```

### New Database Tables (v2.0)

```sql
-- Assembly System
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

-- Auto Count
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

-- Review System
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

### Exports
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/projects/{id}/export` | Generate export |
| GET | `/api/v1/exports/{id}` | Get export status/download |

### Assemblies (NEW v2.0)
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

### Auto Count (NEW v2.0)
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

### Review (NEW v2.0)
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

## Development Phases Timeline

### Original Timeline (Months 1-12)

```
Month 1-2: Foundation
├── Week 1: Project setup, dev environment
├── Weeks 2-4: Document ingestion pipeline
└── Weeks 5-6: OCR and text extraction

Month 3-4: Intelligence Layer
├── Weeks 7-9: Page classification with LLM
├── Weeks 10-12: Scale detection system
└── Weeks 13-14: Integration testing

Month 5-7: Core Takeoff Engine
├── Weeks 15-18: Measurement engine
├── Weeks 19-22: Condition management
└── Weeks 23-26: AI-assisted takeoff generation

Month 8-10: User Interface & Review
├── Weeks 27-30: Review interface
├── Weeks 31-34: Refinement tools
└── Weeks 35-38: Export system

Month 11-12: Polish & Deploy
├── Weeks 39-42: Testing and QA
├── Weeks 43-46: Performance optimization
└── Weeks 47-48: Production deployment
```

### Updated Phase Checklist (v2.0)

```
Phase 1: Project Setup (Weeks 1-3)
    ├── [ ] Repository structure
    ├── [ ] Development environment (Docker, PostgreSQL, Redis)
    ├── [ ] FastAPI backend scaffold
    ├── [ ] React + TypeScript frontend scaffold
    └── [ ] CI/CD pipeline
    ↓
Phase 2: Document Ingestion (Weeks 4-6)
    ├── [ ] PDF upload and storage
    ├── [ ] TIFF support
    ├── [ ] Page extraction (fixed 1568px resolution)
    ├── [ ] Thumbnail generation
    └── [ ] Document status tracking
    ↓
Phase 3A: OCR & Text Extraction (Weeks 7-9)
    ├── [ ] Tesseract OCR integration
    ├── [ ] Text region detection
    ├── [ ] Scale text extraction
    └── [ ] Dimension parsing
    ↓
Phase 3B: Page Classification (Weeks 10-12)
    ├── [ ] Multi-provider LLM integration (Claude, GPT-4o, Gemini, Grok)
    ├── [ ] Plan type detection (foundation, slab, site, detail)
    ├── [ ] Confidence scoring
    └── [ ] Classification review UI
    ↓
Phase 3C: Scale Detection (Weeks 13-15)
    ├── [ ] Scale bar detection via LLM
    ├── [ ] Written scale parsing ("1/4" = 1'-0"")
    ├── [ ] Manual calibration tool
    └── [ ] pixels_per_foot calculation
    ↓
Phase 4A: Measurement Engine (Weeks 16-17)
    ├── [ ] Geometry primitives (polygon, polyline, point, rectangle)
    ├── [ ] Area calculation (Shoelace formula)
    ├── [ ] Linear measurement
    ├── [ ] Volume calculation (area × depth)
    └── [ ] Unit conversions
    ↓
Phase 4B: Condition Management (Weeks 18-19)
    ├── [ ] Condition CRUD API
    ├── [ ] Condition templates (concrete types)
    ├── [ ] Measurement grouping
    └── [ ] Condition totals
    ↓
Phase 4C: Assembly System ← NEW (Weeks 20-22)
    ├── [ ] Assembly model with components
    ├── [ ] Formula engine for quantity calculations
    ├── [ ] Component types (material, labor, equipment, subcontract)
    ├── [ ] Assembly templates for concrete work
    ├── [ ] Cost database integration
    ├── [ ] Waste factors and productivity rates
    ├── [ ] Markup and pricing calculations
    └── [ ] Assembly builder UI
    ↓
Phase 5A: AI Takeoff Generation (Weeks 23-25)
    ├── [ ] LLM-based element detection
    ├── [ ] Multi-provider support with fallback
    ├── [ ] Confidence scoring
    ├── [ ] Boundary extraction
    └── [ ] Measurement generation
    ↓
Phase 5B: Auto Count Feature ← NEW (Weeks 26-27)
    ├── [ ] Template matching (OpenCV)
    ├── [ ] LLM similarity detection
    ├── [ ] Hybrid detection combining both methods
    ├── [ ] User template selection
    ├── [ ] Match review workflow
    └── [ ] Bulk measurement creation
    ↓
Phase 6: Review Interface ← ENHANCED (Weeks 28-30)
    ├── [ ] Review queue with confidence sorting
    ├── [ ] Keyboard shortcuts (A/R/E/N/P)
    ├── [ ] Auto-accept threshold feature
    ├── [ ] Bulk operations
    ├── [ ] Measurement history/audit trail
    ├── [ ] AI vs Modified overlay
    ├── [ ] Statistics dashboard
    └── [ ] Quick adjust tools (15-QUICK-ADJUST-TOOLS.md)
    ↓
Phase 7: Export System (Weeks 31-32)
    ├── [ ] Excel export (detailed + summary)
    ├── [ ] OST XML format
    ├── [ ] CSV export
    └── [ ] PDF report generation
    ↓
Phase 8: Testing & Deployment (Weeks 33-36)
    ├── [ ] Unit tests (95% coverage for geometry)
    ├── [ ] Integration tests
    ├── [ ] E2E tests with Playwright
    ├── [ ] AI accuracy benchmarking
    ├── [ ] GCP deployment
    └── [ ] Monitoring setup
```

---

## Success Metrics (v2.0)

| Metric | Target | Measurement |
|--------|--------|-------------|
| AI detection accuracy | 75%+ | Approved without changes / Total AI |
| Review throughput | 3x baseline | Measurements reviewed per hour |
| Auto count recall | 90%+ | Found / Actual instances |
| Auto count precision | 85%+ | True positives / Total detections |
| Assembly completeness | 95%+ | Components with formulas |
| Export accuracy | 100% | Quantity match original |

---

## Risk Mitigation (v2.0)

| Risk | Mitigation |
|------|------------|
| Assembly formula complexity | Pre-built templates for common concrete work |
| Auto count false positives | Confidence threshold + mandatory review |
| Review speed regression | Keyboard shortcuts + auto-accept |
| Feature creep | Phase gates with verification checklists |

---

## Getting Started

1. **Begin with `01-PROJECT-SETUP.md`** to establish your repository and development environment
2. **Follow the task lists** in sequential order within each phase document
3. **Provide context to the LLM** by including relevant completed code when starting new phases
4. **Run tests continuously** as specified in each phase

---

## Important Conventions

### Code Style
- **Python**: Follow PEP 8, use type hints, async/await for I/O
- **TypeScript**: Strict mode, explicit return types, functional components
- **Naming**: snake_case (Python), camelCase (TypeScript), PascalCase (components/classes)

### Git Workflow
- `main` - production-ready code
- `develop` - integration branch
- `feature/*` - new features
- `fix/*` - bug fixes

### Environment Variables
All configuration via environment variables. Never commit secrets.

---

## Next Step

→ **Open `01-PROJECT-SETUP.md`** and provide it to your LLM assistant to begin.
