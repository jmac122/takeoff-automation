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

// Mock lucide-react with all icons used across workspace components
vi.mock('lucide-react', () => {
  const stub = (name: string) => {
    const C = ({ className, size }: { className?: string; size?: number }) => (
      <span data-testid={`icon-${name.toLowerCase()}`} className={className} data-size={size} />
    );
    C.displayName = name;
    return C;
  };
  return {
    // TopToolbar
    MousePointer2: stub('MousePointer2'), Minus: stub('Minus'), Hexagon: stub('Hexagon'),
    Square: stub('Square'), Circle: stub('Circle'), Ruler: stub('Ruler'),
    Undo2: stub('Undo2'), Redo2: stub('Redo2'), ZoomIn: stub('ZoomIn'), ZoomOut: stub('ZoomOut'),
    Search: stub('Search'), Sparkles: stub('Sparkles'), ScanSearch: stub('ScanSearch'),
    Grid3X3: stub('Grid3X3'), ClipboardCheck: stub('ClipboardCheck'), Zap: stub('Zap'),
    Loader2: stub('Loader2'), Palette: stub('Palette'),
    PanelLeftClose: stub('PanelLeftClose'), PanelLeftOpen: stub('PanelLeftOpen'),
    PanelRightClose: stub('PanelRightClose'), PanelRightOpen: stub('PanelRightOpen'),
    // ExportDropdown
    FileSpreadsheet: stub('FileSpreadsheet'), FileText: stub('FileText'),
    FileCode: stub('FileCode'), FileType: stub('FileType'), Download: stub('Download'),
    // ConditionPanel / RightPanel
    ChevronDown: stub('ChevronDown'), ChevronRight: stub('ChevronRight'),
    Grid3x3: stub('Grid3x3'), List: stub('List'), MoreHorizontal: stub('MoreHorizontal'),
    Plus: stub('Plus'), Eye: stub('Eye'), EyeOff: stub('EyeOff'),
    Pencil: stub('Pencil'), Trash2: stub('Trash2'), Copy: stub('Copy'),
    ArrowUp: stub('ArrowUp'), ArrowDown: stub('ArrowDown'),
    // AssemblyPanel
    Calculator: stub('Calculator'), Lock: stub('Lock'), Unlock: stub('Unlock'),
    Package: stub('Package'), HardHat: stub('HardHat'), Truck: stub('Truck'),
    Wrench: stub('Wrench'), DollarSign: stub('DollarSign'),
    // RevisionChainPanel
    GitBranch: stub('GitBranch'), Layers: stub('Layers'),
    // PlanOverlayView
    X: stub('X'), ChevronLeft: stub('ChevronLeft'),
    // ReviewMeasurementPanel
    Check: stub('Check'), AlertCircle: stub('AlertCircle'), History: stub('History'),
    ExternalLink: stub('ExternalLink'), ArrowRight: stub('ArrowRight'),
    // BottomStatusBar
    Info: stub('Info'),
    // LinkRevisionDialog
    Link: stub('Link'), Calendar: stub('Calendar'),
  };
});

// Mock Konva and all components that use it (native canvas unavailable in test env)
vi.mock('konva/lib/index-node', () => ({}));
vi.mock('react-konva', () => ({}));
vi.mock('../CenterCanvas', () => ({
  CenterCanvas: ({ projectId }: { projectId: string }) => (
    <div data-testid="center-canvas" data-project-id={projectId} />
  ),
  getReviewColor: () => '#ef4444',
  filterMeasurementsForCanvas: (m: unknown[]) => m,
}));
vi.mock('@/components/viewer/GhostPointLayer', () => ({
  GhostPointLayer: () => null,
}));
vi.mock('@/components/viewer/MeasurementShape', () => ({
  MeasurementShape: () => null,
}));

vi.mock('@/components/document/PlanOverlayView', () => ({
  PlanOverlayView: () => <div data-testid="plan-overlay-view" />,
}));

vi.mock('@/components/document/RevisionChainPanel', () => ({
  RevisionChainPanel: () => <div data-testid="revision-chain-panel" />,
}));

vi.mock('@/components/document/LinkRevisionDialog', () => ({
  LinkRevisionDialog: () => <div data-testid="link-revision-dialog" />,
}));

// Mock useAiAssist to avoid deep Konva imports
vi.mock('@/hooks/useAiAssist', () => ({
  useAiAssist: () => ({ runBatchAi: vi.fn(), isRunning: false }),
}));

// Mock useReviewKeyboardShortcuts (depends on FocusProvider context)
vi.mock('@/hooks/useReviewKeyboardShortcuts', () => ({
  useReviewKeyboardShortcuts: () => {},
}));

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
