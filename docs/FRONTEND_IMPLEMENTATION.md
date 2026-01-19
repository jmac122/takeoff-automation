# Frontend Implementation - Phase 1A: Document Ingestion

## Overview

The frontend implementation for Phase 1A provides a React-based user interface for document upload and management. Built with modern React patterns, TypeScript, and TailwindCSS, it offers drag-and-drop file uploads with progress tracking and real-time status updates.

## Technology Stack

### Core Technologies

- **React 18** - Component-based UI framework
- **TypeScript** - Type-safe JavaScript
- **Vite** - Fast build tool and dev server
- **TailwindCSS** - Utility-first CSS framework
- **React Query (TanStack)** - Data fetching and caching
- **Axios** - HTTP client for API calls
- **React Router** - Client-side routing (future use)

### Development Tools

- **ESLint** - Code linting
- **PostCSS** - CSS processing
- **Autoprefixer** - CSS vendor prefixing
- **TypeScript Compiler** - Type checking

## Project Structure

```
frontend/
├── public/
│   └── vite.svg
├── src/
│   ├── api/                 # API client and endpoints
│   │   ├── client.ts       # Axios configuration
│   │   └── documents.ts    # Document API functions
│   ├── components/         # Reusable UI components
│   │   └── document/       # Document-specific components
│   │       └── DocumentUploader.tsx
│   ├── hooks/              # Custom React hooks
│   ├── pages/              # Page components
│   │   └── Dashboard.tsx
│   ├── stores/             # State management (future)
│   ├── types/              # TypeScript type definitions
│   │   └── index.ts
│   ├── lib/                # Utilities
│   │   └── utils.ts       # Utility functions
│   ├── App.tsx            # Main app component
│   ├── App.css            # Global styles
│   ├── index.css          # CSS imports
│   └── main.tsx           # App entry point
├── package.json
├── tsconfig.json
├── tailwind.config.js
├── postcss.config.js
└── vite.config.ts
```

## Component Architecture

### DocumentUploader Component

The main component for file uploads with drag-and-drop functionality.

```tsx
interface DocumentUploaderProps {
  projectId: string;
  onUploadComplete?: () => void;
}

interface FileWithProgress {
  file: File;
  progress: number;
  status: 'pending' | 'uploading' | 'complete' | 'error';
  error?: string;
}
```

#### Key Features

1. **Drag-and-Drop Interface**
   - Visual feedback for drag states
   - File type validation
   - Multiple file support

2. **Progress Tracking**
   - Real-time upload progress
   - Individual file status
   - Error handling and display

3. **File Management**
   - Sequential upload processing
   - File removal before upload
   - Completed file cleanup

#### Implementation Details

```tsx
export function DocumentUploader({ projectId, onUploadComplete }: DocumentUploaderProps) {
  const [files, setFiles] = useState<FileWithProgress[]>([]);
  const queryClient = useQueryClient();

  // Upload mutation with React Query
  const uploadMutation = useMutation({
    mutationFn: async ({ file, index }: { file: File; index: number }) => {
      return uploadDocument(projectId, file, (progress) => {
        setFiles((prev) =>
          prev.map((f, i) =>
            i === index ? { ...f, progress: progress.percentage } : f
          )
        );
      });
    },
    onSuccess: (_, { index }) => {
      setFiles((prev) =>
        prev.map((f, i) =>
          i === index ? { ...f, status: 'complete', progress: 100 } : f
        )
      );
      queryClient.invalidateQueries({ queryKey: ['documents', projectId] });
    },
    onError: (error: Error, { index }) => {
      setFiles((prev) =>
        prev.map((f, i) =>
          i === index ? { ...f, status: 'error', error: error.message } : f
        )
      );
    },
  });

  // File selection handler
  const handleFileSelect = useCallback(
    async (event: React.ChangeEvent<HTMLInputElement>) => {
      const selectedFiles = Array.from(event.target.files || []);
      const newFiles: FileWithProgress[] = selectedFiles.map((file) => ({
        file,
        progress: 0,
        status: 'pending' as const,
      }));

      setFiles((prev) => [...prev, ...newFiles]);

      // Upload files sequentially
      const startIndex = files.length;
      for (let i = 0; i < selectedFiles.length; i++) {
        const index = startIndex + i;
        setFiles((prev) =>
          prev.map((f, idx) =>
            idx === index ? { ...f, status: 'uploading' } : f
          )
        );
        await uploadMutation.mutateAsync({ file: selectedFiles[i], index });
      }

      onUploadComplete?.();
    },
    [files.length, uploadMutation, onUploadComplete]
  );

  // Drag and drop handlers
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: handleFileSelect,
    accept: {
      'application/pdf': ['.pdf'],
      'image/tiff': ['.tiff', '.tif'],
    },
    multiple: true,
  });

  return (
    <div className="space-y-4">
      {/* Drop zone */}
      <div
        {...getRootProps()}
        className={cn(
          'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors',
          isDragActive
            ? 'border-primary bg-primary/5'
            : 'border-muted-foreground/25 hover:border-primary/50'
        )}
      >
        <input {...getInputProps()} />
        <Upload className="mx-auto h-12 w-12 text-muted-foreground" />
        <p className="mt-2 text-sm text-muted-foreground">
          {isDragActive
            ? 'Drop the files here...'
            : 'Drag & drop PDF or TIFF files here, or click to select'}
        </p>
        <p className="mt-1 text-xs text-muted-foreground">
          Supports PDF and multi-page TIFF files
        </p>
      </div>

      {/* File list */}
      {files.length > 0 && (
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <h4 className="text-sm font-medium">Uploads</h4>
            {files.some((f) => f.status === 'complete') && (
              <Button variant="ghost" size="sm" onClick={clearCompleted}>
                Clear completed
              </Button>
            )}
          </div>

          {files.map((f, index) => (
            <div
              key={index}
              className="flex items-center gap-3 p-3 bg-muted rounded-lg"
            >
              <File className="h-5 w-5 text-muted-foreground flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{f.file.name}</p>
                {f.status === 'uploading' && (
                  <Progress value={f.progress} className="h-1 mt-1" />
                )}
                {f.status === 'error' && (
                  <p className="text-xs text-destructive">{f.error}</p>
                )}
              </div>
              <div className="flex-shrink-0">
                {f.status === 'uploading' && (
                  <Loader2 className="h-4 w-4 animate-spin text-primary" />
                )}
                {f.status === 'complete' && (
                  <span className="text-xs text-green-600">Complete</span>
                )}
                {(f.status === 'pending' || f.status === 'error') && (
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6"
                    onClick={() => removeFile(index)}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

## API Integration

### Axios Configuration

```typescript
// src/api/client.ts
import axios from 'axios';

export const apiClient = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
});
```

### Document API Functions

```typescript
// src/api/documents.ts
export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}

export async function uploadDocument(
  projectId: string,
  file: File,
  onProgress?: (progress: UploadProgress) => void
): Promise<Document> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post<Document>(
    `/projects/${projectId}/documents`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          onProgress({
            loaded: progressEvent.loaded,
            total: progressEvent.total,
            percentage: Math.round((progressEvent.loaded * 100) / progressEvent.total),
          });
        }
      },
    }
  );

  return response.data;
}

export async function getDocument(documentId: string): Promise<Document> {
  const response = await apiClient.get<Document>(`/documents/${documentId}`);
  return response.data;
}

export async function getDocumentStatus(
  documentId: string
): Promise<{ status: string; page_count: number | null; error: string | null }> {
  const response = await apiClient.get(`/documents/${documentId}/status`);
  return response.data;
}

export async function deleteDocument(documentId: string): Promise<void> {
  await apiClient.delete(`/documents/${documentId}`);
}
```

## TypeScript Types

### API Response Types

```typescript
// src/types/index.ts

// Document Types
export interface PageSummary {
  id: string;
  page_number: number;
  classification?: string | null;
  scale_calibrated: boolean;
  thumbnail_url?: string | null;
}

export interface Document {
  id: string;
  project_id: string;
  filename: string;
  original_filename: string;
  file_type: string;
  file_size: number;
  status: string;
  page_count?: number | null;
  processing_error?: string | null;
  created_at: string;
  updated_at: string;
  pages: PageSummary[];
}

// Project Types (for future use)
export interface Project {
  id: string;
  name: string;
  description?: string;
  client_name?: string;
  status: string;
  created_at: string;
  updated_at: string;
  documents?: Document[];
}
```

## State Management

### React Query Configuration

```tsx
// src/main.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 3,
    },
    mutations: {
      retry: 1,
    },
  },
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </React.StrictMode>,
);
```

## Styling

### TailwindCSS Configuration

```javascript
// tailwind.config.js
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        // ... more color definitions
      },
    },
  },
  plugins: [],
}
```

### Utility Functions

```typescript
// src/lib/utils.ts
import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

## Component Patterns

### Custom Hooks (Future)

```typescript
// src/hooks/useDocuments.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getDocument, uploadDocument, deleteDocument } from '@/api/documents';

export function useDocument(documentId: string) {
  return useQuery({
    queryKey: ['document', documentId],
    queryFn: () => getDocument(documentId),
    enabled: !!documentId,
  });
}

export function useDocumentUpload() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ projectId, file }: { projectId: string; file: File }) =>
      uploadDocument(projectId, file),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['documents', data.project_id] });
    },
  });
}
```

## Error Handling

### Global Error Boundary

```tsx
// src/components/ErrorBoundary.tsx
import React from 'react';

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends React.Component<
  React.PropsWithChildren<{}>,
  ErrorBoundaryState
> {
  constructor(props: React.PropsWithChildren<{}>) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-red-600 mb-4">
              Something went wrong
            </h2>
            <p className="text-gray-600 mb-4">
              {this.state.error?.message || 'An unexpected error occurred'}
            </p>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Reload Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
```

### API Error Handling

```tsx
// src/hooks/useApiError.ts
import { useQueryClient } from '@tanstack/react-query';
import { AxiosError } from 'axios';

export function useApiError() {
  const queryClient = useQueryClient();

  const handleError = (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
      queryClient.clear();
      window.location.href = '/login';
    } else if (error.response?.status === 403) {
      // Handle forbidden
      console.error('Access denied');
    } else {
      // Handle other errors
      console.error('API Error:', error.response?.data || error.message);
    }
  };

  return { handleError };
}
```

## Performance Optimizations

### Code Splitting

```tsx
// src/App.tsx
import { lazy, Suspense } from 'react';

const DocumentUploader = lazy(() => import('./components/document/DocumentUploader'));

function App() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <DocumentUploader projectId="123" />
    </Suspense>
  );
}
```

### Image Lazy Loading

```tsx
// Future implementation for page thumbnails
import { useState, useRef, useEffect } from 'react';

export function LazyImage({ src, alt }: { src: string; alt: string }) {
  const [isLoaded, setIsLoaded] = useState(false);
  const [isInView, setIsInView] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsInView(true);
          observer.disconnect();
        }
      }
    );

    if (imgRef.current) {
      observer.observe(imgRef.current);
    }

    return () => observer.disconnect();
  }, []);

  return (
    <img
      ref={imgRef}
      src={isInView ? src : undefined}
      alt={alt}
      onLoad={() => setIsLoaded(true)}
      style={{ opacity: isLoaded ? 1 : 0.5 }}
    />
  );
}
```

## Accessibility

### ARIA Labels and Roles

```tsx
// Accessible file upload
<div
  {...getRootProps()}
  role="button"
  tabIndex={0}
  aria-label="Upload PDF or TIFF files"
  onKeyDown={(e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      // Trigger file selection
    }
  }}
>
  <input {...getInputProps()} aria-hidden="true" />
  <p>Drag and drop files here or press Enter to select files</p>
</div>
```

### Keyboard Navigation

```tsx
// Keyboard support for file management
const handleKeyDown = (event: React.KeyboardEvent, index: number) => {
  if (event.key === 'Delete' || event.key === 'Backspace') {
    removeFile(index);
  }
};
```

## Testing

### Component Testing

```tsx
// src/components/document/DocumentUploader.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { DocumentUploader } from './DocumentUploader';

describe('DocumentUploader', () => {
  it('renders upload area', () => {
    render(<DocumentUploader projectId="123" />);
    expect(screen.getByText(/drag & drop/i)).toBeInTheDocument();
  });

  it('handles file selection', async () => {
    render(<DocumentUploader projectId="123" />);
    const input = screen.getByTestId('file-input');

    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });
    fireEvent.change(input, { target: { files: [file] } });

    expect(await screen.findByText('test.pdf')).toBeInTheDocument();
  });
});
```

### API Testing

```typescript
// src/api/documents.test.ts
import { uploadDocument } from './documents';
import { apiClient } from './client';

jest.mock('./client');

describe('uploadDocument', () => {
  it('uploads file successfully', async () => {
    const mockResponse = { data: { id: '123', status: 'uploaded' } };
    (apiClient.post as jest.Mock).mockResolvedValue(mockResponse);

    const file = new File(['test'], 'test.pdf');
    const result = await uploadDocument('project-123', file);

    expect(result.id).toBe('123');
    expect(apiClient.post).toHaveBeenCalledWith(
      '/projects/project-123/documents',
      expect.any(FormData),
      expect.objectContaining({
        headers: { 'Content-Type': 'multipart/form-data' },
      })
    );
  });
});
```

## Build and Deployment

### Development Server

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Environment Configuration

```bash
# .env.development
VITE_API_BASE_URL=http://localhost:8000/api/v1

# .env.production
VITE_API_BASE_URL=https://api.takeoff-platform.com/api/v1
```

### Docker Configuration

```dockerfile
# Dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 80
CMD ["npm", "run", "preview", "--", "--port", "80", "--host"]
```

## Future Enhancements

### Phase 1B: OCR Integration
- Add OCR progress indicators
- Display extracted text previews
- Search functionality for OCR text

### Phase 2A: Page Classification
- Classification status indicators
- Confidence score displays
- Bulk classification operations

### Phase 2B: Scale Calibration
- Visual scale calibration interface
- Measurement unit selection
- Calibration validation

### Phase 3A: Measurement Tools
- Canvas-based measurement interface
- Real-time quantity calculations
- Measurement history and undo/redo

This frontend implementation provides a solid foundation for the document ingestion workflow with modern React patterns, comprehensive error handling, and scalability for future phases.