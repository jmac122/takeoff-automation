import { useWorkspaceStore } from '@/stores/workspaceStore';
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

export function TopToolbar() {
  const activeTool = useWorkspaceStore((s) => s.activeTool);
  const setActiveTool = useWorkspaceStore((s) => s.setActiveTool);
  const viewport = useWorkspaceStore((s) => s.viewport);
  const setZoom = useWorkspaceStore((s) => s.setZoom);
  const leftPanelCollapsed = useWorkspaceStore((s) => s.leftPanelCollapsed);
  const rightPanelCollapsed = useWorkspaceStore((s) => s.rightPanelCollapsed);
  const toggleLeftPanel = useWorkspaceStore((s) => s.toggleLeftPanel);
  const toggleRightPanel = useWorkspaceStore((s) => s.toggleRightPanel);

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

      <div className="flex-1" />

      {/* Search */}
      <button
        className="rounded p-1.5 text-neutral-400 hover:bg-neutral-800 hover:text-white"
        title="Search (Ctrl+F)"
      >
        <Search size={16} />
      </button>

      {/* AI Assist */}
      <button
        className="flex items-center gap-1 rounded px-2 py-1.5 text-xs text-neutral-400 hover:bg-neutral-800 hover:text-white"
        title="AI Assist"
      >
        <Sparkles size={16} />
        <span className="hidden lg:inline">AI Assist</span>
      </button>

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
