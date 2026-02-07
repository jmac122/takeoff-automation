import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Mock lucide-react icons used by condition components
vi.mock('lucide-react', () => {
  const stub = (name: string) => {
    const C = ({ className }: { className?: string }) => (
      <span data-testid={`icon-${name.toLowerCase()}`} className={className} />
    );
    C.displayName = name;
    return C;
  };
  return {
    Plus: stub('plus'),
    ChevronDown: stub('chevrondown'),
    ChevronRight: stub('chevronright'),
    Eye: stub('eye'),
    EyeOff: stub('eyeoff'),
    Pencil: stub('pencil'),
    Trash2: stub('trash2'),
    Copy: stub('copy'),
    ArrowUp: stub('arrowup'),
    ArrowDown: stub('arrowdown'),
  };
});

import { ConditionPanel } from '../ConditionPanel';
import { useWorkspaceStore } from '@/stores/workspaceStore';
import type { Condition } from '@/types';

// Mock the hooks
vi.mock('@/hooks/useConditions', () => ({
  useConditions: vi.fn(),
  useConditionTemplates: vi.fn(() => ({ data: [] })),
  useCreateConditionFromTemplate: vi.fn(() => ({ mutate: vi.fn(), isPending: false })),
  useDeleteCondition: vi.fn(() => ({ mutate: vi.fn() })),
  useDuplicateCondition: vi.fn(() => ({ mutate: vi.fn() })),
  useUpdateCondition: vi.fn(() => ({ mutate: vi.fn() })),
  useReorderConditions: vi.fn(() => ({ mutate: vi.fn() })),
}));

import { useConditions } from '@/hooks/useConditions';

const mockConditions: Condition[] = [
  {
    id: 'cond-1',
    project_id: 'proj-1',
    name: '4" SOG',
    description: null,
    scope: 'concrete',
    category: 'slabs',
    measurement_type: 'area',
    color: '#22C55E',
    line_width: 2,
    fill_opacity: 0.3,
    unit: 'SF',
    depth: 4,
    thickness: null,
    total_quantity: 2450,
    measurement_count: 5,
    sort_order: 0,
    is_ai_generated: false,
    is_visible: true,
    extra_metadata: null,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  },
  {
    id: 'cond-2',
    project_id: 'proj-1',
    name: 'Strip Footing',
    description: null,
    scope: 'concrete',
    category: 'foundations',
    measurement_type: 'linear',
    color: '#EF4444',
    line_width: 2,
    fill_opacity: 0.3,
    unit: 'LF',
    depth: 12,
    thickness: null,
    total_quantity: 320,
    measurement_count: 3,
    sort_order: 1,
    is_ai_generated: false,
    is_visible: true,
    extra_metadata: null,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  },
];

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

describe('ConditionPanel', () => {
  beforeEach(() => {
    useWorkspaceStore.setState({
      activeConditionId: null,
      activeTool: 'select',
      focusRegion: 'canvas',
      toolRejectionMessage: null,
    });
    vi.mocked(useConditions).mockReturnValue({
      data: { conditions: mockConditions, total: 2 },
      isLoading: false,
      error: null,
    } as ReturnType<typeof useConditions>);
  });

  it('renders the three-section layout', () => {
    render(<ConditionPanel projectId="proj-1" />, { wrapper: createWrapper() });
    expect(screen.getByTestId('condition-panel')).toBeDefined();
    expect(screen.getByTestId('quick-create-btn')).toBeDefined();
    expect(screen.getByTestId('condition-list')).toBeDefined();
    expect(screen.getByTestId('properties-empty')).toBeDefined();
  });

  it('renders all conditions in the list', () => {
    render(<ConditionPanel projectId="proj-1" />, { wrapper: createWrapper() });
    expect(screen.getByTestId('condition-row-0')).toBeDefined();
    expect(screen.getByTestId('condition-row-1')).toBeDefined();
    expect(screen.getByText('4" SOG')).toBeDefined();
    expect(screen.getByText('Strip Footing')).toBeDefined();
  });

  it('shows empty state when no conditions', () => {
    vi.mocked(useConditions).mockReturnValue({
      data: { conditions: [], total: 0 },
      isLoading: false,
      error: null,
    } as ReturnType<typeof useConditions>);

    render(<ConditionPanel projectId="proj-1" />, { wrapper: createWrapper() });
    expect(screen.getByTestId('condition-list-empty')).toBeDefined();
  });

  it('clicking a condition sets it active in the store', () => {
    render(<ConditionPanel projectId="proj-1" />, { wrapper: createWrapper() });

    fireEvent.click(screen.getByTestId('condition-row-0'));
    expect(useWorkspaceStore.getState().activeConditionId).toBe('cond-1');
  });

  it('clicking active condition deselects it', () => {
    useWorkspaceStore.setState({ activeConditionId: 'cond-1' });

    render(<ConditionPanel projectId="proj-1" />, { wrapper: createWrapper() });
    fireEvent.click(screen.getByTestId('condition-row-0'));
    expect(useWorkspaceStore.getState().activeConditionId).toBeNull();
  });

  it('shows properties inspector when condition is active', () => {
    useWorkspaceStore.setState({ activeConditionId: 'cond-1' });

    render(<ConditionPanel projectId="proj-1" />, { wrapper: createWrapper() });
    expect(screen.getByTestId('properties-inspector')).toBeDefined();
    // Check property values
    expect(screen.getByText('Area')).toBeDefined();
    expect(screen.getByText('Square Feet')).toBeDefined();
  });

  it('shows visibility toggles for each condition', () => {
    render(<ConditionPanel projectId="proj-1" />, { wrapper: createWrapper() });
    expect(screen.getByTestId('visibility-toggle-0')).toBeDefined();
    expect(screen.getByTestId('visibility-toggle-1')).toBeDefined();
  });

  it('shows shortcut numbers for conditions 1-9', () => {
    render(<ConditionPanel projectId="proj-1" />, { wrapper: createWrapper() });
    expect(screen.getByText('1')).toBeDefined();
    expect(screen.getByText('2')).toBeDefined();
  });

  it('number key selects condition by position', () => {
    render(<ConditionPanel projectId="proj-1" />, { wrapper: createWrapper() });

    fireEvent.keyDown(window, { key: '2' });
    expect(useWorkspaceStore.getState().activeConditionId).toBe('cond-2');

    fireEvent.keyDown(window, { key: '1' });
    expect(useWorkspaceStore.getState().activeConditionId).toBe('cond-1');
  });

  it('Delete key shows delete confirmation dialog', () => {
    useWorkspaceStore.setState({ activeConditionId: 'cond-1' });

    render(<ConditionPanel projectId="proj-1" />, { wrapper: createWrapper() });
    fireEvent.keyDown(window, { key: 'Delete' });

    expect(screen.getByTestId('delete-confirm-dialog')).toBeDefined();
    expect(screen.getByTestId('confirm-delete-btn')).toBeDefined();
  });

  it('shows context menu on right-click', () => {
    render(<ConditionPanel projectId="proj-1" />, { wrapper: createWrapper() });

    fireEvent.contextMenu(screen.getByTestId('condition-row-0'));
    expect(screen.getByTestId('condition-context-menu')).toBeDefined();
  });

  it('template dropdown opens on click', () => {
    render(<ConditionPanel projectId="proj-1" />, { wrapper: createWrapper() });

    fireEvent.click(screen.getByTestId('quick-create-btn'));
    expect(screen.getByTestId('template-dropdown')).toBeDefined();
  });

  it('displays total quantity and unit per condition', () => {
    render(<ConditionPanel projectId="proj-1" />, { wrapper: createWrapper() });
    // 2450 SF should display as "2.5k"
    expect(screen.getByText('2.5k')).toBeDefined();
    expect(screen.getByText('320')).toBeDefined();
  });
});
