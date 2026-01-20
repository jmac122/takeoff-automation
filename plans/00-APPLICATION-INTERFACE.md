# Phase 0: Application Interface & Project Management
## Core User Interface for Project and Document Management

> **Duration**: 1-2 weeks  
> **Prerequisites**: Phase 0 (Project Setup) complete  
> **Outcome**: Full-featured application interface for managing projects, documents, and navigation

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

**What's Missing:**
- Projects list page
- Project detail page
- Create project modal
- Proper navigation/header
- Document management within projects
- Breadcrumb navigation

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

### Task 0.1: Projects List Page

**File:** `frontend/src/pages/Projects.tsx`

**Features:**
- Grid layout of project cards (responsive: 1-2-3-4 columns)
- Search bar to filter by name or client
- "Create Project" button in header
- Empty state when no projects
- Loading state while fetching
- Click project card → Navigate to `/projects/:projectId`

**API Integration:**
```typescript
// Fetch all projects
const { data: projects, isLoading } = useQuery({
  queryKey: ['projects'],
  queryFn: async () => {
    const response = await apiClient.get('/projects');
    return response.data.projects;
  },
});
```

**Project Card Data:**
```typescript
interface ProjectCard {
  id: string;
  name: string;
  description?: string;
  client_name?: string;
  project_address?: string;
  document_count: number;
  created_at: string;
  updated_at: string;
}
```

**Layout:**
```tsx
<div className="container mx-auto px-4 py-6">
  {/* Header */}
  <div className="flex items-center justify-between mb-6">
    <div>
      <h1 className="text-3xl font-bold">Projects</h1>
      <p className="text-gray-600">Manage your construction takeoff projects</p>
    </div>
    <Button onClick={() => setShowCreateModal(true)}>
      <Plus className="w-4 h-4 mr-2" />
      Create Project
    </Button>
  </div>

  {/* Search */}
  <div className="mb-6">
    <Input
      placeholder="Search projects by name or client..."
      value={searchTerm}
      onChange={(e) => setSearchTerm(e.target.value)}
      className="max-w-md"
    />
  </div>

  {/* Projects Grid */}
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
    {filteredProjects.map((project) => (
      <ProjectCard key={project.id} project={project} />
    ))}
  </div>
</div>
```

---

### Task 0.2: Create Project Modal

**File:** `frontend/src/components/project/CreateProjectModal.tsx`

**Features:**
- Modal dialog with form
- Fields: name (required), description, client_name, project_address
- Form validation
- Submit → POST to `/api/v1/projects`
- Success → Close modal, refetch projects, navigate to new project

**Form Schema:**
```typescript
interface CreateProjectForm {
  name: string;              // Required, max 200 chars
  description?: string;      // Optional, max 1000 chars
  client_name?: string;      // Optional, max 200 chars
  project_address?: string;  // Optional, max 500 chars
}
```

**Implementation:**
```tsx
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';

export function CreateProjectModal({ open, onClose }: CreateProjectModalProps) {
  const [formData, setFormData] = useState<CreateProjectForm>({
    name: '',
    description: '',
    client_name: '',
    project_address: '',
  });

  const createMutation = useMutation({
    mutationFn: async (data: CreateProjectForm) => {
      const response = await apiClient.post('/projects', data);
      return response.data;
    },
    onSuccess: (newProject) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      onClose();
      navigate(`/projects/${newProject.id}`);
    },
  });

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Create New Project</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="name">Project Name *</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
              maxLength={200}
            />
          </div>
          
          <div>
            <Label htmlFor="client_name">Client Name</Label>
            <Input
              id="client_name"
              value={formData.client_name}
              onChange={(e) => setFormData({ ...formData, client_name: e.target.value })}
              maxLength={200}
            />
          </div>

          <div>
            <Label htmlFor="project_address">Project Address</Label>
            <Input
              id="project_address"
              value={formData.project_address}
              onChange={(e) => setFormData({ ...formData, project_address: e.target.value })}
              maxLength={500}
            />
          </div>

          <div>
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={3}
              maxLength={1000}
            />
          </div>

          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={createMutation.isPending}>
              {createMutation.isPending ? 'Creating...' : 'Create Project'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
```

---

### Task 0.3: Project Detail Page

**File:** `frontend/src/pages/ProjectDetail.tsx`

**Features:**
- Breadcrumb navigation: Projects > [Project Name]
- Project header with name, client, address
- Edit project button
- Document grid showing all documents in project
- Upload document button
- Empty state when no documents
- Click document → Navigate to `/projects/:projectId/documents/:documentId`

**API Integration:**
```typescript
// Fetch project details
const { data: project } = useQuery({
  queryKey: ['project', projectId],
  queryFn: async () => {
    const response = await apiClient.get(`/projects/${projectId}`);
    return response.data;
  },
});

// Fetch documents for project
const { data: documents } = useQuery({
  queryKey: ['documents', projectId],
  queryFn: async () => {
    const response = await apiClient.get(`/projects/${projectId}/documents`);
    return response.data.documents;
  },
});
```

**Layout:**
```tsx
<div className="container mx-auto px-4 py-6">
  {/* Breadcrumbs */}
  <Breadcrumbs items={[
    { label: 'Projects', href: '/projects' },
    { label: project.name, href: `/projects/${project.id}` },
  ]} />

  {/* Project Header */}
  <div className="flex items-start justify-between mb-6 mt-4">
    <div>
      <h1 className="text-3xl font-bold mb-2">{project.name}</h1>
      {project.client_name && (
        <p className="text-lg text-gray-600">Client: {project.client_name}</p>
      )}
      {project.project_address && (
        <p className="text-sm text-gray-500">{project.project_address}</p>
      )}
      {project.description && (
        <p className="text-sm text-gray-600 mt-2">{project.description}</p>
      )}
    </div>
    <div className="flex gap-2">
      <Button variant="outline" onClick={() => setShowEditModal(true)}>
        <Edit className="w-4 h-4 mr-2" />
        Edit Project
      </Button>
      <Button onClick={() => setShowUploadModal(true)}>
        <Upload className="w-4 h-4 mr-2" />
        Upload Documents
      </Button>
    </div>
  </div>

  {/* Documents Section */}
  <Card>
    <CardHeader>
      <CardTitle>Documents ({documents?.length || 0})</CardTitle>
      <CardDescription>Plan sets and drawings for this project</CardDescription>
    </CardHeader>
    <CardContent>
      {documents?.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="No documents yet"
          description="Upload your first plan set to get started"
          action={
            <Button onClick={() => setShowUploadModal(true)}>
              Upload Documents
            </Button>
          }
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {documents.map((doc) => (
            <DocumentCard key={doc.id} document={doc} projectId={projectId} />
          ))}
        </div>
      )}
    </CardContent>
  </Card>
</div>
```

---

### Task 0.4: Document Detail Page

**File:** `frontend/src/pages/DocumentDetail.tsx`

**Features:**
- Breadcrumb navigation: Projects > [Project] > [Document]
- Document header with filename, page count, status
- Page grid showing all pages with thumbnails
- "Open Takeoff" button on each page
- Processing status indicator
- Classify pages button (Phase 2A integration)

**API Integration:**
```typescript
// Fetch document details
const { data: document } = useQuery({
  queryKey: ['document', documentId],
  queryFn: async () => {
    const response = await apiClient.get(`/documents/${documentId}`);
    return response.data;
  },
});

// Fetch pages for document
const { data: pages } = useQuery({
  queryKey: ['pages', documentId],
  queryFn: async () => {
    const response = await apiClient.get(`/documents/${documentId}/pages`);
    return response.data.pages;
  },
  refetchInterval: document?.status === 'processing' ? 3000 : false,
});
```

**Layout:**
```tsx
<div className="container mx-auto px-4 py-6">
  {/* Breadcrumbs */}
  <Breadcrumbs items={[
    { label: 'Projects', href: '/projects' },
    { label: project.name, href: `/projects/${projectId}` },
    { label: document.original_filename, href: `/projects/${projectId}/documents/${documentId}` },
  ]} />

  {/* Document Header */}
  <div className="flex items-start justify-between mb-6 mt-4">
    <div>
      <h1 className="text-3xl font-bold mb-2">{document.original_filename}</h1>
      <div className="flex items-center gap-4 text-sm text-gray-600">
        <span>{document.page_count} pages</span>
        <span>•</span>
        <StatusBadge status={document.status} />
        <span>•</span>
        <span>Uploaded {formatDate(document.created_at)}</span>
      </div>
    </div>
    <div className="flex gap-2">
      <Button variant="outline" onClick={() => handleClassifyPages()}>
        <Sparkles className="w-4 h-4 mr-2" />
        Classify Pages
      </Button>
      <Button variant="outline" onClick={() => handleDownload()}>
        <Download className="w-4 h-4 mr-2" />
        Download
      </Button>
    </div>
  </div>

  {/* Pages Grid */}
  <Card>
    <CardHeader>
      <CardTitle>Pages</CardTitle>
      <CardDescription>Click a page to view details or open the takeoff viewer</CardDescription>
    </CardHeader>
    <CardContent>
      {document.status === 'processing' ? (
        <Alert>
          <AlertDescription>
            Document is being processed. Pages will appear shortly...
          </AlertDescription>
        </Alert>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
          {pages.map((page) => (
            <PageCard
              key={page.id}
              page={page}
              documentId={documentId}
              projectId={projectId}
            />
          ))}
        </div>
      )}
    </CardContent>
  </Card>
</div>
```

---

### Task 0.5: Navigation Components

**File:** `frontend/src/components/layout/Header.tsx`

**Features:**
- Sticky header at top of page
- App logo/title
- Breadcrumb navigation
- User menu (future)
- Consistent across all pages

**Implementation:**
```tsx
import { useLocation, Link } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';

export function Header() {
  return (
    <header className="border-b bg-white sticky top-0 z-50 shadow-sm">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link to="/projects" className="flex items-center gap-2">
              <h1 className="text-2xl font-bold text-primary">ForgeX Takeoffs</h1>
            </Link>
          </div>
        </div>
      </div>
    </header>
  );
}
```

**File:** `frontend/src/components/layout/Breadcrumbs.tsx`

```tsx
import { Link } from 'react-router-dom';
import { ChevronRight } from 'lucide-react';

interface BreadcrumbItem {
  label: string;
  href: string;
}

interface BreadcrumbsProps {
  items: BreadcrumbItem[];
}

export function Breadcrumbs({ items }: BreadcrumbsProps) {
  return (
    <nav className="flex items-center gap-2 text-sm text-gray-600">
      {items.map((item, index) => (
        <div key={item.href} className="flex items-center gap-2">
          {index > 0 && <ChevronRight className="w-4 h-4" />}
          {index === items.length - 1 ? (
            <span className="font-medium text-gray-900">{item.label}</span>
          ) : (
            <Link to={item.href} className="hover:text-primary transition-colors">
              {item.label}
            </Link>
          )}
        </div>
      ))}
    </nav>
  );
}
```

---

### Task 0.6: Reusable Components

**File:** `frontend/src/components/project/ProjectCard.tsx`

```tsx
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useNavigate } from 'react-router-dom';
import { FileText, Calendar } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface ProjectCardProps {
  project: {
    id: string;
    name: string;
    description?: string;
    client_name?: string;
    document_count: number;
    created_at: string;
  };
}

export function ProjectCard({ project }: ProjectCardProps) {
  const navigate = useNavigate();

  return (
    <Card
      className="hover:shadow-lg transition-shadow cursor-pointer"
      onClick={() => navigate(`/projects/${project.id}`)}
    >
      <CardHeader>
        <CardTitle className="text-xl truncate">{project.name}</CardTitle>
        {project.client_name && (
          <CardDescription className="truncate">{project.client_name}</CardDescription>
        )}
      </CardHeader>
      <CardContent>
        <div className="space-y-2 text-sm text-gray-600">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4" />
            <span>{project.document_count} document{project.document_count !== 1 ? 's' : ''}</span>
          </div>
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4" />
            <span>Created {formatDistanceToNow(new Date(project.created_at), { addSuffix: true })}</span>
          </div>
        </div>
        {project.description && (
          <p className="text-sm text-gray-500 mt-3 line-clamp-2">{project.description}</p>
        )}
      </CardContent>
    </Card>
  );
}
```

**File:** `frontend/src/components/document/DocumentCard.tsx`

```tsx
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useNavigate } from 'react-router-dom';
import { FileText, Calendar } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface DocumentCardProps {
  document: {
    id: string;
    original_filename: string;
    page_count: number | null;
    status: string;
    created_at: string;
  };
  projectId: string;
}

export function DocumentCard({ document, projectId }: DocumentCardProps) {
  const navigate = useNavigate();

  const statusColors = {
    pending: 'bg-yellow-100 text-yellow-800',
    processing: 'bg-blue-100 text-blue-800',
    completed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
  };

  return (
    <Card
      className="hover:shadow-lg transition-shadow cursor-pointer"
      onClick={() => navigate(`/projects/${projectId}/documents/${document.id}`)}
    >
      <CardHeader>
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-base truncate flex-1">{document.original_filename}</CardTitle>
          <Badge className={statusColors[document.status] || 'bg-gray-100 text-gray-800'}>
            {document.status}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2 text-sm text-gray-600">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4" />
            <span>{document.page_count || 0} pages</span>
          </div>
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4" />
            <span>{formatDistanceToNow(new Date(document.created_at), { addSuffix: true })}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
```

**File:** `frontend/src/components/document/PageCard.tsx`

```tsx
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';
import { Pencil } from 'lucide-react';

interface PageCardProps {
  page: {
    id: string;
    page_number: number;
    classification?: string | null;
    scale_calibrated: boolean;
    thumbnail_url?: string | null;
  };
  documentId: string;
  projectId: string;
}

export function PageCard({ page, documentId, projectId }: PageCardProps) {
  const navigate = useNavigate();

  return (
    <div className="border rounded-lg p-3 hover:shadow-md transition-shadow">
      {/* Thumbnail */}
      <div className="aspect-[8.5/11] bg-gray-100 rounded mb-2 overflow-hidden">
        {page.thumbnail_url ? (
          <img
            src={page.thumbnail_url}
            alt={`Page ${page.page_number}`}
            className="w-full h-full object-contain"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-400">
            No preview
          </div>
        )}
      </div>

      {/* Page Info */}
      <div className="space-y-2">
        <div>
          <p className="font-medium text-sm">Page {page.page_number}</p>
          {page.classification && (
            <p className="text-xs text-gray-600 truncate">{page.classification}</p>
          )}
          {page.scale_calibrated && (
            <Badge variant="secondary" className="mt-1 text-xs">Calibrated</Badge>
          )}
        </div>

        {/* Open Takeoff Button */}
        <Button
          size="sm"
          variant="outline"
          className="w-full text-xs"
          onClick={() => navigate(`/documents/${documentId}/pages/${page.id}`)}
        >
          <Pencil className="w-3 h-3 mr-1" />
          Open Takeoff
        </Button>
      </div>
    </div>
  );
}
```

**File:** `frontend/src/components/common/EmptyState.tsx`

```tsx
import { LucideIcon } from 'lucide-react';

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: React.ReactNode;
}

export function EmptyState({ icon: Icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <Icon className="w-16 h-16 text-gray-400 mb-4" />
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      <p className="text-gray-600 mb-4 max-w-md">{description}</p>
      {action}
    </div>
  );
}
```

---

### Task 0.7: Update Routing

**File:** `frontend/src/App.tsx`

Update routing to include new pages:

```tsx
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { Header } from "./components/layout/Header";
import Projects from "./pages/Projects";
import ProjectDetail from "./pages/ProjectDetail";
import DocumentDetail from "./pages/DocumentDetail";
import { TakeoffViewer } from "./pages/TakeoffViewer";
import "./App.css";

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Header />
        <main>
          <Routes>
            {/* Redirect root to projects */}
            <Route path="/" element={<Navigate to="/projects" replace />} />
            
            {/* Projects */}
            <Route path="/projects" element={<Projects />} />
            <Route path="/projects/:projectId" element={<ProjectDetail />} />
            
            {/* Documents */}
            <Route path="/projects/:projectId/documents/:documentId" element={<DocumentDetail />} />
            
            {/* Takeoff Viewer */}
            <Route path="/documents/:documentId/pages/:pageId" element={<TakeoffViewer />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
```

---

### Task 0.8: Update Document Uploader

**File:** `frontend/src/components/document/DocumentUploader.tsx`

Update the existing DocumentUploader to work within a project context:

```tsx
// Add projectId prop
interface DocumentUploaderProps {
  projectId: string;
  onUploadComplete?: (documentId: string) => void;
}

// Update upload endpoint
const uploadMutation = useMutation({
  mutationFn: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('project_id', projectId);
    
    const response = await axios.post('/api/v1/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
  onSuccess: (data) => {
    queryClient.invalidateQueries({ queryKey: ['documents', projectId] });
    onUploadComplete?.(data.document_id);
  },
});
```

---

### Task 0.9: API Client Updates

**File:** `frontend/src/api/projects.ts`

Create API client functions for projects:

```typescript
import { apiClient } from './client';

export interface Project {
  id: string;
  name: string;
  description?: string;
  client_name?: string;
  project_address?: string;
  document_count: number;
  created_at: string;
  updated_at: string;
}

export interface CreateProjectRequest {
  name: string;
  description?: string;
  client_name?: string;
  project_address?: string;
}

export const projectsApi = {
  // List all projects
  list: async () => {
    const response = await apiClient.get<{ projects: Project[] }>('/projects');
    return response.data;
  },

  // Get single project
  get: async (projectId: string) => {
    const response = await apiClient.get<Project>(`/projects/${projectId}`);
    return response.data;
  },

  // Create project
  create: async (data: CreateProjectRequest) => {
    const response = await apiClient.post<Project>('/projects', data);
    return response.data;
  },

  // Update project
  update: async (projectId: string, data: Partial<CreateProjectRequest>) => {
    const response = await apiClient.put<Project>(`/projects/${projectId}`, data);
    return response.data;
  },

  // Delete project
  delete: async (projectId: string) => {
    await apiClient.delete(`/projects/${projectId}`);
  },

  // Get documents for project
  getDocuments: async (projectId: string) => {
    const response = await apiClient.get(`/projects/${projectId}/documents`);
    return response.data;
  },
};
```

---

### Task 0.10: Type Definitions

**File:** `frontend/src/types/index.ts`

Add/update type definitions:

```typescript
// Project types
export interface Project {
  id: string;
  name: string;
  description?: string | null;
  client_name?: string | null;
  project_address?: string | null;
  document_count: number;
  created_at: string;
  updated_at: string;
}

export interface CreateProjectRequest {
  name: string;
  description?: string;
  client_name?: string;
  project_address?: string;
}

// Update Document type to include project relationship
export interface Document {
  id: string;
  project_id: string;
  filename: string;
  original_filename: string;
  file_type: string;
  file_size: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  page_count?: number | null;
  processing_error?: string | null;
  created_at: string;
  updated_at: string;
  pages?: PageSummary[];
}
```

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

## Testing Workflow

### Manual Testing Steps

1. **Start with empty database:**
   ```bash
   cd docker && docker compose down -v
   docker compose up -d
   ```

2. **Test project creation:**
   - Open http://localhost:5173
   - Should redirect to /projects
   - See empty state
   - Click "Create Project"
   - Fill form and submit
   - Verify navigation to project detail

3. **Test document upload:**
   - On project detail page, click "Upload Documents"
   - Upload a test PDF from `tests/` folder
   - Verify document appears in grid
   - Wait for processing to complete

4. **Test navigation:**
   - Click document card
   - Verify pages appear
   - Click "Open Takeoff" on a page
   - Verify TakeoffViewer opens
   - Click "Back" button
   - Verify return to document page

5. **Test breadcrumbs:**
   - Navigate deep: Projects > Project > Document
   - Click each breadcrumb level
   - Verify correct navigation

6. **Test search/filter:**
   - Create multiple projects
   - Use search bar on projects page
   - Verify filtering works

---

## Common Issues & Solutions

### Issue: Projects not loading
**Solution:** Check backend API is running and `/api/v1/projects` endpoint works:
```bash
curl http://localhost:8000/api/v1/projects
```

### Issue: Document upload fails
**Solution:** Verify project_id is being sent in FormData and backend accepts it

### Issue: Breadcrumbs show wrong path
**Solution:** Ensure all parent data is fetched (project name for document page, etc.)

### Issue: TypeScript errors on navigation
**Solution:** Ensure all route params are properly typed in useParams hooks

### Issue: Images not loading
**Solution:** Check CORS settings and MinIO URL configuration

---

## Next Steps

After completing Phase 0 (Application Interface):

1. **Phase 3B (Condition Management)** - Add conditions UI to projects
2. **Phase 4A (AI Takeoff Generation)** - Integrate AI measurement generation
3. **Phase 4B (Review Interface)** - Add measurement editing capabilities
4. **Phase 5A (Export System)** - Add export functionality to projects

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
