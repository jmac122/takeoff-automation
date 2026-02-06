/**
 * UI constants for the ForgeX workspace.
 * All magic numbers centralized here per audit Section 4.2.
 */

// ============================================================================
// Zoom
// ============================================================================
export const DEFAULT_ZOOM = 1;
export const MIN_ZOOM = 0.1;
export const MAX_ZOOM = 10;
export const ZOOM_STEP = 0.1;

// ============================================================================
// Canvas & Drawing
// ============================================================================
export const SNAP_THRESHOLD_PX = 10;
export const DEFAULT_STROKE_WIDTH = 2;
export const SELECTION_HANDLE_SIZE = 8;
export const SELECTION_COLOR = '#3B82F6';
export const DEFAULT_FILL_OPACITY = 0.2;

// ============================================================================
// Undo / Redo
// ============================================================================
export const UNDO_STACK_DEPTH = 100;

// ============================================================================
// Panel Dimensions
// ============================================================================
export const LEFT_PANEL_DEFAULT_WIDTH = 280;
export const LEFT_PANEL_MIN_WIDTH = 200;
export const LEFT_PANEL_MAX_WIDTH = 450;

export const RIGHT_PANEL_DEFAULT_WIDTH = 340;
export const RIGHT_PANEL_MIN_WIDTH = 260;
export const RIGHT_PANEL_MAX_WIDTH = 500;

export const TOP_TOOLBAR_HEIGHT = 48;
export const BOTTOM_STATUS_BAR_HEIGHT = 28;

// ============================================================================
// Timing
// ============================================================================
export const AUTOTAB_TIMEOUT_MS = 2000;
export const EDIT_DEBOUNCE_MS = 500;

// ============================================================================
// Scale Confidence Thresholds
// ============================================================================
export const SCALE_CONFIDENCE_HIGH = 0.85;
export const SCALE_CONFIDENCE_MEDIUM = 0.5;

// ============================================================================
// Feature Flags
// ============================================================================
export const ENABLE_NEW_WORKSPACE = true;

// ============================================================================
// Z-Order Layers (lower = further back)
// ============================================================================
export const Z_ORDER = {
  AREAS: 0,
  LINES: 1,
  POINTS: 2,
  SELECTED: 3,
  PREVIEW: 4,
  AI_GHOSTS: 5,
} as const;

// ============================================================================
// LocalStorage Keys
// ============================================================================
export const LS_SHEET_TREE_STATE = 'forgex-sheet-tree-state';
export const LS_LEFT_PANEL_WIDTH = 'forgex-left-panel-width';
export const LS_RIGHT_PANEL_WIDTH = 'forgex-right-panel-width';
export const LS_LEFT_PANEL_COLLAPSED = 'forgex-left-panel-collapsed';
export const LS_RIGHT_PANEL_COLLAPSED = 'forgex-right-panel-collapsed';
export const LS_SHEET_VIEW_MODE = 'forgex-sheet-view-mode';
