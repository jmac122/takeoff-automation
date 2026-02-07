# Export Pipeline Flow

## Overview

Sequence diagram showing the full export lifecycle from user initiation through file download.

## Export Lifecycle

```
┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐
│ Frontend │      │  FastAPI  │      │ Database │      │  Celery  │      │  MinIO   │
└────┬─────┘      └────┬─────┘      └────┬─────┘      └────┬─────┘      └────┬─────┘
     │                  │                 │                  │                 │
     │  POST /export    │                 │                  │                 │
     │  {format:"excel"}│                 │                  │                 │
     │─────────────────►│                 │                  │                 │
     │                  │                 │                  │                 │
     │                  │  Verify project │                  │                 │
     │                  │────────────────►│                  │                 │
     │                  │◄────────────────│                  │                 │
     │                  │                 │                  │                 │
     │                  │  Create ExportJob                  │                 │
     │                  │  (status: pending)                 │                 │
     │                  │────────────────►│                  │                 │
     │                  │                 │                  │                 │
     │                  │  Create TaskRecord                 │                 │
     │                  │────────────────►│                  │                 │
     │                  │                 │                  │                 │
     │                  │  Queue Celery task                 │                 │
     │                  │───────────────────────────────────►│                 │
     │                  │                 │                  │                 │
     │  202 Accepted    │                 │                  │                 │
     │  {task_id,       │                 │                  │                 │
     │   export_id}     │                 │                  │                 │
     │◄─────────────────│                 │                  │                 │
     │                  │                 │                  │                 │
     │                  │                 │    Worker picks  │                 │
     │                  │                 │    up task       │                 │
     │                  │                 │                  │                 │
     │                  │                 │  Fetch project   │                 │
     │                  │                 │◄─────────────────│                 │
     │                  │                 │─────────────────►│                 │
     │                  │                 │                  │                 │
     │                  │                 │  Fetch conditions│                 │
     │                  │                 │  + measurements  │                 │
     │                  │                 │◄─────────────────│                 │
     │                  │                 │─────────────────►│                 │
     │                  │                 │                  │                 │
     │                  │                 │         Build ExportData           │
     │                  │                 │         Select exporter            │
     │                  │                 │         Sanitize fields            │
     │                  │                 │         Generate file bytes        │
     │                  │                 │                  │                 │
     │                  │                 │                  │  Upload file    │
     │                  │                 │                  │────────────────►│
     │                  │                 │                  │◄────────────────│
     │                  │                 │                  │                 │
     │                  │                 │  Update ExportJob│                 │
     │                  │                 │  (status:        │                 │
     │                  │                 │   completed,     │                 │
     │                  │                 │   file_key,      │                 │
     │                  │                 │   file_size)     │                 │
     │                  │                 │◄─────────────────│                 │
     │                  │                 │                  │                 │
     │  Poll: GET       │                 │                  │                 │
     │  /tasks/{id}     │                 │                  │                 │
     │─────────────────►│                 │                  │                 │
     │  {status:        │                 │                  │                 │
     │   completed}     │                 │                  │                 │
     │◄─────────────────│                 │                  │                 │
     │                  │                 │                  │                 │
     │  GET /exports/   │                 │                  │                 │
     │  {export_id}     │                 │                  │                 │
     │─────────────────►│                 │                  │                 │
     │                  │                 │                  │  Generate       │
     │                  │                 │                  │  presigned URL  │
     │                  │                 │                  │  (3600s expiry) │
     │                  │─────────────────────────────────────────────────────►│
     │                  │◄─────────────────────────────────────────────────────│
     │  {download_url}  │                 │                  │                 │
     │◄─────────────────│                 │                  │                 │
     │                  │                 │                  │                 │
     │  Download file   │                 │                  │                 │
     │  via presigned   │                 │                  │                 │
     │  URL             │                 │                  │                 │
     │───────────────────────────────────────────────────────────────────────►│
     │◄──────────────────────────────────────────────────────────────────────│
     │                  │                 │                  │                 │
```

## Exporter Selection

```
format parameter
     │
     ├── "csv"   → CSVExporter.generate(data)   → .csv
     ├── "excel" → ExcelExporter.generate(data)  → .xlsx
     ├── "pdf"   → PDFExporter.generate(data)    → .pdf
     └── "ost"   → OSTExporter.generate(data)    → .xml
```

## Data Assembly

```
ExportData
├── project_id, project_name, project_description, client_name
│
└── conditions[]
    ├── ConditionData
    │   ├── id, name, description, scope, category
    │   ├── measurement_type, color, unit
    │   ├── depth, thickness
    │   ├── total_quantity, measurement_count
    │   ├── building, area, elevation
    │   │
    │   └── measurements[]
    │       └── MeasurementData
    │           ├── id, condition_name, condition_id
    │           ├── page_id, page_number, sheet_number, sheet_title
    │           ├── geometry_type, geometry_data
    │           ├── quantity, unit
    │           ├── pixel_length, pixel_area
    │           ├── is_ai_generated, is_verified
    │           └── notes
    │
    └── all_measurements  (property: flattened list across all conditions)
```

## Error Handling

```
Export Task
├── Success → status: "completed", file_key set
├── Exporter Error → status: "failed", error_message set
├── Storage Error → status: "failed", error_message set
└── Task Timeout → status remains "processing" (Celery handles)
```

## Storage Pattern

```
MinIO bucket
└── exports/
    └── {project_id}/
        └── {export_id}.{extension}
            │
            └── Presigned URL (3600s expiry)
                └── Direct browser download
```
