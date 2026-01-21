# Celery Task Chain

How background tasks are orchestrated and chained together.

## Task Dependency Graph

```mermaid
flowchart TD
    subgraph Trigger["API Trigger"]
        UPLOAD[Document Upload API]
    end

    subgraph DocTasks["Document Tasks"]
        PDT[process_document_task]
    end

    subgraph OCRTasks["OCR Tasks"]
        PDOT[process_document_ocr_task]
        PPOT[process_page_ocr_task]
    end

    subgraph ClassTasks["Classification Tasks"]
        CDT[classify_document_task]
        CPT[classify_page_task]
    end

    subgraph ScaleTasks["Scale Tasks"]
        DPST[detect_page_scale_task]
    end

    UPLOAD --> PDT
    PDT --> |"On success"| PDOT
    PDOT --> |"For each page"| PPOT
    PPOT --> |"On all complete"| CDT
    CDT --> |"For each page"| CPT
    CPT --> |"On success"| DPST

    style Trigger fill:#e3f2fd
    style DocTasks fill:#fff8e1
    style OCRTasks fill:#f3e5f5
    style ClassTasks fill:#e8f5e9
    style ScaleTasks fill:#fce4ec
```

## Task Execution Sequence

```mermaid
sequenceDiagram
    participant API as FastAPI
    participant Redis as Redis Queue
    participant Worker as Celery Worker
    participant DB as PostgreSQL
    participant Storage as MinIO
    participant GCV as Google Cloud Vision
    participant LLM as Vision LLM

    API->>Redis: Queue process_document_task
    Redis->>Worker: Dequeue task
    
    Worker->>Storage: Download PDF
    Worker->>Worker: Extract pages
    Worker->>Storage: Store page images
    Worker->>DB: Create Page records
    Worker->>Redis: Queue process_document_ocr_task
    
    Redis->>Worker: Dequeue OCR task
    loop For each page
        Worker->>Storage: Download page image
        Worker->>GCV: Send for OCR
        GCV-->>Worker: OCR results
        Worker->>DB: Store ocr_text, ocr_blocks
    end
    Worker->>Redis: Queue classify_document_task
    
    Redis->>Worker: Dequeue classification task
    loop For each page
        Worker->>DB: Get page + OCR data
        alt Has OCR text
            Worker->>Worker: OCR-based classification
        else No OCR text
            Worker->>LLM: Vision classification
        end
        Worker->>DB: Store classification
        Worker->>Redis: Queue detect_page_scale_task
    end
    
    Redis->>Worker: Dequeue scale task
    Worker->>Storage: Download page image
    Worker->>LLM: Detect scale
    LLM-->>Worker: Scale text + bbox
    Worker->>DB: Get OCR blocks
    Worker->>Worker: Match bbox to OCR
    Worker->>DB: Store scale_calibration_data
```

## Task Configuration

```mermaid
flowchart TD
    subgraph CeleryApp["Celery App Configuration"]
        BROKER[Redis Broker<br/>redis://redis:6379/0]
        BACKEND[Redis Backend<br/>redis://redis:6379/0]
        
        CONFIG[Task Config]
        CONFIG --> SERIAL[task_serializer: json]
        CONFIG --> TIMEOUT[task_time_limit: 3600s]
        CONFIG --> RETRY[max_retries: 3]
        CONFIG --> PREFETCH[prefetch_multiplier: 1]
    end

    subgraph Workers["Worker Processes"]
        W1[Worker 1]
        W2[Worker 2]
        W3[Worker N...]
    end

    BROKER --> Workers
    Workers --> BACKEND

    style CeleryApp fill:#e3f2fd
    style Workers fill:#e8f5e9
```

## Error Handling & Retries

```mermaid
flowchart TD
    subgraph Execution["Task Execution"]
        START[Task starts] --> EXEC[Execute task logic]
        EXEC --> CHECK{Success?}
    end

    subgraph Success["Success Path"]
        CHECK -->|Yes| UPDATE[Update DB status]
        UPDATE --> CHAIN[Queue next task]
        CHAIN --> DONE[Task complete]
    end

    subgraph Failure["Failure Path"]
        CHECK -->|No| ERROR[Catch exception]
        ERROR --> LOG[Log error]
        LOG --> RETRY_CHECK{Retries left?}
        RETRY_CHECK -->|Yes| WAIT[Wait countdown]
        WAIT --> EXEC
        RETRY_CHECK -->|No| FAIL[Mark as failed]
        FAIL --> DB_ERROR[Update DB: status=error]
    end

    style Execution fill:#e3f2fd
    style Success fill:#e8f5e9
    style Failure fill:#ffebee
```

## Task Definitions

| Task | File | Triggers | Queues Next |
|------|------|----------|-------------|
| `process_document_task` | `document_tasks.py` | Document upload API | `process_document_ocr_task` |
| `process_document_ocr_task` | `ocr_tasks.py` | Document processing complete | `classify_document_task` |
| `process_page_ocr_task` | `ocr_tasks.py` | Called by document OCR | - |
| `classify_document_task` | `classification_tasks.py` | OCR complete | `detect_page_scale_task` |
| `classify_page_task` | `classification_tasks.py` | Called by document classify | - |
| `detect_page_scale_task` | `scale_tasks.py` | Classification complete | - |

## Database Synchronization Pattern

```mermaid
flowchart TD
    subgraph Problem["Problem: Async DB in Celery"]
        P1[Celery uses multiprocessing]
        P2[asyncpg doesn't work across processes]
        P3[InterfaceError on async queries]
    end

    subgraph Solution["Solution: Sync DB in Workers"]
        S1[FastAPI routes: async SQLAlchemy]
        S2[Celery workers: sync SQLAlchemy]
        S3[Same models, different engines]
    end

    subgraph Code["Implementation"]
        C1["# In workers
sync_url = url.replace('+asyncpg', '')
sync_engine = create_engine(sync_url)
SyncSession = sessionmaker(bind=sync_engine)"]
    end

    Problem --> Solution --> Code

    style Problem fill:#ffebee
    style Solution fill:#e8f5e9
    style Code fill:#f5f5f5
```

## Monitoring & Debugging

```mermaid
flowchart LR
    subgraph Logs["Logging"]
        STRUCT[structlog]
        STRUCT --> JSON[JSON formatted logs]
        JSON --> TASK_ID[Includes task_id]
        JSON --> DOC_ID[Includes document_id]
        JSON --> PAGE_ID[Includes page_id]
    end

    subgraph Status["Status Tracking"]
        DB_STATUS[Document.status]
        DB_STATUS --> UPLOADED
        DB_STATUS --> PROCESSING
        DB_STATUS --> READY
        DB_STATUS --> ERROR
    end

    subgraph Debug["Debug Tools"]
        FLOWER[Celery Flower UI]
        REDIS_CLI[redis-cli monitor]
        LOGS_CMD[docker logs worker]
    end

    style Logs fill:#e3f2fd
    style Status fill:#fff8e1
    style Debug fill:#f3e5f5
```

## Docker Compose Services

```yaml
# Relevant services for task processing
services:
  api:
    # FastAPI - queues tasks
    
  worker:
    # Celery worker - processes tasks
    command: celery -A app.workers.celery_app worker
    
  redis:
    # Message broker & result backend
    
  db:
    # PostgreSQL - shared by API and workers
```
