import { create } from 'zustand';
import {
  LEFT_PANEL_DEFAULT_WIDTH,
  LEFT_PANEL_MIN_WIDTH,
  LEFT_PANEL_MAX_WIDTH,
  RIGHT_PANEL_DEFAULT_WIDTH,
  RIGHT_PANEL_MIN_WIDTH,
  RIGHT_PANEL_MAX_WIDTH,
  DEFAULT_ZOOM,
  MIN_ZOOM,
  MAX_ZOOM,
} from '@/lib/constants';

// ============================================================================
// Types
// ============================================================================

export type DrawingTool =
  | 'select'
  | 'line'
  | 'polyline'
  | 'polygon'
  | 'rectangle'
  | 'circle'
  | 'point'     // Single-click count marker
  | 'measure'  // "M" key — no condition required
  | null;

export type FocusRegion =
  | 'canvas'
  | 'sheet-tree'
  | 'conditions'
  | 'properties'
  | 'toolbar'
  | 'dialog'
  | 'search';

export interface Point {
  x: number;
  y: number;
}

export interface ViewportState {
  zoom: number;
  panX: number;
  panY: number;
}

export type SheetViewMode = 'tree' | 'thumbnails';

// ============================================================================
// Store Interface
// ============================================================================

interface WorkspaceState {
  // Sheet navigation
  activeSheetId: string | null;
  selectedSheetIds: string[];
  highlightedSheetId: string | null;

  // Per-sheet viewport persistence (CM-036)
  sheetViewports: Record<string, ViewportState>;

  // Conditions & Drawing
  activeConditionId: string | null;
  activeTool: DrawingTool;
  isDrawing: boolean;
  currentPoints: Point[];

  // Selection
  selectedMeasurementIds: string[];

  // Viewport
  viewport: ViewportState;

  // Focus
  focusRegion: FocusRegion;

  // UI Chrome
  leftPanelWidth: number;
  rightPanelWidth: number;
  leftPanelCollapsed: boolean;
  rightPanelCollapsed: boolean;
  sheetViewMode: SheetViewMode;

  // Sheet tree
  expandedGroups: Record<string, boolean>;
  sheetSearchQuery: string;

  // AI Assist
  autoTabEnabled: boolean;
  pendingPrediction: boolean;
  ghostPrediction: {
    geometry_type: string;
    geometry_data: Record<string, unknown>;
    confidence: number;
  } | null;
  aiConfidenceOverlay: boolean;
  batchAiTaskId: string | null;

  // Transient feedback (cleared on next successful action)
  toolRejectionMessage: string | null;

  // Review mode
  reviewMode: boolean;
  reviewCurrentId: string | null;
  reviewConfidenceFilter: number;
  reviewAutoAdvance: boolean;

  // Quick Adjust / Grid
  snapToGrid: boolean;
  gridSize: number;     // pixels
  showGrid: boolean;
}

interface WorkspaceActions {
  // Sheet
  setActiveSheet: (sheetId: string | null) => void;
  setSelectedSheets: (sheetIds: string[]) => void;
  setHighlightedSheet: (sheetId: string | null) => void;

  // Conditions & Drawing
  setActiveCondition: (conditionId: string | null) => void;
  setActiveTool: (tool: DrawingTool) => void;
  setIsDrawing: (isDrawing: boolean) => void;
  setCurrentPoints: (points: Point[]) => void;
  addCurrentPoint: (point: Point) => void;

  // Selection
  setSelectedMeasurements: (ids: string[]) => void;
  clearSelection: () => void;

  // Viewport
  setViewport: (viewport: Partial<ViewportState>) => void;
  setZoom: (zoom: number) => void;

  // Focus
  setFocusRegion: (region: FocusRegion) => void;

  // UI Chrome
  setLeftPanelWidth: (width: number) => void;
  setRightPanelWidth: (width: number) => void;
  toggleLeftPanel: () => void;
  toggleRightPanel: () => void;
  setSheetViewMode: (mode: SheetViewMode) => void;

  // Sheet tree
  toggleGroupExpanded: (groupName: string) => void;
  setExpandedGroups: (groups: Record<string, boolean>) => void;
  setSheetSearchQuery: (query: string) => void;

  // AI
  setAutoTabEnabled: (enabled: boolean) => void;
  setPendingPrediction: (pending: boolean) => void;
  setGhostPrediction: (prediction: WorkspaceState['ghostPrediction']) => void;
  clearGhostPrediction: () => void;
  toggleAiConfidenceOverlay: () => void;
  setBatchAiTaskId: (taskId: string | null) => void;
  clearBatchAiTaskId: () => void;

  // Feedback
  clearToolRejection: () => void;

  // Review mode
  toggleReviewMode: () => void;
  setReviewMode: (active: boolean) => void;
  setReviewCurrentId: (id: string | null) => void;
  setReviewConfidenceFilter: (threshold: number) => void;
  advanceReview: (nextId: string | null) => void;

  // Quick Adjust / Grid
  toggleSnapToGrid: () => void;
  setGridSize: (size: number) => void;
  toggleShowGrid: () => void;

  // Reset
  resetDrawingState: () => void;
  escapeAll: () => void;
}

export type WorkspaceStore = WorkspaceState & WorkspaceActions;

// ============================================================================
// Helpers
// ============================================================================

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

// ============================================================================
// Store
// ============================================================================

export const useWorkspaceStore = create<WorkspaceStore>((set, get) => ({
  // --- Default State ---
  activeSheetId: null,
  selectedSheetIds: [],
  highlightedSheetId: null,
  sheetViewports: {},

  activeConditionId: null,
  activeTool: 'select',
  isDrawing: false,
  currentPoints: [],

  selectedMeasurementIds: [],

  viewport: { zoom: DEFAULT_ZOOM, panX: 0, panY: 0 },

  focusRegion: 'canvas',

  leftPanelWidth: LEFT_PANEL_DEFAULT_WIDTH,
  rightPanelWidth: RIGHT_PANEL_DEFAULT_WIDTH,
  leftPanelCollapsed: false,
  rightPanelCollapsed: false,
  sheetViewMode: 'tree',

  expandedGroups: {},
  sheetSearchQuery: '',

  autoTabEnabled: false,
  pendingPrediction: false,
  ghostPrediction: null,
  aiConfidenceOverlay: false,
  batchAiTaskId: null,

  toolRejectionMessage: null,

  reviewMode: false,
  reviewCurrentId: null,
  reviewConfidenceFilter: 0.0,
  reviewAutoAdvance: true,

  snapToGrid: false,
  gridSize: 10,
  showGrid: false,

  // --- Actions ---

  // CM-037: Save viewport state when switching sheets
  setActiveSheet: (sheetId) => {
    const { activeSheetId, viewport, sheetViewports } = get();
    const nextViewports = activeSheetId
      ? { ...sheetViewports, [activeSheetId]: { ...viewport } }
      : sheetViewports;
    set({ activeSheetId: sheetId, sheetViewports: nextViewports });
  },

  setSelectedSheets: (sheetIds) =>
    set({ selectedSheetIds: sheetIds }),

  setHighlightedSheet: (sheetId) =>
    set({ highlightedSheetId: sheetId }),

  setActiveCondition: (conditionId) =>
    set({ activeConditionId: conditionId }),

  setActiveTool: (tool) => {
    const state = get();
    // Invariant: cannot set a drawing tool without an active condition
    // Exception: 'measure' (M key) and 'select' work without condition
    if (
      tool !== null &&
      tool !== 'select' &&
      tool !== 'measure' &&
      !state.activeConditionId
    ) {
      set({ toolRejectionMessage: 'Select a condition first' });
      return;
    }
    // Selecting a tool clears measurement selection (drawing vs selecting exclusive)
    set({
      activeTool: tool,
      toolRejectionMessage: null,
      selectedMeasurementIds: tool && tool !== 'select' ? [] : state.selectedMeasurementIds,
    });
  },

  setIsDrawing: (isDrawing) =>
    set({ isDrawing }),

  setCurrentPoints: (points) =>
    set({ currentPoints: points }),

  addCurrentPoint: (point) =>
    set((s) => ({ currentPoints: [...s.currentPoints, point] })),

  setSelectedMeasurements: (ids) =>
    set({ selectedMeasurementIds: ids }),

  clearSelection: () =>
    set({ selectedMeasurementIds: [] }),

  setViewport: (partial) =>
    set((s) => ({
      viewport: {
        ...s.viewport,
        ...partial,
        zoom: partial.zoom !== undefined
          ? clamp(partial.zoom, MIN_ZOOM, MAX_ZOOM)
          : s.viewport.zoom,
      },
    })),

  setZoom: (zoom) =>
    set((s) => ({
      viewport: { ...s.viewport, zoom: clamp(zoom, MIN_ZOOM, MAX_ZOOM) },
    })),

  setFocusRegion: (region) =>
    set({ focusRegion: region }),

  setLeftPanelWidth: (width) =>
    set({ leftPanelWidth: clamp(width, LEFT_PANEL_MIN_WIDTH, LEFT_PANEL_MAX_WIDTH) }),

  setRightPanelWidth: (width) =>
    set({ rightPanelWidth: clamp(width, RIGHT_PANEL_MIN_WIDTH, RIGHT_PANEL_MAX_WIDTH) }),

  toggleLeftPanel: () =>
    set((s) => ({ leftPanelCollapsed: !s.leftPanelCollapsed })),

  toggleRightPanel: () =>
    set((s) => ({ rightPanelCollapsed: !s.rightPanelCollapsed })),

  setSheetViewMode: (mode) =>
    set({ sheetViewMode: mode }),

  toggleGroupExpanded: (groupName) =>
    set((s) => ({
      expandedGroups: {
        ...s.expandedGroups,
        [groupName]: s.expandedGroups[groupName] === false,
      },
    })),

  setExpandedGroups: (groups) =>
    set({ expandedGroups: groups }),

  setSheetSearchQuery: (query) =>
    set({ sheetSearchQuery: query }),

  setAutoTabEnabled: (enabled) =>
    set({ autoTabEnabled: enabled }),

  setPendingPrediction: (pending) =>
    set({ pendingPrediction: pending }),

  setGhostPrediction: (prediction) =>
    set({ ghostPrediction: prediction }),

  clearGhostPrediction: () =>
    set({ ghostPrediction: null }),

  toggleAiConfidenceOverlay: () =>
    set((s) => ({ aiConfidenceOverlay: !s.aiConfidenceOverlay })),

  setBatchAiTaskId: (taskId) =>
    set({ batchAiTaskId: taskId }),

  clearBatchAiTaskId: () =>
    set({ batchAiTaskId: null }),

  clearToolRejection: () =>
    set({ toolRejectionMessage: null }),

  toggleReviewMode: () => {
    const state = get();
    const newMode = !state.reviewMode;
    set({
      reviewMode: newMode,
      reviewCurrentId: newMode ? state.reviewCurrentId : null,
      activeTool: newMode ? 'select' : state.activeTool,
    });
  },

  setReviewMode: (active) => {
    set({
      reviewMode: active,
      reviewCurrentId: active ? get().reviewCurrentId : null,
      activeTool: active ? 'select' : get().activeTool,
    });
  },

  setReviewCurrentId: (id) =>
    set({ reviewCurrentId: id }),

  setReviewConfidenceFilter: (threshold) =>
    set({ reviewConfidenceFilter: clamp(threshold, 0, 1) }),

  advanceReview: (nextId) =>
    set({
      reviewCurrentId: nextId,
      selectedMeasurementIds: nextId ? [nextId] : [],
    }),

  toggleSnapToGrid: () =>
    set((s) => ({ snapToGrid: !s.snapToGrid })),

  setGridSize: (size) =>
    set({ gridSize: Math.max(1, size) }),

  toggleShowGrid: () =>
    set((s) => ({ showGrid: !s.showGrid })),

  resetDrawingState: () =>
    set({
      isDrawing: false,
      currentPoints: [],
      activeTool: 'select',
    }),

  escapeAll: () =>
    set({
      isDrawing: false,
      currentPoints: [],
      activeTool: 'select',
      selectedMeasurementIds: [],
      reviewMode: false,
      reviewCurrentId: null,
      ghostPrediction: null,
    }),
}));

// ============================================================================
// Selectors
// ============================================================================

export const selectActiveSheetId = (s: WorkspaceStore) => s.activeSheetId;
export const selectActiveTool = (s: WorkspaceStore) => s.activeTool;
export const selectActiveConditionId = (s: WorkspaceStore) => s.activeConditionId;
export const selectIsDrawing = (s: WorkspaceStore) => s.isDrawing;
export const selectViewport = (s: WorkspaceStore) => s.viewport;
export const selectFocusRegion = (s: WorkspaceStore) => s.focusRegion;
export const selectLeftPanelCollapsed = (s: WorkspaceStore) => s.leftPanelCollapsed;
export const selectRightPanelCollapsed = (s: WorkspaceStore) => s.rightPanelCollapsed;
export const selectSheetViewMode = (s: WorkspaceStore) => s.sheetViewMode;
export const selectSheetSearchQuery = (s: WorkspaceStore) => s.sheetSearchQuery;
export const selectExpandedGroups = (s: WorkspaceStore) => s.expandedGroups;
export const selectHighlightedSheetId = (s: WorkspaceStore) => s.highlightedSheetId;
export const selectToolRejectionMessage = (s: WorkspaceStore) => s.toolRejectionMessage;
export const selectReviewMode = (s: WorkspaceStore) => s.reviewMode;
export const selectReviewCurrentId = (s: WorkspaceStore) => s.reviewCurrentId;
export const selectReviewConfidenceFilter = (s: WorkspaceStore) => s.reviewConfidenceFilter;
export const selectReviewAutoAdvance = (s: WorkspaceStore) => s.reviewAutoAdvance;
export const selectSnapToGrid = (s: WorkspaceStore) => s.snapToGrid;
export const selectGridSize = (s: WorkspaceStore) => s.gridSize;
export const selectShowGrid = (s: WorkspaceStore) => s.showGrid;
export const selectGhostPrediction = (s: WorkspaceStore) => s.ghostPrediction;
export const selectAiConfidenceOverlay = (s: WorkspaceStore) => s.aiConfidenceOverlay;
export const selectBatchAiTaskId = (s: WorkspaceStore) => s.batchAiTaskId;