import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Mock constants
vi.mock('@/lib/constants', async (importOriginal) => {
  const orig = (await importOriginal()) as Record<string, unknown>;
  return {
    ...orig,
    ENABLE_NEW_WORKSPACE: true,
  };
});

// Mock lucide-react with all icons used by workspace components
vi.mock('lucide-react', () => {
  const stub = (name: string) => {
    const C = ({ className }: { className?: string }) => (
      <span data-testid={`icon-${name.toLowerCase()}`} className={className} />
    );
    C.displayName = name;
    return C;
  };
  return {
    Loader2: stub('loader2'),
    MousePointer2: stub('mousepointer2'),
    Minus: stub('minus'),
    Hexagon: stub('hexagon'),
    Square: stub('square'),
    Circle: stub('circle'),
    Ruler: stub('ruler'),
    Undo2: stub('undo2'),
    Redo2: stub('redo2'),
    ZoomIn: stub('zoomin'),
    ZoomOut: stub('zoomout'),
    Search: stub('search'),
    Sparkles: stub('sparkles'),
    PanelLeftClose: stub('panelleftclose'),
    PanelLeftOpen: stub('panelleftopen'),
    PanelRightClose: stub('panelrightclose'),
    PanelRightOpen: stub('panelrightopen'),
    ChevronDown: stub('chevrondown'),
    ChevronRight: stub('chevronright'),
    FileText: stub('filetext'),
    Grid3x3: stub('grid3x3'),
    List: stub('list'),
    MoreHorizontal: stub('morehorizontal'),
    Plus: stub('plus'),
    Eye: stub('eye'),
    EyeOff: stub('eyeoff'),
    Pencil: stub('pencil'),
    Trash2: stub('trash2'),
    Copy: stub('copy'),
    ArrowUp: stub('arrowup'),
    ArrowDown: stub('arrowdown'),
  };
});

// Mock react-resizable-panels
vi.mock('react-resizable-panels', () => ({
  Panel: ({ children, ...props }: Record<string, unknown> & { children?: React.ReactNode }) => (
    <div data-testid={(props['data-testid'] as string) || `panel-${props.id}`}>{children}</div>
  ),
  Group: ({ children }: { children?: React.ReactNode }) => <div data-testid="panel-group">{children}</div>,
  Separator: () => <div data-testid="panel-resize-handle" />,
}));

// Mock sub-components that are rendered inside TakeoffWorkspace
vi.mock('@/components/sheets/SheetTree', () => ({
  SheetTree: ({ projectId }: { projectId: string }) => (
    <div data-testid="sheet-tree" data-project-id={projectId} />
  ),
}));

vi.mock('@/components/sheets/ScaleBadge', () => ({
  ScaleBadge: () => <span data-testid="scale-badge" />,
}));

vi.mock('@/components/sheets/SheetContextMenu', () => ({
  SheetContextMenu: () => <div data-testid="sheet-context-menu" />,
}));

vi.mock('@/components/sheets/ThumbnailStrip', () => ({
  ThumbnailStrip: () => <div data-testid="thumbnail-strip" />,
}));

// Mock the conditions hooks used by ConditionPanel (via RightPanel)
vi.mock('@/hooks/useConditions', () => ({
  useConditions: vi.fn(() => ({ data: { conditions: [], total: 0 }, isLoading: false, error: null })),
  useConditionTemplates: vi.fn(() => ({ data: [] })),
  useCreateConditionFromTemplate: vi.fn(() => ({ mutate: vi.fn(), isPending: false })),
  useDeleteCondition: vi.fn(() => ({ mutate: vi.fn() })),
  useDuplicateCondition: vi.fn(() => ({ mutate: vi.fn() })),
  useUpdateCondition: vi.fn(() => ({ mutate: vi.fn() })),
  useReorderConditions: vi.fn(() => ({ mutate: vi.fn() })),
}));

// Mock the API client
vi.mock('@/api/client', () => ({
  apiClient: {
    get: vi.fn(),
    put: vi.fn(),
    post: vi.fn(),
  },
}));

vi.mock('@/api/sheets', () => ({
  getProjectSheets: vi.fn(),
}));

import { apiClient } from '@/api/client';
import { getProjectSheets } from '@/api/sheets';
import { useWorkspaceStore } from '@/stores/workspaceStore';
import { TakeoffWorkspace } from '../TakeoffWorkspace';

function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
}

function renderWorkspace(projectId: string = 'proj-123') {
  const queryClient = createQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[`/projects/${projectId}/workspace`]}>
        <Routes>
          <Route
            path="/projects/:id/workspace"
            element={<TakeoffWorkspace />}
          />
          <Route
            path="/projects/:id"
            element={<div data-testid="old-project-page">Old project page</div>}
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('TakeoffWorkspace', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useWorkspaceStore.setState({
      activeSheetId: null,
      highlightedSheetId: null,
      leftPanelCollapsed: false,
      rightPanelCollapsed: false,
      expandedGroups: {},
      sheetSearchQuery: '',
      sheetViewMode: 'tree',
      focusRegion: 'canvas',
    });
  });

  it('renders three-panel layout', async () => {
    (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: { id: 'proj-123', name: 'Test Project' },
    });
    (getProjectSheets as ReturnType<typeof vi.fn>).mockResolvedValue({
      groups: [],
      total: 0,
    });

    renderWorkspace();

    expect(await screen.findByTestId('takeoff-workspace')).toBeInTheDocument();
    expect(screen.getByTestId('panel-group')).toBeInTheDocument();
    expect(screen.getByTestId('sheet-tree')).toBeInTheDocument();
  });

  it('shows loading state while fetching project', () => {
    (apiClient.get as ReturnType<typeof vi.fn>).mockReturnValue(
      new Promise(() => {}),
    );
    (getProjectSheets as ReturnType<typeof vi.fn>).mockReturnValue(
      new Promise(() => {}),
    );

    renderWorkspace();

    expect(screen.getByTestId('icon-loader2')).toBeInTheDocument();
  });

  it('shows project not found when API errors', async () => {
    (apiClient.get as ReturnType<typeof vi.fn>).mockRejectedValue(
      new Error('Not found'),
    );
    (getProjectSheets as ReturnType<typeof vi.fn>).mockRejectedValue(
      new Error('Not found'),
    );

    renderWorkspace();

    expect(await screen.findByTestId('project-not-found')).toBeInTheDocument();
    expect(screen.getByText('Project not found')).toBeInTheDocument();
  });

  it('passes projectId to SheetTree', async () => {
    (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: { id: 'proj-456', name: 'Another Project' },
    });
    (getProjectSheets as ReturnType<typeof vi.fn>).mockResolvedValue({
      groups: [],
      total: 0,
    });

    renderWorkspace('proj-456');

    const sheetTree = await screen.findByTestId('sheet-tree');
    expect(sheetTree).toHaveAttribute('data-project-id', 'proj-456');
  });
});
