# AI-Powered Construction Takeoff Platform
## Master Implementation Plan

> **Purpose**: This document serves as the master guide for building an AI-powered construction takeoff automation platform. It is designed to be used with an LLM coding assistant (Claude Opus 4.5 in Cursor) to incrementally build the system.

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
| `09-REVIEW-INTERFACE.md` | 4 | Weeks 20-26 | Human review and refinement UI |
| `10-EXPORT-SYSTEM.md` | 5 | Weeks 24-28 | Excel and OST export functionality |
| `11-TESTING-QA.md` | 5 | Weeks 26-32 | Testing strategy and quality assurance |
| `12-DEPLOYMENT.md` | 6 | Weeks 30-36 | Production deployment and monitoring |

### How to Use These Documents

1. **Start each phase** by providing the relevant document to Cursor/Opus
2. **Include context** from previous phases as needed (the LLM will reference completed work)
3. **Task lists** in each document are designed to be worked through sequentially
4. **Code examples** show expected patterns—the LLM should follow these conventions

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
│   │   │   └── export.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── project.py
│   │   │   ├── document.py
│   │   │   ├── page.py
│   │   │   ├── condition.py
│   │   │   ├── measurement.py
│   │   │   └── export.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── document_processor.py
│   │   │   ├── ocr_service.py
│   │   │   ├── page_classifier.py
│   │   │   ├── scale_detector.py
│   │   │   ├── measurement_engine.py
│   │   │   ├── ai_takeoff.py
│   │   │   ├── export_service.py
│   │   │   └── llm_client.py
│   │   ├── workers/
│   │   │   ├── __init__.py
│   │   │   ├── celery_app.py
│   │   │   ├── document_tasks.py
│   │   │   ├── ocr_tasks.py
│   │   │   ├── classification_tasks.py
│   │   │   ├── scale_tasks.py
│   │   │   └── takeoff_tasks.py
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
│   │   │   └── useKeyboardShortcuts.ts
│   │   ├── stores/
│   │   │   ├── projectStore.ts
│   │   │   ├── viewerStore.ts
│   │   │   ├── takeoffStore.ts
│   │   │   └── uiStore.ts
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── ProjectDetail.tsx
│   │   │   ├── TakeoffWorkspace.tsx
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
│   │   │   └── measurement.ts
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

### Core Entities

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

---

## Development Phases Timeline

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
