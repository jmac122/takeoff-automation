# Takeoff Platform - API Conventions

> **Purpose**: Ensure consistent API design across all backend endpoints
> **Stack**: FastAPI, Pydantic, SQLAlchemy

---

## URL Structure

### Base Pattern

```
/api/v1/{resource}
/api/v1/{resource}/{id}
/api/v1/{resource}/{id}/{sub-resource}
```

### Examples

```
GET    /api/v1/documents              # List documents
POST   /api/v1/documents              # Create document
GET    /api/v1/documents/{id}         # Get single document
PUT    /api/v1/documents/{id}         # Update document
DELETE /api/v1/documents/{id}         # Delete document

GET    /api/v1/documents/{id}/pages   # List pages for document
POST   /api/v1/documents/{id}/pages   # Create page for document

POST   /api/v1/documents/{id}/process # Trigger processing action
```

### Naming Rules

1. **Use plural nouns** for resources: `documents`, `pages`, `conditions`
2. **Use kebab-case** for multi-word resources: `export-jobs`, `ai-takeoffs`
3. **Use verbs only for actions**: `process`, `classify`, `export`
4. **Never use trailing slashes**

---

## HTTP Methods

| Method | Purpose | Idempotent | Request Body | Response |
|--------|---------|------------|--------------|----------|
| GET | Retrieve resource(s) | Yes | No | Resource(s) |
| POST | Create resource or trigger action | No | Yes | Created resource |
| PUT | Full update of resource | Yes | Yes | Updated resource |
| PATCH | Partial update of resource | Yes | Yes | Updated resource |
| DELETE | Remove resource | Yes | No | 204 No Content |

---

## Request/Response Schemas

### Naming Convention

```python
# Schema naming pattern
{Resource}Create      # POST request body
{Resource}Update      # PUT/PATCH request body  
{Resource}Response    # Single resource response
{Resource}List        # List response with pagination
{Resource}Brief       # Minimal resource representation (for lists/references)
```

### Example

```python
# backend/app/schemas/document.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID


class DocumentBase(BaseModel):
    """Shared fields between create/update/response."""
    name: str
    description: Optional[str] = None


class DocumentCreate(DocumentBase):
    """Fields required to create a document."""
    pass  # Inherits name, description


class DocumentUpdate(BaseModel):
    """Fields that can be updated (all optional)."""
    name: Optional[str] = None
    description: Optional[str] = None


class DocumentBrief(BaseModel):
    """Minimal representation for lists and references."""
    id: UUID
    name: str
    page_count: int
    status: str
    
    class Config:
        from_attributes = True


class DocumentResponse(DocumentBase):
    """Full document representation."""
    id: UUID
    status: str
    page_count: int
    file_path: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DocumentList(BaseModel):
    """Paginated list of documents."""
    items: list[DocumentBrief]
    total: int
    page: int
    page_size: int
    pages: int
```

---

## Pagination

### Standard Query Parameters

```python
@router.get("/documents", response_model=DocumentList)
async def list_documents(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    db: AsyncSession = Depends(get_db),
):
    ...
```

### Response Format

```json
{
  "items": [...],
  "total": 156,
  "page": 1,
  "page_size": 20,
  "pages": 8
}
```

### Helper Function

```python
# backend/app/utils/pagination.py
from typing import TypeVar, Generic
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int


async def paginate(
    db: AsyncSession,
    query,
    page: int,
    page_size: int,
) -> tuple[list, int]:
    """Execute query with pagination, return (items, total)."""
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # Get paginated items
    offset = (page - 1) * page_size
    items_query = query.offset(offset).limit(page_size)
    result = await db.execute(items_query)
    items = result.scalars().all()
    
    return items, total


def create_paginated_response(
    items: list,
    total: int,
    page: int,
    page_size: int,
) -> dict:
    """Create standard pagination response."""
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    }
```

---

## Filtering

### Query Parameters

```python
@router.get("/pages", response_model=PageList)
async def list_pages(
    document_id: Optional[UUID] = Query(None, description="Filter by document"),
    classification: Optional[str] = Query(None, description="Filter by classification"),
    has_scale: Optional[bool] = Query(None, description="Filter by scale detection"),
    status: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search in OCR text"),
    ...
):
    ...
```

### Complex Filters

For complex filtering, use a filter schema:

```python
class PageFilter(BaseModel):
    document_id: Optional[UUID] = None
    classifications: Optional[list[str]] = None  # Multiple values
    status: Optional[list[str]] = None
    has_scale: Optional[bool] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    search: Optional[str] = None


@router.post("/pages/search", response_model=PageList)
async def search_pages(
    filters: PageFilter,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ...
):
    ...
```

---

## Error Responses

### Standard Error Schema

```python
# backend/app/schemas/error.py
from pydantic import BaseModel
from typing import Optional, Any


class ErrorDetail(BaseModel):
    loc: list[str]  # Location of error (field path)
    msg: str        # Human-readable message
    type: str       # Error type identifier


class ErrorResponse(BaseModel):
    error: str              # Error code
    message: str            # Human-readable message
    details: Optional[list[ErrorDetail]] = None
```

### HTTP Status Codes

| Status | When to Use | Error Code |
|--------|-------------|------------|
| 400 | Invalid request body/params | `validation_error` |
| 401 | Missing/invalid auth | `unauthorized` |
| 403 | Authenticated but not allowed | `forbidden` |
| 404 | Resource not found | `not_found` |
| 409 | Conflict (duplicate, state issue) | `conflict` |
| 422 | Validation failed | `validation_error` |
| 500 | Server error | `internal_error` |

### Exception Handlers

```python
# backend/app/api/errors.py
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError


class AppException(Exception):
    """Base application exception."""
    def __init__(
        self, 
        status_code: int, 
        error: str, 
        message: str,
        details: list = None
    ):
        self.status_code = status_code
        self.error = error
        self.message = message
        self.details = details


class NotFoundError(AppException):
    def __init__(self, resource: str, id: str):
        super().__init__(
            status_code=404,
            error="not_found",
            message=f"{resource} with id '{id}' not found"
        )


class ConflictError(AppException):
    def __init__(self, message: str):
        super().__init__(
            status_code=409,
            error="conflict",
            message=message
        )


# Register handlers in main.py
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error,
            "message": exc.message,
            "details": exc.details,
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": "validation_error",
            "message": "Request validation failed",
            "details": [
                {"loc": list(e["loc"]), "msg": e["msg"], "type": e["type"]}
                for e in exc.errors()
            ]
        }
    )
```

---

## Async Operations

For long-running tasks, return a job/task resource:

### Pattern

```python
# 1. Trigger async operation
POST /api/v1/documents/{id}/process
Response: 202 Accepted
{
  "task_id": "abc-123",
  "status": "pending",
  "status_url": "/api/v1/tasks/abc-123"
}

# 2. Poll for status
GET /api/v1/tasks/{task_id}
Response: 200 OK
{
  "task_id": "abc-123",
  "status": "processing",  // pending, processing, completed, failed
  "progress": 45,
  "result": null
}

# 3. Final result
GET /api/v1/tasks/{task_id}
Response: 200 OK
{
  "task_id": "abc-123",
  "status": "completed",
  "progress": 100,
  "result": {
    "pages_processed": 12,
    "classifications": {...}
  }
}
```

### Implementation

```python
# backend/app/api/routes/documents.py
from celery.result import AsyncResult


@router.post("/{document_id}/process", status_code=202)
async def process_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Trigger document processing (async)."""
    document = await get_document_or_404(db, document_id)
    
    # Trigger Celery task
    task = process_document_task.delay(str(document_id))
    
    return {
        "task_id": task.id,
        "status": "pending",
        "status_url": f"/api/v1/tasks/{task.id}"
    }


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get status of async task."""
    result = AsyncResult(task_id)
    
    response = {
        "task_id": task_id,
        "status": result.status.lower(),
    }
    
    if result.status == "PROGRESS":
        response["progress"] = result.info.get("progress", 0)
    elif result.status == "SUCCESS":
        response["progress"] = 100
        response["result"] = result.result
    elif result.status == "FAILURE":
        response["error"] = str(result.result)
    
    return response
```

---

## File Uploads

### Multipart Form Data

```python
from fastapi import UploadFile, File


@router.post("/documents", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(..., description="PDF or TIFF file"),
    name: Optional[str] = Form(None, description="Document name (defaults to filename)"),
    db: AsyncSession = Depends(get_db),
):
    """Upload a new document."""
    # Validate file type
    if file.content_type not in ["application/pdf", "image/tiff"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Must be PDF or TIFF."
        )
    
    # Validate file size (e.g., 100MB limit)
    content = await file.read()
    if len(content) > 100 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum size is 100MB."
        )
    
    # Process upload...
```

### File Download

```python
from fastapi.responses import StreamingResponse
import aiofiles


@router.get("/exports/{export_id}/download")
async def download_export(
    export_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Download an export file."""
    export_job = await get_export_or_404(db, export_id)
    
    if export_job.status != "completed":
        raise HTTPException(status_code=400, detail="Export not ready")
    
    async def file_iterator():
        async with aiofiles.open(export_job.file_path, "rb") as f:
            while chunk := await f.read(8192):
                yield chunk
    
    return StreamingResponse(
        file_iterator(),
        media_type=export_job.mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{export_job.filename}"'
        }
    )
```

---

## API Versioning

All endpoints are prefixed with `/api/v1/`. If breaking changes are needed:

1. Create new router with `/api/v2/` prefix
2. Maintain `/api/v1/` for backward compatibility
3. Add deprecation headers to v1 endpoints
4. Document migration path

```python
# backend/app/api/router.py
from fastapi import APIRouter

api_v1_router = APIRouter(prefix="/api/v1")
api_v2_router = APIRouter(prefix="/api/v2")  # Future

# Include all v1 routes
api_v1_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_v1_router.include_router(pages.router, prefix="/pages", tags=["pages"])
...
```

---

## OpenAPI Documentation

### Tags

Group endpoints by resource:

```python
# In each router file
router = APIRouter(tags=["documents"])
```

### Descriptions

```python
@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get document by ID",
    description="Retrieve a single document with all its metadata.",
    responses={
        404: {"description": "Document not found"},
    }
)
async def get_document(document_id: UUID, ...):
    """
    Get a document by its unique identifier.
    
    Returns the full document object including:
    - Basic metadata (name, description)
    - Processing status
    - Page count
    - Timestamps
    """
    ...
```

### Response Examples

```python
from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    id: UUID = Field(..., example="550e8400-e29b-41d4-a716-446655440000")
    name: str = Field(..., example="Foundation Plans.pdf")
    status: str = Field(..., example="processed")
    page_count: int = Field(..., example=24)
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Foundation Plans.pdf",
                "status": "processed",
                "page_count": 24,
                "created_at": "2025-01-15T10:30:00Z",
            }
        }
```

---

## Testing API Endpoints

### Test Structure

```python
# backend/tests/api/test_documents.py
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_document(client: AsyncClient, test_pdf: bytes):
    """Test document upload."""
    response = await client.post(
        "/api/v1/documents",
        files={"file": ("test.pdf", test_pdf, "application/pdf")},
    )
    
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["name"] == "test.pdf"
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_get_document_not_found(client: AsyncClient):
    """Test 404 for missing document."""
    response = await client.get(
        "/api/v1/documents/00000000-0000-0000-0000-000000000000"
    )
    
    assert response.status_code == 404
    assert response.json()["error"] == "not_found"
```

---

## Checklist for New Endpoints

- [ ] URL follows naming conventions
- [ ] Correct HTTP method for the action
- [ ] Request/response schemas defined
- [ ] Pagination for list endpoints
- [ ] Error responses documented
- [ ] OpenAPI tags and descriptions
- [ ] Unit/integration tests written
- [ ] Added to router in `api/router.py`
