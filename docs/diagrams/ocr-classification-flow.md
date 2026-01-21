# OCR and Classification Flow

How pages are processed through OCR, classification, and scale detection.

## Task Chain Diagram

```mermaid
flowchart TD
    subgraph Trigger["Trigger"]
        A[Document processing complete] --> B[Queue OCR task]
    end

    subgraph OCR["1. OCR Processing"]
        B --> C[process_document_ocr_task]
        C --> D[For each page in document]
        D --> E[Download page image from MinIO]
        E --> F[Send to Google Cloud Vision]
        F --> G[Receive OCR response]
        G --> H[Extract text blocks with bounding boxes]
        H --> I[Detect patterns: scales, titles, sheet numbers]
        I --> J[Store in Page.ocr_text and Page.ocr_blocks]
    end

    subgraph Classification["2. Classification"]
        J --> K[Queue classification task]
        K --> L[classify_document_task]
        L --> M[For each page]
        M --> N{Has OCR text?}
        N -->|Yes| O[OCR-based classification]
        N -->|No| P[Vision LLM classification]
        O --> Q[Analyze text patterns]
        P --> R[Send image to LLM]
        Q --> S[Determine discipline & page type]
        R --> S
        S --> T[Calculate concrete relevance score]
        T --> U[Store classification in Page record]
    end

    subgraph Scale["3. Scale Detection"]
        U --> V[Queue scale detection task]
        V --> W[detect_page_scale_task]
        W --> X[Download page image]
        X --> Y[Send to Vision LLM]
        Y --> Z[LLM returns scale text + bbox]
        Z --> AA{OCR blocks available?}
        AA -->|Yes| AB[Match scale text to OCR blocks]
        AA -->|No| AC[Use LLM bbox directly]
        AB --> AD[Get pixel-perfect bbox from OCR]
        AC --> AD
        AD --> AE[Store in Page.scale_calibration_data]
    end

    style Trigger fill:#e3f2fd
    style OCR fill:#fff8e1
    style Classification fill:#f3e5f5
    style Scale fill:#e8f5e9
```

## Celery Task Dependencies

```mermaid
sequenceDiagram
    participant DT as document_tasks
    participant OT as ocr_tasks
    participant CT as classification_tasks
    participant ST as scale_tasks

    DT->>DT: process_document_task
    Note over DT: Extract pages, store images
    DT->>OT: process_document_ocr_task.delay()
    
    OT->>OT: Process all pages OCR
    Note over OT: Google Cloud Vision
    OT->>CT: classify_document_task.delay()
    
    CT->>CT: Classify all pages
    Note over CT: OCR-based or LLM vision
    CT->>ST: For each page: detect_page_scale_task.delay()
    
    ST->>ST: Detect scale per page
    Note over ST: Vision LLM + OCR bbox matching
```

## Data Flow

```mermaid
flowchart LR
    subgraph Input
        IMG[Page Image<br/>1568x max px]
    end

    subgraph OCR
        GCV[Google Cloud Vision]
        GCV --> |text| TEXT[ocr_text]
        GCV --> |blocks| BLOCKS[ocr_blocks<br/>with bounding boxes]
    end

    subgraph Classification
        CLASS[Classifier]
        CLASS --> DISC[discipline]
        CLASS --> TYPE[page_type]
        CLASS --> CONF[confidence]
        CLASS --> REL[concrete_relevance]
    end

    subgraph Scale
        SCALE[Scale Detector]
        SCALE --> STXT[scale_text]
        SCALE --> SVAL[scale_value]
        SCALE --> BBOX[bbox coordinates]
    end

    IMG --> GCV
    IMG --> CLASS
    IMG --> SCALE
    TEXT --> CLASS
    BLOCKS --> SCALE

    style Input fill:#e1f5fe
    style OCR fill:#fff3e0
    style Classification fill:#f3e5f5
    style Scale fill:#e8f5e9
```

## Page Record After Processing

```json
{
  "id": "uuid",
  "page_number": 1,
  "width": 1568,
  "height": 1045,
  
  "ocr_text": "FOUNDATION PLAN\nSCALE: 1/4\" = 1'-0\"...",
  "ocr_blocks": {
    "blocks": [
      {
        "text": "SCALE: 1/4\" = 1'-0\"",
        "bounding_box": { "x": 2100, "y": 2850, "width": 150, "height": 20 }
      }
    ]
  },
  
  "classification": "foundation_plan",
  "classification_confidence": 0.95,
  "discipline": "structural",
  "page_type": "plan",
  "concrete_relevance": "high",
  
  "scale_text": "1/4\" = 1'-0\"",
  "scale_value": 48.0,
  "scale_calibrated": true,
  "scale_calibration_data": {
    "best_scale": {
      "text": "1/4\" = 1'-0\"",
      "ratio": 48.0,
      "bbox": { "x": 2100, "y": 2850, "width": 150, "height": 20 },
      "confidence": 0.95
    }
  }
}
```

---

## Experimental Note: TIFF Storage (January 2026)

> **Status**: Testing in progress

As of January 2026, page images are experimentally stored as TIFF instead of PNG:

- **Storage key**: `image.tiff` (was `image.png`)
- **Content type**: `image/tiff` (was `image/png`)
- **Compression**: TIFF LZW (lossless)
- **Thumbnails**: Still PNG for web compatibility

This change is being tested to evaluate whether TIFF format improves coordinate accuracy by ensuring PDFs are fully flattened to clean raster images before OCR and LLM analysis.

See [Scale Detection Accuracy](./scale-detection-accuracy.md#experimental-tiff-format-for-coordinate-accuracy-january-2026) and [Document Processing Pipeline](./document-processing-pipeline.md#experimental-tiff-storage-format-january-2026) for full details.
