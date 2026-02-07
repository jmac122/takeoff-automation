# Documentation Index

Complete documentation for the ForgeX Takeoffs platform.

---

## Quick Links

| Document | Description |
|----------|-------------|
| [System Architecture](./architecture/SYSTEM_ARCHITECTURE.md) | High-level system overview, tech stack, design decisions |
| [Docker Workflow](./development/DOCKER_WORKFLOW.md) | Docker-first development guide |
| [API Reference](./api/API_REFERENCE.md) | Complete API endpoint documentation |
| [Database Schema](./database/DATABASE_SCHEMA.md) | Database structure and relationships |
| [Workspace Layout](./features/WORKSPACE_LAYOUT.md) | Three-panel workspace feature guide |
| [Condition Panel](./features/CONDITION_PANEL.md) | Condition management panel feature guide |

---

## Documentation Structure

### `/architecture/` - Architecture Documentation
- **[SYSTEM_ARCHITECTURE.md](./architecture/SYSTEM_ARCHITECTURE.md)** - High-level system architecture, tech stack, service topology, design decisions
- **[FRONTEND_ARCHITECTURE.md](./architecture/FRONTEND_ARCHITECTURE.md)** - React component hierarchy, Zustand + React Query state management, routing
- **[BACKEND_ARCHITECTURE.md](./architecture/BACKEND_ARCHITECTURE.md)** - FastAPI layered architecture, service layer, database patterns, background tasks

### `/api/` - API Documentation
- **[API_REFERENCE.md](./api/API_REFERENCE.md)** - General API reference and conventions
- **[CONDITIONS_API.md](./api/CONDITIONS_API.md)** - Condition CRUD, templates, reorder, duplicate, visibility
- **[SHEETS_API.md](./api/SHEETS_API.md)** - Sheet tree, page display, relevance, batch scale
- **[EXPORTS_API.md](./api/EXPORTS_API.md)** - Export job lifecycle (CSV, Excel, PDF, OST)
- **[OCR_API.md](./api/OCR_API.md)** - OCR and text extraction endpoints
- **[API-CONVENTIONS.md](./api/API-CONVENTIONS.md)** - API design patterns and standards

### `/features/` - Feature Documentation
- **[WORKSPACE_LAYOUT.md](./features/WORKSPACE_LAYOUT.md)** - Three-panel workspace layout (Phase A)
- **[CONDITION_PANEL.md](./features/CONDITION_PANEL.md)** - Condition panel with visibility toggle (Phase B)
- **[EXPORT_SYSTEM.md](./features/EXPORT_SYSTEM.md)** - Multi-format export system (Phase C)
- **[SHEET_NAVIGATION.md](./features/SHEET_NAVIGATION.md)** - Sheet tree navigation and management (Phase A)
- **[CONDITION_MANAGEMENT.md](./features/CONDITION_MANAGEMENT.md)** - Original condition management (Phase 3B)

### `/design/` - Design System
- **[DESIGN-SYSTEM.md](./design/DESIGN-SYSTEM.md)** - Color system, typography, component patterns
- **[COMPONENT_LIBRARY.md](./design/COMPONENT_LIBRARY.md)** - shadcn/ui component catalog
- **[WORKSPACE_DESIGN.md](./design/WORKSPACE_DESIGN.md)** - Workspace design decisions and rationale

### `/diagrams/` - System Diagrams
- **[README.md](./diagrams/README.md)** - Diagram index
- **[workspace-component-hierarchy.md](./diagrams/workspace-component-hierarchy.md)** - Full workspace component tree and data flow
- **[export-pipeline-flow.md](./diagrams/export-pipeline-flow.md)** - Export lifecycle sequence diagram
- **[condition-management-flow.md](./diagrams/condition-management-flow.md)** - Condition lifecycle and interaction flows
- **[document-processing-pipeline.md](./diagrams/document-processing-pipeline.md)** - Document ingestion flow
- **[celery-task-chain.md](./diagrams/celery-task-chain.md)** - Background task processing
- **[ocr-classification-flow.md](./diagrams/ocr-classification-flow.md)** - OCR and classification pipeline
- **[scale-detection-accuracy.md](./diagrams/scale-detection-accuracy.md)** - Scale detection accuracy analysis
- **[project-lifecycle.md](./diagrams/project-lifecycle.md)** - Project state machine
- **[frontend-viewer-rendering.md](./diagrams/frontend-viewer-rendering.md)** - Frontend rendering pipeline

### `/database/` - Database Documentation
- **[DATABASE_SCHEMA.md](./database/DATABASE_SCHEMA.md)** - Tables, relationships, and data models

### `/deployment/` - Deployment & Operations
- **[DEPLOYMENT_SETUP.md](./deployment/DEPLOYMENT_SETUP.md)** - Production deployment guide
- **[DOCKER_GUIDE.md](./deployment/DOCKER_GUIDE.md)** - Docker configuration and commands
- **[DOCKER_QUICK_REFERENCE.md](./deployment/DOCKER_QUICK_REFERENCE.md)** - Quick Docker commands
- **[DOCKER_WORKFLOW.md](./deployment/DOCKER_WORKFLOW.md)** - Docker-first development guide
- **[GOOGLE_CLOUD_SETUP.md](./deployment/GOOGLE_CLOUD_SETUP.md)** - Google Cloud Platform setup

### `/development/` - Development Workflow
- **[DOCKER_WORKFLOW.md](./development/DOCKER_WORKFLOW.md)** - Docker-first development guide
- **[TROUBLESHOOTING_GUIDE.md](./development/TROUBLESHOOTING_GUIDE.md)** - Common issues and fixes
- **[PAGE_LOAD_BLACK_SCREEN.md](./development/PAGE_LOAD_BLACK_SCREEN.md)** - Black screen diagnosis
- **[VERIFICATION_CHECKLIST.md](./development/VERIFICATION_CHECKLIST.md)** - Pre-release verification

### `/services/` - Service Documentation
- **[OCR_SERVICE.md](./services/OCR_SERVICE.md)** - OCR service (Google Cloud Vision)
- **[SCALE_SERVICE.md](./services/SCALE_SERVICE.md)** - Scale detection and calibration
- **[MEASUREMENT_SERVICE.md](./services/MEASUREMENT_SERVICE.md)** - Measurement engine

### `/frontend/` - Frontend Documentation
- **[FRONTEND_IMPLEMENTATION.md](./frontend/FRONTEND_IMPLEMENTATION.md)** - React architecture and components
- **[DASHBOARD_REFACTOR.md](./frontend/DASHBOARD_REFACTOR.md)** - Dashboard refactoring notes
- **[SHADCN_UI_MIGRATION.md](./frontend/SHADCN_UI_MIGRATION.md)** - shadcn/ui migration details

### `/phase-guides/` - Phase Completion Reports
- **PHASE_1A_COMPLETE.md** - Document ingestion
- **PHASE_1B_COMPLETE.md** - OCR and text extraction
- **PHASE_2A_COMPLETE.md** - Page classification
- **PHASE_2B_COMPLETE.md** - Scale detection and calibration
- **PHASE_3A_COMPLETE.md** - Measurement engine
- **PHASE_3A_GUIDE.md** - Measurement engine complete guide

### `/plans/` - Implementation Plans
- **forgex-ui-overhaul/** - UI/UX overhaul plan (Phases A-E)
  - **FORGEX_UI_OVERHAUL_IMPLEMENTATION_PLAN_v2.md** - Full implementation plan
  - **PHASE_CONTEXTS.md** - Phase-specific implementation contexts

---

## Current Status

### UI Overhaul (Feb 2026)
- **Phase A**: Workspace Layout & Sheet Navigation (complete)
- **Phase B**: Condition Panel with Visibility Toggle (complete)
- **Phase C**: Export System (complete)
- Phase D: AI Assist (planned)
- Phase E: Export & Reporting UI (planned)

### Foundation Phases (Jan 2026)
- Phase 0: Project Setup
- Phase 1A: Document Ingestion
- Phase 1B: OCR and Text Extraction
- Phase 2A: Page Classification
- Phase 2B: Scale Detection and Calibration
- Phase 3A: Measurement Engine
- Phase 3B: Condition Management

### Services Running
- PostgreSQL (localhost:5432)
- Redis (localhost:6379)
- MinIO (localhost:9000)
- API (http://localhost:8000)
- Frontend (http://localhost:5173)
- Celery Worker (background processing)

---

## AI/LLM Features

### Multi-Provider LLM Support
| Provider | Model | Best For |
|----------|-------|----------|
| Anthropic | Claude 3.5 Sonnet | Recommended primary - best accuracy |
| OpenAI | GPT-4o | Fast, good accuracy |
| Google | Gemini 2.0 Flash | Cost-effective |
| xAI | Grok Vision | Alternative option |

### Classification Methods
| Method | Cost | Accuracy | Speed |
|---|---|---|---|
| OCR-based | Free | ~95% | Fast |
| LLM Vision | ~$0.01/page | ~99% | Slow (2-5s) |

### Scale Detection
- 15+ scale formats (architectural, engineering, metric)
- Visual scale bar detection (OpenCV)
- Manual calibration workflow
- Auto-calibration for high-confidence detections (>=85%)

---

## Contributing to Documentation

When adding new documentation:

1. **Place in appropriate folder:**
   - Architecture decisions → `/architecture/`
   - API endpoints → `/api/`
   - Feature guides → `/features/`
   - Design rationale → `/design/`
   - Flow diagrams → `/diagrams/`

2. **Update this index** with links to new docs

3. **Follow naming convention:**
   - Use UPPERCASE with underscores: `FEATURE_NAME.md`
   - Diagrams use lowercase with hyphens: `flow-name.md`

---

**Last Updated:** February 7, 2026 - Added architecture, feature, API, design, and diagram documentation for Phases A/B/C
