# OCR API Reference - Phase 1B

## Overview

The OCR (Optical Character Recognition) API provides endpoints for extracting text from construction plan pages, detecting scales and sheet numbers, parsing title blocks, and searching across document text. This API integrates with Google Cloud Vision for text extraction.

**Base URL:** `http://localhost:8000/api/v1`

---

## Endpoints

### Page Management

#### GET /documents/{document_id}/pages

List all pages for a document with OCR metadata.

**Parameters:**
- `document_id` (path, required) - UUID of the document

**Response:** `200 OK`
```json
{
  "pages": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "document_id": "660e8400-e29b-41d4-a716-446655440000",
      "page_number": 1,
      "width": 2550,
      "height": 3300,
      "classification": "floor_plan",
      "title": "FOUNDATION PLAN",
      "sheet_number": "A1.01",
      "scale_text": "1/4\" = 1'-0\"",
      "scale_calibrated": false,
      "status": "ready",
      "thumbnail_url": "https://minio:9000/..."
    }
  ],
  "total": 1
}
```

**Status Codes:**
- `200` - Success
- `404` - Document not found

---

#### GET /pages/{page_id}

Get detailed page information including OCR metadata.

**Parameters:**
- `page_id` (path, required) - UUID of the page

**Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "document_id": "660e8400-e29b-41d4-a716-446655440000",
  "page_number": 1,
  "width": 2550,
  "height": 3300,
  "classification": "floor_plan",
  "classification_confidence": 0.95,
  "title": "FOUNDATION PLAN",
  "sheet_number": "A1.01",
  "scale_text": "1/4\" = 1'-0\"",
  "scale_value": 48.0,
  "scale_unit": "foot",
  "scale_calibrated": false,
  "status": "ready",
  "image_url": "https://minio:9000/...",
  "thumbnail_url": "https://minio:9000/..."
}
```

**Status Codes:**
- `200` - Success
- `404` - Page not found

---

#### GET /pages/{page_id}/image

Get a redirect to the page image URL (presigned URL for direct access).

**Parameters:**
- `page_id` (path, required) - UUID of the page

**Response:** `302 Found`
- Redirects to presigned S3/MinIO URL
- URL valid for 1 hour

**Status Codes:**
- `302` - Redirect to image
- `404` - Page not found

---

### OCR Data

#### GET /pages/{page_id}/ocr

Get complete OCR data for a page including detected text, blocks, and extracted elements.

**Parameters:**
- `page_id` (path, required) - UUID of the page

**Response:** `200 OK`
```json
{
  "full_text": "FOUNDATION PLAN\nSCALE: 1/4\" = 1'-0\"\nSHEET A1.01\n...",
  "blocks": [
    {
      "text": "FOUNDATION PLAN",
      "confidence": 0.98,
      "bounding_box": {
        "x": 100,
        "y": 50,
        "width": 400,
        "height": 60
      }
    }
  ],
  "detected_scales": [
    "1/4\" = 1'-0\"",
    "SCALE: 1/4\" = 1'-0\""
  ],
  "detected_sheet_numbers": [
    "A1.01"
  ],
  "detected_titles": [
    "FOUNDATION PLAN"
  ],
  "sheet_number": "A1.01",
  "title": "FOUNDATION PLAN",
  "scale_text": "1/4\" = 1'-0\""
}
```

**Field Descriptions:**
- `full_text` - Complete extracted text from the page
- `blocks` - Individual text blocks with positions and confidence scores
- `detected_scales` - All scale notations found on the page
- `detected_sheet_numbers` - All sheet numbers found
- `detected_titles` - All potential titles found
- `sheet_number` - Primary sheet number (first detected)
- `title` - Primary title (first detected)
- `scale_text` - Primary scale notation (first detected)

**Status Codes:**
- `200` - Success
- `404` - Page not found

---

#### POST /pages/{page_id}/reprocess-ocr

Reprocess OCR for a specific page (useful if initial OCR failed or needs updating).

**Parameters:**
- `page_id` (path, required) - UUID of the page

**Response:** `202 Accepted`
```json
{
  "status": "queued",
  "page_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Status Codes:**
- `202` - OCR task queued
- `404` - Page not found

**Notes:**
- OCR processing is asynchronous via Celery
- Check page status or OCR data endpoint to see when complete
- Typically takes 1-3 seconds per page

---

### Search

#### GET /projects/{project_id}/search

Search for text across all pages in a project using full-text search.

**Parameters:**
- `project_id` (path, required) - UUID of the project
- `q` (query, required) - Search query text

**Example:**
```
GET /projects/550e8400-e29b-41d4-a716-446655440000/search?q=foundation
```

**Response:** `200 OK`
```json
{
  "results": [
    {
      "page_id": "660e8400-e29b-41d4-a716-446655440000",
      "document_id": "770e8400-e29b-41d4-a716-446655440000",
      "page_number": 1,
      "title": "FOUNDATION PLAN",
      "sheet_number": "A1.01",
      "relevance": 0.8567
    },
    {
      "page_id": "880e8400-e29b-41d4-a716-446655440000",
      "document_id": "770e8400-e29b-41d4-a716-446655440000",
      "page_number": 5,
      "title": "FOUNDATION DETAILS",
      "sheet_number": "A1.05",
      "relevance": 0.7234
    }
  ],
  "total": 2
}
```

**Field Descriptions:**
- `relevance` - Search relevance score (0-1, higher is better)
- Results are sorted by relevance (most relevant first)
- Limited to 50 results

**Search Features:**
- Full-text search using PostgreSQL `to_tsvector`
- Fuzzy matching for typos (trigram similarity)
- Stemming and stop word removal
- Ranked by relevance

**Status Codes:**
- `200` - Success
- `404` - Project not found

---

## OCR Processing Flow

### Automatic Processing

OCR is automatically triggered when a document is uploaded:

```
1. Document uploaded → POST /documents/upload
2. Document processed → Pages extracted
3. OCR automatically queued for all pages
4. Each page processed independently
5. OCR data stored in database
```

### Manual Reprocessing

To reprocess OCR for a specific page:

```
POST /pages/{page_id}/reprocess-ocr
```

Use cases:
- Initial OCR failed
- Better quality image available
- Pattern detection needs updating

---

## Pattern Detection

### Scale Patterns

The OCR service detects the following scale notation formats:

**Architectural Scales:**
- `1/4" = 1'-0"`
- `1/8" = 1'-0"`
- `3/8" = 1'-0"`

**Engineering Scales:**
- `1" = 10'`
- `1" = 20'`
- `1" = 50'`

**Metric Scales:**
- `SCALE: 1:100`
- `1:50 SCALE`

**Not to Scale:**
- `NTS`
- `NOT TO SCALE`

### Sheet Number Patterns

**Standard Formats:**
- `A1.01` - Architectural, floor 1, sheet 1
- `S-101` - Structural, sheet 101
- `M101` - Mechanical, sheet 101

**With Labels:**
- `SHEET NO: A1.01`
- `SHEET NUMBER: A1.01`
- `DWG. NO: A1.01`

### Title Patterns

**Common Titles:**
- `FOUNDATION PLAN`
- `SITE PLAN`
- `FLOOR PLAN`
- `ROOF PLAN`
- `ELEVATION`
- `SECTION`
- `DETAIL`
- `SCHEDULE`

**With Labels:**
- `TITLE: FOUNDATION PLAN`

---

## Title Block Parsing

The OCR service automatically parses title blocks (typically in the bottom-right corner) to extract:

- **Sheet Number** - Drawing identifier
- **Sheet Title** - Drawing name
- **Project Name** - Project identifier
- **Project Number** - Job number
- **Date** - Drawing date
- **Revision** - Revision number/letter
- **Scale** - Drawing scale
- **Drawn By** - Drafter initials
- **Checked By** - Checker initials

**Title Block Region:**
- Bottom-right 30% x 30% of page
- Parsed using regex patterns
- Fields stored in `ocr_blocks.title_block`

---

## Error Handling

### OCR Errors

If OCR processing fails:

1. **Automatic Retry** - Up to 3 attempts with 30-second backoff
2. **Error Tracking** - Error message stored in `page.processing_error`
3. **Status Update** - Page status remains "processing" or set to "error"

**Common Errors:**
- Google Cloud Vision API quota exceeded
- Invalid credentials
- Image format not supported
- Network timeout

**Resolution:**
- Check Google Cloud Vision credentials
- Verify API quota
- Reprocess page: `POST /pages/{page_id}/reprocess-ocr`

### Search Errors

If search fails:
- Verify full-text search indexes exist
- Run migration: `alembic upgrade head`
- Check PostgreSQL `pg_trgm` extension installed

---

## Performance

### OCR Processing Time

- **Single Page:** 1-3 seconds (Google Cloud Vision API)
- **Large Documents:** Pages processed in parallel via Celery
- **Retry Logic:** 3 attempts with 30-second backoff

### Search Performance

- **Query Time:** <100ms for typical searches
- **Index Type:** GIN (Generalized Inverted Index)
- **Optimization:** Indexes on `ocr_text` column

### Cost Considerations

**Google Cloud Vision Pricing:**
- First 1,000 images/month: Free
- After free tier: $1.50 per 1,000 images

**Optimization Tips:**
- Cache OCR results
- Only reprocess when necessary
- Monitor API usage

---

## Examples

### Complete Workflow Example

```bash
# 1. Upload document
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@plans.pdf" \
  -F "project_id=550e8400-e29b-41d4-a716-446655440000"

# Response: {"id": "660e8400-...", "status": "processing"}

# 2. Wait for processing (check status)
curl http://localhost:8000/api/v1/documents/660e8400-e29b-41d4-a716-446655440000

# Response: {"status": "ready", "page_count": 10}

# 3. List pages with OCR data
curl http://localhost:8000/api/v1/documents/660e8400-e29b-41d4-a716-446655440000/pages

# 4. Get detailed OCR for a page
curl http://localhost:8000/api/v1/pages/770e8400-e29b-41d4-a716-446655440000/ocr

# 5. Search across all pages
curl "http://localhost:8000/api/v1/projects/550e8400-e29b-41d4-a716-446655440000/search?q=foundation"
```

### Reprocess OCR Example

```bash
# Reprocess OCR for a specific page
curl -X POST http://localhost:8000/api/v1/pages/770e8400-e29b-41d4-a716-446655440000/reprocess-ocr

# Response: {"status": "queued", "page_id": "770e8400-..."}

# Check OCR status
curl http://localhost:8000/api/v1/pages/770e8400-e29b-41d4-a716-446655440000/ocr
```

---

## Related Documentation

- [Database Schema](../database/DATABASE_SCHEMA.md) - OCR data storage structure
- [Phase 1B Complete](../phase-guides/PHASE_1B_COMPLETE.md) - Implementation details
- [API Conventions](./API-CONVENTIONS.md) - General API patterns

---

**Last Updated:** January 19, 2026 - Phase 1B Complete
