import { describe, it, expect, beforeEach } from 'vitest';
import { useWorkspaceStore } from '@/stores/workspaceStore';
import {
  LEFT_PANEL_MIN_WIDTH,
  LEFT_PANEL_MAX_WIDTH,
  MIN_ZOOM,
  MAX_ZOOM,
} from '@/lib/constants';

describe('WorkspaceStore', () => {
  beforeEach(() => {
    // Reset store to defaults before each test
    useWorkspaceStore.setState({
      activeSheetId: null,
      selectedSheetIds: [],
      highlightedSheetId: null,
      activeConditionId: null,
      activeTool: 'select',
      isDrawing: false,
      currentPoints: [],
      selectedMeasurementIds: [],
      viewport: { zoom: 1, panX: 0, panY: 0 },
      focusRegion: 'canvas',
      leftPanelWidth: 280,
      rightPanelWidth: 340,
      leftPanelCollapsed: false,
      rightPanelCollapsed: false,
      sheetViewMode: 'tree',
      expandedGroups: {},
      sheetSearchQuery: '',
      autoTabEnabled: false,
      pendingPrediction: false,
    });
  });

  it('initializes with default values', () => {
    const state = useWorkspaceStore.getState();
    expect(state.activeTool).toBe('select');
    expect(state.activeSheetId).toBeNull();
    expect(state.activeConditionId).toBeNull();
    expect(state.isDrawing).toBe(false);
    expect(state.viewport.zoom).toBe(1);
    expect(state.focusRegion).toBe('canvas');
    expect(state.leftPanelCollapsed).toBe(false);
    expect(state.rightPanelCollapsed).toBe(false);
    expect(state.sheetViewMode).toBe('tree');
  });

  it('setActiveSheet updates activeSheetId', () => {
    const { setActiveSheet } = useWorkspaceStore.getState();
    setActiveSheet('sheet-123');
    expect(useWorkspaceStore.getState().activeSheetId).toBe('sheet-123');
  });

  it('setActiveTool prevents tool activation without active condition', () => {
    const state = useWorkspaceStore.getState();
    // No activeConditionId set
    expect(state.activeConditionId).toBeNull();

    // Try to set tool to 'polygon' — should be rejected
    state.setActiveTool('polygon');
    expect(useWorkspaceStore.getState().activeTool).toBe('select'); // unchanged

    // 'measure' should work without condition
    state.setActiveTool('measure');
    expect(useWorkspaceStore.getState().activeTool).toBe('measure');

    // 'select' should work without condition
    state.setActiveTool('select');
    expect(useWorkspaceStore.getState().activeTool).toBe('select');
  });

  it('setActiveTool allows drawing tools when condition is active', () => {
    useWorkspaceStore.setState({ activeConditionId: 'cond-1' });
    const { setActiveTool } = useWorkspaceStore.getState();

    setActiveTool('polygon');
    expect(useWorkspaceStore.getState().activeTool).toBe('polygon');

    setActiveTool('line');
    expect(useWorkspaceStore.getState().activeTool).toBe('line');
  });

  it('setActiveTool clears selection when setting non-select tool', () => {
    useWorkspaceStore.setState({
      activeConditionId: 'cond-1',
      selectedMeasurementIds: ['m1', 'm2'],
    });

    const { setActiveTool } = useWorkspaceStore.getState();
    setActiveTool('polygon');

    expect(useWorkspaceStore.getState().selectedMeasurementIds).toEqual([]);
  });

  it('panel widths respect min/max bounds', () => {
    const { setLeftPanelWidth } = useWorkspaceStore.getState();

    // Below minimum
    setLeftPanelWidth(50);
    expect(useWorkspaceStore.getState().leftPanelWidth).toBe(LEFT_PANEL_MIN_WIDTH);

    // Above maximum
    setLeftPanelWidth(9999);
    expect(useWorkspaceStore.getState().leftPanelWidth).toBe(LEFT_PANEL_MAX_WIDTH);

    // Within range
    setLeftPanelWidth(300);
    expect(useWorkspaceStore.getState().leftPanelWidth).toBe(300);
  });

  it('zoom respects min/max bounds', () => {
    const { setZoom } = useWorkspaceStore.getState();

    setZoom(0.01);
    expect(useWorkspaceStore.getState().viewport.zoom).toBe(MIN_ZOOM);

    setZoom(999);
    expect(useWorkspaceStore.getState().viewport.zoom).toBe(MAX_ZOOM);

    setZoom(2.5);
    expect(useWorkspaceStore.getState().viewport.zoom).toBe(2.5);
  });

  it('escapeAll resets drawing state and selection', () => {
    useWorkspaceStore.setState({
      isDrawing: true,
      currentPoints: [{ x: 10, y: 20 }],
      activeTool: 'polygon',
      selectedMeasurementIds: ['m1'],
    });

    useWorkspaceStore.getState().escapeAll();

    const state = useWorkspaceStore.getState();
    expect(state.isDrawing).toBe(false);
    expect(state.currentPoints).toEqual([]);
    expect(state.activeTool).toBe('select');
    expect(state.selectedMeasurementIds).toEqual([]);
  });

  it('toggleLeftPanel toggles collapsed state', () => {
    const { toggleLeftPanel } = useWorkspaceStore.getState();

    expect(useWorkspaceStore.getState().leftPanelCollapsed).toBe(false);
    toggleLeftPanel();
    expect(useWorkspaceStore.getState().leftPanelCollapsed).toBe(true);
    toggleLeftPanel();
    expect(useWorkspaceStore.getState().leftPanelCollapsed).toBe(false);
  });

  it('toggleGroupExpanded toggles group state', () => {
    const { toggleGroupExpanded } = useWorkspaceStore.getState();

    toggleGroupExpanded('Structural');
    expect(useWorkspaceStore.getState().expandedGroups['Structural']).toBe(true);

    toggleGroupExpanded('Structural');
    expect(useWorkspaceStore.getState().expandedGroups['Structural']).toBe(false);
  });

  it('addCurrentPoint appends to currentPoints', () => {
    const { addCurrentPoint } = useWorkspaceStore.getState();

    addCurrentPoint({ x: 10, y: 20 });
    addCurrentPoint({ x: 30, y: 40 });

    expect(useWorkspaceStore.getState().currentPoints).toEqual([
      { x: 10, y: 20 },
      { x: 30, y: 40 },
    ]);
  });

  it('setSheetSearchQuery updates search query', () => {
    const { setSheetSearchQuery } = useWorkspaceStore.getState();

    setSheetSearchQuery('S1');
    expect(useWorkspaceStore.getState().sheetSearchQuery).toBe('S1');
  });

  it('setSheetViewMode switches between tree and thumbnails', () => {
    const { setSheetViewMode } = useWorkspaceStore.getState();

    setSheetViewMode('thumbnails');
    expect(useWorkspaceStore.getState().sheetViewMode).toBe('thumbnails');

    setSheetViewMode('tree');
    expect(useWorkspaceStore.getState().sheetViewMode).toBe('tree');
  });
});
