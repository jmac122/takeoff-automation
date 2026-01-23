# Phase 0: Application Interface & Project Management
## Core User Interface for Project and Document Management

> **Duration**: 1-2 weeks  
> **Prerequisites**: Phase 0 (Project Setup) complete  
> **Outcome**: Full-featured application interface for managing projects, documents, and navigation

---

## ⚠️ CRITICAL: Docker-Based Development

**ALL development happens in Docker containers. NEVER install packages locally.**

This project uses Docker Compose to orchestrate all services. The frontend, backend, database, Redis, MinIO, and Celery worker all run in separate containers.

### Quick Start

```bash
# Start all services
cd docker && docker compose up -d

# View status
docker compose ps

# View logs
docker compose logs -f frontend
```

### Key Commands

```bash
# Rebuild frontend after package.json changes
docker compose down frontend
docker compose up -d --build frontend

# Fresh start (removes all data)
docker compose down -v
docker compose up -d

# Stop all services
docker compose down
```

**Frontend URL:** http://localhost:5173  
**Backend API:** http://localhost:8000  
**API Docs:** http://localhost:8000/docs  

---

## Overview

This phase implements the **foundational user interface** that was missing from the original implementation plan. It provides a complete project management system that allows users to:

- View all projects in a grid/list
- Create new projects with metadata
- Navigate into projects to see documents
- Upload documents to specific projects
- Browse pages within documents
- Navigate to the TakeoffViewer for measurements

**This should have been Phase 0.5** - built before the technical pipeline. It creates the "application shell" that ties all other phases together.

---

## Context for LLM Assistant

You are building the **main application interface** for a construction takeoff platform. Currently, the app has a single "Dashboard" page that's just a testing interface for Phase 2A (page classification). 

Users need a proper application where they can:
1. See all their projects
2. Create new projects
3. Click into a project to see its documents
4. Upload documents to a project
5. View pages within documents
6. Open the TakeoffViewer to create measurements

### Current State

**What Exists:**
- Backend API endpoints for projects (`/api/v1/projects`)
- Database models for Project, Document, Page
- TakeoffViewer page (Phase 3A+) at `/documents/:documentId/pages/:pageId`
- Basic Dashboard with document upload (testing interface only)
- Docker-based development environment (ALL services run in containers)
- Design system documentation (`@docs/design/DESIGN-SYSTEM.md`)
- Component library documentation (`@docs/design/COMPONENT_LIBRARY.md`)

**What's Missing:**
- Projects list page
- Project detail page
- Create project modal
- Proper navigation/header
- Document management within projects
- Breadcrumb navigation

### Tech Stack & Infrastructure

**⚠️ CRITICAL: All development happens in Docker containers**

```
Project Structure:
takeoff-automation/
├── docker/
│   ├── docker-compose.yml       # Orchestrates all services
│   ├── Dockerfile.frontend      # React app container
│   ├── Dockerfile.api          # FastAPI container
│   └── Dockerfile.worker       # Celery worker container
├── frontend/                    # React source (mounted in container)
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
├── backend/                     # Python source (mounted in container)
│   ├── app/
│   ├── requirements.txt
│   └── alembic/
└── tests/                      # Test files (PDFs, etc.)
```

**Services (all in Docker):**
- **frontend**: React 18 + Vite (port 5173)
- **api**: FastAPI + Python 3.11 (port 8000)
- **db**: PostgreSQL 15 (port 5432)
- **redis**: Redis 7 (port 6379)
- **minio**: S3-compatible storage (port 9000)
- **worker**: Celery background tasks

**Frontend Stack:**
- React 18 + TypeScript (strict mode)
- Vite for build tooling
- React Router for navigation
- TanStack Query (React Query) for data fetching
- shadcn/ui components (already installed)
- Tailwind CSS for styling
- Lucide React for icons
- Konva.js for canvas drawing

**NEVER install npm packages locally - always rebuild Docker container!**

---

## User Workflows

### Workflow 1: New User Creates First Project

```
1. User opens app → Lands on Projects page (empty state)
2. User clicks "Create Project" button
3. Modal opens with form (name, description, client, address)
4. User fills form and clicks "Create"
5. Project card appears in grid
6. User clicks project card → Navigates to Project Detail page
7. User clicks "Upload Documents" → Uploads PDF
8. Document appears in grid with page count
9. User clicks document → Sees page thumbnails
10. User clicks "Open Takeoff" on a page → Opens TakeoffViewer
```

### Workflow 2: Returning User Manages Projects

```
1. User opens app → Sees grid of all projects
2. User searches/filters projects by name or client
3. User clicks a project → Sees all documents in that project
4. User uploads additional documents to project
5. User navigates between projects using breadcrumbs
6. User edits project details (name, description, etc.)
```

### Workflow 3: Working on Takeoffs

```
1. User navigates to project → document → page
2. User clicks "Open Takeoff" on page card
3. TakeoffViewer opens with drawing tools
4. User creates measurements
5. User clicks "Back" → Returns to document page
6. User continues to next page
```

---

## Design System Requirements

**CRITICAL:** Follow the established design system from `@docs/design/DESIGN-SYSTEM.md` and `@docs/design/COMPONENT_LIBRARY.md`.

### MANDATORY Reading Before Implementation

**1. Read `@docs/design/DESIGN-SYSTEM.md` (870 lines)**
   - Complete color system with HSL tokens
   - Measurement colors for drawing (`MEASUREMENT_COLORS`)
   - Typography scale and usage rules
   - Spacing patterns and tokens
   - Component patterns and layouts
   - Accessibility checklist
   - File organization

**2. Read `@docs/design/COMPONENT_LIBRARY.md` (1099 lines)**
   - All shadcn/ui components with full examples
   - Button variants and sizes
   - Card composition pattern
   - Dialog/Modal patterns
   - Form components (Input, Label, Select)
   - Badge, Skeleton, Alert, Progress
   - Common patterns (forms, loading, errors)
   - Utility functions (`cn()`)

**Key Principles:**
- ✅ Use semantic color tokens (e.g., `bg-primary`, `text-muted-foreground`)
- ✅ Import components from `@/components/ui/`
- ✅ Use Lucide React icons exclusively
- ✅ Follow typography scale (`text-sm`, `text-lg`, `text-2xl`)
- ✅ Use consistent spacing (`gap-2`, `gap-4`, `p-4`)
- ❌ NEVER hardcode colors (use design tokens)
- ❌ NEVER use raw hex values
- ❌ NEVER import from external UI libraries

### Key UI Patterns

**Project Cards:**
```tsx
<Card className="hover:shadow-lg transition-shadow cursor-pointer">
  <CardHeader>
    <CardTitle className="text-xl">{project.name}</CardTitle>
    <CardDescription>{project.client_name}</CardDescription>
  </CardHeader>
  <CardContent>
    <div className="space-y-2 text-sm text-gray-600">
      <p>{project.document_count} documents</p>
      <p>Created {formatDate(project.created_at)}</p>
    </div>
  </CardContent>
</Card>
```

**Navigation Header:**
```tsx
<header className="border-b bg-white sticky top-0 z-50">
  <div className="container mx-auto px-4 py-4">
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-4">
        <h1 className="text-2xl font-bold">ForgeX Takeoffs</h1>
        <Breadcrumbs />
      </div>
      <div className="flex items-center gap-2">
        <Button>Create Project</Button>
      </div>
    </div>
  </div>
</header>
```

**Empty States:**
```tsx
<div className="flex flex-col items-center justify-center py-12 text-center">
  <FolderOpen className="w-16 h-16 text-gray-400 mb-4" />
  <h3 className="text-lg font-semibold mb-2">No projects yet</h3>
  <p className="text-gray-600 mb-4">Create your first project to get started</p>
  <Button onClick={onCreateProject}>Create Project</Button>
</div>
```

---

## Implementation Tasks

> **Note:** The implementation tasks (Tasks 0.1 through 0.11) remain unchanged from the original document. They cover:
> - Task 0.1: Projects List Page
> - Task 0.2: Create Project Modal
> - Task 0.3: Project Detail Page
> - Task 0.4: Document Detail Page
> - Task 0.5: Navigation Components
> - Task 0.6: Reusable Components
> - Task 0.7: Update Routing
> - Task 0.8: Update Document Uploader
> - Task 0.9: API Client Updates
> - Task 0.10: Type Definitions
> - Task 0.11: Final Integration & Testing

*[Full implementation task details preserved from original document - see original for complete code examples]*

---

## Verification Checklist

After completing all tasks, verify:

### Projects Page
- [ ] Projects list loads and displays all projects
- [ ] Empty state shows when no projects exist
- [ ] "Create Project" button opens modal
- [ ] Search bar filters projects by name/client
- [ ] Clicking project card navigates to project detail
- [ ] Project cards show document count and creation date

### Create Project Modal
- [ ] Modal opens and closes properly
- [ ] Form validation works (name required)
- [ ] Submit creates project via API
- [ ] Success navigates to new project page
- [ ] Error handling displays messages

### Project Detail Page
- [ ] Breadcrumbs show correct navigation path
- [ ] Project details display correctly
- [ ] Documents grid shows all documents
- [ ] Empty state shows when no documents
- [ ] "Upload Documents" button works
- [ ] Clicking document navigates to document detail

### Document Detail Page
- [ ] Breadcrumbs show correct path
- [ ] Document metadata displays correctly
- [ ] Pages grid shows all pages with thumbnails
- [ ] "Open Takeoff" button navigates to TakeoffViewer
- [ ] Processing status updates automatically
- [ ] "Classify Pages" button triggers classification

### Navigation
- [ ] Header appears on all pages
- [ ] Breadcrumbs update based on current route
- [ ] Back navigation works correctly
- [ ] URL structure is logical and clean

### Integration
- [ ] TakeoffViewer still works from new navigation
- [ ] Document upload integrates with projects
- [ ] All API endpoints connect properly
- [ ] No TypeScript compilation errors
- [ ] No console errors in browser

---

## Docker Development Workflow

### Starting Development Environment

```bash
# Navigate to docker directory
cd D:\Repos\takeoff-automation\docker

# Start all services
docker compose up -d

# Verify services are running
docker compose ps

# View logs (optional)
docker compose logs -f frontend
docker compose logs -f api
```

**Services will be available at:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Making Code Changes

**Frontend changes (automatic hot reload):**
1. Edit files in `frontend/src/` directory
2. Vite automatically reloads changes in browser
3. No rebuild needed for code changes

**Adding new npm packages:**
```bash
# 1. Edit frontend/package.json to add dependency
# 2. Rebuild frontend container:
cd docker
docker compose down frontend
docker compose up -d --build frontend
```

**⚠️ NEVER run `npm install` locally - always rebuild container!**

### Rebuilding Frontend Container

**When to rebuild:**
- After adding/removing npm packages
- After changing package.json
- After TypeScript configuration changes
- If hot reload stops working

**How to rebuild:**
```bash
cd docker
docker compose down frontend
docker compose up -d --build frontend
```

**Full rebuild (if issues persist):**
```bash
cd docker
docker compose down
docker compose up -d --build
```

### Verifying Changes

```bash
# Check TypeScript compilation
docker compose exec frontend npm run build

# Check for linter errors
docker compose exec frontend npm run lint

# View container logs
docker compose logs -f frontend
```

---

## Common Issues & Solutions

### Issue: Changes not appearing in browser
**Cause:** Frontend container not rebuilt after package changes  
**Solution:**
```bash
cd docker
docker compose down frontend
docker compose up -d --build frontend
```

### Issue: "Cannot find module" errors
**Cause:** New npm package not installed in container  
**Solution:**
1. Add package to `frontend/package.json`
2. Rebuild container (see above)
3. **DO NOT run `npm install` locally**

### Issue: Projects not loading
**Cause:** Backend API not running or database not initialized  
**Solution:**
```bash
# Check API is running
curl http://localhost:8000/api/v1/health

# Check all services
cd docker && docker compose ps

# View API logs
docker compose logs -f api
```

### Issue: Port already in use
**Cause:** Previous containers still running  
**Solution:**
```bash
cd docker
docker compose down
docker compose up -d
```

### Issue: TypeScript compilation errors
**Cause:** Type mismatches or missing imports  
**Solution:**
```bash
# Check compilation in container
docker compose exec frontend npm run build

# View detailed errors
docker compose logs frontend
```

### Issue: Document upload fails
**Cause:** project_id not sent or MinIO not running  
**Solution:**
1. Verify FormData includes project_id
2. Check MinIO container: `docker compose ps minio`
3. Check backend logs: `docker compose logs -f api`

### Issue: Breadcrumbs show wrong path
**Cause:** Parent data not fetched  
**Solution:** Ensure all parent entities are fetched (project name for document page, etc.)

### Issue: Images/thumbnails not loading
**Cause:** MinIO URL misconfigured or CORS issues  
**Solution:**
1. Check MinIO is running: `docker compose ps minio`
2. Verify MinIO URL in backend config
3. Check browser console for CORS errors

### Issue: Hot reload not working
**Cause:** Vite HMR connection lost  
**Solution:**
1. Refresh browser
2. Restart frontend container: `docker compose restart frontend`
3. Check no firewall blocking port 5173

---

## Next Steps

After completing Phase 0 (Application Interface):

1. **Phase 3B (Condition Management)** - Add conditions UI to projects
2. **Phase 3C (Assembly System)** - Cost estimation with material/labor/equipment components ← **NEW**
3. **Phase 4A (AI Takeoff Generation)** - Integrate AI measurement generation
4. **Phase 4B (Auto Count)** - Template matching for repetitive elements ← **NEW**
5. **Phase 4C (Review Interface Enhanced)** - Keyboard shortcuts, auto-accept, confidence filtering ← **ENHANCED**
6. **Phase 5A (Export System)** - Add export functionality to projects

---

## Notes for LLM Assistant

- **Follow existing patterns** from TakeoffViewer and Dashboard
- **Use shadcn/ui components** consistently
- **Implement proper loading states** for all async operations
- **Add error boundaries** for graceful error handling
- **Use React Query** for all data fetching
- **Follow TypeScript strict mode** - no `any` types
- **Add proper ARIA labels** for accessibility
- **Test navigation flows** thoroughly
- **Keep components small** and focused (SOLID principles)
- **Reuse components** where possible (DRY principle)
