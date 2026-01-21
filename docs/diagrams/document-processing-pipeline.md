# Document Processing Pipeline

How uploaded documents (PDF/TIFF) are processed into page images.

## Flow Diagram

```mermaid
flowchart TD
    subgraph Upload["1. Upload"]
        A[User uploads PDF/TIFF] --> B[FastAPI endpoint]
        B --> C{Validate file type}
        C -->|Invalid| D[Return 400 error]
        C -->|Valid| E[Create Document record]
    end

    subgraph Storage["2. Original Storage"]
        E --> F[Store original in MinIO]
        F --> G[Update Document.storage_key]
        G --> H[Queue process_document_task]
    end

    subgraph Processing["3. Celery Worker Processing"]
        H --> I[Download original from MinIO]
        I --> J{File type?}
        
        J -->|PDF| K[PyMuPDF renders page]
        J -->|TIFF| L[PIL opens TIFF frame]
        
        K --> M[Raw pixels in memory]
        L --> M
        
        M --> N[Resize to max 1568px]
        N --> O[Save as PNG bytes]
    end

    subgraph PageStorage["4. Page Storage"]
        O --> P[Store page image in MinIO]
        P --> Q[Create thumbnail 256px]
        Q --> R[Store thumbnail in MinIO]
        R --> S[Create Page record in DB]
    end

    subgraph Completion["5. Completion"]
        S --> T[Update Document status = ready]
        T --> U[Queue OCR task]
    end

    style Upload fill:#e1f5fe
    style Storage fill:#fff3e0
    style Processing fill:#f3e5f5
    style PageStorage fill:#e8f5e9
    style Completion fill:#fce4ec
```

## Key Components

| Component | File | Purpose |
|-----------|------|---------|
| Upload endpoint | `backend/app/api/routes/documents.py` | Receives file, validates, creates record |
| Document processor | `backend/app/services/document_processor.py` | Orchestrates extraction and storage |
| PDF utilities | `backend/app/utils/pdf_utils.py` | PDF/TIFF rendering and resizing |
| Celery task | `backend/app/workers/document_tasks.py` | Async processing worker |
| Storage service | `backend/app/utils/storage.py` | MinIO S3-compatible storage |

## Storage Structure

```
MinIO Bucket
└── projects/{project_id}/
    └── documents/{document_id}/
        ├── original/
        │   └── {filename}.pdf          # Original uploaded file
        └── pages/{page_id}/
            ├── image.png               # Full resolution (max 1568px)
            └── thumbnail.png           # 256px thumbnail
```

## Database Records

```mermaid
erDiagram
    Document ||--o{ Page : contains
    Document {
        uuid id PK
        uuid project_id FK
        string filename
        string storage_key
        string status
        int page_count
    }
    Page {
        uuid id PK
        uuid document_id FK
        int page_number
        int width
        int height
        string image_key
        string thumbnail_key
        string status
    }
```

---

## Experimental: TIFF Storage Format (January 2026)

> **Status**: Testing in progress. This section documents an experimental change to evaluate coordinate accuracy improvements.

### Rationale

PDFs can contain embedded fonts, layers, transparency, and other elements that may render inconsistently across different tools. By converting all pages to TIFF format at a fixed resolution, we ensure:

1. **Flattened raster output** - What you see is what OCR and LLM see
2. **Consistent format** - No format conversion needed between storage and analysis
3. **Eliminated compression artifacts** - LZW is lossless, unlike JPEG
4. **Single coordinate system** - Fixed 1568px max dimension means no scale factor tracking

### Dual-Format Storage (Final Implementation)

| Format | Purpose | Storage Key |
|--------|---------|-------------|
| TIFF (LZW) | OCR, LLM vision analysis | `image.tiff` |
| PNG | Frontend viewer (browser-compatible) | `image.png` |
| PNG | Thumbnail | `thumbnail.png` |

### Updated Storage Structure

```
MinIO Bucket
└── projects/{project_id}/
    └── documents/{document_id}/
        ├── original/
        │   └── {filename}.pdf          # Original uploaded file
        └── pages/{page_id}/
            ├── image.tiff              # For OCR/LLM (flattened, consistent)
            ├── image.png               # For frontend viewer (browser-compatible)
            └── thumbnail.png           # 256px thumbnail
```

### Processing Flow

```mermaid
flowchart TD
    subgraph Processing["Page Processing"]
        A[PDF/TIFF uploaded] --> B[PyMuPDF or PIL extracts page]
        B --> C[Convert to RGB]
        C --> D[Resize to max 1568px]
        D --> E[Save as TIFF with LZW]
        E --> F[Store image.tiff in MinIO]
        E --> G[Convert to PNG]
        G --> H[Store image.png in MinIO]
    end

    subgraph Usage["Usage"]
        F --> I[OCR - Google Cloud Vision]
        F --> J[LLM Vision - Claude/GPT/Gemini]
        H --> K[Frontend Viewer]
    end

    style Processing fill:#e8f5e9
    style Usage fill:#fff8e1
```

### Files Modified

| File | Change |
|------|--------|
| `backend/app/utils/pdf_utils.py` | Added `convert_to_png()`, TIFF with LZW compression |
| `backend/app/services/document_processor.py` | Stores both TIFF and PNG formats |
| `backend/app/api/routes/pages.py` | Returns PNG URL for frontend via `get_viewer_image_key()` |

### Why Dual Format?

1. **TIFF for backend**: Flattens PDF layers/fonts into clean raster, consistent for OCR/LLM
2. **PNG for frontend**: Browsers don't natively support TIFF, PNG is universally compatible
3. **Same coordinates**: Both formats have identical pixel dimensions (1568px max), so coordinates match exactly

### Testing Checklist

- [ ] Upload PDF → Verify both `.tiff` and `.png` stored
- [ ] OCR works on TIFF images
- [ ] Scale detection returns accurate coordinates
- [ ] LLM vision analysis works with TIFF
- [ ] Frontend viewer displays PNG correctly
- [ ] Thumbnails remain PNG for web display
