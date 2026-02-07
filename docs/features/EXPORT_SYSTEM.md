# Export System (Phase C)

## Overview

The export system generates downloadable files from project takeoff data in four formats: CSV, Excel (.xlsx), PDF, and OST XML. Exports are processed asynchronously via Celery workers and stored in MinIO for secure download via presigned URLs.

## Supported Formats

| Format | Extension | MIME Type | Use Case |
|---|---|---|---|
| CSV | `.csv` | `text/csv` | Simple data exchange, spreadsheet import |
| Excel | `.xlsx` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` | Rich spreadsheets with formatting |
| PDF | `.pdf` | `application/pdf` | Printable reports |
| OST XML | `.xml` | `application/xml` | Construction takeoff industry standard (On-Screen Takeoff) |

## Architecture

### Data Flow

```
Frontend                          Backend                              Worker
   │                                │                                    │
   │  POST /projects/{id}/export    │                                    │
   │  { format: "excel" }          │                                    │
   │ ─────────────────────────────►│                                    │
   │                                │  Create ExportJob (pending)        │
   │                                │  Create TaskRecord                 │
   │                                │  Queue Celery task                 │
   │  ◄──── 202 Accepted ──────── │ ──── generate_export_task ────────►│
   │  { task_id, export_id }       │                                    │
   │                                │                                    │  Fetch project data
   │  GET /tasks/{task_id}/status  │                                    │  Fetch conditions
   │ ─────────────────────────────►│                                    │  Fetch measurements
   │  ◄──── { status: processing } │                                    │  Build ExportData
   │                                │                                    │  Select exporter
   │  GET /tasks/{task_id}/status  │                                    │  Generate file bytes
   │ ─────────────────────────────►│                                    │  Upload to MinIO
   │  ◄──── { status: completed }  │  ◄─── Update ExportJob ──────────│
   │                                │       (completed, file_key)        │
   │  GET /exports/{export_id}     │                                    │
   │ ─────────────────────────────►│                                    │
   │  ◄──── { download_url }       │  Generate presigned URL            │
   │                                │  (3600s expiry)                    │
   │  Download file via URL        │                                    │
```

### Export Data Model

All exporters receive an `ExportData` instance containing the full project snapshot:

```python
@dataclass
class ExportData:
    project_id: uuid.UUID
    project_name: str
    project_description: str | None
    client_name: str | None
    conditions: list[ConditionData]

    @property
    def all_measurements(self) -> list[MeasurementData]
        # Flattens measurements across all conditions

@dataclass
class ConditionData:
    id: uuid.UUID
    name: str
    description: str | None
    scope: str               # e.g., "concrete"
    category: str | None     # e.g., "slabs"
    measurement_type: str    # "linear" | "area" | "volume" | "count"
    color: str               # Hex color code
    unit: str                # "LF" | "SF" | "CY" | "EA"
    depth: float | None
    thickness: float | None
    total_quantity: float
    measurement_count: int
    building: str | None
    area: str | None
    elevation: str | None
    measurements: list[MeasurementData]

@dataclass
class MeasurementData:
    id: uuid.UUID
    condition_name: str
    condition_id: uuid.UUID
    page_id: uuid.UUID
    page_number: int | None
    sheet_number: str | None
    sheet_title: str | None
    geometry_type: str       # "line" | "polyline" | "polygon" | ...
    geometry_data: dict      # Raw geometry coordinates
    quantity: float
    unit: str
    pixel_length: float | None
    pixel_area: float | None
    is_ai_generated: bool
    is_verified: bool
    notes: str | None
```

## Exporter Interface

All exporters implement the `BaseExporter` abstract class:

```python
class BaseExporter(abc.ABC):
    @abc.abstractmethod
    def generate(self, data: ExportData, options: dict | None = None) -> bytes:
        """Generate export file bytes from project data."""

    @property
    @abc.abstractmethod
    def content_type(self) -> str:
        """MIME content type for the export format."""

    @property
    @abc.abstractmethod
    def file_extension(self) -> str:
        """File extension for the export format."""
```

## Security: Formula Injection Prevention

All text fields are sanitized before export to prevent spreadsheet formula injection:

```python
_FORMULA_PREFIXES = ('=', '+', '-', '@', '\t', '\r')

def sanitize_field(value: str) -> str:
    if value and value[0] in _FORMULA_PREFIXES:
        return "'" + value  # Prefix with apostrophe
    return value
```

This prevents cells starting with `=`, `+`, `-`, `@`, tab, or carriage return from being interpreted as formulas when opened in Excel or Google Sheets.

## API Endpoints

### Start Export
```
POST /projects/{project_id}/export
```
**Status**: 202 Accepted

**Request**:
```json
{
  "format": "excel",
  "options": {}
}
```

**Response**:
```json
{
  "task_id": "uuid",
  "export_id": "uuid",
  "message": "Export job started for format: excel"
}
```

### Get Export Status
```
GET /exports/{export_id}
```

**Response**:
```json
{
  "id": "uuid",
  "project_id": "uuid",
  "format": "excel",
  "status": "completed",
  "file_key": "exports/project-uuid/export-uuid.xlsx",
  "file_size": 45321,
  "error_message": null,
  "download_url": "https://minio.example.com/...",
  "options": {},
  "started_at": "2026-02-01T10:00:01Z",
  "completed_at": "2026-02-01T10:00:05Z",
  "created_at": "2026-02-01T10:00:00Z",
  "updated_at": "2026-02-01T10:00:05Z"
}
```

### List Project Exports
```
GET /projects/{project_id}/exports
```

**Response**:
```json
{
  "exports": [...],
  "total": 5
}
```

### Delete Export
```
DELETE /exports/{export_id}
```
**Status**: 204 No Content

Deletes the ExportJob record and its associated file from MinIO storage.

## Task Tracking Integration

Each export job creates a `TaskRecord` for progress tracking:

```python
await TaskTracker.register_async(
    db,
    task_id=task_id,
    task_type="export",
    task_name=f"Export {format.upper()} for {project.name}",
    project_id=str(project_id),
    metadata={"export_job_id": str(export_job.id), "format": format},
)
```

The frontend polls `GET /tasks/{task_id}/status` to track progress.

## Storage

Export files are stored in MinIO with the key pattern:
```
exports/{project_id}/{export_id}.{extension}
```

Download URLs are presigned with a 3600-second (1-hour) expiry. If presigned URL generation fails, the export response omits the `download_url` field gracefully.

## Key Files

| File | Purpose |
|---|---|
| `backend/app/services/export/base.py` | BaseExporter ABC, data classes, sanitization |
| `backend/app/services/export/csv_exporter.py` | CSV format generator |
| `backend/app/services/export/excel_exporter.py` | Excel format generator |
| `backend/app/services/export/pdf_exporter.py` | PDF format generator |
| `backend/app/services/export/ost_exporter.py` | OST XML format generator |
| `backend/app/api/routes/exports.py` | Export API routes |
| `backend/app/models/export_job.py` | ExportJob database model |
| `backend/app/schemas/export.py` | Export request/response schemas |
| `backend/app/workers/export_tasks.py` | Celery export task |
| `backend/app/services/task_tracker.py` | Task lifecycle management |

## Testing

### Backend Tests
- `test_exports_api.py` — Integration tests for export endpoints
- `test_export/` — Unit tests for each exporter format
- Tests verify: formula injection prevention, data mapping, file generation, error handling
