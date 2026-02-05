# Phase 1: Foundation Task List

## AI-Powered Construction Takeoff Platform

**Objective:** Establish the core infrastructure enabling users to upload construction plans (PDF/TIFF) and view them page-by-page with pan/zoom functionality.

**Deliverable:** Users can upload plans and view them page-by-page.

---

## Task Overview

| Category | Task Count | Priority |
|----------|------------|----------|
| 1. Project Infrastructure | 8 tasks | Critical |
| 2. Backend Foundation | 12 tasks | Critical |
| 3. Frontend Foundation | 10 tasks | Critical |
| 4. Document Ingestion | 9 tasks | High |
| 5. Document Viewer | 8 tasks | High |
| 6. Integration & Testing | 6 tasks | High |

**Total: 53 tasks**

---

## 1. Project Infrastructure

### 1.1 Repository Structure
- [ ] **P1-001**: Create monorepo directory structure
  ```
  /
  ├── backend/           # FastAPI application
  ├── frontend/          # React application
  ├── docker/            # Docker configurations
  ├── docs/              # Documentation
  ├── scripts/           # Utility scripts
  └── .github/           # CI/CD workflows
  ```

- [ ] **P1-002**: Create `.gitignore` with Python, Node.js, and IDE exclusions

- [ ] **P1-003**: Create `docker-compose.yml` for local development
  - PostgreSQL 15+ service
  - Redis 7+ service
  - MinIO service (S3-compatible storage)
  - Backend service
  - Frontend service

- [ ] **P1-004**: Create `docker-compose.override.yml` for development hot-reloading

### 1.2 Development Environment
- [ ] **P1-005**: Create `Makefile` with common development commands
  - `make setup` - Initialize development environment
  - `make dev` - Start all services
  - `make test` - Run all tests
  - `make lint` - Run linters
  - `make clean` - Clean generated files

- [ ] **P1-006**: Create `.env.example` with all required environment variables

- [ ] **P1-007**: Create `scripts/setup-dev.sh` for first-time setup

- [ ] **P1-008**: Create basic GitHub Actions CI workflow
  - Run linting on PRs
  - Run tests on PRs
  - Build Docker images

---

## 2. Backend Foundation

### 2.1 FastAPI Project Setup
- [ ] **P1-009**: Initialize Python project structure
  ```
  backend/
  ├── app/
  │   ├── __init__.py
  │   ├── main.py           # FastAPI app entry point
  │   ├── config.py         # Configuration management
  │   ├── api/              # API routes
  │   ├── models/           # SQLAlchemy models
  │   ├── schemas/          # Pydantic schemas
  │   ├── services/         # Business logic
  │   ├── core/             # Core utilities
  │   └── db/               # Database utilities
  ├── tests/
  ├── requirements.txt
  ├── requirements-dev.txt
  └── Dockerfile
  ```

- [ ] **P1-010**: Create `requirements.txt` with core dependencies
  - fastapi, uvicorn[standard]
  - sqlalchemy[asyncio], asyncpg
  - pydantic, pydantic-settings
  - python-multipart (file uploads)
  - redis, celery
  - boto3 (S3 client)
  - pdf2image, Pillow, pymupdf
  - python-jose[cryptography], passlib[bcrypt]
  - httpx

- [ ] **P1-011**: Create `requirements-dev.txt`
  - pytest, pytest-asyncio
  - black, isort, flake8, mypy
  - httpx (for testing)

- [ ] **P1-012**: Create `app/config.py` using Pydantic Settings
  - Database URL
  - Redis URL
  - S3/MinIO configuration
  - JWT secret and algorithm
  - File upload limits
  - CORS origins

- [ ] **P1-013**: Create `app/main.py` with FastAPI application
  - CORS middleware
  - Exception handlers
  - Health check endpoint
  - API router mounting

- [ ] **P1-014**: Create backend `Dockerfile` (Python 3.11+)

### 2.2 Database Setup
- [ ] **P1-015**: Create `app/db/database.py` with async SQLAlchemy engine
  - Connection pooling configuration
  - Session factory

- [ ] **P1-016**: Create `app/db/base.py` with declarative base

- [ ] **P1-017**: Create initial database models
  - `User` model (id, email, hashed_password, is_active, created_at)
  - `Project` model (id, name, description, user_id, status, created_at, updated_at)
  - `Document` model (id, project_id, filename, original_filename, file_path, file_size, page_count, status, created_at)
  - `Page` model (id, document_id, page_number, image_path, thumbnail_path, width, height, dpi, status)

- [ ] **P1-018**: Create database migration setup (Alembic)
  - `alembic.ini` configuration
  - Initial migration with all models

### 2.3 Authentication System
- [ ] **P1-019**: Create `app/core/security.py`
  - Password hashing (bcrypt)
  - JWT token creation/verification
  - Token expiration handling

- [ ] **P1-020**: Create `app/api/routes/auth.py`
  - `POST /api/auth/register` - User registration
  - `POST /api/auth/login` - User login (returns JWT)
  - `POST /api/auth/refresh` - Refresh token
  - `GET /api/auth/me` - Get current user

---

## 3. Frontend Foundation

### 3.1 React Project Setup
- [ ] **P1-021**: Initialize React project with Vite + TypeScript
  ```
  frontend/
  ├── src/
  │   ├── components/       # Reusable components
  │   ├── pages/            # Page components
  │   ├── hooks/            # Custom hooks
  │   ├── services/         # API services
  │   ├── stores/           # Zustand stores
  │   ├── types/            # TypeScript types
  │   ├── utils/            # Utility functions
  │   ├── App.tsx
  │   └── main.tsx
  ├── public/
  ├── package.json
  ├── tsconfig.json
  ├── vite.config.ts
  └── Dockerfile
  ```

- [ ] **P1-022**: Install and configure core dependencies
  - react, react-dom
  - react-router-dom
  - @tanstack/react-query
  - zustand
  - axios
  - zod

- [ ] **P1-023**: Install and configure Tailwind CSS + Shadcn/ui
  - tailwindcss, postcss, autoprefixer
  - @radix-ui primitives
  - class-variance-authority, clsx, tailwind-merge

- [ ] **P1-024**: Create `tsconfig.json` with strict mode and path aliases

- [ ] **P1-025**: Create frontend `Dockerfile` (Node.js)

### 3.2 Core Frontend Infrastructure
- [ ] **P1-026**: Create API client service (`src/services/api.ts`)
  - Axios instance with base URL
  - Request/response interceptors
  - JWT token injection
  - Error handling

- [ ] **P1-027**: Create authentication store (`src/stores/authStore.ts`)
  - User state
  - Login/logout actions
  - Token persistence (localStorage)

- [ ] **P1-028**: Create React Query configuration
  - Query client setup
  - Default options (stale time, retry logic)

- [ ] **P1-029**: Create routing configuration (`src/App.tsx`)
  - Public routes (login, register)
  - Protected routes wrapper
  - Layout components

- [ ] **P1-030**: Create base UI components using Shadcn/ui
  - Button, Input, Card, Dialog
  - Toast notifications
  - Loading spinners
  - Form components

---

## 4. Document Ingestion

### 4.1 File Upload System
- [ ] **P1-031**: Create S3/MinIO service (`app/services/storage.py`)
  - Upload file to bucket
  - Download file from bucket
  - Generate presigned URLs
  - Delete file
  - List files

- [ ] **P1-032**: Create file upload API endpoint
  - `POST /api/documents/upload` - Upload PDF/TIFF file
  - Validate file type (PDF, TIFF)
  - Validate file size limits
  - Store original file in S3
  - Create Document record in database
  - Return document ID for processing

- [ ] **P1-033**: Create project management API endpoints
  - `GET /api/projects` - List user's projects
  - `POST /api/projects` - Create new project
  - `GET /api/projects/{id}` - Get project details
  - `PUT /api/projects/{id}` - Update project
  - `DELETE /api/projects/{id}` - Delete project
  - `GET /api/projects/{id}/documents` - List project documents

### 4.2 Document Processing Pipeline
- [ ] **P1-034**: Create Celery configuration (`app/core/celery.py`)
  - Celery app initialization
  - Task routing
  - Worker configuration

- [ ] **P1-035**: Create PDF processing service (`app/services/pdf_processor.py`)
  - Extract PDF metadata (page count, dimensions)
  - Render each page to PNG (300 DPI minimum)
  - Generate thumbnail for each page
  - Store rendered images in S3
  - Update Page records in database

- [ ] **P1-036**: Create TIFF processing service (`app/services/tiff_processor.py`)
  - Handle multi-page TIFF files
  - Convert pages to PNG
  - Preserve DPI metadata
  - Generate thumbnails
  - Store in S3 and database

- [ ] **P1-037**: Create document processing Celery task
  - `process_document` task
  - Determine file type
  - Route to appropriate processor
  - Update document status (PENDING → PROCESSING → COMPLETED/FAILED)
  - Handle errors gracefully

- [ ] **P1-038**: Create document status API endpoints
  - `GET /api/documents/{id}` - Get document details with page list
  - `GET /api/documents/{id}/status` - Get processing status
  - `GET /api/documents/{id}/pages` - List all pages with thumbnails

- [ ] **P1-039**: Create WebSocket endpoint for processing updates
  - Real-time progress updates during document processing
  - Connection authentication

---

## 5. Document Viewer

### 5.1 PDF.js Integration
- [ ] **P1-040**: Install and configure PDF.js
  - pdfjs-dist package
  - Worker setup for Vite

- [ ] **P1-041**: Create PDF viewer component (`src/components/viewer/PDFViewer.tsx`)
  - Canvas-based rendering
  - Handle high-resolution displays
  - Memory management for large documents

### 5.2 Viewer Features
- [ ] **P1-042**: Implement zoom controls
  - Zoom in/out buttons
  - Zoom slider
  - Fit to width/height options
  - Zoom range: 10% to 1000%
  - Keyboard shortcuts (Ctrl +/-)

- [ ] **P1-043**: Implement pan functionality
  - Mouse drag to pan
  - Touch support for tablets
  - Smooth animation

- [ ] **P1-044**: Create page navigation
  - Previous/next page buttons
  - Page number input (jump to page)
  - Keyboard shortcuts (arrow keys, Page Up/Down)

- [ ] **P1-045**: Create thumbnail sidebar (`src/components/viewer/ThumbnailSidebar.tsx`)
  - Display page thumbnails
  - Click to navigate
  - Highlight current page
  - Virtual scrolling for large documents

- [ ] **P1-046**: Create viewer toolbar (`src/components/viewer/ViewerToolbar.tsx`)
  - Zoom controls
  - Page navigation
  - Fullscreen toggle
  - Download original button

- [ ] **P1-047**: Create document viewer page (`src/pages/DocumentViewer.tsx`)
  - Fetch document and pages from API
  - Combine all viewer components
  - Handle loading states
  - Error handling for failed loads

---

## 6. Integration & Testing

### 6.1 Backend Testing
- [ ] **P1-048**: Create pytest configuration and fixtures
  - Test database setup/teardown
  - Test client fixture
  - Authentication fixtures

- [ ] **P1-049**: Write tests for authentication endpoints
  - Registration validation
  - Login success/failure
  - Token verification

- [ ] **P1-050**: Write tests for document upload and processing
  - File upload validation
  - Processing pipeline (unit tests)
  - API endpoint integration tests

### 6.2 Frontend Testing
- [ ] **P1-051**: Configure Vitest for frontend testing
  - Test setup and configuration
  - MSW for API mocking

- [ ] **P1-052**: Write tests for core components
  - Authentication flow
  - Document upload
  - Viewer basic functionality

### 6.3 End-to-End Integration
- [ ] **P1-053**: Create integration test suite
  - Full upload → process → view workflow
  - Multi-page document handling
  - Error scenarios

---

## Dependency Graph

```
P1-001 → P1-002 → P1-003 → P1-004
                      ↓
P1-009 → P1-010 → P1-014 → P1-003 (backend service)
                      ↓
P1-015 → P1-016 → P1-017 → P1-018
                      ↓
P1-019 → P1-020 (requires P1-017)
                      ↓
P1-021 → P1-022 → P1-025 → P1-003 (frontend service)
                      ↓
P1-026 → P1-027 → P1-028 → P1-029
                      ↓
P1-031 → P1-032 → P1-033 (requires P1-017, P1-020)
                      ↓
P1-034 → P1-035 → P1-036 → P1-037 → P1-038 → P1-039
                      ↓
P1-040 → P1-041 → P1-042 → P1-043 → P1-044 → P1-045 → P1-046 → P1-047
                      ↓
P1-048 → P1-049 → P1-050 → P1-051 → P1-052 → P1-053
```

---

## Implementation Order (Suggested Sprints)

### Sprint 1: Infrastructure & Project Setup
**Tasks:** P1-001 through P1-008
- Set up repository structure
- Docker Compose configuration
- Development environment scripts
- CI/CD pipeline basics

### Sprint 2: Backend Core
**Tasks:** P1-009 through P1-020
- FastAPI project scaffold
- Database models and migrations
- Authentication system

### Sprint 3: Frontend Core
**Tasks:** P1-021 through P1-030
- React project scaffold
- UI component library
- Routing and state management
- API client

### Sprint 4: Document Upload & Processing
**Tasks:** P1-031 through P1-039
- S3/MinIO integration
- File upload endpoints
- PDF/TIFF processing pipeline
- Celery task queue

### Sprint 5: Document Viewer
**Tasks:** P1-040 through P1-047
- PDF.js integration
- Zoom and pan controls
- Page navigation
- Thumbnail sidebar

### Sprint 6: Testing & Polish
**Tasks:** P1-048 through P1-053
- Unit tests
- Integration tests
- End-to-end workflow testing
- Bug fixes and refinements

---

## Definition of Done

Each task is considered complete when:

1. **Code is written** following project conventions
2. **Unit tests pass** (where applicable)
3. **Code is reviewed** (if working with team)
4. **Documentation is updated** (API docs auto-generate with FastAPI)
5. **No linting errors** exist
6. **Feature works end-to-end** in local development

---

## Phase 1 Acceptance Criteria

Phase 1 is complete when a user can:

1. ✅ Register and log in to the application
2. ✅ Create a new project
3. ✅ Upload a PDF or TIFF construction plan
4. ✅ See real-time processing status
5. ✅ View the uploaded document with:
   - Pan and zoom controls
   - Page-by-page navigation
   - Thumbnail sidebar for quick navigation
6. ✅ View multiple documents within a project
7. ✅ Log out and have session properly terminated

---

## Technical Notes

### File Size Considerations
- Construction plans can be 50-200MB per document
- Configure upload limits appropriately (recommend 500MB max)
- Use streaming uploads for large files
- Consider chunked upload for reliability

### Image Processing Performance
- PDF rendering at 300 DPI creates large images
- A 36"x48" E-size drawing at 300 DPI = 10,800 x 14,400 pixels
- Use progressive JPEG/WebP for thumbnails
- Consider generating multiple resolution tiers

### Database Indexes
Ensure indexes on:
- `documents.project_id`
- `documents.status`
- `pages.document_id`
- `pages.page_number`
- `projects.user_id`

### Security Considerations
- Validate file types by magic bytes, not just extension
- Sanitize filenames before storage
- Use signed URLs for S3 access (short expiration)
- Rate limit upload endpoints
- Implement file scanning for malware (consider ClamAV)
