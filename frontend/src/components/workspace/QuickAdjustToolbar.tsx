import {
  ArrowUp,
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  Grid3X3,
  ArrowUpRight,
  Scissors,
  Copy,
  Split,
  Merge,
} from 'lucide-react';
import { useAdjustMeasurement } from '@/hooks/useQuickAdjust';
import { useWorkspaceStore } from '@/stores/workspaceStore';
import type { GeometryAdjustAction } from '@/types';

interface QuickAdjustToolbarProps {
  className?: string;
}

/**
 * Floating toolbar for quick geometry adjustments.
 * Only renders when one or more measurements are selected.
 */
export function QuickAdjustToolbar({ className = '' }: QuickAdjustToolbarProps) {
  const selectedIds = useWorkspaceStore((s) => s.selectedMeasurementIds);
  const snapToGrid = useWorkspaceStore((s) => s.snapToGrid);
  const gridSize = useWorkspaceStore((s) => s.gridSize);
  const adjustMut = useAdjustMeasurement();

  if (selectedIds.length === 0) return null;

  function handleAdjust(action: GeometryAdjustAction, params: Record<string, unknown>) {
    for (const id of selectedIds) {
      adjustMut.mutate({ measurementId: id, action, params });
    }
  }

  const btnBase =
    'rounded p-1.5 text-neutral-400 hover:bg-neutral-700 hover:text-white disabled:opacity-30 transition-colors';
  const btnActive = 'bg-blue-600 text-white';

  return (
    <div
      className={`flex items-center gap-0.5 rounded-lg border border-neutral-700 bg-neutral-800/95 px-1.5 py-1 shadow-lg backdrop-blur-sm ${className}`}
      data-testid="quick-adjust-toolbar"
    >
      {/* Nudge arrows */}
      <div className="flex items-center gap-0.5">
        <button
          className={btnBase}
          onClick={() => handleAdjust('nudge', { direction: 'up', distance_px: 1 })}
          title="Nudge Up (Arrow Up)"
        >
          <ArrowUp size={14} />
        </button>
        <button
          className={btnBase}
          onClick={() => handleAdjust('nudge', { direction: 'down', distance_px: 1 })}
          title="Nudge Down (Arrow Down)"
        >
          <ArrowDown size={14} />
        </button>
        <button
          className={btnBase}
          onClick={() => handleAdjust('nudge', { direction: 'left', distance_px: 1 })}
          title="Nudge Left (Arrow Left)"
        >
          <ArrowLeft size={14} />
        </button>
        <button
          className={btnBase}
          onClick={() => handleAdjust('nudge', { direction: 'right', distance_px: 1 })}
          title="Nudge Right (Arrow Right)"
        >
          <ArrowRight size={14} />
        </button>
      </div>

      <div className="mx-0.5 h-4 w-px bg-neutral-600" />

      {/* Snap to grid */}
      <button
        className={`${btnBase} ${snapToGrid ? btnActive : ''}`}
        onClick={() => handleAdjust('snap_to_grid', { grid_size_px: gridSize })}
        title={`Snap to Grid (Shift+G) — grid: ${gridSize}px`}
      >
        <Grid3X3 size={14} />
      </button>

      {/* Extend */}
      <button
        className={btnBase}
        onClick={() => handleAdjust('extend', { endpoint: 'end', distance_px: 20 })}
        title="Extend End (X)"
      >
        <ArrowUpRight size={14} />
      </button>

      {/* Trim */}
      <button
        className={btnBase}
        onClick={() => {
          // Trim requires a trim_point — use center of canvas as rough default
          // In practice, user clicks on canvas to supply trim_point
          handleAdjust('trim', { trim_point: { x: 0, y: 0 } });
        }}
        title="Trim (T + click)"
      >
        <Scissors size={14} />
      </button>

      {/* Offset */}
      <button
        className={btnBase}
        onClick={() => handleAdjust('offset', { distance_px: 10, corner_type: 'miter' })}
        title="Offset +10px (O)"
      >
        <Copy size={14} />
      </button>

      <div className="mx-0.5 h-4 w-px bg-neutral-600" />

      {/* Split */}
      <button
        className={btnBase}
        onClick={() => {
          // Split requires a split_point — placeholder
          handleAdjust('split', { split_point: { x: 0, y: 0 } });
        }}
        title="Split (/ + click)"
      >
        <Split size={14} />
      </button>

      {/* Join */}
      <button
        className={btnBase}
        disabled={selectedIds.length < 2}
        onClick={() => {
          if (selectedIds.length >= 2) {
            adjustMut.mutate({
              measurementId: selectedIds[0],
              action: 'join',
              params: { other_measurement_id: selectedIds[1], tolerance_px: 15 },
            });
          }
        }}
        title="Join (J) — select 2 measurements"
      >
        <Merge size={14} />
      </button>

      {adjustMut.isPending && (
        <span className="ml-1 text-xs text-neutral-500">...</span>
      )}
    </div>
  );
}
