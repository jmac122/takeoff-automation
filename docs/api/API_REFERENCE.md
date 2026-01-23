# API Reference - Phases 1A, 1B, 2A, 2B & 3B: Document Ingestion, OCR, Classification, Scale Detection & Condition Management

## Overview

The ForgeX Takeoffs API provides RESTful endpoints for managing construction plan documents, projects, OCR text extraction, AI-powered page classification, scale detection, and condition management. All endpoints are prefixed with `/api/v1` and return JSON responses.

## Authentication

Currently, no authentication is implemented (development phase). Authentication will be added in future phases.

## Base URL

```
http://localhost:8000/api/v1
```

## Response Format

### Success Response
```json
{
  "id": "uuid-string",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "...": "..."
}
```

### Error Response
```json
{
  "detail": "Error message description"
}
```

## Endpoints

## Health Check

### GET /health

Health check endpoint for monitoring service availability.

**Response:**
```json
{
  "status": "healthy"
}
```

**Status Codes:**
- `200` - Service is healthy

---

## Projects

### POST /projects

Create a new project.

**Request Body:**
```json
{
  "name": "Downtown Office Building",
  "description": "Multi-story office building construction project",
  "client_name": "ABC Construction Corp"
}
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Downtown Office Building",
  "description": "Multi-story office building construction project",
  "client_name": "ABC Construction Corp",
  "status": "draft",
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:00:00Z"
}
```

**Status Codes:**
- `201` - Project created successfully
- `422` - Validation error

### GET /projects/{project_id}

Get project details by ID.

**Parameters:**
- `project_id` (path) - UUID of the project

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Downtown Office Building",
  "description": "Multi-story office building construction project",
  "client_name": "ABC Construction Corp",
  "status": "draft",
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:00:00Z",
  "documents": []
}
```

**Status Codes:**
- `200` - Project found
- `404` - Project not found

---

## Documents

### POST /projects/{project_id}/documents

Upload a document to a project.

**Parameters:**
- `project_id` (path) - UUID of the project

**Request Body:**
- `file` (form-data) - PDF or TIFF file to upload

**Content-Type:** `multipart/form-data`

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/v1/projects/550e8400-e29b-41d4-a716-446655440000/documents \
  -F "file=@floor_plan.pdf"
```

**Response:**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "660e8400-e29b-41d4-a716-446655440001.pdf",
  "original_filename": "floor_plan.pdf",
  "file_type": "pdf",
  "file_size": 2457600,
  "mime_type": "application/pdf",
  "status": "uploaded",
  "page_count": null,
  "processing_error": null,
  "created_at": "2024-01-01T10:05:00Z",
  "updated_at": "2024-01-01T10:05:00Z",
  "pages": []
}
```

**Status Codes:**
- `201` - Document uploaded successfully
- `400` - Invalid file or validation error
- `404` - Project not found
- `500` - Storage or processing error

**Supported File Types:**
- `application/pdf` (.pdf)
- `image/tiff` (.tiff, .tif)

**File Size Limits:**
- Maximum: 500MB (configurable)
- Recommended: < 100MB for optimal processing

### GET /documents/{document_id}

Get document details and processing status.

**Parameters:**
- `document_id` (path) - UUID of the document

**Response:**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "660e8400-e29b-41d4-a716-446655440001.pdf",
  "original_filename": "floor_plan.pdf",
  "file_type": "pdf",
  "file_size": 2457600,
  "mime_type": "application/pdf",
  "status": "ready",
  "page_count": 5,
  "processing_error": null,
  "created_at": "2024-01-01T10:05:00Z",
  "updated_at": "2024-01-01T10:10:00Z",
  "pages": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440002",
      "page_number": 1,
      "classification": null,
      "scale_calibrated": false,
      "thumbnail_url": "/api/v1/thumbnails/770e8400-e29b-41d4-a716-446655440002"
    }
  ]
}
```

**Status Codes:**
- `200` - Document found
- `404` - Document not found

### GET /documents/{document_id}/status

Get document processing status (lightweight endpoint for polling).

**Parameters:**
- `document_id` (path) - UUID of the document

**Response:**
```json
{
  "status": "processing",
  "page_count": null,
  "error": null
}
```

**Status Values:**
- `"uploaded"` - File uploaded, processing not started
- `"processing"` - Document being processed by worker
- `"ready"` - Processing complete, pages available
- `"error"` - Processing failed

**Status Codes:**
- `200` - Status retrieved successfully
- `404` - Document not found

### DELETE /documents/{document_id}

Delete a document and all associated files.

**Parameters:**
- `document_id` (path) - UUID of the document

**Response:**
- `204 No Content` - Document deleted successfully

**Status Codes:**
- `204` - Document deleted
- `404` - Document not found

**Note:** This operation deletes:
- Document record from database
- All associated page records
- All stored files (original, images, thumbnails)

---

## Pages

### GET /pages/{page_id}

Get page details (to be implemented in future phases).

### GET /pages/{page_id}/image

Get full-resolution page image (to be implemented).

### GET /pages/{page_id}/thumbnail

Get page thumbnail (to be implemented).

---

## Condition Management (Phase 3B)

Condition management endpoints allow creating, updating, and organizing takeoff line items (conditions) with templates, filtering, duplication, and reordering capabilities.

### GET /condition-templates

List available condition templates. Templates provide pre-configured conditions for common concrete scopes (foundations, slabs, paving, vertical, miscellaneous).

**Query Parameters:**
- `scope` (optional) - Filter by scope (e.g., "concrete")
- `category` (optional) - Filter by category (e.g., "foundations", "slabs")

**Response:**
```json
[
  {
    "name": "Strip Footing",
    "scope": "concrete",
    "category": "foundations",
    "measurement_type": "linear",
    "unit": "LF",
    "depth": 12,
    "color": "#EF4444",
    "line_width": 2,
    "fill_opacity": 0.3
  },
  {
    "name": "4\" SOG",
    "scope": "concrete",
    "category": "slabs",
    "measurement_type": "area",
    "unit": "SF",
    "depth": 4,
    "color": "#22C55E",
    "line_width": 2,
    "fill_opacity": 0.3
  }
]
```

**Status Codes:**
- `200` - Success

---

### GET /projects/{project_id}/conditions

List all conditions for a project, optionally filtered by scope or category.

**Parameters:**
- `project_id` (path) - UUID of the project
- `scope` (query, optional) - Filter by scope
- `category` (query, optional) - Filter by category

**Response:**
```json
{
  "conditions": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "project_id": "660e8400-e29b-41d4-a716-446655440001",
      "name": "Strip Footing",
      "description": null,
      "scope": "concrete",
      "category": "foundations",
      "measurement_type": "linear",
      "unit": "LF",
      "color": "#EF4444",
      "line_width": 2,
      "fill_opacity": 0.3,
      "depth": 12,
      "thickness": null,
      "sort_order": 1,
      "created_at": "2024-01-01T10:00:00Z",
      "updated_at": "2024-01-01T10:00:00Z"
    }
  ],
  "total": 1
}
```

**Status Codes:**
- `200` - Success
- `404` - Project not found

---

### POST /projects/{project_id}/conditions

Create a new custom condition for a project.

**Parameters:**
- `project_id` (path) - UUID of the project

**Request Body:**
```json
{
  "name": "Custom Foundation",
  "description": "Custom foundation condition",
  "scope": "concrete",
  "category": "foundations",
  "measurement_type": "linear",
  "unit": "LF",
  "color": "#EF4444",
  "line_width": 2,
  "fill_opacity": 0.3,
  "depth": 12,
  "thickness": null,
  "extra_metadata": {}
}
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "project_id": "660e8400-e29b-41d4-a716-446655440001",
  "name": "Custom Foundation",
  "description": "Custom foundation condition",
  "scope": "concrete",
  "category": "foundations",
  "measurement_type": "linear",
  "unit": "LF",
  "color": "#EF4444",
  "line_width": 2,
  "fill_opacity": 0.3,
  "depth": 12,
  "thickness": null,
  "sort_order": 1,
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:00:00Z"
}
```

**Status Codes:**
- `201` - Condition created successfully
- `404` - Project not found
- `422` - Validation error

---

### POST /projects/{project_id}/conditions/from-template

Create a condition from a predefined template.

**Parameters:**
- `project_id` (path) - UUID of the project
- `template_name` (query, required) - Name of the template (e.g., "Strip Footing")

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "project_id": "660e8400-e29b-41d4-a716-446655440001",
  "name": "Strip Footing",
  "scope": "concrete",
  "category": "foundations",
  "measurement_type": "linear",
  "unit": "LF",
  "color": "#EF4444",
  "line_width": 2,
  "fill_opacity": 0.3,
  "depth": 12,
  "sort_order": 1,
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:00:00Z"
}
```

**Status Codes:**
- `201` - Condition created successfully
- `404` - Project or template not found

---

### GET /conditions/{condition_id}

Get condition details including measurement summaries.

**Parameters:**
- `condition_id` (path) - UUID of the condition

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "project_id": "660e8400-e29b-41d4-a716-446655440001",
  "name": "Strip Footing",
  "description": null,
  "scope": "concrete",
  "category": "foundations",
  "measurement_type": "linear",
  "unit": "LF",
  "color": "#EF4444",
  "line_width": 2,
  "fill_opacity": 0.3,
  "depth": 12,
  "thickness": null,
  "sort_order": 1,
  "measurements": [],
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:00:00Z"
}
```

**Status Codes:**
- `200` - Success
- `404` - Condition not found

---

### PUT /conditions/{condition_id}

Update a condition.

**Parameters:**
- `condition_id` (path) - UUID of the condition

**Request Body:**
```json
{
  "name": "Updated Strip Footing",
  "color": "#FF0000",
  "line_width": 3
}
```

All fields are optional. Only provided fields will be updated.

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Updated Strip Footing",
  "color": "#FF0000",
  "line_width": 3,
  "...": "..."
}
```

**Status Codes:**
- `200` - Condition updated successfully
- `404` - Condition not found
- `422` - Validation error

---

### DELETE /conditions/{condition_id}

Delete a condition and all its measurements.

**Parameters:**
- `condition_id` (path) - UUID of the condition

**Status Codes:**
- `204` - Condition deleted successfully
- `404` - Condition not found

---

### POST /conditions/{condition_id}/duplicate

Duplicate a condition (without measurements). The new condition will have "(Copy)" appended to its name.

**Parameters:**
- `condition_id` (path) - UUID of the condition to duplicate

**Response:**
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "name": "Strip Footing (Copy)",
  "...": "..."
}
```

**Status Codes:**
- `200` - Condition duplicated successfully
- `404` - Condition not found

---

### PUT /projects/{project_id}/conditions/reorder

Reorder conditions by providing an ordered list of condition IDs. All condition IDs for the project must be included.

**Parameters:**
- `project_id` (path) - UUID of the project

**Request Body:**
```json
[
  "550e8400-e29b-41d4-a716-446655440000",
  "660e8400-e29b-41d4-a716-446655440001",
  "770e8400-e29b-41d4-a716-446655440002"
]
```

**Response:**
```json
{
  "status": "success",
  "reordered_count": 3
}
```

**Status Codes:**
- `200` - Conditions reordered successfully
- `400` - Invalid request (duplicate IDs or missing conditions)
- `404` - Project or conditions not found

**Notes:**
- The order of IDs in the request determines the new sort order
- All condition IDs for the project must be included
- Sort order is persisted and used for display sequencing

---

## Measurements

### GET /conditions/{condition_id}/measurements

List measurements (stub implementation).

### POST /conditions/{condition_id}/measurements

Create measurement (stub implementation).

---

## Exports

### POST /projects/{project_id}/export

Export project data (stub implementation).

---

## Settings

### GET /settings

Get application settings (stub implementation).

---

## Error Codes

### Common HTTP Status Codes

- `200` - OK (successful request)
- `201` - Created (resource created)
- `204` - No Content (successful deletion)
- `400` - Bad Request (validation error)
- `404` - Not Found (resource doesn't exist)
- `422` - Unprocessable Entity (validation error)
- `500` - Internal Server Error (server error)

### Validation Errors

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "name"],
      "msg": "Field required"
    }
  ]
}
```

### File Upload Errors

```json
{
  "detail": "Unsupported file type: application/octet-stream"
}
```

```json
{
  "detail": "Invalid file: PDF file corrupted or incomplete"
}
```

## Rate Limiting

Currently not implemented. Will be added in production deployment.

## CORS

Cross-Origin Resource Sharing is configured for development:

```javascript
// Allowed origins
["http://localhost:5173", "http://localhost:3000"]
```

## Content Types

- Request: `application/json` for data, `multipart/form-data` for file uploads
- Response: `application/json` for all endpoints

## Pagination

Not implemented in Phase 1A. Will be added for list endpoints in future phases.

## Filtering & Sorting

Not implemented in Phase 1A. Will be added based on requirements.

## Webhooks

Not implemented in Phase 1A. Consider for production deployment to notify external systems of processing completion.

## SDKs & Libraries

### JavaScript/TypeScript

```typescript
// Example usage with axios
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1'
});

// Create project
const project = await api.post('/projects', {
  name: 'New Project',
  description: 'Project description'
});

// Upload document
const formData = new FormData();
formData.append('file', fileInput.files[0]);
const document = await api.post(`/projects/${project.data.id}/documents`, formData);

// Check status
const status = await api.get(`/documents/${document.data.id}/status`);
```

### Python

```python
import requests

base_url = "http://localhost:8000/api/v1"

# Create project
project = requests.post(f"{base_url}/projects", json={
    "name": "New Project",
    "description": "Description"
}).json()

# Upload document
with open('document.pdf', 'rb') as f:
    files = {'file': f}
    document = requests.post(
        f"{base_url}/projects/{project['id']}/documents",
        files=files
    ).json()

# Poll status
status = requests.get(f"{base_url}/documents/{document['id']}/status").json()
```

## Testing

### Unit Tests

```bash
# Run backend tests
cd backend
pytest

# Run frontend tests
cd frontend
npm test
```

### Integration Tests

```bash
# Test full upload workflow
# 1. Create project
# 2. Upload document
# 3. Poll status until complete
# 4. Verify pages created
# 5. Download images
```

### Load Testing

Consider using tools like:
- Artillery (JavaScript)
- Locust (Python)
- k6 (Go)

For testing concurrent file uploads and processing.

## Monitoring

### Health Checks

```bash
# Application health
curl http://localhost:8000/api/v1/health

# Database connectivity (to be implemented)
curl http://localhost:8000/api/v1/health/db

# Storage connectivity (to be implemented)
curl http://localhost:8000/api/v1/health/storage

# Worker status (to be implemented)
curl http://localhost:8000/api/v1/health/workers
```

### Metrics

Not implemented in Phase 1A. Consider adding:
- Request/response times
- Error rates
- File processing times
- Storage usage
- Queue depths

### Logging

Structured logging with `structlog`:

```json
{
  "timestamp": "2024-01-01T10:00:00Z",
  "level": "info",
  "event": "document_uploaded",
  "document_id": "660e8400-e29b-41d4-a716-446655440001",
  "file_size": 2457600,
  "file_type": "pdf"
}
```

## Deployment

### Development

```bash
# Start backend
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# Start frontend
cd frontend
npm install
npm run dev

# Start services
redis-server
celery -A app.workers.celery_app worker
```

### Production

```bash
# Docker deployment (to be implemented)
docker-compose up -d

# Kubernetes deployment (future)
kubectl apply -f k8s/
```

## Troubleshooting

### Common Issues

1. **File Upload Fails**
   - Check file size limits
   - Verify supported file types
   - Check storage service connectivity

2. **Processing Never Completes**
   - Check Celery worker status
   - Verify Redis connectivity
   - Check worker logs

3. **Database Errors**
   - Verify DATABASE_URL configuration
   - Check database connectivity
   - Run migrations: `alembic upgrade head`

4. **Storage Errors**
   - Verify MinIO/S3 credentials
   - Check storage service availability
   - Verify bucket permissions

### Debug Headers

```bash
# Add debug headers to requests
curl -H "X-Debug: true" http://localhost:8000/api/v1/health
```

### Log Levels

```bash
# Set log level
export LOG_LEVEL=DEBUG
uvicorn app.main:app
```

## Version History

- **v1.2.1** - Classification optimizations (January 20, 2026)
  - OCR-based classification by default (fast, free)
  - Image compression for LLM vision models (handles 5MB limit)
  - Automatic classification after OCR processing
  - `use_vision` parameter for classification endpoints
  - Document timestamp updates on classification

- **v1.2.0** - Phase 2A complete (January 19, 2026)
  - Multi-provider LLM client (Anthropic, OpenAI, Google, xAI)
  - AI-powered page classification
  - Discipline and page type detection
  - Concrete relevance scoring
  - Classification API endpoints
  - LLM provider selection endpoint

- **v1.1.0** - Phase 1B complete (January 19, 2026)
  - OCR text extraction with Google Cloud Vision
  - Page listing and OCR data endpoints
  - Full-text search across pages
  - Scale, sheet number, and title detection
  - Title block parsing
  - OCR reprocessing capability

- **v1.0.0** - Phase 1A complete
  - Document upload and processing
  - Project management
  - Basic file validation
  - Async processing with Celery

## Phase 1B Endpoints (OCR)

For complete OCR API documentation, see [OCR API Reference](./OCR_API.md).

**Quick Reference:**
- `GET /documents/{id}/pages` - List pages with OCR metadata
- `GET /pages/{id}` - Get page details
- `GET /pages/{id}/ocr` - Get complete OCR data
- `POST /pages/{id}/reprocess-ocr` - Reprocess OCR
- `GET /projects/{id}/search?q=text` - Search pages by text

## Phase 2A Endpoints - Page Classification

### POST /pages/{page_id}/classify

Trigger AI classification for a single page.

**Parameters:**
- `page_id` (path) - UUID of the page

**Request Body (optional):**
```json
{
  "use_vision": false,  // Default: false (fast OCR-based classification)
  "provider": "anthropic"  // Optional: Only used if use_vision=true
}
```

**Parameters:**
- `use_vision` (boolean, default: `false`) - If `false`, uses fast OCR-based classification (free, instant). If `true`, uses LLM vision model (costs $0.003-0.015 per page, takes 3-5 seconds).
- `provider` (string, optional) - LLM provider to use when `use_vision=true`. Options: `anthropic`, `openai`, `google`, `xai`.

**Response:**
```json
{
  "task_id": "abc123-task-id",
  "message": "Classification started for page 550e8400-e29b-41d4-a716-446655440000"
}
```

**Status Codes:**
- `202` - Classification task started
- `400` - Invalid provider specified
- `404` - Page not found

**Note:** Pages are automatically classified using OCR-based method after OCR processing completes. This endpoint is primarily for re-classification or when detailed LLM vision analysis is needed.

---

### POST /documents/{document_id}/classify

Trigger AI classification for all pages in a document.

**Parameters:**
- `document_id` (path) - UUID of the document

**Request Body (optional):**
```json
{
  "use_vision": false,  // Default: false (fast OCR-based classification)
  "provider": "anthropic"  // Optional: Only used if use_vision=true
}
```

**Parameters:**
- `use_vision` (boolean, default: `false`) - If `false`, uses fast OCR-based classification (free, instant). If `true`, uses LLM vision model (costs $0.003-0.015 per page, takes 3-5 seconds).
- `provider` (string, optional) - LLM provider to use when `use_vision=true`. Options: `anthropic`, `openai`, `google`, `xai`.

**Response:**
```json
{
  "document_id": "660e8400-e29b-41d4-a716-446655440001",
  "pages_queued": 5,
  "task_ids": ["task-1", "task-2", "task-3", "task-4", "task-5"]
}
```

**Status Codes:**
- `202` - Classification tasks started
- `400` - Invalid provider specified
- `404` - Document not found

**Note:** Pages are automatically classified using OCR-based method after OCR processing completes. This endpoint is primarily for re-classification or when detailed LLM vision analysis is needed.

---

### GET /pages/{page_id}/classification

Get classification results for a page.

**Parameters:**
- `page_id` (path) - UUID of the page

**Response:**
```json
{
  "page_id": "770e8400-e29b-41d4-a716-446655440002",
  "classification": "Structural:Plan",
  "confidence": 0.92,
  "concrete_relevance": "high",
  "metadata": {
    "discipline": "Structural",
    "discipline_confidence": 0.95,
    "page_type": "Plan",
    "page_type_confidence": 0.90,
    "concrete_elements": ["slab", "foundation wall", "footing"],
    "description": "Foundation plan showing footings and grade beams",
    "llm_provider": "anthropic",
    "llm_model": "claude-3-5-sonnet-20241022",
    "llm_latency_ms": 2450.5
  }
}
```

**Classification Values:**

| Field | Possible Values |
|-------|-----------------|
| discipline | Structural, Architectural, Civil, Mechanical, Electrical, Plumbing, Landscape, General |
| page_type | Plan, Elevation, Section, Detail, Schedule, Notes, Cover, Title |
| concrete_relevance | high, medium, low, none |

**Status Codes:**
- `200` - Classification found
- `404` - Page not found

---

### GET /settings/llm/providers

List available LLM providers and their configuration.

**Response:**
```json
{
  "providers": {
    "anthropic": {
      "name": "anthropic",
      "display_name": "Anthropic Claude",
      "model": "claude-3-5-sonnet-20241022",
      "strengths": "Best accuracy for construction documents",
      "cost_tier": "medium-high",
      "available": true,
      "is_default": true
    },
    "openai": {
      "name": "openai",
      "display_name": "OpenAI GPT-4o",
      "model": "gpt-4o",
      "strengths": "Fast response, good accuracy",
      "cost_tier": "high",
      "available": true,
      "is_default": false
    },
    "google": {
      "name": "google",
      "display_name": "Google Gemini",
      "model": "gemini-1.5-pro",
      "strengths": "Cost-effective, good for batch processing",
      "cost_tier": "medium",
      "available": true,
      "is_default": false
    },
    "xai": {
      "name": "xai",
      "display_name": "xAI Grok",
      "model": "grok-vision-beta",
      "strengths": "Alternative option",
      "cost_tier": "medium",
      "available": false,
      "is_default": false
    }
  },
  "default_provider": "anthropic"
}
```

---

## Scale Detection & Calibration

### POST /pages/{page_id}/detect-scale

Trigger automatic scale detection for a page using OCR text analysis and pattern matching.

**Parameters:**
- `page_id` (path) - UUID of the page

**Response:**
```json
{
  "status": "queued",
  "page_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Status Codes:**
- `202` - Detection task queued successfully
- `404` - Page not found

**Process:**
1. Queues a Celery task for async processing
2. Analyzes OCR text for scale patterns (e.g., "1/4\" = 1'-0\"")
3. Detects graphical scale bars using computer vision
4. Updates page with detected scale if confidence >= 85%

---

### PUT /pages/{page_id}/scale

Manually set or update the scale for a page.

**Parameters:**
- `page_id` (path) - UUID of the page

**Request Body:**
```json
{
  "scale_value": 10.5,
  "scale_unit": "foot",
  "scale_text": "1/4\" = 1'-0\""
}
```

**Fields:**
- `scale_value` (required) - Pixels per foot
- `scale_unit` (optional) - Unit system (default: "foot")
- `scale_text` (optional) - Human-readable scale notation

**Response:**
```json
{
  "status": "success",
  "page_id": "550e8400-e29b-41d4-a716-446655440000",
  "scale_value": 10.5,
  "scale_unit": "foot",
  "scale_calibrated": true
}
```

**Status Codes:**
- `200` - Scale updated successfully
- `404` - Page not found
- `422` - Validation error

---

### POST /pages/{page_id}/calibrate

Calibrate page scale using a known distance measurement.

**Parameters:**
- `page_id` (path) - UUID of the page
- `pixel_distance` (query) - Distance in pixels
- `real_distance` (query) - Real-world distance
- `real_unit` (query, optional) - Unit of measurement (default: "foot")

**Example Request:**
```
POST /pages/{id}/calibrate?pixel_distance=100&real_distance=10&real_unit=foot
```

**Response:**
```json
{
  "status": "success",
  "page_id": "550e8400-e29b-41d4-a716-446655440000",
  "pixels_per_foot": 10.0,
  "estimated_scale_ratio": 15.0
}
```

**Status Codes:**
- `200` - Calibration successful
- `400` - Invalid distance values
- `404` - Page not found

**Workflow:**
1. User draws a line on the plan
2. Frontend calculates pixel distance
3. User enters real-world distance
4. Backend calculates pixels_per_foot
5. Page marked as calibrated

---

### POST /pages/{page_id}/copy-scale-from/{source_page_id}

Copy scale settings from another page.

**Parameters:**
- `page_id` (path) - Target page UUID
- `source_page_id` (path) - Source page UUID

**Response:**
```json
{
  "status": "success",
  "page_id": "550e8400-e29b-41d4-a716-446655440000",
  "scale_value": 10.5,
  "copied_from": "660e8400-e29b-41d4-a716-446655440001"
}
```

**Status Codes:**
- `200` - Scale copied successfully
- `400` - Source page not calibrated
- `404` - Page not found

**Use Case:**
When multiple pages in a document have the same scale, calibrate one page and copy the scale to others instead of recalibrating each page individually.

---

## Scale Detection Details

### Supported Scale Formats

**Architectural Scales:**
- `1/4" = 1'-0"` (1:48) - Common for floor plans
- `1/8" = 1'-0"` (1:96) - Smaller buildings
- `3/16" = 1'-0"` (1:64)
- `1/2" = 1'-0"` (1:24) - Details
- `1" = 1'-0"` (1:12) - Large scale details
- `3" = 1'-0"` (1:4) - Full size

**Engineering Scales:**
- `1" = 10'` (1:120)
- `1" = 20'` (1:240) - Site plans
- `1" = 30'` (1:360)
- `1" = 50'` (1:600)
- `1" = 100'` (1:1200)

**Metric Scales:**
- `1:50`
- `1:100`
- `1:200`
- `1:500`

**Special:**
- `N.T.S.` or `NOT TO SCALE`

### Detection Methods

1. **OCR Text Patterns**: Regex matching on extracted text
2. **Visual Scale Bars**: OpenCV-based detection of graphical scales
3. **Confidence Scoring**: Each detection receives a confidence score (0-1)
4. **Auto-Calibration**: High confidence (≥0.85) automatically marks page as calibrated

---

## Future Endpoints

### Phase 3A - Measurement Engine
- `POST /measurements` - Create measurements
- `GET /measurements/{id}` - Get measurement details
- `PUT /measurements/{id}` - Update measurements
- `DELETE /measurements/{id}` - Delete measurements

### Phase 3A - Measurement Engine
- `POST /measurements` - Create measurements
- `GET /measurements/{id}` - Get measurement details
- `PUT /measurements/{id}` - Update measurements
- `DELETE /measurements/{id}` - Delete measurements

This API reference will be updated as new endpoints are implemented in future phases.

---

**Last Updated:** January 22, 2026 - Phase 3B Condition Management complete