# Phase 0: Application Interface - Implementation Prompt

> **RECOMMENDED MODEL**: Claude 3.5 Sonnet (2024-10-22 or later)  
> **ALTERNATIVE**: GPT-4 Turbo or GPT-4o  
> **CONTEXT WINDOW**: Use at least 200k tokens  

---

# Implementation Task: Phase 0 Application Interface

## ⚠️ CRITICAL FIRST STEP - READ THE SPECIFICATION

**BEFORE YOU DO ANYTHING ELSE:**

1. **Open and read `@plans/00-APPLICATION-INTERFACE.md` in its entirety** (800+ lines)
2. This specification file contains:
   - Complete implementation code for all components
   - Full routing structure
   - API integration patterns
   - Type definitions
   - Navigation components
3. **MANDATORY**: After reading the spec, create your task list with **Task #0** being:
   ```
   ✅ Task #0: Read and understood complete specification file (@plans/00-APPLICATION-INTERFACE.md)
   ```
4. Reference the spec file for ALL implementation details - **DO NOT improvise or guess**

**The spec file is your source of truth. This prompt is just a roadmap.**

---

## Context

The current application has a single "Dashboard" page that's just a testing interface for Phase 2A (page classification). There's no way to:
- View all projects
- Create new projects
- Navigate into projects to see documents
- Manage documents within projects
- Properly navigate the application

You will implement a **complete project management interface** that serves as the foundation for all other features.

## Prerequisites (Already Complete)

✅ **Backend API endpoints working**: `/api/v1/projects`, `/api/v1/documents`  
✅ **Database models exist**: Project, Document, Page  
✅ **TakeoffViewer page exists**: Phase 3A+ manual drawing tools  
✅ **Document upload component exists**: DocumentUploader.tsx  

## Tech Stack & Development Environment

### ⚠️ CRITICAL: Docker-Based Development

**ALL development happens in Docker containers. NEVER install packages locally.**

```bash
# Project structure
takeoff-automation/
├── docker/
│   ├── docker-compose.yml       # Service orchestration
│   ├── Dockerfile.frontend      # Frontend container
│   ├── Dockerfile.api          # Backend API container
│   └── Dockerfile.worker       # Celery worker container
├── frontend/                    # React app (runs in container)
├── backend/                     # FastAPI app (runs in container)
└── tests/                      # Test files (PDFs, etc.)
```

### Frontend Stack (Docker Container)
- **React 18** + TypeScript (strict mode)
- **Vite** for build tooling
- **React Router** for navigation
- **TanStack Query** (React Query) for data fetching
- **shadcn/ui** components (already installed)
- **Tailwind CSS** for styling
- **Lucide React** for icons
- **Konva.js** for canvas drawing (Phase 3A+)

### Backend Stack (Docker Container)
- **Python 3.11+** with FastAPI
- **PostgreSQL 15+** database
- **Redis 7+** for caching/Celery
- **MinIO** (S3-compatible storage)
- **Celery** for background tasks

### Design System (MANDATORY READING)

**BEFORE writing any UI code, read these files:**

1. **`@docs/design/DESIGN-SYSTEM.md`** (870 lines)
   - Complete color system (HSL tokens, measurement colors)
   - Typography scale and usage rules
   - Spacing patterns
   - Component patterns
   - Accessibility guidelines

2. **`@docs/design/COMPONENT_LIBRARY.md`** (1099 lines)
   - All shadcn/ui components with examples
   - Button, Card, Dialog, Input, Select, Badge, etc.
   - Usage patterns and best practices
   - Common patterns (forms, loading states, errors)
   - Accessibility guidelines

**Key Design Principles:**
- Use semantic color tokens (never hardcode colors)
- Follow typography scale (`text-sm`, `text-lg`, `text-2xl`)
- Use consistent spacing (`gap-2`, `gap-4`, `p-4`)
- Import shadcn/ui from `@/components/ui/`
- Use Lucide React icons exclusively

## Pages to Build

Refer to **`@plans/00-APPLICATION-INTERFACE.md`** for complete implementation code:

### 1. Projects List Page
**Location**: `frontend/src/pages/Projects.tsx`  
**Spec Reference**: Task 0.1  
**Features**:
- Grid of project cards (responsive)
- Search/filter by name or client
- "Create Project" button
- Empty state when no projects
- Click card → Navigate to project detail

### 2. Create Project Modal
**Location**: `frontend/src/components/project/CreateProjectModal.tsx`  
**Spec Reference**: Task 0.2  
**Features**:
- Modal dialog with form
- Fields: name (required), client_name, project_address, description
- Form validation
- Submit → POST to API → Navigate to new project

### 3. Project Detail Page
**Location**: `frontend/src/pages/ProjectDetail.tsx`  
**Spec Reference**: Task 0.3  
**Features**:
- Breadcrumb navigation
- Project header with metadata
- Document grid
- Upload documents button
- Empty state when no documents
- Click document → Navigate to document detail

### 4. Document Detail Page
**Location**: `frontend/src/pages/DocumentDetail.tsx`  
**Spec Reference**: Task 0.4  
**Features**:
- Breadcrumb navigation
- Document header with status
- Page grid with thumbnails
- "Open Takeoff" button on each page
- Processing status indicator
- Classify pages button

### 5. Navigation Components
**Locations**: 
- `frontend/src/components/layout/Header.tsx`
- `frontend/src/components/layout/Breadcrumbs.tsx`

**Spec Reference**: Task 0.5  
**Features**:
- Sticky header with app title
- Breadcrumb navigation component
- Consistent across all pages

### 6. Reusable Components
**Locations**:
- `frontend/src/components/project/ProjectCard.tsx`
- `frontend/src/components/document/DocumentCard.tsx`
- `frontend/src/components/document/PageCard.tsx`
- `frontend/src/components/common/EmptyState.tsx`

**Spec Reference**: Task 0.6  
**Features**:
- Consistent card designs
- Hover effects
- Click handlers
- Empty state component

### 7. Update Routing
**Location**: `frontend/src/App.tsx`  
**Spec Reference**: Task 0.7  
**Add Routes**:
- `/projects` - Projects list
- `/projects/:projectId` - Project detail
- `/projects/:projectId/documents/:documentId` - Document detail
- `/documents/:documentId/pages/:pageId` - TakeoffViewer (already exists)

### 8. API Client
**Location**: `frontend/src/api/projects.ts`  
**Spec Reference**: Task 0.9  
**Functions**:
- `list()` - Get all projects
- `get(id)` - Get single project
- `create(data)` - Create project
- `update(id, data)` - Update project
- `getDocuments(id)` - Get project documents

### 9. Type Definitions
**Location**: `frontend/src/types/index.ts`  
**Spec Reference**: Task 0.10  
**Add Types**:
- `Project` interface
- `CreateProjectRequest` interface
- Update `Document` interface with project_id

---

## Implementation Sequence

Follow this order exactly:

**Task #0**: ✅ Read `@plans/00-APPLICATION-INTERFACE.md` completely (MANDATORY)

**Task #1**: Create type definitions in `types/index.ts`

**Task #2**: Create API client in `api/projects.ts`

**Task #3**: Create reusable components (ProjectCard, DocumentCard, PageCard, EmptyState)

**Task #4**: Create navigation components (Header, Breadcrumbs)

**Task #5**: Create Projects list page

**Task #6**: Create CreateProjectModal component

**Task #7**: Create ProjectDetail page

**Task #8**: Create DocumentDetail page

**Task #9**: Update routing in App.tsx

**Task #10**: Update DocumentUploader to accept projectId prop

**Task #11**: Test complete navigation flow with browser tools

---

## Design System Requirements

**CRITICAL**: Follow the established design system:

### Color Palette
- Primary: Blue (`bg-blue-600`, `text-blue-600`)
- Gray scale: `gray-50`, `gray-100`, `gray-200`, etc.
- Status colors: Yellow (pending), Blue (processing), Green (completed), Red (failed)

### Typography
- Page titles: `text-3xl font-bold`
- Section headings: `text-xl font-semibold`
- Card titles: `text-lg font-medium`
- Body text: `text-sm` or `text-base`
- Muted text: `text-gray-600`

### Spacing
- Container padding: `px-4 py-6`
- Card padding: `p-3` or `p-4`
- Grid gaps: `gap-4` or `gap-6`
- Section spacing: `space-y-4` or `space-y-6`

### Components
- Use shadcn/ui components exclusively
- Button variants: `default`, `outline`, `ghost`
- Card composition: `Card` → `CardHeader` → `CardTitle` + `CardDescription` → `CardContent`
- Always pair `Label` with form inputs using `htmlFor`

---

## Testing with Cursor Browser Tools

**CRITICAL**: Use Cursor's built-in browser tools for testing. Do NOT create separate test files.

### Quick Testing Steps

1. **Start services**:
   ```bash
   cd docker && docker compose down -v  # Fresh start
   cd docker && docker compose up -d
   ```

2. **Test with browser tools**:
   - `browser_navigate("http://localhost:5173")`
   - Should redirect to `/projects`
   - `browser_snapshot()` to inspect UI
   
3. **Test project creation**:
   - `browser_click()` on "Create Project" button
   - `browser_type()` to fill form fields
   - `browser_click()` to submit
   - Verify navigation to project detail page

4. **Test document upload**:
   - On project detail page, click "Upload Documents"
   - Upload test PDF from `tests/` folder
   - Wait for processing
   - Verify document appears

5. **Test navigation flow**:
   - Click document card → Document detail page
   - Click "Open Takeoff" on page → TakeoffViewer opens
   - Click "Back" → Returns to document page
   - Use breadcrumbs to navigate up

6. **Verify checklist** (see spec lines for complete list):
   - [ ] Projects list loads and displays
   - [ ] Create project modal works
   - [ ] Project detail page shows documents
   - [ ] Document detail page shows pages
   - [ ] "Open Takeoff" navigates to TakeoffViewer
   - [ ] Breadcrumbs work correctly
   - [ ] Search/filter works on projects page
   - [ ] Empty states display properly

**Full testing workflow**: See spec file Task 0.11 for complete testing steps

---

## User Workflows

### Workflow 1: New User Creates First Project
```
1. Open app → Lands on /projects (empty state)
2. Click "Create Project"
3. Fill form (name, client, address)
4. Submit → Navigate to project detail
5. Click "Upload Documents"
6. Upload PDF → Wait for processing
7. Click document → See pages
8. Click "Open Takeoff" → TakeoffViewer opens
```

### Workflow 2: Returning User
```
1. Open app → See grid of projects
2. Search for project by name
3. Click project → See documents
4. Click document → See pages
5. Continue working on takeoffs
```

---

## Success Criteria

- [ ] **Task #0 completed**: Spec file read and understood
- [ ] All 4 pages created **exactly from spec** (NO improvisation)
- [ ] All reusable components created
- [ ] Navigation components work correctly
- [ ] Routing configured properly
- [ ] Projects list loads and displays
- [ ] Create project modal works
- [ ] Project detail page shows documents
- [ ] Document detail page shows pages
- [ ] "Open Takeoff" navigates to TakeoffViewer
- [ ] Breadcrumbs update correctly
- [ ] Search/filter works
- [ ] Empty states display
- [ ] No TypeScript compilation errors
- [ ] Frontend container rebuilds successfully

---

## Critical Warnings

⚠️ **DO NOT improvise code** - Copy EXACTLY from the spec file  
⚠️ **DO NOT skip components** - Build all reusable components first  
⚠️ **DO NOT create test files** - Use Cursor's browser tools  
⚠️ **DO reference the spec constantly** - When in doubt, check the spec  
⚠️ **DO include Task #0 in your task list** - Shows you read the spec  
⚠️ **DO rebuild the frontend container** - Changes won't appear otherwise  

---

## Common Pitfalls (see spec for details)

1. **Forgetting to rebuild container**: Changes won't appear in browser
2. **Not passing projectId**: Document upload needs project context
3. **Missing breadcrumb data**: Need to fetch parent entities
4. **TypeScript strict mode**: All props need explicit types
5. **React Query cache**: Invalidate queries after mutations
6. **Route params**: Properly type useParams hooks
7. **Empty states**: Handle loading and empty data states

---

## Questions to Ask Before Starting

If anything is unclear about the existing codebase:
- Current API endpoint structure
- Existing type definitions location
- Environment variables for API base URL
- Document upload implementation details

---

## Docker Workflow (CRITICAL)

### Starting Development

```bash
# Navigate to docker directory
cd D:\Repos\takeoff-automation\docker

# Start all services (API, frontend, database, redis, minio, worker)
docker compose up -d

# Check service status
docker compose ps

# View logs
docker compose logs -f frontend  # Frontend logs
docker compose logs -f api       # Backend logs
```

### Making Code Changes

**Frontend changes:**
1. Edit files in `frontend/src/` directory
2. Changes are hot-reloaded automatically (Vite HMR)
3. If you add NEW dependencies or change package.json:
   ```bash
   cd docker
   docker compose down frontend
   docker compose up -d --build frontend
   ```

**NEVER run `npm install` locally - always rebuild container!**

### Installing New Packages

```bash
# WRONG ❌ - Do NOT do this
cd frontend && npm install package-name

# CORRECT ✅ - Add to package.json, then rebuild
# 1. Edit frontend/package.json to add dependency
# 2. Rebuild container:
cd docker
docker compose up -d --build frontend
```

### Testing Changes

```bash
# Frontend runs at: http://localhost:5173
# Backend API at: http://localhost:8000
# API docs at: http://localhost:8000/docs

# Use Cursor's browser tools to test:
browser_navigate("http://localhost:5173")
browser_snapshot()
browser_click()
```

### Troubleshooting

**Issue: Changes not appearing**
```bash
# Rebuild frontend container
cd docker
docker compose down frontend
docker compose up -d --build frontend
```

**Issue: TypeScript errors**
```bash
# Check compilation in container
docker compose exec frontend npm run build
```

**Issue: Port conflicts**
```bash
# Stop all containers
docker compose down

# Remove volumes (fresh start)
docker compose down -v
```

## Expected Completion Time

- Type definitions & API client: 15-20 minutes
- Reusable components: 30-45 minutes
- Pages (Projects, ProjectDetail, DocumentDetail): 60-90 minutes
- Navigation components: 15-20 minutes
- Routing & integration: 15-20 minutes
- **Container rebuild**: 5-10 minutes
- Testing & bug fixes: 30-45 minutes
- **Total: 3-4 hours**

---

## After Completion

Once Phase 0 is complete, you'll have:
- ✅ Complete project management interface
- ✅ Document management within projects
- ✅ Proper navigation throughout the app
- ✅ Foundation for all other features

Next phases can build on this:
- **Phase 3B**: Add conditions management to projects
- **Phase 4A**: Integrate AI takeoff generation
- **Phase 5A**: Add export functionality

---

**Ready to start?** 

1. Read the spec file first (`@plans/00-APPLICATION-INTERFACE.md`)
2. Create your task list with Task #0
3. Implement each component sequentially
4. Reference the spec constantly - it has ALL the code you need
5. Test with browser tools
6. Rebuild the frontend container
7. Verify the complete navigation flow

Good luck! 🚀
