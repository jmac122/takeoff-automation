# Scale Detection Accuracy

How scale detection achieves pixel-perfect bounding box accuracy.

## The Problem (Before Fix)

```mermaid
flowchart TD
    subgraph Problem["Previous Approach - Error Prone"]
        A[Large image 3000x2000px] --> B[Compress for LLM 5MB limit]
        B --> C[Send compressed image 1500x1000px]
        C --> D[LLM returns bbox in compressed coords]
        D --> E[Scale bbox back: multiply by 2.0]
        E --> F[❌ Inaccurate coordinates]
    end

    style Problem fill:#ffebee
```

**Issues:**
- Compression scale factor tracking was complex
- Reverse-scaling introduced rounding errors
- LLM bbox estimates were approximate, not pixel-perfect

## The Solution (Current)

```mermaid
flowchart TD
    subgraph Solution["Current Approach - Pixel Perfect"]
        A[PDF uploaded] --> B[Extract at max 1568px]
        B --> C[Store fixed-size image]
        C --> D[Send to LLM - no compression needed]
        D --> E[LLM returns scale text + approximate bbox]
        E --> F[Search OCR blocks for scale text]
        F --> G{OCR match found?}
        G -->|Yes| H[✅ Use OCR bbox - pixel perfect]
        G -->|No| I[Use LLM bbox as fallback]
        H --> J[Store bbox in scale_calibration_data]
        I --> J
    end

    style Solution fill:#e8f5e9
```

## Detailed Scale Detection Flow

```mermaid
flowchart TD
    subgraph Input["Input"]
        IMG[Page Image<br/>max 1568px] 
        OCR[OCR Blocks<br/>with bounding boxes]
    end

    subgraph LLM["1. LLM Analysis"]
        IMG --> PROMPT[Prompt: Find scale notation]
        PROMPT --> GEMINI[Gemini 2.5 Flash]
        GEMINI --> RESPONSE[JSON Response]
        RESPONSE --> PARSE[Parse scale_text + bbox]
    end

    subgraph Match["2. OCR Matching"]
        PARSE --> NORMALIZE[Normalize scale text<br/>remove spaces, quotes, etc]
        OCR --> SEARCH[Search OCR blocks]
        NORMALIZE --> SEARCH
        SEARCH --> SCORE[Calculate match scores]
        SCORE --> BEST{Best match > 0.5?}
    end

    subgraph Result["3. Final Bbox"]
        BEST -->|Yes| OCR_BBOX[Use OCR bounding box<br/>✅ Pixel perfect]
        BEST -->|No| LLM_BBOX[Use LLM bounding box<br/>⚠️ Approximate]
        OCR_BBOX --> STORE[Store in scale_calibration_data]
        LLM_BBOX --> STORE
    end

    style Input fill:#e3f2fd
    style LLM fill:#fff8e1
    style Match fill:#f3e5f5
    style Result fill:#e8f5e9
```

## OCR Block Matching Algorithm

```mermaid
flowchart TD
    A[LLM detected: "1/4\" = 1'-0\""] --> B[Normalize: "1410"]
    
    C[OCR Blocks] --> D[For each block]
    D --> E[Normalize block text]
    E --> F{Exact match?}
    F -->|Yes| G[Score = 1.0]
    F -->|No| H{Partial match?}
    H -->|Yes| I[Score = overlap ratio]
    H -->|No| J[Score = 0]
    
    G --> K[Track best match]
    I --> K
    J --> K
    
    K --> L{Best score > 0.5?}
    L -->|Yes| M[Return OCR bbox]
    L -->|No| N[Try combining nearby blocks]
    N --> O{Combined match?}
    O -->|Yes| P[Return combined bbox]
    O -->|No| Q[Fall back to LLM bbox]
```

## Why Fixed Resolution Matters

```mermaid
flowchart LR
    subgraph Before["Before: Variable Resolution"]
        B1[3000px image] --> B2[Compress to 1500px]
        B2 --> B3[LLM bbox: x=100]
        B3 --> B4[Scale back: x=200]
        B4 --> B5[❌ Rounding error]
    end

    subgraph After["After: Fixed Resolution"]
        A1[1568px image] --> A2[No compression]
        A2 --> A3[LLM bbox: x=100]
        A3 --> A4[OCR bbox: x=102]
        A4 --> A5[✅ Exact match]
    end

    style Before fill:#ffebee
    style After fill:#e8f5e9
```

## Coordinate System

```
(0,0) ─────────────────────────────► X
  │
  │    ┌─────────────────────────┐
  │    │                         │
  │    │      Page Image         │
  │    │      1568 x 1045        │
  │    │                         │
  │    │   ┌──────────────┐      │
  │    │   │ Scale: 1/4"  │ ◄── bbox {x, y, width, height}
  │    │   └──────────────┘      │
  │    │                         │
  │    └─────────────────────────┘
  ▼
  Y

All coordinates are in pixels, origin top-left.
No scaling or transformation needed.
```

## Key Files

| File | Role |
|------|------|
| `backend/app/services/scale_detector.py` | Main detection logic, OCR matching |
| `backend/app/services/llm_client.py` | LLM API calls (no compression) |
| `backend/app/workers/scale_tasks.py` | Celery task orchestration |
| `frontend/src/pages/TakeoffViewer.tsx` | Renders bbox overlay on canvas |

---

## Experimental: TIFF Format for Coordinate Accuracy (January 2026)

> **Status**: Testing in progress. This section documents an experimental approach to further improve coordinate accuracy.

### Hypothesis

By storing page images as TIFF instead of PNG, we can:

1. **Eliminate format inconsistencies** - PDFs with embedded fonts, layers, and transparency are flattened to clean raster images
2. **Ensure identical input** - OCR, LLM, and frontend all see the exact same pixels
3. **Remove any potential PNG encoding variations** - TIFF with LZW is a simpler, more predictable format

### The Experimental Approach

```mermaid
flowchart TD
    subgraph Current["Current: Fixed Resolution PNG"]
        A1[PDF uploaded] --> B1[Extract at max 1568px]
        B1 --> C1[Save as PNG]
        C1 --> D1[Store in MinIO]
        D1 --> E1[Send PNG to LLM/OCR]
    end

    subgraph Experimental["Experimental: Fixed Resolution TIFF"]
        A2[PDF uploaded] --> B2[Extract at max 1568px]
        B2 --> C2[Save as TIFF with LZW]
        C2 --> D2[Store in MinIO]
        D2 --> E2[Send TIFF to LLM/OCR]
    end

    subgraph Benefit["Expected Benefit"]
        F[PDF layers/fonts/effects]
        F --> G[Flattened to clean raster]
        G --> H[Consistent coordinates across all tools]
    end

    style Current fill:#e3f2fd
    style Experimental fill:#e8f5e9
    style Benefit fill:#fff8e1
```

### Why TIFF?

| Factor | PNG | TIFF (LZW) |
|--------|-----|------------|
| Compression | Lossless | Lossless |
| PDF flattening | Yes | Yes |
| Industry standard for plans | Common | Very common |
| Multi-page support | No | Yes (native) |
| LLM compatibility | All providers | All providers |

### Changes Made

1. **`backend/app/utils/pdf_utils.py`**
   - `extract_pdf_pages_as_images()` default format: `PNG` → `TIFF`
   - `extract_tiff_pages_as_images()` default format: `PNG` → `TIFF`
   - `resize_image_for_llm()` default format: `PNG` → `TIFF`
   - Added `_save_image()` helper with LZW compression for TIFF

2. **`backend/app/services/document_processor.py`**
   - Storage key: `image.png` → `image.tiff`
   - Content type: `image/png` → `image/tiff`
   - Thumbnails remain PNG (web-friendly)

3. **`backend/app/services/llm_client.py`**
   - No changes needed - `_detect_media_type()` already handles TIFF magic bytes

### Coordinate System (Unchanged)

```
(0,0) ─────────────────────────────► X
  │
  │    ┌─────────────────────────┐
  │    │                         │
  │    │   Page Image (TIFF)     │
  │    │      1568 x 1045        │
  │    │                         │
  │    │   ┌──────────────┐      │
  │    │   │ Scale: 1/4"  │ ◄── bbox {x, y, width, height}
  │    │   └──────────────┘      │
  │    │                         │
  │    └─────────────────────────┘
  ▼
  Y

All coordinates remain in pixels, origin top-left.
The only change is the underlying image format.
```

### Testing Metrics

To validate this approach, compare:

| Metric | Before (PNG) | After (TIFF) |
|--------|--------------|--------------|
| OCR bbox accuracy | Baseline | TBD |
| LLM scale detection | Baseline | TBD |
| Scale highlight alignment | Baseline | TBD |
| File size | Baseline | TBD |

### Rollback Plan

If TIFF doesn't improve accuracy or causes issues:

1. Revert `fmt` defaults back to `"PNG"` in `pdf_utils.py`
2. Revert storage key to `image.png` in `document_processor.py`
3. Revert content type to `image/png`

No database schema changes are required - only storage keys in existing records would reference `.png` vs `.tiff`.
