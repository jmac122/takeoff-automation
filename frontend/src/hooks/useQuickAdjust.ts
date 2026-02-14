import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useCallback, useEffect } from 'react';
import { adjustMeasurement } from '@/api/measurements';
import { useWorkspaceStore } from '@/stores/workspaceStore';
import type { GeometryAdjustAction, GeometryAdjustResponse } from '@/types';

/**
 * React Query mutation for adjusting a measurement's geometry.
 */
export function useAdjustMeasurement() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      measurementId,
      action,
      params,
    }: {
      measurementId: string;
      action: GeometryAdjustAction;
      params: Record<string, unknown>;
    }) => adjustMeasurement(measurementId, { action, params }),

    onSuccess: (_data: GeometryAdjustResponse) => {
      // Invalidate measurement queries so overlays refresh
      queryClient.invalidateQueries({ queryKey: ['measurements'] });
      queryClient.invalidateQueries({ queryKey: ['conditions'] });
    },
  });
}

/**
 * Keyboard-driven quick adjust hook.
 *
 * Listens for keyboard shortcuts when the canvas is focused and a
 * measurement is selected. Dispatches adjust mutations automatically.
 *
 * Shortcuts:
 *  Arrow keys        — nudge 1 px
 *  Shift + Arrow     — nudge 10 px
 *  G                 — snap to grid
 *  X                 — extend end by 20 px
 *  Shift + X         — extend start by 20 px
 *  T                 — (no-op; requires click to set trim point)
 *  O                 — (no-op; requires distance input)
 *  /                 — (no-op; requires click to set split point)
 *  J                 — (no-op; requires second measurement selection)
 */
export function useQuickAdjustKeyboard() {
  const focusRegion = useWorkspaceStore((s) => s.focusRegion);
  const selectedIds = useWorkspaceStore((s) => s.selectedMeasurementIds);
  const snapToGrid = useWorkspaceStore((s) => s.snapToGrid);
  const gridSize = useWorkspaceStore((s) => s.gridSize);
  const toggleSnapToGrid = useWorkspaceStore((s) => s.toggleSnapToGrid);
  const adjustMut = useAdjustMeasurement();

  const handleAdjust = useCallback(
    (action: GeometryAdjustAction, params: Record<string, unknown>) => {
      if (selectedIds.length === 0) return;

      // Apply to all selected measurements
      for (const id of selectedIds) {
        adjustMut.mutate({ measurementId: id, action, params });
      }
    },
    [selectedIds, adjustMut],
  );

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      // Only act when canvas is focused and there is a selection
      if (focusRegion !== 'canvas') return;
      if (selectedIds.length === 0) return;

      // Ignore if user is typing in an input/textarea
      const target = e.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) {
        return;
      }

      const dist = e.shiftKey ? 10 : 1;

      switch (e.key) {
        case 'ArrowUp':
          e.preventDefault();
          handleAdjust('nudge', { direction: 'up', distance_px: dist });
          break;
        case 'ArrowDown':
          e.preventDefault();
          handleAdjust('nudge', { direction: 'down', distance_px: dist });
          break;
        case 'ArrowLeft':
          e.preventDefault();
          handleAdjust('nudge', { direction: 'left', distance_px: dist });
          break;
        case 'ArrowRight':
          e.preventDefault();
          handleAdjust('nudge', { direction: 'right', distance_px: dist });
          break;
        case 'g':
        case 'G':
          if (!e.ctrlKey && !e.metaKey) {
            e.preventDefault();
            if (e.shiftKey) {
              // Shift+G = snap selected to grid
              handleAdjust('snap_to_grid', { grid_size_px: gridSize });
            } else {
              // G = toggle snap mode
              toggleSnapToGrid();
            }
          }
          break;
        case 'x':
        case 'X':
          if (!e.ctrlKey && !e.metaKey) {
            e.preventDefault();
            handleAdjust('extend', {
              endpoint: e.shiftKey ? 'start' : 'end',
              distance_px: 20,
            });
          }
          break;
        default:
          break;
      }
    }

    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [focusRegion, selectedIds, handleAdjust, gridSize, toggleSnapToGrid]);

  return {
    adjust: handleAdjust,
    isAdjusting: adjustMut.isPending,
    snapToGrid,
    gridSize,
    toggleSnapToGrid,
  };
}
