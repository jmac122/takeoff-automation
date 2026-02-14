import { useState, useCallback } from 'react';
import { useWorkspaceStore } from '@/stores/workspaceStore';
import type { DrawingTool, Point } from '@/stores/workspaceStore';

export type PreviewShape =
  | { type: 'line'; data: { start: Point; end: Point } }
  | { type: 'polyline'; data: { points: Point[] } }
  | { type: 'polygon'; data: { points: Point[] } }
  | { type: 'rectangle'; data: { x: number; y: number; width: number; height: number } }
  | { type: 'circle'; data: { center: Point; radius: number } };

/**
 * CM-013: Workspace-aware drawing state hook.
 * Bridges workspaceStore (activeTool, isDrawing, currentPoints) with drawing
 * preview logic. Manages point history for per-point undo/redo during drawing.
 */
export function useWorkspaceDrawingState() {
  const activeTool = useWorkspaceStore((s) => s.activeTool);
  const isDrawing = useWorkspaceStore((s) => s.isDrawing);
  const currentPoints = useWorkspaceStore((s) => s.currentPoints);
  const setIsDrawing = useWorkspaceStore((s) => s.setIsDrawing);
  const setCurrentPoints = useWorkspaceStore((s) => s.setCurrentPoints);

  const [previewShape, setPreviewShape] = useState<PreviewShape | null>(null);
  const [pointHistory, setPointHistory] = useState<{ history: Point[][]; index: number }>({
    history: [],
    index: -1,
  });

  const canUndo = pointHistory.index > 0;
  const canRedo =
    pointHistory.index >= 0 && pointHistory.index < pointHistory.history.length - 1;

  const startDrawing = useCallback((point: Point) => {
    setIsDrawing(true);
    const pts = [point];
    setCurrentPoints(pts);
    setPointHistory({ history: [pts], index: 0 });
    setPreviewShape(null);
  }, [setIsDrawing, setCurrentPoints]);

  const addPoint = useCallback((point: Point) => {
    const state = useWorkspaceStore.getState();
    const base = state.currentPoints;
    const next = [...base, point];
    setCurrentPoints(next);
    setPointHistory((prev) => {
      const nextHistory = [...prev.history.slice(0, prev.index + 1), next];
      return { history: nextHistory, index: nextHistory.length - 1 };
    });
  }, [setCurrentPoints]);

  const updatePreview = useCallback((mousePos: Point) => {
    const state = useWorkspaceStore.getState();
    if (!state.isDrawing || state.currentPoints.length === 0) return;
    const pts = state.currentPoints;
    const tool = state.activeTool;

    switch (tool) {
      case 'line':
        if (pts.length === 1) {
          setPreviewShape({ type: 'line', data: { start: pts[0], end: mousePos } });
        }
        break;
      case 'polyline':
        setPreviewShape({ type: 'polyline', data: { points: [...pts, mousePos] } });
        break;
      case 'polygon':
        setPreviewShape({ type: 'polygon', data: { points: [...pts, mousePos] } });
        break;
      case 'rectangle':
        if (pts.length === 1) {
          const s = pts[0];
          setPreviewShape({
            type: 'rectangle',
            data: {
              x: Math.min(s.x, mousePos.x),
              y: Math.min(s.y, mousePos.y),
              width: Math.abs(mousePos.x - s.x),
              height: Math.abs(mousePos.y - s.y),
            },
          });
        }
        break;
      case 'circle':
        if (pts.length === 1) {
          const c = pts[0];
          const radius = Math.hypot(mousePos.x - c.x, mousePos.y - c.y);
          setPreviewShape({ type: 'circle', data: { center: c, radius } });
        }
        break;
    }
  }, []);

  const finishDrawing = useCallback((overridePoints?: Point[]) => {
    const state = useWorkspaceStore.getState();
    const finalPoints = overridePoints ?? state.currentPoints;
    const result = { tool: state.activeTool as DrawingTool, points: finalPoints, previewShape };

    setIsDrawing(false);
    setCurrentPoints([]);
    setPreviewShape(null);
    setPointHistory({ history: [], index: -1 });

    return result;
  }, [previewShape, setIsDrawing, setCurrentPoints]);

  const cancelDrawing = useCallback(() => {
    setIsDrawing(false);
    setCurrentPoints([]);
    setPreviewShape(null);
    setPointHistory({ history: [], index: -1 });
  }, [setIsDrawing, setCurrentPoints]);

  const undo = useCallback(() => {
    setPointHistory((prev) => {
      if (prev.index <= 0) return prev;
      const nextIndex = prev.index - 1;
      setCurrentPoints(prev.history[nextIndex]);
      return { ...prev, index: nextIndex };
    });
  }, [setCurrentPoints]);

  const redo = useCallback(() => {
    setPointHistory((prev) => {
      if (prev.index < 0 || prev.index >= prev.history.length - 1) return prev;
      const nextIndex = prev.index + 1;
      setCurrentPoints(prev.history[nextIndex]);
      return { ...prev, index: nextIndex };
    });
  }, [setCurrentPoints]);

  return {
    tool: activeTool,
    isDrawing,
    points: currentPoints,
    previewShape,
    startDrawing,
    addPoint,
    updatePreview,
    finishDrawing,
    cancelDrawing,
    canUndo,
    canRedo,
    undo,
    redo,
  };
}
