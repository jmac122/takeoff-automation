import { useWorkspaceStore } from '@/stores/workspaceStore';
import { useReviewStats } from '@/hooks/useReviewStats';
import { TOP_TOOLBAR_HEIGHT } from '@/lib/constants';
import {
  MousePointer2,
  Minus,
  Hexagon,
  Square,
  Circle,
  Ruler,
  Undo2,
  Redo2,
  ZoomIn,
  ZoomOut,
  Search,
  Sparkles,
  ScanSearch,
  Grid3X3,
  ClipboardCheck,
  Zap,
  Loader2,
  Palette,
  PanelLeftClose,
  PanelLeftOpen,
  PanelRightClose,
  PanelRightOpen,
} from 'lucide-react';
import type { DrawingTool } from '@/stores/workspaceStore';

const tools: { tool: DrawingTool; icon: React.ReactNode; label: string; shortcut?: string }[] = [
  { tool: 'select', icon: <MousePointer2 size={16} />, label: 'Select', shortcut: 'V' },
  { tool: 'line', icon: <Minus size={16} />, label: 'Line', shortcut: 'L' },
  { tool: 'polyline', icon: <Minus size={16} className="rotate-45" />, label: 'Polyline', shortcut: 'P' },
  { tool: 'polygon', icon: <Hexagon size={16} />, label: 'Polygon', shortcut: 'A' },
  { tool: 'rectangle', icon: <Square size={16} />, label: 'Rectangle', shortcut: 'R' },
  { tool: 'circle', icon: <Circle size={16} />, label: 'Circle', shortcut: 'C' },
  { tool: 'measure', icon: <Ruler size={16} />, label: 'Measure', shortcut: 'M' },
];

interface TopToolbarProps {
  projectId?: string;
  onAutoAccept?: (threshold: number) => void;
  isAutoAccepting?: boolean;
  onRunBatchAi?: () => void;
  isBatchAiRunning?: boolean;
}

export function TopToolbar({ projectId, onAutoAccept, isAutoAccepting, onRunBatchAi, isBatchAiRunning }: TopToolbarProps) {
  const activeTool = useWorkspaceStore((s) => s.activeTool);
  const setActiveTool = useWorkspaceStore((s) => s.setActiveTool);
  const viewport = useWorkspaceStore((s) => s.viewport);
  const setZoom = useWorkspaceStore((s) => s.setZoom);
  const leftPanelCollapsed = useWorkspaceStore((s) => s.leftPanelCollapsed);
  const rightPanelCollapsed = useWorkspaceStore((s) => s.rightPanelCollapsed);
  const toggleLeftPanel = useWorkspaceStore((s) => s.toggleLeftPanel);
  const toggleRightPanel = useWorkspaceStore((s) => s.toggleRightPanel);
  const reviewMode = useWorkspaceStore((s) => s.reviewMode);
  const toggleReviewMode = useWorkspaceStore((s) => s.toggleReviewMode);
  const reviewConfidenceFilter = useWorkspaceStore((s) => s.reviewConfidenceFilter);
  const setReviewConfidenceFilter = useWorkspaceStore((s) => s.setReviewConfidenceFilter);
  const showGrid = useWorkspaceStore((s) => s.showGrid);
  const toggleShowGrid = useWorkspaceStore((s) => s.toggleShowGrid);
  const aiConfidenceOverlay = useWorkspaceStore((s) => s.aiConfidenceOverlay);
  const toggleAiConfidenceOverlay = useWorkspaceStore((s) => s.toggleAiConfidenceOverlay);
  const { data: reviewStats } = useReviewStats(projectId);

  return (
    <div
      className="flex items-center gap-1 border-b border-neutral-700 bg-neutral-900 px-3"
      style={{ height: TOP_TOOLBAR_HEIGHT }}
      data-focus-region="toolbar"
      data-testid="top-toolbar"
    >
      {/* Panel toggles */}
      <button
        className="rounded p-1.5 text-neutral-400 hover:bg-neutral-800 hover:text-white"
        onClick={toggleLeftPanel}
        title={leftPanelCollapsed ? 'Show left panel' : 'Hide left panel'}
      >
        {leftPanelCollapsed ? <PanelLeftOpen size={16} /> : <PanelLeftClose size={16} />}
      </button>

      <div className="mx-1 h-5 w-px bg-neutral-700" />

      {/* Drawing tools */}
      {tools.map(({ tool, icon, label, shortcut }) => (
        <button
          key={tool}
          className={`flex items-center gap-1 rounded px-2 py-1.5 text-xs transition-colors ${
            activeTool === tool
              ? 'bg-blue-600 text-white'
              : 'text-neutral-400 hover:bg-neutral-800 hover:text-white'
          }`}
          onClick={() => setActiveTool(tool)}
          title={`${label}${shortcut ? ` (${shortcut})` : ''}`}
          data-testid={`tool-${tool}`}
        >
          {icon}
          <span className="hidden lg:inline">{label}</span>
        </button>
      ))}

      <div className="mx-1 h-5 w-px bg-neutral-700" />

      {/* Zoom controls */}
      <button
        className="rounded p-1.5 text-neutral-400 hover:bg-neutral-800 hover:text-white"
        onClick={() => setZoom(viewport.zoom - 0.1)}
        title="Zoom out"
      >
        <ZoomOut size={16} />
      </button>
      <span className="min-w-[3rem] text-center text-xs text-neutral-300">
        {Math.round(viewport.zoom * 100)}%
      </span>
      <button
        className="rounded p-1.5 text-neutral-400 hover:bg-neutral-800 hover:text-white"
        onClick={() => setZoom(viewport.zoom + 0.1)}
        title="Zoom in"
      >
        <ZoomIn size={16} />
      </button>

      <div className="mx-1 h-5 w-px bg-neutral-700" />

      {/* Undo/Redo */}
      <button
        className="rounded p-1.5 text-neutral-400 hover:bg-neutral-800 hover:text-white"
        title="Undo (Ctrl+Z)"
        disabled
      >
        <Undo2 size={16} />
      </button>
      <button
        className="rounded p-1.5 text-neutral-400 hover:bg-neutral-800 hover:text-white"
        title="Redo (Ctrl+Shift+Z)"
        disabled
      >
        <Redo2 size={16} />
      </button>

      <div className="mx-1 h-5 w-px bg-neutral-700" />

      {/* Grid toggle */}
      <button
        className={`rounded p-1.5 transition-colors ${
          showGrid
            ? 'bg-blue-600 text-white'
            : 'text-neutral-400 hover:bg-neutral-800 hover:text-white'
        }`}
        onClick={toggleShowGrid}
        title={`${showGrid ? 'Hide' : 'Show'} Grid (G)`}
        data-testid="grid-toggle"
      >
        <Grid3X3 size={16} />
      </button>

      <div className="flex-1" />

      {/* Search */}
      <button
        className="rounded p-1.5 text-neutral-400 hover:bg-neutral-800 hover:text-white"
        title="Search (Ctrl+F)"
      >
        <Search size={16} />
      </button>

      {/* Auto Count */}
      <button
        className="flex items-center gap-1 rounded px-2 py-1.5 text-xs text-cyan-400 hover:bg-neutral-800 hover:text-cyan-300"
        title="Auto Count — Find & count repeated elements"
      >
        <ScanSearch size={16} />
        <span className="hidden lg:inline">Auto Count</span>
      </button>

      {/* AI Assist */}
      <button
        className={`flex items-center gap-1 rounded px-2 py-1.5 text-xs transition-colors ${
          isBatchAiRunning
            ? 'bg-purple-600 text-white'
            : 'text-neutral-400 hover:bg-neutral-800 hover:text-white'
        } disabled:opacity-50`}
        title="AI Assist — Run autonomous AI takeoff on current sheet"
        onClick={onRunBatchAi}
        disabled={isBatchAiRunning}
      >
        {isBatchAiRunning ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}
        <span className="hidden lg:inline">{isBatchAiRunning ? 'AI Running...' : 'AI Assist'}</span>
      </button>

      {/* AI Confidence Overlay Toggle */}
      <button
        className={`rounded p-1.5 transition-colors ${
          aiConfidenceOverlay
            ? 'bg-blue-600 text-white'
            : 'text-neutral-400 hover:bg-neutral-800 hover:text-white'
        }`}
        onClick={toggleAiConfidenceOverlay}
        title={`${aiConfidenceOverlay ? 'Hide' : 'Show'} AI Confidence Colors`}
        data-testid="confidence-overlay-toggle"
      >
        <Palette size={16} />
      </button>

      {/* Review Mode Toggle */}
      <button
        className={`flex items-center gap-1 rounded px-2 py-1.5 text-xs transition-colors ${
          reviewMode
            ? 'bg-green-600 text-white'
            : 'text-neutral-400 hover:bg-neutral-800 hover:text-white'
        }`}
        onClick={toggleReviewMode}
        title="Toggle Review Mode"
        data-testid="review-mode-toggle"
      >
        <ClipboardCheck size={16} />
        <span className="hidden lg:inline">Review</span>
      </button>

      {/* Review mode controls */}
      {reviewMode && (
        <>
          {/* Review progress */}
          {reviewStats && (
            <span className="text-xs text-neutral-300">
              {reviewStats.total - reviewStats.pending}/{reviewStats.total}
            </span>
          )}

          {/* Confidence filter slider */}
          <div className="flex items-center gap-1">
            <input
              type="range"
              min={0}
              max={100}
              value={Math.round(reviewConfidenceFilter * 100)}
              onChange={(e) => setReviewConfidenceFilter(Number(e.target.value) / 100)}
              className="h-1 w-16 cursor-pointer accent-green-500"
              title={`Confidence filter: >= ${Math.round(reviewConfidenceFilter * 100)}%`}
            />
            <span className="text-xs text-neutral-400 min-w-[2.5rem]">
              {`>=${Math.round(reviewConfidenceFilter * 100)}%`}
            </span>
          </div>

          {/* Auto-accept button */}
          <button
            className="flex items-center gap-1 rounded bg-amber-600 px-2 py-1 text-xs font-medium text-white hover:bg-amber-500 disabled:opacity-50"
            onClick={() => onAutoAccept?.(reviewConfidenceFilter || 0.9)}
            disabled={isAutoAccepting}
            title={`Auto-Accept >= ${Math.round((reviewConfidenceFilter || 0.9) * 100)}%`}
          >
            {isAutoAccepting ? <Loader2 size={14} className="animate-spin" /> : <Zap size={14} />}
            <span className="hidden lg:inline">Auto-Accept</span>
          </button>
        </>
      )}

      <div className="mx-1 h-5 w-px bg-neutral-700" />

      {/* Right panel toggle */}
      <button
        className="rounded p-1.5 text-neutral-400 hover:bg-neutral-800 hover:text-white"
        onClick={toggleRightPanel}
        title={rightPanelCollapsed ? 'Show right panel' : 'Hide right panel'}
      >
        {rightPanelCollapsed ? <PanelRightOpen size={16} /> : <PanelRightClose size={16} />}
      </button>
    </div>
  );
}
