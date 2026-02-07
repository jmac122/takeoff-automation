# System Architecture

## Overview

Takeoff Automation is a full-stack web application for construction takeoff estimation. It processes construction plan documents (PDF/TIFF), classifies pages, detects scales, and enables measurement of quantities (linear, area, volume, count) organized by conditions.

The system follows an **estimator-first with AI assist** philosophy — the core workflow is manual measurement driven by human expertise, with AI capabilities available to accelerate repetitive tasks.

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              Frontend (React)                                │
│  ┌──────────┐  ┌────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │ Sheet    │  │  Center    │  │  Condition   │  │ Top Toolbar /         │  │
│  │ Tree     │  │  Canvas    │  │  Panel       │  │ Bottom Status Bar     │  │
│  │ (Left)   │  │  (Konva)   │  │  (Right)     │  │                       │  │
│  └─────┬────┘  └─────┬──────┘  └──────┬───────┘  └───────────────────────┘  │
│        │             │                │                                       │
│  ┌─────┴─────────────┴────────────────┴───────────────────────────────┐      │
│  │              Zustand Store (workspaceStore)                         │      │
│  │  activeSheetId, activeConditionId, activeTool, viewport, ...       │      │
│  └────────────────────────────┬────────────────────────────────────────┘      │
│                               │                                              │
│  ┌────────────────────────────┴────────────────────────────────────────┐      │
│  │           React Query (Server State Cache)                          │      │
│  │  ['project-sheets', id], ['conditions', id], ['project', id]       │      │
│  └────────────────────────────┬────────────────────────────────────────┘      │
│                               │ HTTP/REST                                    │
└───────────────────────────────┼──────────────────────────────────────────────┘
                                │
┌───────────────────────────────┼──────────────────────────────────────────────┐
│                        FastAPI Backend                                        │
│                               │                                              │
│  ┌────────────────────────────┴────────────────────────────────────────┐      │
│  │                     API Routes Layer                                │      │
│  │  /projects, /documents, /pages, /conditions, /measurements,        │      │
│  │  /sheets, /exports, /tasks, /health, /settings, /takeoff           │      │
│  └──────────┬───────────────┬──────────────────┬──────────────────────┘      │
│             │               │                  │                             │
│  ┌──────────┴──┐  ┌────────┴────────┐  ┌──────┴──────────────────────┐      │
│  │   Models    │  │    Services     │  │      Workers (Celery)       │      │
│  │ (SQLAlchemy)│  │ (Business Logic)│  │  document_processor         │      │
│  │  Project    │  │  ai_takeoff     │  │  export_tasks               │      │
│  │  Document   │  │  scale_detector │  │  classification_tasks       │      │
│  │  Page       │  │  ocr_service    │  │                             │      │
│  │  Condition  │  │  llm_client     │  └──────────────────────────────┘      │
│  │  Measurement│  │  measurement_   │                                        │
│  │  ExportJob  │  │    engine       │                                        │
│  │  TaskRecord │  │  page_classifier│                                        │
│  └──────┬──────┘  │  export/*       │                                        │
│         │         └─────────────────┘                                        │
│         │                                                                    │
└─────────┼────────────────────────────────────────────────────────────────────┘
          │
    ┌─────┴──────────────────────────────────────────────────────┐
    │                    Infrastructure                           │
    │  ┌────────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
    │  │ PostgreSQL │  │  Redis   │  │  MinIO   │  │ Google   │ │
    │  │ (Database) │  │ (Cache / │  │ (Object  │  │ Cloud    │ │
    │  │            │  │  Broker) │  │  Storage)│  │ Vision   │ │
    │  └────────────┘  └──────────┘  └──────────┘  └──────────┘ │
    └────────────────────────────────────────────────────────────┘
```

## Technology Stack

### Frontend
| Technology | Purpose |
|---|---|
| React 18 | UI framework |
| TypeScript | Type safety |
| Vite | Build tool and dev server |
| TailwindCSS | Utility-first styling |
| Zustand | Client-side state management |
| React Query | Server state and caching |
| Konva.js | Canvas-based drawing engine |
| react-resizable-panels | Three-panel workspace layout |
| Radix UI / shadcn/ui | Accessible component primitives |
| dnd-kit | Drag-and-drop interactions |
| React Router | Client-side routing |

### Backend
| Technology | Purpose |
|---|---|
| Python 3.11 | Runtime |
| FastAPI | Async REST API framework |
| SQLAlchemy 2.0 | ORM with async support |
| Pydantic | Request/response validation |
| Alembic | Database migrations |
| Celery | Background task queue |
| structlog | Structured logging |

### Infrastructure
| Technology | Purpose |
|---|---|
| PostgreSQL 15 | Primary database |
| Redis | Cache layer and Celery broker |
| MinIO | S3-compatible object storage |
| Google Cloud Vision | OCR and text extraction |
| Docker / Docker Compose | Container orchestration |

### External AI Providers
| Provider | Models | Use Case |
|---|---|---|
| Anthropic | Claude 3.5 Sonnet | Page classification, AI takeoff |
| OpenAI | GPT-4o | Page classification, AI takeoff |
| Google | Gemini 2.0 Flash | Page classification, AI takeoff |
| xAI | Grok Vision Beta | Page classification |

## Service Architecture

### Request Flow

```
Browser → Frontend (Vite dev / static build)
       → FastAPI (REST API)
       → SQLAlchemy (Database ORM)
       → PostgreSQL (Persistence)
```

### Async Processing Flow

```
API Route → Create TaskRecord → Queue Celery Task
                                      │
                                      ▼
                              Celery Worker
                              ├── Document Processing (PDF → pages)
                              ├── OCR Extraction (Google Vision)
                              ├── Page Classification (OCR / LLM)
                              ├── Scale Detection
                              └── Export Generation
                                      │
                                      ▼
                              Update TaskRecord status
                              Store artifacts in MinIO
```

### Storage Architecture

- **PostgreSQL**: Structured data (projects, documents, pages, conditions, measurements, task records, export jobs)
- **MinIO**: Binary objects (uploaded PDFs/TIFFs, extracted page images, thumbnails, generated export files)
- **Redis**: Celery task broker, rate limiting, temporary cache
- **Presigned URLs**: All MinIO objects are accessed via time-limited presigned URLs (default: 3600s)

## Database Models

| Model | Description | Key Relations |
|---|---|---|
| `Project` | Top-level container | Has many Documents, Conditions |
| `Document` | Uploaded file (PDF/TIFF) | Belongs to Project, has many Pages |
| `Page` | Individual sheet/page | Belongs to Document, has many Measurements |
| `Condition` | Takeoff line item (e.g., "4\" SOG") | Belongs to Project, has many Measurements |
| `Measurement` | Geometry + quantity | Belongs to Condition and Page |
| `ClassificationHistory` | Version tracking for page classification | Belongs to Page |
| `TaskRecord` | Background task status | Belongs to Project |
| `ExportJob` | Export generation tracking | Belongs to Project |

See [DATABASE_SCHEMA.md](../database/DATABASE_SCHEMA.md) for full schema details.

## Key Design Decisions

### 1. Estimator-First Philosophy
The UI prioritizes manual workflows with optional AI acceleration, rather than requiring AI for basic operations.

### 2. Single Zustand Store
All workspace UI state lives in one Zustand store (`workspaceStore`) for predictable state updates and easy cross-component coordination (e.g., selecting a condition enables drawing tools).

### 3. Server State via React Query
All data fetched from the backend uses React Query with explicit cache invalidation on mutations. This separates "what the server knows" from "what the UI is doing."

### 4. Optimized Database Queries
The sheets endpoint uses a single query with a measurement-count subquery to avoid N+1 performance problems. Condition reordering uses project-level row locking.

### 5. Async Processing for Heavy Operations
Document processing, OCR, classification, and export generation run as Celery background tasks with progress tracking via TaskRecord.

### 6. Multi-Provider LLM Support
The LLM client supports multiple AI providers with automatic fallback, allowing cost optimization (OCR-based classification is free and 95%+ accurate; LLM vision is available for complex cases).

### 7. Formula Injection Prevention
All export formats sanitize text fields to prevent spreadsheet formula injection attacks.

## Deployment

The application runs as 6 Docker containers:

| Container | Port | Purpose |
|---|---|---|
| `frontend` | 5173 | Vite dev server / static build |
| `api` | 8000 | FastAPI application |
| `worker` | — | Celery background worker |
| `postgres` | 5432 | PostgreSQL database |
| `redis` | 6379 | Redis cache/broker |
| `minio` | 9000/9001 | Object storage (API/Console) |

See [DEPLOYMENT_SETUP.md](../deployment/DEPLOYMENT_SETUP.md) and [DOCKER_GUIDE.md](../deployment/DOCKER_GUIDE.md) for details.
