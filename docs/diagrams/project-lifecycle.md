# Project Lifecycle

Complete workflow from project creation to takeoff completion.

## High-Level Overview

```mermaid
flowchart TD
    subgraph Create["1. Project Creation"]
        A[User creates project] --> B[Project record in DB]
        B --> C[Project status: draft]
    end

    subgraph Upload["2. Document Upload"]
        C --> D[Upload PDF/TIFF files]
        D --> E[Documents queued for processing]
        E --> F[Background processing starts]
    end

    subgraph Process["3. Automated Processing"]
        F --> G[Extract pages as images]
        G --> H[Run OCR on each page]
        H --> I[Classify pages by type]
        I --> J[Detect scales]
    end

    subgraph Review["4. Review & Calibration"]
        J --> K[User reviews classifications]
        K --> L[User calibrates scales if needed]
        L --> M[Pages ready for takeoff]
    end

    subgraph Takeoff["5. Takeoff Work"]
        M --> N[Create conditions]
        N --> O[Draw measurements]
        O --> P[AI-assisted detection]
        P --> Q[Review & refine]
    end

    subgraph Export["6. Export"]
        Q --> R[Export to Excel]
        R --> S[Export to OST format]
        S --> T[Project complete]
    end

    style Create fill:#e3f2fd
    style Upload fill:#fff8e1
    style Process fill:#f3e5f5
    style Review fill:#e8f5e9
    style Takeoff fill:#fce4ec
    style Export fill:#e0f2f1
```

## Detailed State Machine

```mermaid
stateDiagram-v2
    [*] --> ProjectCreated: Create project

    state ProjectCreated {
        [*] --> Draft
        Draft --> InProgress: Start work
    }

    state DocumentProcessing {
        [*] --> Uploaded
        Uploaded --> Processing: Worker picks up
        Processing --> Ready: Success
        Processing --> Error: Failure
        Error --> Processing: Retry
    }

    state PageProcessing {
        [*] --> Pending
        Pending --> OCRProcessing
        OCRProcessing --> Classifying
        Classifying --> ScaleDetecting
        ScaleDetecting --> Ready
    }

    ProjectCreated --> DocumentProcessing: Upload document
    DocumentProcessing --> PageProcessing: For each page
    PageProcessing --> TakeoffReady: All pages ready

    state TakeoffReady {
        [*] --> ReviewingPages
        ReviewingPages --> CalibratingScales
        CalibratingScales --> CreatingConditions
        CreatingConditions --> DrawingMeasurements
        DrawingMeasurements --> Reviewing
    }

    TakeoffReady --> Exporting: Export
    Exporting --> [*]: Complete
```

## API Endpoints by Phase

```mermaid
flowchart LR
    subgraph Project["Project APIs"]
        P1[POST /projects]
        P2[GET /projects/:id]
        P3[PUT /projects/:id]
    end

    subgraph Document["Document APIs"]
        D1[POST /projects/:id/documents]
        D2[GET /documents/:id]
        D3[GET /documents/:id/status]
    end

    subgraph Page["Page APIs"]
        PG1[GET /documents/:id/pages]
        PG2[GET /pages/:id]
        PG3[GET /pages/:id/image]
        PG4[POST /pages/:id/detect-scale]
        PG5[PUT /pages/:id/scale]
    end

    subgraph Condition["Condition APIs"]
        C1[POST /projects/:id/conditions]
        C2[GET /conditions/:id]
        C3[PUT /conditions/:id]
    end

    subgraph Measurement["Measurement APIs"]
        M1[POST /conditions/:id/measurements]
        M2[GET /measurements/:id]
        M3[PUT /measurements/:id]
    end

    subgraph Export["Export APIs"]
        E1[POST /projects/:id/export]
        E2[GET /exports/:id]
    end

    Project --> Document --> Page --> Condition --> Measurement --> Export
```

## User Journey

```mermaid
journey
    title Construction Takeoff User Journey
    section Setup
      Create new project: 5: User
      Upload plan set PDF: 5: User
      Wait for processing: 3: System
    section Review
      View processed pages: 4: User
      Check classifications: 4: User
      Calibrate scales: 3: User
    section Takeoff
      Create conditions: 4: User
      Draw measurements: 4: User
      Use AI detection: 5: User, System
      Review AI results: 4: User
    section Export
      Generate Excel report: 5: System
      Download export: 5: User
```

## Data Model Relationships

```mermaid
erDiagram
    Project ||--o{ Document : contains
    Project ||--o{ Condition : has
    Document ||--o{ Page : contains
    Condition ||--o{ Measurement : has
    Page ||--o{ Measurement : displays

    Project {
        uuid id PK
        string name
        string status
        timestamp created_at
    }

    Document {
        uuid id PK
        uuid project_id FK
        string filename
        string status
        int page_count
    }

    Page {
        uuid id PK
        uuid document_id FK
        int page_number
        string classification
        string scale_text
        float scale_value
        json scale_calibration_data
    }

    Condition {
        uuid id PK
        uuid project_id FK
        string name
        string color
        string unit
    }

    Measurement {
        uuid id PK
        uuid condition_id FK
        uuid page_id FK
        string geometry_type
        json geometry_data
        float quantity
    }
```

## Processing Timeline

```mermaid
gantt
    title Document Processing Timeline
    dateFormat  ss
    axisFormat %S

    section Upload
    File upload           :a1, 00, 2s
    Store original        :a2, after a1, 1s

    section Extraction
    Extract pages         :b1, after a2, 5s
    Generate thumbnails   :b2, after b1, 2s

    section OCR
    OCR processing        :c1, after b2, 10s

    section Classification
    Classify pages        :d1, after c1, 5s

    section Scale
    Detect scales         :e1, after d1, 8s

    section Ready
    Pages ready           :milestone, after e1, 0s
```
