# ForgeX Takeoffs — AI-Powered Construction Takeoff Automation

## Project Overview

ForgeX Takeoffs automates construction plan analysis using AI (Claude, GPT-4o, Gemini, Grok).
Upload blueprints, classify pages, detect elements, generate measurements — replacing
manual takeoff tools like On Screen Takeoff / Bluebeam.

## Tech Stack

- **Backend:** FastAPI, SQLAlchemy 2.0 (async + sync), PostgreSQL, Celery + Redis
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS, Radix UI
- **Canvas:** Konva.js / react-konva for drawing/measurement overlay
- **State:** @tanstack/react-query v5 (server state), Zustand (client state)
- **AI:** Multi-provider LLM (Anthropic, OpenAI, Google, xAI)
- **Storage:** Local filesystem (dev), GCS (prod)

## Implementation Phases

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

**Master Plan:** `plans/00-MASTER-IMPLEMENTATION-PLAN-UPDATED-v3.md` is the canonical roadmap.
The `-v3` version includes Kreo-inspired enhancements (Unified Task API, Plan Overlay prep,
Vector PDF prep, NL Query prep) and the UI Overhaul parallel track.

## Core Data Model

```
Project (1) ──< Document (many) ──< Page (many)
    │                                    │
    ├──< TaskRecord (many)               ▼
    │                            Measurement (many)
    ▼                                    ▲
Condition (many) ────────────────────────┘
```

- **Project** — top-level container
- **Document** — uploaded PDF/TIFF with revision tracking columns
- **Page** — individual sheet with classification, scale, OCR, vector detection
- **Condition** — takeoff line item (e.g. "Slab on Grade") with spatial grouping
- **Measurement** — geometry + quantity tied to a page and condition
- **TaskRecord** — tracks lifecycle of every Celery async task

## API Endpoints (prefix: `/api/v1`)

### Projects
```
GET    /projects/                     # List projects
POST   /projects/                     # Create project
GET    /projects/{id}                 # Get project
PUT    /projects/{id}                 # Update project
DELETE /projects/{id}                 # Delete project
```

### Documents
```
POST   /projects/{id}/documents/upload   # Upload document
GET    /projects/{id}/documents          # List project documents
GET    /documents/{id}                   # Get document
```

### Pages
```
GET    /documents/{id}/pages             # List document pages
GET    /pages/{id}                       # Get page details
```

### Conditions
```
GET    /projects/{id}/conditions         # List project conditions
POST   /projects/{id}/conditions         # Create condition
PUT    /conditions/{id}                  # Update condition
DELETE /conditions/{id}                  # Delete condition
```

### Measurements
```
GET    /pages/{id}/measurements          # List page measurements
POST   /conditions/{id}/measurements     # Create measurement
PUT    /measurements/{id}                # Update measurement
DELETE /measurements/{id}                # Delete measurement
```

### AI Takeoff
```
POST   /pages/{id}/ai-takeoff           # Generate AI takeoff (single page + condition)
POST   /pages/{id}/autonomous-takeoff   # Autonomous AI takeoff (AI picks elements)
POST   /pages/{id}/compare-providers    # Compare LLM providers
POST   /batch-ai-takeoff                # Batch AI takeoff (multiple pages)
GET    /ai-takeoff/providers            # List available AI providers
```

### Tasks (new)
```
GET    /tasks/{task_id}              # Unified task status
POST   /tasks/{task_id}/cancel       # Cancel running task
GET    /tasks/project/{project_id}   # List project tasks
```

### Exports
```
POST   /projects/{id}/export            # Export project data
```

## Key Patterns

- **Models**: `backend/app/models/`, inherit `Base, UUIDMixin, TimestampMixin`
  - Exception: `TaskRecord` uses string PK (Celery task_id), only `Base, TimestampMixin`
- **Schemas**: Pydantic v2 in `backend/app/schemas/`
- **Routes**: `backend/app/api/routes/`, registered in `backend/app/main.py`
- **Workers**: Celery tasks use SYNC SQLAlchemy (psycopg2), NOT async
- **Frontend hooks**: `frontend/src/hooks/` using @tanstack/react-query
- **API client**: `frontend/src/api/client.ts` (Axios, base URL `/api/v1`)
- **Logging**: `structlog` with key-value pairs throughout
