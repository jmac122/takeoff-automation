---
name: ai-construction-takeoff
description: Implementation guide for building an AI-powered construction takeoff platform. Use this skill when working on the Takeoff Platform project, implementing features from the specification documents, or when asked about project architecture, API contracts, database models, or development workflow. Triggers include mentions of takeoff, concrete measurement, plan processing, page classification, scale detection, or any reference to the Takeoff Platform codebase.
---

# AI Construction Takeoff Platform - Implementation Guide

This skill provides implementation guidance for building an AI-powered construction takeoff automation platform that analyzes PDF/TIFF plan sets using vision-language models to detect concrete scopes and generate draft measurements.

## Project Overview

**Goal**: 75% automated accuracy with human review for refinement

**Tech Stack**:
- Backend: Python 3.11+, FastAPI, Celery, SQLAlchemy, PostgreSQL, Redis
- Frontend: React 18, TypeScript, Vite, TailwindCSS, Konva.js
- AI/ML: Claude 3.5 Sonnet, GPT-4o, Gemini 1.5 Pro (multi-provider), OpenCV, Google Cloud Vision
- Infrastructure: Docker, MinIO (S3-compatible), Nginx

## Implementation Phases

Follow these phases in order. Each has a detailed specification in the `references/` folder.

| Phase | Document | Duration | Key Deliverables |
|-------|----------|----------|------------------|
| 0 | `01-PROJECT-SETUP.md` | Week 1 | Repo structure, Docker, CI/CD |
| 1A | `02-DOCUMENT-INGESTION.md` | Weeks 2-5 | PDF/TIFF upload, page extraction |
| 1B | `03-OCR-TEXT-EXTRACTION.md` | Weeks 4-6 | Google Cloud Vision OCR, title blocks |
| 2A | `04-PAGE-CLASSIFICATION.md` | Weeks 6-9 | LLM vision page type detection |
| 2B | `05-SCALE-DETECTION.md` | Weeks 8-11 | Scale parsing, manual calibration |
| 3A | `06-MEASUREMENT-ENGINE.md` | Weeks 10-16 | Geometry tools, calculations |
| 3B | `07-CONDITION-MANAGEMENT.md` | Weeks 14-18 | Takeoff line items, templates |
| 4A | `08-AI-TAKEOFF-GENERATION.md` | Weeks 16-22 | AI element detection |
| 4B | `09-REVIEW-INTERFACE.md` | Weeks 20-26 | Human review workflow |
| 5A | `10-EXPORT-SYSTEM.md` | Weeks 24-28 | Excel, OST XML, PDF export |
| 5B | `11-TESTING-QA.md` | Weeks 26-32 | Test suite, AI benchmarks |
| 6 | `12-DEPLOYMENT.md` | Weeks 30-36 | Production infrastructure |

## How to Use This Skill

1. **Before implementing any feature**, read the corresponding specification document in `references/`
2. **Follow the task lists** in each document sequentially
3. **Use the code examples** as patterns - they define expected conventions
4. **Run verification checklists** after completing each phase

## Core Data Model

```
Project (1) ──< Document (many) ──< Page (many)
    │                                    │
    │                                    │
    ▼                                    ▼
Condition (many) ──────────────< Measurement (many)
```

- **Project**: Contains plan sets and takeoff conditions
- **Document**: A PDF/TIFF file (can be 100+ pages)
- **Page**: Individual sheet with classification, scale, OCR data
- **Condition**: Takeoff line item (e.g., "4" Concrete Slab")
- **Measurement**: Geometry on a page linked to a condition

## Key Architectural Decisions

### Multi-LLM Provider Support
The system supports Anthropic, OpenAI, Google, and xAI for AI operations:
- Default provider configurable via `DEFAULT_LLM_PROVIDER`
- Per-task provider overrides for optimization
- Automatic fallback on provider failure
- Provider comparison for benchmarking

### Async Processing
- Document processing runs via Celery workers
- All heavy operations (OCR, AI analysis) are queued
- Real-time status updates via polling

### Scale Calibration
Critical for accurate measurements:
- Auto-detect from OCR text (architectural/engineering formats)
- Manual calibration via draw-and-enter
- Pixels-per-foot stored per page

## Code Conventions

### Python (Backend)
```python
# Use type hints everywhere
async def process_document(document_id: uuid.UUID) -> DocumentResponse:
    ...

# Use structlog for logging
logger = structlog.get_logger()
logger.info("processing_document", document_id=str(document_id))

# Pydantic for all schemas
class MeasurementCreate(BaseModel):
    condition_id: uuid.UUID
    geometry_type: str
    geometry_data: dict[str, Any]
```

### TypeScript (Frontend)
```typescript
// Strict mode, explicit types
interface Measurement {
  id: string;
  conditionId: string;
  geometryType: 'polygon' | 'polyline' | 'line' | 'point';
  quantity: number;
}

// React Query for data fetching
const { data, isLoading } = useQuery({
  queryKey: ['measurements', pageId],
  queryFn: () => fetchMeasurements(pageId),
});
```

## API Patterns

All endpoints follow REST conventions under `/api/v1/`:

```
Projects:     /projects, /projects/{id}
Documents:    /projects/{id}/documents, /documents/{id}
Pages:        /documents/{id}/pages, /pages/{id}
Conditions:   /projects/{id}/conditions, /conditions/{id}
Measurements: /conditions/{id}/measurements, /measurements/{id}
```

## Quick Reference Commands

```bash
# Start development environment
make dev

# Run backend tests
cd backend && pytest

# Run frontend
cd frontend && npm run dev

# Database migrations
cd backend && alembic upgrade head

# Build Docker images
docker compose build
```

## Specification Document Index

When implementing a feature, read the relevant document first:

- **Document upload/processing**: `references/02-DOCUMENT-INGESTION.md`
- **Text extraction**: `references/03-OCR-TEXT-EXTRACTION.md`
- **Page type classification**: `references/04-PAGE-CLASSIFICATION.md`
- **Scale handling**: `references/05-SCALE-DETECTION.md`
- **Drawing measurements**: `references/06-MEASUREMENT-ENGINE.md`
- **Takeoff conditions**: `references/07-CONDITION-MANAGEMENT.md`
- **AI detection**: `references/08-AI-TAKEOFF-GENERATION.md`
- **Review workflow**: `references/09-REVIEW-INTERFACE.md`
- **Export formats**: `references/10-EXPORT-SYSTEM.md`
- **Testing**: `references/11-TESTING-QA.md`
- **Deployment**: `references/12-DEPLOYMENT.md`

Each document contains complete code examples, database migrations, API schemas, and verification checklists.
