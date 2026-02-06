import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SheetTree } from '../SheetTree';
import { useWorkspaceStore } from '@/stores/workspaceStore';
import type { SheetsResponse, SheetInfo, SheetGroup } from '@/api/sheets';

// Mock lucide-react icons
vi.mock('lucide-react', () => ({
  ChevronDown: () => <span data-testid="icon-chevron-down" />,
  ChevronRight: () => <span data-testid="icon-chevron-right" />,
  FileText: () => <span data-testid="icon-file-text" />,
  Search: () => <span data-testid="icon-search" />,
  Grid3x3: () => <span data-testid="icon-grid" />,
  List: () => <span data-testid="icon-list" />,
  Loader2: ({ className }: { className?: string }) => (
    <span data-testid="icon-loader" className={className} />
  ),
  MoreHorizontal: () => <span data-testid="icon-more" />,
}));

// Mock sub-components
vi.mock('../ScaleBadge', () => ({
  ScaleBadge: ({ sheet }: { sheet: SheetInfo }) => (
    <span data-testid={`scale-badge-${sheet.id}`}>
      {sheet.scale_text || 'no-scale'}
    </span>
  ),
}));

vi.mock('../SheetContextMenu', () => ({
  SheetContextMenu: () => <div data-testid="sheet-context-menu" />,
}));

vi.mock('../ThumbnailStrip', () => ({
  ThumbnailStrip: () => <div data-testid="thumbnail-strip" />,
}));

function makeSheet(overrides: Partial<SheetInfo> = {}): SheetInfo {
  return {
    id: `sheet-${Math.random().toString(36).slice(2, 8)}`,
    document_id: 'doc-1',
    page_number: 1,
    sheet_number: null,
    title: null,
    display_name: null,
    display_order: null,
    group_name: null,
    discipline: null,
    page_type: null,
    classification: null,
    classification_confidence: null,
    scale_text: null,
    scale_value: null,
    scale_calibrated: false,
    scale_detection_method: null,
    measurement_count: 0,
    thumbnail_url: null,
    image_url: null,
    width: 3300,
    height: 2550,
    is_relevant: true,
    ...overrides,
  };
}

function makeSheetsData(groups: SheetGroup[]): SheetsResponse {
  const total = groups.reduce((sum, g) => sum + g.sheets.length, 0);
  return { groups, total };
}

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>,
  );
}

describe('SheetTree', () => {
  beforeEach(() => {
    // Reset store
    useWorkspaceStore.setState({
      activeSheetId: null,
      highlightedSheetId: null,
      expandedGroups: {},
      sheetSearchQuery: '',
      sheetViewMode: 'tree',
      focusRegion: 'canvas',
    });
    localStorage.clear();
  });

  it('renders sheets grouped by discipline', () => {
    const sheetsData = makeSheetsData([
      {
        group_name: 'Structural',
        sheets: [
          makeSheet({ id: 's1', title: 'S1.01', discipline: 'Structural' }),
          makeSheet({ id: 's2', title: 'S1.02', discipline: 'Structural' }),
        ],
      },
      {
        group_name: 'Architectural',
        sheets: [
          makeSheet({ id: 'a1', title: 'A1.01', discipline: 'Architectural' }),
        ],
      },
    ]);

    renderWithProviders(
      <SheetTree projectId="proj-1" sheetsData={sheetsData} isLoading={false} />,
    );

    expect(screen.getByTestId('group-header-Structural')).toBeInTheDocument();
    expect(screen.getByTestId('group-header-Architectural')).toBeInTheDocument();
  });

  it('clicking a sheet sets it as active', () => {
    const sheet = makeSheet({ id: 'sheet-abc', title: 'Test Sheet' });
    const sheetsData = makeSheetsData([
      { group_name: 'General', sheets: [sheet] },
    ]);

    renderWithProviders(
      <SheetTree projectId="proj-1" sheetsData={sheetsData} isLoading={false} />,
    );

    fireEvent.click(screen.getByTestId(`sheet-item-${sheet.id}`));
    expect(useWorkspaceStore.getState().activeSheetId).toBe('sheet-abc');
  });

  it('shows scale badge per sheet', () => {
    const sheet = makeSheet({
      id: 'sheet-scaled',
      title: 'Scaled Sheet',
      scale_text: '1/4" = 1\'',
      scale_calibrated: true,
    });
    const sheetsData = makeSheetsData([
      { group_name: 'Structural', sheets: [sheet] },
    ]);

    renderWithProviders(
      <SheetTree projectId="proj-1" sheetsData={sheetsData} isLoading={false} />,
    );

    expect(screen.getByTestId('scale-badge-sheet-scaled')).toBeInTheDocument();
  });

  it('shows no-scale indicator for uncalibrated sheets', () => {
    const sheet = makeSheet({
      id: 'sheet-noscale',
      title: 'No Scale Sheet',
      scale_text: null,
      scale_calibrated: false,
    });
    const sheetsData = makeSheetsData([
      { group_name: 'General', sheets: [sheet] },
    ]);

    renderWithProviders(
      <SheetTree projectId="proj-1" sheetsData={sheetsData} isLoading={false} />,
    );

    const badge = screen.getByTestId('scale-badge-sheet-noscale');
    expect(badge).toHaveTextContent('no-scale');
  });

  it('persists expand/collapse to localStorage', () => {
    const sheetsData = makeSheetsData([
      { group_name: 'Structural', sheets: [makeSheet({ id: 's1' })] },
    ]);

    // Initially expanded (auto-expanded on first load)
    renderWithProviders(
      <SheetTree projectId="proj-1" sheetsData={sheetsData} isLoading={false} />,
    );

    // Click group header to collapse
    fireEvent.click(screen.getByTestId('group-header-Structural'));

    // Check localStorage
    const saved = JSON.parse(localStorage.getItem('forgex-sheet-tree-state') || '{}');
    expect(saved.expandedGroups?.Structural).toBe(false);
  });

  it('keyboard navigation works', () => {
    const sheets = [
      makeSheet({ id: 'sheet-1', title: 'Sheet 1' }),
      makeSheet({ id: 'sheet-2', title: 'Sheet 2' }),
      makeSheet({ id: 'sheet-3', title: 'Sheet 3' }),
    ];
    const sheetsData = makeSheetsData([{ group_name: 'All', sheets }]);

    renderWithProviders(
      <SheetTree projectId="proj-1" sheetsData={sheetsData} isLoading={false} />,
    );

    const treeList = screen.getByTestId('sheet-tree-list');

    // Press ArrowDown to highlight first sheet
    fireEvent.keyDown(treeList, { key: 'ArrowDown' });
    expect(useWorkspaceStore.getState().highlightedSheetId).toBe('sheet-1');

    // Press ArrowDown again to highlight second
    fireEvent.keyDown(treeList, { key: 'ArrowDown' });
    expect(useWorkspaceStore.getState().highlightedSheetId).toBe('sheet-2');

    // Press Enter to select
    fireEvent.keyDown(treeList, { key: 'Enter' });
    expect(useWorkspaceStore.getState().activeSheetId).toBe('sheet-2');
  });

  it('search filters sheets by name', () => {
    const sheetsData = makeSheetsData([
      {
        group_name: 'Structural',
        sheets: [
          makeSheet({ id: 's1', title: 'S1.01' }),
          makeSheet({ id: 's2', title: 'S1.02' }),
        ],
      },
      {
        group_name: 'Architectural',
        sheets: [makeSheet({ id: 'a1', title: 'A1.01' })],
      },
    ]);

    renderWithProviders(
      <SheetTree projectId="proj-1" sheetsData={sheetsData} isLoading={false} />,
    );

    const searchInput = screen.getByTestId('sheet-search');
    fireEvent.change(searchInput, { target: { value: 'S1' } });

    // S1.01 and S1.02 should be visible, A1.01 should not
    expect(screen.getByText('S1.01')).toBeInTheDocument();
    expect(screen.getByText('S1.02')).toBeInTheDocument();
    expect(screen.queryByText('A1.01')).not.toBeInTheDocument();
  });

  it('handles empty project gracefully', () => {
    renderWithProviders(
      <SheetTree
        projectId="proj-1"
        sheetsData={{ groups: [], total: 0 }}
        isLoading={false}
      />,
    );

    expect(screen.getByTestId('sheet-tree-empty')).toBeInTheDocument();
    expect(screen.getByText('No sheets found')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    renderWithProviders(
      <SheetTree projectId="proj-1" sheetsData={null} isLoading={true} />,
    );

    expect(screen.getByTestId('sheet-tree-loading')).toBeInTheDocument();
  });

  it('switches to thumbnail view', () => {
    const sheetsData = makeSheetsData([
      { group_name: 'All', sheets: [makeSheet({ id: 's1' })] },
    ]);

    renderWithProviders(
      <SheetTree projectId="proj-1" sheetsData={sheetsData} isLoading={false} />,
    );

    // Click thumbnail view button
    fireEvent.click(screen.getByTestId('view-mode-thumbnails'));
    expect(useWorkspaceStore.getState().sheetViewMode).toBe('thumbnails');
    expect(screen.getByTestId('thumbnail-strip')).toBeInTheDocument();
  });
});
