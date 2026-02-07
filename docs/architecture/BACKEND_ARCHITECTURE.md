# Backend Architecture

## Overview

The backend is a Python 3.11 async application built on FastAPI with SQLAlchemy 2.0 ORM, Celery for background processing, and MinIO for object storage. It exposes a REST API consumed by the React frontend.

## Directory Structure

```
backend/
├── app/
│   ├── main.py                  # FastAPI app factory and router registration
│   ├── api/
│   │   ├── deps.py              # Dependency injection (get_db session)
│   │   └── routes/
│   │       ├── health.py        # Health check endpoint
│   │       ├── projects.py      # Project CRUD
│   │       ├── documents.py     # Document upload and processing
│   │       ├── pages.py         # Page operations (classify, calibrate, detect-scale)
│   │       ├── conditions.py    # Condition CRUD, templates, reorder, duplicate
│   │       ├── measurements.py  # Measurement CRUD
│   │       ├── sheets.py        # Sheet tree aggregation for workspace
│   │       ├── exports.py       # Export job management
│   │       ├── takeoff.py       # AI takeoff generation
│   │       ├── tasks.py         # Task status polling
│   │       └── settings.py      # App settings
│   │
│   ├── models/
│   │   ├── base.py              # SQLAlchemy declarative base + TimestampMixin
│   │   ├── project.py           # Project model
│   │   ├── document.py          # Document model
│   │   ├── page.py              # Page model (classification, scale, OCR data)
│   │   ├── condition.py         # Condition model (takeoff line items)
│   │   ├── measurement.py       # Measurement model (geometry + quantity)
│   │   ├── classification_history.py  # Classification version tracking
│   │   ├── task_record.py       # Background task tracking
│   │   └── export_job.py        # Export job tracking
│   │
│   ├── schemas/
│   │   ├── condition.py         # Condition request/response schemas
│   │   ├── document.py          # Document schemas
│   │   ├── export.py            # Export schemas
│   │   ├── measurement.py       # Measurement schemas
│   │   ├── page.py              # Page schemas
│   │   ├── project.py           # Project schemas
│   │   └── task.py              # Task schemas
│   │
│   ├── services/
│   │   ├── ai_takeoff.py        # AI-powered takeoff generation (25KB)
│   │   ├── scale_detector.py    # Scale detection from OCR text (38KB, 15+ formats)
│   │   ├── ocr_service.py       # Google Cloud Vision integration (18KB)
│   │   ├── llm_client.py        # Multi-provider LLM client (19KB)
│   │   ├── measurement_engine.py # Geometry calculations (10KB)
│   │   ├── ocr_classifier.py    # OCR-text-based classification (7KB)
│   │   ├── page_classifier.py   # LLM-vision-based classification (5KB)
│   │   ├── document_processor.py # PDF/TIFF page extraction
│   │   ├── task_tracker.py      # Task lifecycle management
│   │   └── export/
│   │       ├── __init__.py
│   │       ├── base.py          # BaseExporter ABC + data classes
│   │       ├── csv_exporter.py  # CSV format
│   │       ├── excel_exporter.py # Excel (.xlsx) format
│   │       ├── pdf_exporter.py  # PDF format
│   │       └── ost_exporter.py  # OST XML format (construction standard)
│   │
│   ├── workers/
│   │   ├── celery_app.py        # Celery configuration
│   │   ├── document_tasks.py    # Document processing tasks
│   │   ├── classification_tasks.py # Classification tasks
│   │   └── export_tasks.py      # Export generation tasks
│   │
│   └── utils/
│       └── storage.py           # MinIO storage service abstraction
│
├── alembic/
│   ├── env.py                   # Alembic configuration
│   └── versions/                # 19 migration files
│
├── tests/
│   ├── conftest.py              # Shared fixtures
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   └── e2e/                     # End-to-end tests
│
└── pyproject.toml               # Python project configuration
```

## Layered Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      API Routes Layer                        │
│  Request validation (Pydantic) → Business logic → Response   │
│  FastAPI dependency injection for database sessions           │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────┐
│                     Service Layer                            │
│  Domain logic, external integrations, calculations           │
│  ai_takeoff, scale_detector, ocr_service, llm_client,       │
│  measurement_engine, export/*                                │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────┐
│                     Model Layer                              │
│  SQLAlchemy ORM models, relationships, constraints           │
│  Pydantic schemas for serialization                          │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────┐
│                   Infrastructure Layer                        │
│  PostgreSQL (via asyncpg), Redis, MinIO, Google Vision       │
└─────────────────────────────────────────────────────────────┘
```

## API Route Modules

### Core Resources

| Module | Base Path | Operations |
|---|---|---|
| `projects.py` | `/projects` | Create, Get, List, Update, Delete |
| `documents.py` | `/documents` | Upload, Get, List, Delete, Status |
| `pages.py` | `/pages` | Get, Classify, Calibrate, Detect Scale |
| `conditions.py` | `/conditions` | Create, Get, Update, Delete, Duplicate, Reorder, Templates |
| `measurements.py` | `/measurements` | Create, Get, Update, Delete |

### Workspace & Aggregation

| Module | Base Path | Operations |
|---|---|---|
| `sheets.py` | `/projects/{id}/sheets` | Get Sheet Tree, Update Display, Update Relevance, Batch Scale |
| `exports.py` | `/projects/{id}/export` | Start Export, Get Export, List Exports, Delete Export |
| `takeoff.py` | `/takeoff` | Generate AI Takeoff, Compare Providers, Batch Takeoff |
| `tasks.py` | `/tasks` | Get Task Status |

### Utility

| Module | Base Path | Operations |
|---|---|---|
| `health.py` | `/health` | Health check |
| `settings.py` | `/settings` | App configuration |

## Service Layer

### OCR Pipeline
```
Document Upload → Page Extraction → Google Vision OCR → Text Storage
                                                              │
                                    ┌─────────────────────────┤
                                    ▼                         ▼
                            OCR Classifier           Scale Detector
                          (regex + keyword)       (15+ format patterns)
                                    │                         │
                                    ▼                         ▼
                          Page Classification         Scale Value
                          (structural, MEP,          (1/4" = 1'-0", etc.)
                           architectural...)
```

### Classification Methods

| Method | Cost | Accuracy | Speed |
|---|---|---|---|
| OCR-based (`ocr_classifier.py`) | Free | ~95% | Fast |
| LLM Vision (`page_classifier.py`) | ~$0.01/page | ~99% | Slow (2-5s) |

The system defaults to OCR-based classification and offers LLM vision as an upgrade path.

### Scale Detection

The `scale_detector.py` (38KB) parses 15+ scale formats:
- Architectural: `1/4" = 1'-0"`, `3/8" = 1'0"`, `1" = 10'`
- Engineering: `1:50`, `1:100`, `1:200`
- Metric: `1:500mm`, `1cm = 1m`
- Text-based: `SCALE: 1/8" = 1'-0"`
- Visual scale bars (OpenCV detection)

### Export System

```
ExportData (project + conditions + measurements)
     │
     ├── CSVExporter     → .csv  (text/csv)
     ├── ExcelExporter   → .xlsx (application/vnd.openxmlformats...)
     ├── PDFExporter     → .pdf  (application/pdf)
     └── OSTExporter     → .xml  (application/xml, OST standard)
```

All exporters:
- Inherit from `BaseExporter` ABC
- Implement `generate()`, `content_type`, `file_extension`
- Use `sanitize_field()` to prevent formula injection
- Accept format-specific `options` dict

### Measurement Engine

Supports 6 geometry types mapped to 4 measurement types:

| Geometry | Measurement Type | Output Unit |
|---|---|---|
| Line | Linear | LF (Linear Feet) |
| Polyline | Linear | LF |
| Polygon | Area | SF (Square Feet) |
| Rectangle | Area | SF |
| Circle | Area | SF |
| Point | Count | EA (Each) |

Volume calculations multiply area by depth/thickness from the condition.

## Database Patterns

### UUID Primary Keys
All tables use UUID primary keys for globally unique identifiers.

### Timestamp Auditing
All models inherit `TimestampMixin` providing `created_at` and `updated_at` columns.

### JSON Storage
Flexible metadata fields (e.g., `extra_metadata`, `geometry_data`, `ocr_blocks`) use JSON columns for schema-free storage.

### Cascade Deletes
- Deleting a Project cascades to Documents, Conditions
- Deleting a Document cascades to Pages
- Deleting a Condition cascades to Measurements
- Deleting an ExportJob deletes its MinIO file

### Concurrency Control
- Condition reordering uses `SELECT ... FOR UPDATE` on the Project row to prevent sort_order races
- Condition creation locks the project row to safely compute `max(sort_order) + 1`

### Query Optimization
- The sheets endpoint uses a measurement-count subquery to avoid N+1 queries
- Condition listing is ordered by `sort_order, name` with a single query
- Batch scale updates fetch all pages in one query

## Background Task System

### Celery Configuration
- **Broker**: Redis
- **Result Backend**: Redis
- **Serializer**: JSON
- **Task tracking**: Custom `TaskTracker` service writes to `task_records` table

### Task Lifecycle
```
1. API creates TaskRecord (status: 'pending')
2. API queues Celery task with pre-generated task_id
3. Worker picks up task, updates status to 'processing'
4. Worker performs work (export, classification, etc.)
5. Worker updates status to 'completed' or 'failed'
6. Frontend polls task status via /tasks/{task_id}/status
```

### Task Types
| Type | Worker Module | Description |
|---|---|---|
| Document Processing | `document_tasks.py` | PDF → page extraction, thumbnail generation |
| Classification | `classification_tasks.py` | OCR-based or LLM-based page classification |
| Export Generation | `export_tasks.py` | Generate CSV/Excel/PDF/OST files |

## Testing

### Structure
```
tests/
├── conftest.py            # Database fixtures, test factories
├── unit/                  # Isolated unit tests (mocked deps)
│   └── test_export/       # Export format tests
├── integration/           # Tests with real database
│   ├── test_condition_visibility.py
│   ├── test_conditions_api.py
│   ├── test_exports_api.py
│   └── ...
└── e2e/                   # Full-stack tests (require all services)
    ├── test_document_upload.py
    └── test_takeoff_workflow.py
```

### Running Tests
```bash
# All tests (from backend/)
python -m pytest tests/ -v

# Unit tests only
python -m pytest tests/unit/ -v

# Integration tests only
python -m pytest tests/integration/ -v

# Specific test file
python -m pytest tests/integration/test_condition_visibility.py -v
```

## Migrations

Alembic manages 19 database migrations tracking the full schema evolution:

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply all migrations
alembic upgrade head

# Rollback one step
alembic downgrade -1
```

Key migrations include:
- Initial schema (projects, documents, pages)
- Condition management tables
- Measurement geometry fields
- Classification history tracking
- Export job tracking
- `is_visible` field on conditions
