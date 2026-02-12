import { useCallback } from 'react';
import { useWorkspaceStore } from '@/stores/workspaceStore';
import { MIN_ZOOM, MAX_ZOOM } from '@/lib/constants';
import type { StageSize } from './useStageSize';

interface Position {
  x: number;
  y: number;
}

/**
 * CM-007/008: Workspace-aware canvas controls hook.
 * Reads/writes viewport state from workspaceStore instead of local state.
 */
export function useWorkspaceCanvasControls(
  image: HTMLImageElement | null,
  stageSize: StageSize,
) {
  const viewport = useWorkspaceStore((s) => s.viewport);
  const setViewport = useWorkspaceStore((s) => s.setViewport);
  const setZoom = useWorkspaceStore((s) => s.setZoom);

  const handleZoomIn = useCallback(() => {
    const newZoom = Math.min(viewport.zoom * 1.2, MAX_ZOOM);
    setZoom(newZoom);
  }, [viewport.zoom, setZoom]);

  const handleZoomOut = useCallback(() => {
    const newZoom = Math.max(viewport.zoom / 1.2, MIN_ZOOM);
    setZoom(newZoom);
  }, [viewport.zoom, setZoom]);

  const handleFitToScreen = useCallback(() => {
    if (!image || image.width === 0 || image.height === 0 || !stageSize.width || !stageSize.height) return;

    const scaleX = stageSize.width / image.width;
    const scaleY = stageSize.height / image.height;
    const newZoom = Math.min(scaleX, scaleY) * 0.95;
    const panX = (stageSize.width - image.width * newZoom) / 2;
    const panY = (stageSize.height - image.height * newZoom) / 2;

    setViewport({ zoom: newZoom, panX, panY });
  }, [image, stageSize, setViewport]);

  const handleActualSize = useCallback(() => {
    setViewport({ zoom: 1, panX: 0, panY: 0 });
  }, [setViewport]);

  /** CM-008: Scroll-wheel zoom with pointer-anchoring */
  const handleWheel = useCallback((e: WheelEvent, pointerPos: Position) => {
    e.preventDefault();

    const scaleBy = 1.1;
    const { zoom, panX, panY } = useWorkspaceStore.getState().viewport;
    const newZoom = e.deltaY > 0
      ? Math.max(MIN_ZOOM, zoom / scaleBy)
      : Math.min(MAX_ZOOM, zoom * scaleBy);

    // Anchor zoom around pointer position
    const imageX = (pointerPos.x - panX) / zoom;
    const imageY = (pointerPos.y - panY) / zoom;
    const newPanX = pointerPos.x - imageX * newZoom;
    const newPanY = pointerPos.y - imageY * newZoom;

    setViewport({ zoom: newZoom, panX: newPanX, panY: newPanY });
  }, [setViewport]);

  return {
    viewport,
    handleZoomIn,
    handleZoomOut,
    handleFitToScreen,
    handleActualSize,
    handleWheel,
  };
}
