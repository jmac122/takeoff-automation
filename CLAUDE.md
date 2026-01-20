# AI Construction Takeoff Platform - Implementation Guide

## Project Overview

You are helping build an AI-powered construction takeoff platform that:
1. Accepts PDF/TIFF plan sets
2. Uses AI vision models to identify concrete scopes
3. Detects and calibrates to drawing scales
4. Generates draft takeoffs with visual measurement overlays
5. Allows human review and refinement
6. Exports to Excel and On Screen Takeoff-compatible formats

**Target**: 75% automated accuracy with human review for refinement

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | React 18, TypeScript, Vite, TailwindCSS, Konva.js, PDF.js |
| **Backend** | Python 3.11+, FastAPI, Celery, SQLAlchemy |
| **Database** | PostgreSQL 15+, Redis 7+ |
| **AI/ML** | Claude 3.5 Sonnet, GPT-4o, Gemini 2.5 Flash, OpenCV, Google Cloud Vision |
| **Storage** | MinIO (S3-compatible) |
| **Infrastructure** | Docker, Docker Compose, Nginx |

## Implementation Phases

**IMPORTANT**: Before implementing any phase, read the corresponding specification document in the `plans/` folder.

| Phase | Document | Description |
|-------|----------|-------------|
| 0 | `plans/01-PROJECT-SETUP.md` | Repository structure, dev environment, CI/CD |
| 1A | `plans/02-DOCUMENT-INGESTION.md` | PDF/TIFF upload, processing, storage |
| 1B | `plans/03-OCR-TEXT-EXTRACTION.md` | Text extraction, title block parsing |
| 2A | `plans/04-PAGE-CLASSIFICATION.md` | LLM vision for page type identification |
| 2B | `plans/05-SCALE-DETECTION.md` | Scale detection and calibration system |
| 3A | `plans/06-MEASUREMENT-ENGINE.md` | Core measurement tools and geometry |
| 3B | `plans/07-CONDITION-MANAGEMENT.md` | Takeoff conditions data model and UI |
| 4A | `plans/08-AI-TAKEOFF-GENERATION.md` | Automated element detection and measurement |
| 4B | `plans/09-REVIEW-INTERFACE.md` | Human review and refinement UI |
| 5A | `plans/10-EXPORT-SYSTEM.md` | Excel and OST export functionality |
| 5B | `plans/11-TESTING-QA.md` | Testing strategy and quality assurance |
| 6 | `plans/12-DEPLOYMENT.md` | Production deployment and monitoring |

## Core Data Model

```
Project (1) ──< Document (many) ──< Page (many)
    │                                    │
    ▼                                    ▼
Condition (many) ──────────────< Measurement (many)
```

- **Project**: Contains plan sets and takeoff conditions
- **Document**: A PDF/TIFF file (can be 100+ pages)
- **Page**: Individual sheet with classification, scale, OCR data
- **Condition**: Takeoff line item (e.g., "4" Concrete Slab")
- **Measurement**: Geometry on a page linked to a condition

## Code Conventions

### Python (Backend)
- Use type hints everywhere
- Use `structlog` for logging
- Use Pydantic for all schemas
- Async/await for all I/O operations
- Follow PEP 8, use `black` for formatting

```python
async def process_document(document_id: uuid.UUID) -> DocumentResponse:
    logger = structlog.get_logger()
    logger.info("processing_document", document_id=str(document_id))
    ...
```

### TypeScript (Frontend)
- Strict mode enabled
- Explicit return types on functions
- React Query for data fetching
- Zustand for state management

```typescript
interface Measurement {
  id: string;
  conditionId: string;
  geometryType: 'polygon' | 'polyline' | 'line' | 'point';
  quantity: number;
}
```

## API Patterns

All endpoints under `/api/v1/`:

```
Projects:     /projects, /projects/{id}
Documents:    /projects/{id}/documents, /documents/{id}
Pages:        /documents/{id}/pages, /pages/{id}
Conditions:   /projects/{id}/conditions, /conditions/{id}
Measurements: /conditions/{id}/measurements, /measurements/{id}
Exports:      /projects/{id}/export, /exports/{id}
```

## File Structure

```
takeoff-platform/
├── backend/
│   ├── app/
│   │   ├── api/routes/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── workers/
│   │   └── utils/
│   └── tests/
├── frontend/
│   └── src/
│       ├── api/
│       ├── components/
│       ├── hooks/
│       ├── stores/
│       ├── pages/
│       └── types/
├── docker/
└── plans/  (specification documents)
```

## Workflow Instructions

1. When asked to implement a phase, ALWAYS read the corresponding spec document in `plans/` first
2. Follow the task lists in each document sequentially
3. Use the code examples in specs as patterns
4. Run the verification checklist after completing each phase
5. Each spec contains complete code examples, database migrations, and API schemas

## Quick Commands

```bash
make dev              # Start development environment
make test             # Run all tests
make lint             # Run linters
make migrate          # Run database migrations
docker compose up     # Start all services
```
