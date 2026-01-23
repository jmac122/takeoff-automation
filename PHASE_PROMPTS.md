# Takeoff Platform - Complete Phase Prompts

Use these prompts to start each phase. Copy and paste into a new Cursor/Claude chat when ready to begin that phase. Every task from every phase document is included below.

---

## Phase 0: Project Setup (Week 1) - Grok Code

### Prompt:
```
Let's begin implementing the Takeoff Platform. Start with Phase 0 - Project Setup.

Read `plans/01-PROJECT-SETUP.md` and implement all tasks in order:

- Task 0.1: Initialize Repository Structure
  - Create base repository structure (backend, frontend, docker, scripts, docs directories)
  - Create `.gitignore` file with Python, Node, Docker, IDE, and environment exclusions
  - Create `.env.example` with all required environment variables

- Task 0.2: Backend Setup (Python/FastAPI)
  - Create `backend/pyproject.toml` with project configuration
  - Create `backend/requirements.txt` with all dependencies
  - Create `backend/requirements-dev.txt` with dev dependencies
  - Create `backend/app/__init__.py`
  - Create `backend/app/config.py` with Settings class using Pydantic
  - Create `backend/app/main.py` with FastAPI app factory
  - Create `backend/app/api/__init__.py`
  - Create `backend/app/api/routes/__init__.py`
  - Create `backend/app/api/routes/health.py` with health check endpoint
  - Create placeholder route files for projects, documents, pages, conditions, measurements, exports

- Task 0.3: Database Setup with Alembic
  - Create `backend/alembic.ini`
  - Create `backend/alembic/env.py` for async migrations
  - Create `backend/alembic/versions/.gitkeep`
  - Create `backend/app/models/__init__.py`
  - Create `backend/app/models/base.py` with Base, TimestampMixin, UUIDMixin

- Task 0.4: Frontend Setup (React/TypeScript/Vite)
  - Initialize Vite React TypeScript project
  - Install dependencies (@tanstack/react-query, zustand, react-router-dom, axios, konva, react-konva, pdfjs-dist)
  - Configure Tailwind CSS
  - Initialize shadcn/ui
  - Update tailwind.config.js
  - Create frontend/src/styles/globals.css
  - Create frontend/src/api/client.ts with Axios configuration
  - Create frontend/src/App.tsx with React Query and Router setup
  - Configure vite.config.ts with path aliases

- Task 0.5: Docker Configuration
  - Create `docker/docker-compose.yml` with services: db (PostgreSQL), redis, minio, api, worker
  - Create `docker/Dockerfile.api` for FastAPI application
  - Create `docker/Dockerfile.worker` for Celery worker

- Task 0.6: CI/CD Pipeline
  - Create `.github/workflows/ci.yml` with backend-test and frontend-test jobs
  - Configure PostgreSQL and Redis services for tests
  - Set up linting (ruff, mypy) and testing (pytest with coverage)
  - Set up frontend linting, type checking, and build

- Task 0.7: Makefile for Common Commands
  - Create `Makefile` with: setup, dev, up, down, logs, test, lint, format, migrate, migrate-create

- Task 0.8: README
  - Create `README.md` with quick start guide, development instructions, and architecture overview

Run through the verification checklist:
- [ ] `docker compose up` starts all services without errors
- [ ] API responds at `http://localhost:8000/api/v1/health`
- [ ] Frontend builds and runs at `http://localhost:5173`
- [ ] Database connection works
- [ ] Redis connection works
- [ ] MinIO console accessible at `http://localhost:9001`
- [ ] All linters pass
- [ ] Test suite runs (even if minimal)
```

---

## Phase 1A: Document Ingestion (Weeks 2-5) - Grok Code

### Prompt:
```
Continue to Phase 1A - Document Ingestion.

Read `plans/02-DOCUMENT-INGESTION.md` and implement all tasks in order:

- Task 1.1: Create Document and Page Models
  - Create `backend/app/models/project.py` with Project model (id, name, description, client_name, status, relationships to documents and conditions)
  - Create `backend/app/models/document.py` with Document model (project_id, filename, original_filename, file_type, file_size, mime_type, storage_key, status, page_count, processing_error, processing_metadata, relationships)
  - Create `backend/app/models/page.py` with Page model (document_id, page_number, width, height, dpi, image_key, thumbnail_key, classification, title, sheet_number, scale fields, ocr fields, status, relationships)

- Task 1.2: Create Initial Migration
  - Run `alembic revision --autogenerate -m "initial_schema"`
  - Run `alembic upgrade head`

- Task 1.3: Implement S3-Compatible Storage
  - Create `backend/app/utils/storage.py` with StorageService class
  - Implement: upload_file, download_file, delete_file, get_presigned_url, file_exists, list_files
  - Create get_storage_service dependency

- Task 1.4: Document Processing Service
  - Create `backend/app/services/document_processor.py`
  - Implement DocumentProcessor class with:
    - process_document() method
    - _process_pdf() for PDF handling using PyMuPDF
    - _process_tiff() for multi-page TIFF handling
    - _extract_page() for page image extraction
    - _generate_thumbnail() for thumbnail creation
    - _update_page_dimensions() for storing image dimensions

- Task 1.5: Celery Worker Tasks
  - Create `backend/app/workers/__init__.py`
  - Create `backend/app/workers/celery_app.py` with Celery configuration
  - Create `backend/app/workers/document_tasks.py` with:
    - process_document_task() for main document processing
    - Proper error handling and status updates

- Task 1.6: API Endpoints
  - Create/update `backend/app/api/routes/documents.py` with:
    - POST `/projects/{project_id}/documents` - upload document
    - GET `/documents/{document_id}` - get document details
    - GET `/documents/{document_id}/status` - get processing status
    - DELETE `/documents/{document_id}` - delete document
  - Create `backend/app/schemas/document.py` with DocumentCreate, DocumentResponse, DocumentStatusResponse schemas

- Task 1.7: Frontend Upload Component
  - Create `frontend/src/api/documents.ts` with uploadDocument, getDocument, getDocumentStatus, deleteDocument functions
  - Create `frontend/src/components/document/DocumentUploader.tsx` with:
    - Drag-and-drop support using react-dropzone
    - Multi-file upload capability
    - Progress tracking
    - PDF and TIFF file acceptance
    - Upload status display

Run through the verification checklist:
- [ ] Can upload PDF files via API
- [ ] Can upload TIFF files via API
- [ ] Files are stored in MinIO
- [ ] Document record created in database
- [ ] Celery worker processes documents
- [ ] Pages extracted and stored as images
- [ ] Thumbnails generated
- [ ] Page records created in database
- [ ] Status updates correctly (uploaded → processing → ready)
- [ ] Errors handled gracefully
- [ ] Can retrieve document details via API
- [ ] Can poll document status
- [ ] Can delete documents (files and records)
- [ ] Frontend uploader works with drag-and-drop
- [ ] Upload progress shown correctly
```

---

## Phase 1B: OCR and Text Extraction (Weeks 4-6) - Sonnet 4.5 (non-thinking)

### Prompt:
```
Continue to Phase 1B - OCR and Text Extraction.

Read `plans/03-OCR-TEXT-EXTRACTION.md` and implement all tasks in order:

- Task 3.1: Google Cloud Vision Setup
  - Verify google-cloud-vision is installed
  - Set up service account credentials
  - Configure GOOGLE_APPLICATION_CREDENTIALS in .env

- Task 3.2: OCR Service Implementation
  - Create `backend/app/services/ocr_service.py`
  - Implement TextBlock dataclass (text, confidence, bounding_box)
  - Implement OCRResult dataclass (full_text, blocks, detected_scale_texts, detected_sheet_numbers, detected_titles)
  - Implement OCRService class with:
    - SCALE_PATTERNS for architectural/engineering scales
    - SHEET_NUMBER_PATTERNS for sheet identification
    - TITLE_PATTERNS for title extraction
    - extract_text() method using Google Cloud Vision document_text_detection
    - _extract_scales() for scale notation extraction
    - _extract_sheet_numbers() for sheet number identification
    - _extract_titles() for title extraction from text and blocks

- Task 3.3: Title Block Parser
  - Create `backend/app/services/title_block_parser.py`
  - Implement TitleBlockInfo dataclass
  - Implement TitleBlockParser class with:
    - parse() method for extracting title block information
    - _find_title_block_region() for locating title block in image
    - _extract_from_region() for parsing fields
    - Support for common title block layouts

- Task 3.4: OCR Celery Tasks
  - Create `backend/app/workers/ocr_tasks.py`
  - Implement process_page_ocr_task() for single page OCR
  - Implement process_document_ocr_task() for entire document OCR
  - Update document processing to trigger OCR after page extraction
  - Store OCR results in page records

- Task 3.5: Page API Endpoints
  - Update `backend/app/api/routes/pages.py` with:
    - GET `/documents/{document_id}/pages` - list document pages
    - GET `/pages/{page_id}` - get page details
    - GET `/pages/{page_id}/image` - get page image (presigned URL redirect)
    - GET `/pages/{page_id}/ocr` - get OCR data
    - POST `/pages/{page_id}/reprocess-ocr` - reprocess OCR for a page

- Task 3.6: Page Schemas
  - Create `backend/app/schemas/page.py` with:
    - PageResponse schema
    - PageSummaryResponse schema
    - PageListResponse schema
    - PageOCRResponse schema
    - ScaleUpdateRequest schema

- Task 3.7: Search Index (Full-Text Search)
  - Create migration for full-text search index on ocr_text
  - Add GIN index using to_tsvector
  - Add trigram index for fuzzy matching (pg_trgm extension)
  - Add search endpoint GET `/projects/{project_id}/search` with full-text search

Run through the verification checklist:
- [ ] Google Cloud Vision credentials configured
- [ ] OCR service extracts text from plan images
- [ ] Scale text patterns detected correctly
- [ ] Sheet numbers extracted (e.g., "A1.01", "S-101")
- [ ] Sheet titles extracted
- [ ] Title block parsing works for standard formats
- [ ] OCR runs automatically after document processing
- [ ] OCR data stored in page records
- [ ] API endpoints return OCR data
- [ ] Can reprocess OCR for individual pages
- [ ] Full-text search returns relevant results
- [ ] Errors handled gracefully

Test Cases:
1. Upload a PDF with clear title block → verify sheet number and title extracted
2. Upload a PDF with scale notation "1/4" = 1'-0"" → verify scale text detected
3. Upload a scanned TIFF (lower quality) → verify OCR still works
4. Search for text that appears on a page → verify search returns correct page
5. Upload multi-page document → verify all pages get OCR processed
```

---

## Phase 2A: Page Classification (Weeks 6-9) - Composer 1

### Prompt:
```
Continue to Phase 2A - Page Classification.

Read `plans/04-PAGE-CLASSIFICATION.md` and implement all tasks in order:

- Task 4.1: Multi-Provider LLM Client Service
  - Create `backend/app/services/llm_client.py`
  - Implement LLMProvider enum (ANTHROPIC, OPENAI, GOOGLE, XAI)
  - Implement LLMResponse dataclass (content, provider, model, input_tokens, output_tokens, latency_ms)
  - Define PROVIDER_MODELS mapping for each provider
  - Implement LLMClient class with:
    - __init__() with provider and fallback_providers parameters
    - _init_client() for initializing provider-specific clients
    - _ensure_fallback_clients() for lazy loading fallbacks
    - analyze_image() method with retry logic using tenacity
    - _analyze_with_provider() for provider-specific implementations
    - Support for Anthropic Claude 3.5 Sonnet
    - Support for OpenAI GPT-4o
    - Support for Google Gemini 2.5 Flash
    - Support for xAI Grok Vision
  - Create get_llm_client() factory function

- Task 4.2: Page Classification Service
  - Create `backend/app/services/page_classifier.py`
  - Define classification categories:
    - Disciplines: Architectural, Structural, Civil/Site, Mechanical, Electrical, Plumbing, Landscape, General/Cover
    - Page Types: Plan View, Elevation, Section, Detail, Schedule, Notes/Legend, Cover Sheet, Title Sheet
    - Concrete Relevance: high, medium, low, none
  - Implement ClassificationResult dataclass
  - Implement PageClassifier class with:
    - CLASSIFICATION_PROMPT for LLM analysis
    - classify_page() method accepting optional provider override
    - _parse_classification_response() for JSON parsing
    - Confidence scoring
    - Provider metadata tracking

- Task 4.3: Classification Celery Tasks
  - Create `backend/app/workers/classification_tasks.py`
  - Implement classify_page_task() with optional provider parameter
  - Implement classify_document_pages() for batch classification
  - Store classification results with LLM metadata in database
  - Update page model for concrete_relevance field

- Task 4.4: Classification API Endpoints
  - Add to `backend/app/api/routes/pages.py`:
    - POST `/pages/{page_id}/classify` - trigger single page classification with optional provider
    - POST `/documents/{document_id}/classify` - classify all pages with optional provider
    - GET `/pages/{page_id}/classification` - get classification results
  - Create endpoint for available LLM providers: GET `/settings/llm/providers`
  - Create schemas: ClassifyPageRequest, ClassificationTaskResponse, DocumentClassificationResponse

- Task 4.5: Frontend Provider Selector Component
  - Create `frontend/src/components/LLMProviderSelector.tsx`
  - Fetch available providers from API
  - Display provider name, model, strengths, and cost tier
  - Support "Default (Auto)" option
  - Include tooltips with provider details

- Task 4.6: Page Browser with Classification Filters
  - Update `frontend/src/components/document/PageBrowser.tsx`
  - Add filter by discipline (A, S, C, M, E, P, L, G)
  - Add filter by page type
  - Add filter by concrete relevance
  - Highlight high-concrete pages visually
  - Show classification confidence
  - Display provider used for classification

Run through the verification checklist:
- [ ] LLM client connects to all configured providers
- [ ] Provider fallback works when primary fails
- [ ] Page classification returns valid discipline and page type
- [ ] Concrete relevance accurately identifies concrete-heavy pages
- [ ] Classification runs automatically or on-demand
- [ ] Classification data stored in database with LLM metadata
- [ ] Frontend can select provider for classification
- [ ] Frontend filter by discipline works
- [ ] Frontend filter by concrete relevance works
- [ ] High-concrete pages highlighted visually
- [ ] Classification confidence stored
- [ ] Errors handled gracefully with fallback

Test Cases:
1. Upload a Foundation Plan → should classify as "Structural:Plan" with high concrete relevance
2. Upload an Electrical Plan → should classify as "Electrical:Plan" with low/none concrete relevance
3. Upload a Site Plan with paving → should show medium-high concrete relevance
4. Filter to "Structural" pages only → only S-prefixed sheets shown
5. Filter to "high concrete" → only concrete-relevant pages shown
6. Test with different providers → results should be similar across providers
7. Disable primary provider API key → should fallback to secondary provider
```

---

## Phase 2B: Scale Detection (Weeks 8-11) - Opus 4.5 (thinking)

### Prompt:
```
Continue to Phase 2B - Scale Detection and Calibration.

Read `plans/05-SCALE-DETECTION.md` and implement all tasks in order:

- Task 5.1: Scale Parser Service
  - Create `backend/app/services/scale_detector.py`
  - Implement ParsedScale dataclass (original_text, scale_ratio, drawing_unit, real_unit, is_metric, confidence, pixels_per_foot property)
  - Implement ScaleParser class with:
    - ARCH_PATTERNS for architectural scales (1/4" = 1'-0", etc.)
    - ENG_PATTERNS for engineering scales (1" = 20', etc.)
    - RATIO_PATTERNS for ratio scales (1:100, etc.)
    - ARCH_SCALE_MAP for common architectural scale ratios
    - parse_scale_text() method
    - _parse_arch_scale() for architectural format
    - _parse_eng_scale() for engineering format
    - _parse_ratio_scale() for ratio format
    - Handle "NOT TO SCALE" notation

- Task 5.2: Scale Detection Service
  - Add to `backend/app/services/scale_detector.py`:
  - Implement ScaleDetectionResult dataclass
  - Implement ScaleDetector class with:
    - detect_scale() method combining OCR and LLM analysis
    - _detect_from_ocr() for text-based scale detection
    - _detect_from_llm() for visual scale bar detection
    - _detect_scale_bar_cv() using OpenCV for scale bar detection
    - Support for multiple LLM providers
    - Confidence scoring and source tracking

- Task 5.3: Scale Celery Tasks
  - Create `backend/app/workers/scale_tasks.py`
  - Implement detect_page_scale_task() with optional provider
  - Implement detect_document_scales_task() for batch processing
  - Implement calibrate_page_scale_task() for manual calibration
  - Store scale detection results with source metadata

- Task 5.4: Scale API Endpoints
  - Add to `backend/app/api/routes/pages.py`:
    - POST `/pages/{page_id}/detect-scale` - auto-detect scale with optional provider
    - PUT `/pages/{page_id}/scale` - manual scale calibration
    - POST `/pages/{page_id}/calibrate` - calibrate using pixel distance and real distance
    - POST `/pages/{page_id}/copy-scale-from/{source_page_id}` - copy scale from another page
  - Create schemas: ScaleDetectionRequest, ScaleCalibrationRequest, ScaleResponse

- Task 5.5: Frontend Scale Calibration Component
  - Create `frontend/src/components/viewer/ScaleCalibration.tsx`
  - Implement calibration mode with line drawing
  - Implement distance input dialog
  - Support unit selection (feet, inches, meters)
  - Display current scale status (calibrated/uncalibrated)
  - Show scale text and pixels per foot
  - Create CopyScaleButton component for copying scale between pages
  - Integrate with PlanViewer component

Run through the verification checklist:
- [ ] Scale parser correctly parses "1/4" = 1'-0""
- [ ] Scale parser correctly parses "1" = 20'"
- [ ] Scale parser correctly parses "1:100"
- [ ] Scale parser handles "NOT TO SCALE"
- [ ] Automatic scale detection runs on pages
- [ ] Detected scale stored in database
- [ ] Manual calibration calculates correct pixels/foot
- [ ] Scale can be copied between pages
- [ ] Frontend calibration tool works (draw line, enter distance)
- [ ] Scale indicator shows calibrated/uncalibrated status
- [ ] High-confidence auto-detection marks page as calibrated

Test Cases:
1. Upload a page with "1/4" = 1'-0"" visible → auto-detects scale
2. Upload a page with "SCALE: 1" = 20'" → auto-detects as engineering scale
3. Upload a page with no scale → shows "not calibrated"
4. Manually calibrate a page → scale persists
5. Copy scale from one page to another → both have same scale
6. Draw a 100-pixel line, say it's 10 feet → should get 10 px/ft
```

---

## Phase 3A: Measurement Engine (Weeks 10-16) - Sonnet 4.5 (thinking)

### Prompt:
```
Continue to Phase 3A - Measurement Engine.

Read `plans/06-MEASUREMENT-ENGINE.md` and implement all tasks in order:

- Task 6.1: Measurement and Condition Models
  - Create `backend/app/models/condition.py` with Condition model:
    - project_id, name, description, scope, category
    - measurement_type (linear, area, volume, count)
    - color, line_width, fill_opacity
    - unit (LF, SF, CY, EA), depth, thickness
    - total_quantity, measurement_count (denormalized)
    - sort_order, metadata
    - Relationships to project and measurements
  - Create `backend/app/models/measurement.py` with Measurement model:
    - condition_id, page_id
    - geometry_type (line, polyline, polygon, rectangle, circle, point)
    - geometry_data (JSONB)
    - quantity, unit, pixel_length, pixel_area
    - is_ai_generated, ai_confidence, ai_model
    - is_modified, is_verified
    - notes, metadata
    - Relationships to condition and page
  - Run migration: `alembic revision --autogenerate -m "add_conditions_and_measurements"`

- Task 6.2: Geometry Utilities
  - Create `backend/app/utils/geometry.py`
  - Implement Point dataclass with distance_to(), to_dict(), from_dict()
  - Implement helper functions:
    - calculate_line_length()
    - calculate_polyline_length()
    - calculate_polygon_area() using shoelace formula
    - calculate_polygon_perimeter()
    - calculate_rectangle_area()
    - calculate_rectangle_perimeter()
    - calculate_circle_area()
    - calculate_circle_circumference()
  - Implement MeasurementCalculator class with:
    - pixels_per_foot initialization
    - calculate_from_geometry() dispatcher
    - _calculate_line(), _calculate_polyline()
    - _calculate_polygon(), _calculate_rectangle()
    - _calculate_circle(), _calculate_point()
    - convert_to_volume() for depth-based CY calculation

- Task 6.3: Measurement Calculator Service
  - Create `backend/app/services/measurement_engine.py`
  - Implement MeasurementResult dataclass
  - Implement MeasurementEngine class with:
    - create_measurement() method
    - update_measurement() method
    - delete_measurement() method
    - recalculate_condition_totals() method
    - get_measurements_for_page() method
    - get_measurements_for_condition() method
  - Implement get_measurement_engine() factory

- Task 6.4: Measurement API Endpoints
  - Create `backend/app/api/routes/measurements.py` with:
    - GET `/conditions/{condition_id}/measurements` - list measurements for condition
    - POST `/conditions/{condition_id}/measurements` - create measurement
    - GET `/pages/{page_id}/measurements` - list measurements for page
    - GET `/measurements/{measurement_id}` - get measurement details
    - PUT `/measurements/{measurement_id}` - update measurement geometry
    - DELETE `/measurements/{measurement_id}` - delete measurement
    - POST `/pages/{page_id}/recalculate` - recalculate all measurements on page
  - Create `backend/app/schemas/measurement.py` with:
    - MeasurementCreate, MeasurementUpdate, MeasurementResponse schemas
    - GeometryData schemas for each geometry type

- Task 6.5: Frontend Measurement Tools
  - Create `frontend/src/components/takeoff/MeasurementTools.tsx`
  - Implement tool selection bar with:
    - Line tool (two-point)
    - Polyline tool (multi-point)
    - Polygon tool (closed shape)
    - Rectangle tool
    - Circle tool
    - Point/Count tool
  - Implement active tool state management
  - Add keyboard shortcuts for tool selection
  - Display real-time measurement preview during drawing

- Task 6.6: Measurement Layer Component
  - Create `frontend/src/components/viewer/MeasurementLayer.tsx`
  - Implement using Konva.js
  - Create MeasurementShape component with geometry type dispatcher
  - Implement individual shape components:
    - LineShape with length label
    - PolylineShape with total length label
    - PolygonShape with fill, stroke, and area label at centroid
    - RectangleShape with area label
    - CircleShape with area label
    - PointShape with X marker
  - Support selection, hover, and click interactions
  - Display quantity and unit labels scaled to zoom level
  - Implement color and opacity from condition settings

Run through the verification checklist:
- [ ] Line measurement calculates correct length in feet
- [ ] Polyline measurement sums all segments
- [ ] Polygon measurement calculates area in SF
- [ ] Rectangle measurement works correctly
- [ ] Circle measurement calculates area correctly
- [ ] Volume calculation with depth works (SF → CY)
- [ ] Count measurements return 1 each
- [ ] Measurements update condition totals
- [ ] Measurements display on canvas with labels
- [ ] Measurements can be selected and edited
- [ ] Scale changes trigger recalculation
- [ ] API CRUD operations work correctly

Test Cases:
1. Draw a 100-pixel line on a page with scale 10 px/ft → should show 10 LF
2. Draw a 100x100 pixel rectangle → should show 100 SF at 10 px/ft scale
3. Add 4" depth to an area condition → verify CY calculation
4. Delete a measurement → condition total updates
5. Change page scale → all measurements recalculate
```

---

## Phase 3B: Condition Management (Weeks 14-18) - Composer 1

### Prompt:
```
Continue to Phase 3B - Condition Management.

Read `plans/07-CONDITION-MANAGEMENT.md` and implement all tasks in order.

**Important Context - Existing Implementation:**
Some components already exist from earlier phases. Focus on EXTENDING existing code:

Backend (already exists):
- `models/condition.py` - Complete, includes line_width, fill_opacity, extra_metadata
- `models/measurement.py` - Complete
- `schemas/condition.py` - Has ConditionCreate, ConditionUpdate, ConditionResponse, ConditionListResponse
- `routes/conditions.py` - Has basic CRUD (GET list, POST create, GET/PUT/DELETE by ID)
- `routes/measurements.py` - Complete with CRUD and recalculate

Frontend (already exists):
- `viewer/ConditionsPanel.tsx` - Basic panel (needs upgrade)
- `viewer/MeasurementsPanel.tsx` - Complete

- Task 7.1: Condition API Routes
  - EXTEND `backend/app/api/routes/conditions.py` (basic CRUD already exists)
  - ADD CONDITION_TEMPLATES list with common concrete conditions:
    - Foundations: Strip Footing, Spread Footing, Foundation Wall, Grade Beam
    - Slabs: 4" SOG, 6" SOG Reinforced, 4" Sidewalk
    - Paving: 6" Concrete Paving, Curb & Gutter
    - Vertical: Concrete Column, 8" Concrete Wall
    - Miscellaneous: Concrete Pier, Catch Basin
    - Include line_width=2 and fill_opacity=0.3 in each template
  - ADD these new endpoints:
    - GET `/condition-templates` - list available templates with optional scope/category filters
    - POST `/projects/{project_id}/conditions/from-template` - create from template
    - POST `/conditions/{condition_id}/duplicate` - duplicate condition
    - PUT `/projects/{project_id}/conditions/reorder` - reorder conditions
  - UPDATE existing endpoints:
    - Add scope/category query filters to GET `/projects/{project_id}/conditions`
    - Add selectinload(measurements) to GET `/conditions/{condition_id}`

- Task 7.2: Condition Schemas
  - EXTEND `backend/app/schemas/condition.py` (base schemas already exist)
  - ADD these missing schemas:
    - ConditionWithMeasurementsResponse (extends ConditionResponse with measurements list)
    - ConditionTemplateResponse (include line_width, fill_opacity)
    - MeasurementSummary (brief measurement info for condition details)

- Task 7.3: Frontend Condition Panel
  - REPLACE `frontend/src/components/viewer/ConditionsPanel.tsx`
  - Display list of conditions grouped by category
  - Show condition color swatch, name, and total quantity
  - Implement condition selection (highlight active condition)
  - Show measurement count per condition
  - Support expand/collapse for condition groups
  - Add "Add Condition" button
  - Implement context menu for edit, duplicate, delete actions

- Task 7.4: Create Condition Modal
  - Create `frontend/src/components/viewer/CreateConditionModal.tsx`
  - Implement tabbed interface: "From Template" and "Custom"
  - Template tab: Display grouped templates, click to create
  - Custom tab:
    - Name input field
    - Measurement type selector (Linear/Area/Volume/Count)
    - Depth/thickness input for area/volume types
    - Color picker with preset colors
    - Unit auto-selection based on measurement type
  - Use React Query mutations for API calls

- Task 7.5: Condition Hooks
  - Create `frontend/src/hooks/useConditions.ts` with:
    - useConditions() for fetching project conditions
    - useConditionTemplates() for fetching templates
    - useCreateCondition() mutation
    - useCreateConditionFromTemplate() mutation
    - useUpdateCondition() mutation
    - useDeleteCondition() mutation
    - useDuplicateCondition() mutation
    - useReorderConditions() mutation
  - Implement drag-and-drop reordering using @dnd-kit/core and @dnd-kit/sortable

Run through the verification checklist:
- [ ] Can create conditions from templates
- [ ] Can create custom conditions
- [ ] Condition list shows grouped by category
- [ ] Conditions can be selected (highlights in panel)
- [ ] Conditions can be edited
- [ ] Conditions can be duplicated
- [ ] Conditions can be deleted (with measurements)
- [ ] Conditions can be reordered via drag-and-drop
- [ ] Condition totals update when measurements change
- [ ] Project-level totals display correctly
- [ ] Color picker works
- [ ] Depth/thickness stored correctly

Test Cases:
1. Create condition from "4" Concrete Slab" template → appears in list
2. Create custom linear condition → correct unit (LF) assigned
3. Add measurements to condition → total updates
4. Delete condition with measurements → both removed
5. Drag condition to reorder → new order persists
```

---

## Phase 4A: AI Takeoff Generation (Weeks 16-22) - Opus 4.5 (thinking)

### Prompt:
```
Continue to Phase 4A - AI Takeoff Generation.

Read `plans/08-AI-TAKEOFF-GENERATION.md`.
For frontend tasks, also refer to `docs/design/DESIGN-SYSTEM.md`, `docs/design/COMPONENT_LIBRARY.md`, and the `@industrial-tactical-ui.mdc` rule for aesthetic guidance.

- Task 8.1: AI Takeoff Service with Provider Selection
  - Create `backend/app/services/ai_takeoff.py`
  - Implement DetectedElement dataclass (element_type, geometry_type, geometry_data, confidence, description)
  - Implement AITakeoffResult dataclass (elements, page_description, analysis_notes, llm_provider, llm_model, llm_latency_ms, llm_input_tokens, llm_output_tokens)
  - Define prompts:
    - TAKEOFF_SYSTEM_PROMPT for general context
    - AREA_DETECTION_PROMPT for polygon detection (slabs, paving)
    - LINEAR_DETECTION_PROMPT for polyline detection (footings, walls)
    - COUNT_DETECTION_PROMPT for point detection (columns, piers)
  - Implement AITakeoffService class with:
    - ELEMENT_PROMPTS mapping
    - detect_elements() method accepting optional provider parameter
    - _create_prompt() for building analysis prompts
    - _parse_response() for JSON extraction
    - _validate_geometry() for bounds checking
    - Provider metadata tracking for benchmarking

- Task 8.2: Element Detection Prompts
  - Refine prompts for specific element types:
    - Concrete slabs and paving areas
    - Foundation walls and footings
    - Columns and piers (count)
    - Grade beams (linear)
  - Include scale context in prompts
  - Request pixel coordinates in specified format
  - Add confidence thresholds

- Task 8.3: AI Takeoff Celery Tasks
  - Create `backend/app/workers/takeoff_tasks.py`
  - Implement ai_takeoff_page_task() with:
    - Page and condition validation
    - Scale calibration check (block if uncalibrated)
    - LLM provider selection (default or specified)
    - Element detection call
    - Measurement creation from detected elements
    - Confidence scoring
    - Provider and model tracking
  - Implement batch_ai_takeoff_task() for multiple pages
  - Implement compare_providers_task() for provider comparison

- Task 8.4: AI Takeoff API Endpoints
  - Add to API routes:
    - POST `/pages/{page_id}/ai-takeoff` - trigger AI takeoff with:
      - condition_id parameter
      - optional provider parameter
      - optional element_type parameter
    - GET `/tasks/{task_id}/status` - get task status
    - POST `/pages/{page_id}/compare-providers` - run comparison across all providers
  - Create schemas:
    - AITakeoffRequest (condition_id, provider, element_type)
    - AITakeoffResponse (task_id, message, provider)
    - AITakeoffResultResponse with LLM metadata

- Task 8.5: Provider Comparison UI Component
  - Create `frontend/src/components/ProviderComparison.tsx`
  - Implement comparison trigger button
  - Display results from all available providers:
    - Elements detected count
    - Latency in milliseconds
    - Token usage (input/output)
    - Estimated cost calculation
  - Show results in card grid layout
  - Support re-running comparison

- Task 8.6: Frontend AI Takeoff Trigger
  - Create `frontend/src/components/takeoff/AITakeoffButton.tsx`
  - Implement AI takeoff dialog with:
    - Condition selector
    - LLM provider selector (using LLMProviderSelector component)
    - Element type selector
    - Progress indicator during processing
    - Result summary display (elements detected, provider used, latency)
    - Error handling display
  - Poll task status during processing
  - Refresh measurements on completion

Run through the verification checklist:
- [ ] AI service connects to all configured providers
- [ ] Provider fallback works when primary fails
- [ ] Polygon detection works for slab areas
- [ ] Polyline detection works for linear elements
- [ ] Point detection works for count elements
- [ ] Detected geometries are within page bounds
- [ ] Measurements created with correct quantities
- [ ] AI confidence scores stored
- [ ] Provider and model tracked with each measurement
- [ ] is_ai_generated flag set correctly
- [ ] Task polling works correctly
- [ ] Frontend shows provider selection option
- [ ] Frontend shows provider used in results
- [ ] Provider comparison tool works
- [ ] Uncalibrated pages blocked from AI takeoff
- [ ] Errors handled gracefully with fallback

Test Cases:
1. Run AI takeoff on a foundation plan with clear slab area → detects polygon
2. Run AI takeoff on a plan with foundation walls → detects polylines
3. Run AI takeoff with column locations → detects points
4. Verify measurements have correct quantities based on scale
5. Check that low-confidence detections are still created but flagged
6. Run with each provider individually → all produce results
7. Run provider comparison → shows results from all providers
8. Disable primary provider → falls back to secondary

Accuracy Testing:
- Compare AI-generated measurements to manual measurements
- Track accuracy percentage over multiple plans per provider
- Document which plan types work best/worst per provider
- Note common failure modes
- Use data to configure optimal provider per task type
```

---

## Phase 4B: Review Interface (Weeks 20-26) - Composer 1

### Prompt:
```
Continue to Phase 4B - Review Interface.

Read `plans/09-REVIEW-INTERFACE.md`.
For frontend tasks, also refer to `docs/design/DESIGN-SYSTEM.md`, `docs/design/COMPONENT_LIBRARY.md`, and the `@industrial-tactical-ui.mdc` rule for aesthetic guidance.

- Task 9.1: Add Review Fields to Models
  - Update `backend/app/models/measurement.py` with:
    - review_status (pending, approved, modified, verified, flagged)
    - reviewed_by, reviewed_at, review_notes
    - verified_by, verified_at, verification_notes
    - original_geometry (JSONB), original_quantity
    - is_modified, is_verified, is_flagged, flag_reason
  - Run migration: `alembic revision --autogenerate -m "add_review_fields_to_measurements"`

- Task 9.2: Review Statistics Model
  - Create `backend/app/models/review_session.py` with ReviewSession model:
    - project_id, reviewer_name, reviewer_role (estimator, qa_reviewer)
    - started_at, completed_at
    - measurements_reviewed, measurements_approved, measurements_rejected
    - measurements_modified, measurements_flagged
    - ai_measurements_reviewed, ai_measurements_accepted, ai_accuracy_rate
    - notes, session_data (JSONB)

- Task 9.3: Review Service Implementation
  - Create `backend/app/services/review_service.py`
  - Implement ReviewService class with:
    - approve_measurement() - update status to approved, set reviewer info
    - reject_measurement() - delete measurement
    - modify_measurement() - store original, update geometry, recalculate
    - verify_measurement() - QA verification, update status
    - flag_measurement() - set flag with reason
    - bulk_approve() - approve multiple measurements
    - bulk_verify() - verify multiple measurements
    - get_review_statistics() - calculate statistics for project/page
    - get_pending_measurements() - list pending by condition/page
    - get_ai_accuracy_stats() - calculate AI accuracy metrics

- Task 9.4: Review API Endpoints
  - Create `backend/app/api/routes/review.py` with:
    - POST `/measurements/{id}/approve` - approve measurement
    - POST `/measurements/{id}/reject` - reject/delete measurement
    - POST `/measurements/{id}/modify` - modify geometry
    - POST `/measurements/{id}/verify` - QA verify
    - POST `/measurements/{id}/flag` - flag for re-review
    - POST `/measurements/bulk-approve` - bulk approve
    - POST `/measurements/bulk-verify` - bulk verify
    - GET `/projects/{id}/review-stats` - get review statistics
    - GET `/pages/{id}/pending-measurements` - get pending measurements

- Task 9.5: Frontend Review Panel
  - Create `frontend/src/components/review/ReviewPanel.tsx`
  - Display measurements organized by status (pending, approved, modified, flagged)
  - Show AI confidence badge for AI-generated measurements
  - Implement approve/reject/flag buttons
  - Show measurement details on selection
  - Navigate through pending items with next/previous
  - Display review progress (X of Y reviewed)
  - Support estimator and QA modes with different actions

- Task 9.6: Side-by-Side View Component
  - Create `frontend/src/components/review/SideBySideView.tsx`
  - Display two synchronized plan viewers
  - Left panel: clean plan image
  - Right panel: plan with measurement overlays
  - Synchronized pan and zoom between panels
  - Highlight currently selected measurement
  - Show bounding box around selected measurement
  - Implement split view resize handle

- Task 9.7: Bulk Actions Component
  - Create `frontend/src/components/review/BulkActions.tsx`
  - Implement "Approve All" for pending measurements by condition
  - Implement "Verify All" for approved measurements
  - Add confirmation dialogs for bulk operations
  - Show count of affected measurements
  - Support filtering by confidence threshold

- Task 9.8: Review Workspace Page
  - Create `frontend/src/pages/ReviewWorkspace.tsx`
  - Integrate components:
    - Left sidebar: PageBrowser for page navigation
    - Main area: SideBySideView
    - Right sidebar: ReviewPanel
    - Top toolbar: mode selector (estimator/QA), condition filter
  - Implement mode switching between estimator and QA review
  - Track review session statistics
  - Auto-save review progress

Run through the verification checklist:
- [ ] Approve measurement updates status to "approved"
- [ ] Reject measurement deletes it from database
- [ ] Modify measurement stores original and updates geometry
- [ ] Verify measurement (QA) updates status to "verified"
- [ ] Flag measurement marks for re-review with reason
- [ ] Bulk approve works for multiple measurements
- [ ] Bulk verify works for multiple measurements
- [ ] Review statistics calculated correctly
- [ ] AI accuracy tracking works
- [ ] Side-by-side view syncs pan/zoom between panels
- [ ] Highlighted measurement shows bounding box
- [ ] Review panel navigates through pending items
- [ ] Estimator and QA modes show appropriate actions

Test Cases:
1. Generate AI measurements → review panel shows them as pending
2. Approve a measurement → status changes, statistics update
3. Reject a measurement → deleted from list
4. Modify geometry → original stored, new quantity calculated
5. QA verify approved measurement → status changes to verified
6. QA flag measurement → appears in flagged list
7. Check AI accuracy after reviewing 10 AI measurements
```

---

## Phase 5A: Export System (Weeks 24-28) - Composer 1

### Prompt:
```
Continue to Phase 5A - Export System.

Read `plans/10-EXPORT-SYSTEM.md`.
For frontend tasks, also refer to `docs/design/DESIGN-SYSTEM.md`, `docs/design/COMPONENT_LIBRARY.md`, and the `@industrial-tactical-ui.mdc` rule for aesthetic guidance.

- Task 10.1: Export Job Model
  - Create `backend/app/models/export.py` with:
    - ExportJob model:
      - project_id, export_format (xlsx, ost_xml, csv, pdf, json)
      - export_name, scope_type, condition_ids, page_ids
      - include_images, include_summary, include_details, include_unverified
      - group_by (condition, page, csi_code)
      - status (pending, processing, completed, failed), progress
      - started_at, completed_at, file_path, file_size
      - download_url, download_expires_at
      - error_message, error_details
      - conditions_exported, measurements_exported, pages_exported
      - requested_by, export_options
    - ExportTemplate model for saved export configurations
  - Update Project model with exports relationship
  - Run migration: `alembic revision --autogenerate -m "add_export_models"`

- Task 10.2: Base Export Service
  - Create `backend/app/services/export_service.py`
  - Implement ExportServiceError exception
  - Implement BaseExporter abstract class with:
    - __init__() accepting session and job
    - abstract generate() method returning Path
    - get_export_data() for fetching project, conditions, measurements
    - update_progress() for progress tracking
  - Implement ExportService class for job management:
    - create_export_job()
    - get_export_job()
    - start_export()
    - complete_export()
    - fail_export()
    - cleanup_expired_exports()

- Task 10.3: Excel Exporter
  - Create `backend/app/services/exporters/excel_exporter.py`
  - Implement ExcelExporter class extending BaseExporter
  - Generate .xlsx file with openpyxl:
    - Summary sheet: project info, totals by condition, grand totals
    - Detail sheet: all measurements with page, condition, geometry, quantity
    - Per-condition sheets (optional): measurements grouped by condition
  - Apply formatting: headers, number formats, column widths
  - Include formulas for totals
  - Support conditional formatting for AI-generated items

- Task 10.4: OST XML Exporter
  - Create `backend/app/services/exporters/ost_exporter.py`
  - Implement OSTExporter class extending BaseExporter
  - Generate On Screen Takeoff compatible XML:
    - Project metadata
    - Condition definitions with colors and settings
    - Measurement data with geometry
    - Page references
  - Follow OST XML schema requirements

- Task 10.5: CSV Exporter
  - Create `backend/app/services/exporters/csv_exporter.py`
  - Implement CSVExporter class extending BaseExporter
  - Generate CSV with:
    - Header row with column names
    - All measurements as rows
    - Include condition name, page number, quantity, unit
    - Proper encoding (UTF-8 with BOM for Excel compatibility)

- Task 10.6: PDF Report Exporter
  - Create `backend/app/services/exporters/pdf_exporter.py`
  - Implement PDFExporter class extending BaseExporter
  - Generate formatted PDF report with reportlab:
    - Cover page with project information
    - Summary table with condition totals
    - Detail pages with measurement tables
    - Optional: page images with measurement overlays

- Task 10.7: Export Celery Tasks
  - Create `backend/app/workers/export_tasks.py`
  - Implement generate_export_task() with:
    - Job status updates
    - Progress tracking
    - Exporter selection based on format
    - File storage to S3
    - Download URL generation
  - Implement cleanup_expired_exports_task() for scheduled cleanup

- Task 10.8: Export API Endpoints
  - Create `backend/app/api/routes/exports.py` with:
    - POST `/projects/{id}/export` - create export job
    - GET `/projects/{id}/exports` - list project exports with filters
    - GET `/exports/{id}` - get export job status and details
    - GET `/exports/{id}/download` - get download URL
    - POST `/exports/{id}/refresh-url` - refresh expired download URL
    - DELETE `/exports/{id}` - delete export job and file
  - Create schemas: ExportJobCreate, ExportJobResponse, ExportJobListResponse

- Task 10.9: Frontend Export Modal
  - Create `frontend/src/components/export/ExportModal.tsx`
  - Implement format selection (Excel, OST XML, CSV, PDF)
  - Condition selection (all or specific)
  - Options: include images, include summary, include unverified
  - Group by selector
  - Submit button to create export job

- Task 10.10: Frontend Export Preview
  - Create `frontend/src/components/export/ExportPreview.tsx`
  - Show preview of what will be exported
  - Display condition counts and measurement totals
  - Estimated file size

- Task 10.11: Frontend Export Progress
  - Create `frontend/src/components/export/ExportProgress.tsx`
  - Poll export job status
  - Show progress bar
  - Display completion message with download button
  - Handle errors gracefully

- Task 10.12: Frontend Export History
  - Create `frontend/src/components/export/ExportHistory.tsx`
  - List all exports for project
  - Show status badges (pending, processing, completed, failed)
  - Download button for completed exports
  - Refresh URL button for expired downloads
  - Delete button with confirmation
  - File size and timestamp display

- Task 10.13: Export API Client
  - Create `frontend/src/api/exports.ts` with:
    - ExportJobCreate interface
    - ExportJob interface
    - ExportJobList interface
    - exportsApi object with: create, list, get, refreshUrl, delete

- Task 10.14: Export Hook
  - Create `frontend/src/hooks/useExports.ts` with:
    - useExports() with auto-refresh for processing jobs
    - useExport() for single job with polling
    - useCreateExport() mutation
    - useRefreshExportUrl() mutation
    - useDeleteExport() mutation

- Task 10.15: Update Requirements
  - Add to `backend/requirements.txt`:
    - openpyxl>=3.1.2
    - reportlab>=4.0.4

Run through the verification checklist:
- [ ] Excel export generates valid .xlsx file with summary and details sheets
- [ ] OST XML export generates valid XML importable into On Screen Takeoff
- [ ] CSV export generates valid CSV with correct encoding
- [ ] PDF export generates formatted report with tables
- [ ] JSON export generates valid JSON structure
- [ ] Export jobs track progress correctly
- [ ] Download URLs work and can be refreshed
- [ ] Expired exports are cleaned up by scheduled task
- [ ] Export modal allows format selection and configuration
- [ ] Export history shows all exports with status
- [ ] Filtering by conditions works correctly
- [ ] Group by options work for all formats

Test Cases:
1. Create Excel export → Download and verify in Excel
2. Create OST XML export → Verify XML structure
3. Create export with specific conditions → Only those conditions exported
4. Create export excluding unverified → Only approved/verified measurements
5. Export large project → Progress updates in real-time
6. Cancel and retry failed export → Handles gracefully
7. Download expired export → Refresh URL works
8. Wait 30+ days → Old exports cleaned up
```

---

## Phase 5B: Testing & QA (Weeks 26-32) - Composer 1

### Prompt:
```
Continue to Phase 5B - Testing & Quality Assurance.

Read `plans/11-TESTING-QA.md`.
For frontend tests, also refer to `docs/design/DESIGN-SYSTEM.md`, `docs/design/COMPONENT_LIBRARY.md`, and the `@industrial-tactical-ui.mdc` rule for aesthetic guidance.

- Task 11.1: Test Configuration and Fixtures
  - Update `backend/tests/conftest.py` with:
    - get_test_settings() for test configuration
    - event_loop fixture (session scope)
    - async_engine fixture with SQLite for speed
    - db_session fixture with rollback
    - app fixture with dependency overrides
    - client fixture using AsyncClient
    - Mock fixtures for storage_client, llm_client, ocr_service

- Task 11.2: Test Factories
  - Create `backend/tests/factories/__init__.py`
  - Create `backend/tests/factories/project.py` with ProjectFactory
  - Create `backend/tests/factories/document.py` with DocumentFactory
  - Create `backend/tests/factories/page.py` with PageFactory
  - Create `backend/tests/factories/condition.py` with ConditionFactory
  - Create `backend/tests/factories/measurement.py` with MeasurementFactory
  - Use factory_boy with SQLAlchemy integration

- Task 11.3: Unit Tests
  - Create `backend/tests/unit/test_geometry.py`:
    - Test Point.distance_to()
    - Test calculate_line_length()
    - Test calculate_polyline_length()
    - Test calculate_polygon_area() with various shapes
    - Test calculate_circle_area()
  - Create `backend/tests/unit/test_scale_parser.py`:
    - Test parsing "1/4" = 1'-0"" formats
    - Test parsing "1" = 20'" formats
    - Test parsing "1:100" ratio formats
    - Test "NOT TO SCALE" handling
    - Test invalid input handling
  - Create `backend/tests/unit/test_measurement_calculator.py`:
    - Test MeasurementCalculator with various geometries
    - Test unit conversions
    - Test volume calculations
  - Create `backend/tests/unit/test_llm_client.py`:
    - Test provider initialization
    - Test fallback logic
    - Test retry behavior
    - Test response parsing

- Task 11.4: Integration Tests
  - Create `backend/tests/integration/test_api_projects.py`:
    - Test CRUD operations for projects
    - Test project listing with pagination
    - Test project deletion cascades
  - Create `backend/tests/integration/test_api_documents.py`:
    - Test document upload
    - Test document status polling
    - Test document deletion
  - Create `backend/tests/integration/test_api_pages.py`:
    - Test page listing
    - Test scale calibration
    - Test OCR retrieval
  - Create `backend/tests/integration/test_api_conditions.py`:
    - Test condition CRUD
    - Test template creation
    - Test reordering
  - Create `backend/tests/integration/test_api_measurements.py`:
    - Test measurement creation
    - Test quantity recalculation
    - Test review status updates
  - Create `backend/tests/integration/test_api_exports.py`:
    - Test export job creation
    - Test export status polling
    - Test download URL generation
  - Create `backend/tests/integration/test_llm_settings_api.py`:
    - Test provider listing endpoint
    - Test default provider setting

- Task 11.5: E2E Tests
  - Create `backend/tests/e2e/test_full_takeoff_workflow.py`:
    - Upload document
    - Wait for processing
    - Create condition
    - Create measurements
    - Verify totals
    - Export to Excel
  - Create `backend/tests/e2e/test_review_workflow.py`:
    - Generate AI measurements
    - Approve/reject measurements
    - Verify statistics
  - Set up Playwright for frontend E2E:
    - Create `frontend/tests/e2e/playwright/takeoff.spec.ts`
    - Create `frontend/tests/e2e/playwright/review.spec.ts`

- Task 11.6: AI Accuracy Benchmark System
  - Create `backend/tests/fixtures/golden_dataset/` structure
  - Create `backend/tests/fixtures/golden_dataset/manifest.json`
  - Create sample plan directories with:
    - page.png
    - expected_measurements.json
    - metadata.json
  - Create `backend/tests/accuracy/benchmark_runner.py` with:
    - BenchmarkRunner class
    - run_benchmark() method
    - _compare_measurements() with tolerance
    - _calculate_accuracy_metrics()
  - Create `backend/tests/accuracy/accuracy_reporter.py` for report generation

- Task 11.7: Multi-Provider Benchmark
  - Create `backend/tests/accuracy/test_multi_provider_benchmark.py`:
    - Test class for running benchmarks across providers
    - Per-provider accuracy tracking
    - Cost estimation per provider
    - Latency comparison
  - Create `backend/tests/accuracy/multi_provider_benchmark.py` with:
    - MultiProviderBenchmarkRunner class
    - run_comparison() across all available providers
    - generate_report() with recommendations
    - PROVIDER_PRICING dictionary for cost estimation

- Task 11.8: CI/CD Quality Gates
  - Update `.github/workflows/ci.yml`:
    - Add coverage threshold check (80%)
    - Add separate job for accuracy tests on main branch
    - Generate test reports
    - Upload coverage to Codecov
  - Create `.github/workflows/accuracy-benchmark.yml`:
    - Trigger on main branch
    - Run multi-provider benchmark
    - Upload results as artifact
    - Fail if accuracy below 75%

- Task 11.9: Performance Tests
  - Create `backend/tests/performance/test_large_documents.py`:
    - Test document processing with 100+ pages
    - Test measurement creation at scale
    - Test export generation for large projects
  - Create `backend/tests/performance/locustfile.py`:
    - TakeoffUser class simulating user behavior
    - list_projects task
    - get_project task
    - create_condition task
    - health_check task
    - Configure wait times and weights

Run through the verification checklist:

Unit Tests:
- [ ] Geometry calculations pass all test cases
- [ ] Scale parsing handles all common formats
- [ ] Measurement calculator edge cases handled
- [ ] All validators have test coverage
- [ ] LLM client multi-provider tests pass
- [ ] Provider fallback logic tested

Integration Tests:
- [ ] API endpoints return correct status codes
- [ ] CRUD operations work for all entities
- [ ] Measurement totals update correctly
- [ ] Cascade deletes work properly
- [ ] LLM settings API tests pass

AI Accuracy:
- [ ] Golden dataset has 10+ annotated plans
- [ ] Benchmark runner executes successfully
- [ ] Overall accuracy >= 75% target
- [ ] Quantity errors within tolerance
- [ ] Multi-provider benchmark runs against all available providers
- [ ] Per-provider accuracy tracked and compared
- [ ] Cost estimates calculated for each provider
- [ ] Comparison report generated with recommendations

E2E Tests:
- [ ] Can create project and upload document
- [ ] Can draw measurements on canvas
- [ ] Can approve/reject AI measurements
- [ ] Export workflow completes

CI/CD:
- [ ] Unit tests run on every PR
- [ ] Coverage threshold enforced (80%)
- [ ] Accuracy tests run on main branch
- [ ] Test reports generated 

Performance:
- [ ] API responses under 200ms
- [ ] Document processing scales linearly
- [ ] No memory leaks in long operations
```

---

## Phase 6: Deployment & Operations (Weeks 30-36) - Composer 1

### Prompt:
```
Continue to Phase 6 - Deployment & Operations.

Read `plans/12-DEPLOYMENT.md`.
For frontend tasks, also refer to `docs/design/DESIGN-SYSTEM.md`, `docs/design/COMPONENT_LIBRARY.md`, and the `@industrial-tactical-ui.mdc` rule for aesthetic guidance.

- Task 12.1: Production Dockerfiles
  - Create `docker/Dockerfile.api` (multi-stage build):
    - Builder stage: install build dependencies, create venv, install pip packages
    - Production stage: install runtime dependencies only, copy venv, copy app code
    - Non-root user, health check, expose port 8000
  - Create `docker/Dockerfile.worker` (multi-stage build):
    - Similar to API but with poppler-utils and tesseract-ocr
    - Celery worker command with concurrency and max-tasks-per-child
  - Create `docker/Dockerfile.frontend`:
    - Builder stage: npm ci, npm run build
    - Production stage: nginx, copy built files, copy nginx config

- Task 12.2: Nginx Configuration
  - Create `docker/nginx/nginx.conf`:
    - Worker processes, connections
    - Gzip compression
    - Include sites-enabled
  - Create `docker/nginx/default.conf`:
    - Server block for port 80
    - Static file serving for frontend
    - API proxy pass to upstream
    - WebSocket support for /ws
    - Security headers
    - Cache control for static assets

- Task 12.3: Docker Compose Production
  - Create `docker/docker-compose.prod.yml`:
    - All services with production settings
    - Resource limits (memory, CPUs)
    - Restart policies
    - Volume mounts for persistent data
    - Environment variable configuration
    - Logging configuration
    - Network configuration

- Task 12.4: GitHub Actions Workflows
  - Create `.github/workflows/deploy-staging.yml`:
    - Trigger on push to develop
    - Build and push Docker images to ECR
    - Deploy to staging ECS cluster
    - Run smoke tests
  - Create `.github/workflows/deploy-prod.yml`:
    - Trigger on release or manual dispatch
    - Require manual approval
    - Build and push Docker images
    - Deploy to production ECS cluster
    - Run smoke tests
    - Notify team on success/failure

- Task 12.5: Terraform Modules
  - Create `infrastructure/terraform/modules/networking/`:
    - VPC with public and private subnets
    - Internet gateway, NAT gateway
    - Route tables, security groups
  - Create `infrastructure/terraform/modules/database/`:
    - RDS PostgreSQL with Multi-AZ
    - Parameter group, subnet group
    - Security group, secrets manager
  - Create `infrastructure/terraform/modules/storage/`:
    - S3 bucket for documents
    - Lifecycle rules, versioning
    - CORS configuration
  - Create `infrastructure/terraform/modules/compute/`:
    - ECS cluster, services, task definitions
    - Application Load Balancer
    - Auto-scaling policies
    - CloudWatch log groups
  - Create `infrastructure/terraform/environments/staging/` and `production/`:
    - main.tf with module calls
    - variables.tf and terraform.tfvars

- Task 12.6: Monitoring
  - Create `monitoring/prometheus/prometheus.yml`:
    - Global scrape config
    - Job configurations for api, workers, node
    - Alertmanager configuration
  - Create `monitoring/prometheus/alerts/`:
    - api-alerts.yml (high latency, error rate, 5xx responses)
    - worker-alerts.yml (queue depth, task failures)
    - infrastructure-alerts.yml (CPU, memory, disk)
  - Create `monitoring/grafana/provisioning/dashboards/`:
    - api-dashboard.json
    - worker-dashboard.json
    - ai-accuracy-dashboard.json (track per-provider metrics)
    - business-metrics-dashboard.json

- Task 12.7: Alerting Configuration
  - Create `monitoring/alertmanager/alertmanager.yml`:
    - Route configuration
    - Receiver configuration (Slack, email)
    - Inhibit rules
    - Silence patterns
  - Configure PagerDuty integration for critical alerts

- Task 12.8: Backup Scripts
  - Create `infrastructure/scripts/backup-db.sh`:
    - pg_dump with compression
    - Upload to S3 with timestamp
    - Retention policy (keep 7 daily, 4 weekly, 12 monthly)
  - Create `infrastructure/scripts/restore-db.sh`:
    - Download from S3
    - pg_restore with options
    - Verification steps
  - Set up automated daily backups via cron/CloudWatch Events

- Task 12.9: Operational Runbooks
  - Create `docs/operations/runbooks/incident-response.md`:
    - Severity levels and response times
    - Escalation procedures
    - Communication templates
  - Create `docs/operations/runbooks/scaling-procedures.md`:
    - Manual scaling steps
    - Auto-scaling configuration
    - Database scaling
  - Create `docs/operations/runbooks/backup-restore.md`:
    - Backup verification
    - Point-in-time recovery
    - Disaster recovery steps
  - Create `docs/operations/runbooks/troubleshooting.md`:
    - Common issues and solutions
    - Log locations
    - Debug procedures

- Task 12.10: Security Configuration
  - Configure WAF rules for API protection
  - Set up KMS for encryption at rest
  - Enable VPC Flow Logs
  - Configure SSL/TLS certificates with ACM
  - Implement secrets rotation

- Task 12.11: DNS and SSL
  - Configure Route53 hosted zone
  - Create A records for api.takeoff.example.com and app.takeoff.example.com
  - Request ACM certificates
  - Configure HTTPS on ALB

- Task 12.12: Log Aggregation
  - Create `logging/fluentd/fluent.conf` for log collection
  - Configure CloudWatch Logs integration
  - Set up log retention policies
  - Create log-based metrics

- Task 12.13: Cost Monitoring
  - Set up AWS Budgets alerts
  - Configure Cost Explorer tags
  - Create cost allocation reports
  - Track LLM API usage and costs per provider

- Task 12.14: Pre-Deployment Checklist
  - Create `docs/operations/deployment-checklist.md`:
    - Pre-deployment checks (code, testing, infrastructure)
    - Deployment execution steps
    - Verification steps
    - Rollback triggers and procedures
    - Emergency contacts

Complete the production readiness checklist:
- [ ] All services containerized and tested
- [ ] Infrastructure provisioned via Terraform
- [ ] CI/CD pipeline operational
- [ ] Monitoring and alerting configured
- [ ] Backup system tested
- [ ] Runbooks documented and reviewed
- [ ] Security hardening applied
- [ ] Load testing completed
- [ ] Disaster recovery plan documented
- [ ] Team trained on operational procedures
```

---

## Resuming Mid-Phase

If you need to start a new chat in the middle of a phase, use this template:

```
I'm working on the Takeoff Platform, currently in Phase [X] - [Phase Name].

Read `plans/[XX-DOCUMENT-NAME.md]`.

I've completed:
- Task X.1: [Name]
- Task X.2: [Name]

Continue with Task X.3: [Name]

Here's the current state of the relevant files:
[Paste any relevant code context]
```

---

## Troubleshooting / Debugging

```
I'm working on the Takeoff Platform and encountering an issue.

Phase: [X] - [Phase Name]
Relevant spec: `plans/[XX-DOCUMENT-NAME.md]`

Issue: [Describe the problem]

Error message:
```
[Paste any error messages]
```

Relevant code:
```
[Paste relevant code]
```

What I've tried:
- [List troubleshooting steps]
```

---

## Quick Reference: Phase Summary

| Phase | Document | Duration | Key Deliverables |
|-------|----------|----------|------------------|
| 0 | 01-PROJECT-SETUP.md | Week 1 | Repository, Docker, CI/CD |
| 1A | 02-DOCUMENT-INGESTION.md | Weeks 2-5 | Upload, processing, storage |
| 1B | 03-OCR-TEXT-EXTRACTION.md | Weeks 4-6 | OCR, title blocks, search |
| 2A | 04-PAGE-CLASSIFICATION.md | Weeks 6-9 | Multi-provider LLM classification |
| 2B | 05-SCALE-DETECTION.md | Weeks 8-11 | Scale detection, calibration |
| 3A | 06-MEASUREMENT-ENGINE.md | Weeks 10-16 | Geometry, measurements |
| 3B | 07-CONDITION-MANAGEMENT.md | Weeks 14-18 | Conditions, templates |
| 4A | 08-AI-TAKEOFF-GENERATION.md | Weeks 16-22 | AI detection, provider comparison |
| 4B | 09-REVIEW-INTERFACE.md | Weeks 20-26 | Review workflow, QA |
| 5A | 10-EXPORT-SYSTEM.md | Weeks 24-28 | Excel, OST, CSV, PDF exports |
| 5B | 11-TESTING-QA.md | Weeks 26-32 | Tests, benchmarks, CI/CD |
| 6 | 12-DEPLOYMENT.md | Weeks 30-36 | Production, monitoring, ops |
