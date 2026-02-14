import { useState, useCallback, useEffect } from 'react';
import Konva from 'konva';
import { useWorkspaceStore } from '@/stores/workspaceStore';
import type { Point } from '@/stores/workspaceStore';
import type { MeasurementResult } from '@/utils/measurementUtils';

interface Position {
  x: number;
  y: number;
}

interface UseWorkspaceCanvasEventsOptions {
  drawing: {
    tool: string | null;
    isDrawing: boolean;
    points: Point[];
    startDrawing: (point: Point) => void;
    addPoint: (point: Point) => void;
    updatePreview: (point: Point) => void;
    finishDrawing: (overridePoints?: Point[]) => {
      tool: string | null;
      points: Point[];
      previewShape: unknown;
    };
  };
  onMeasurementCreate: (result: MeasurementResult) => void;
  handleWheel: (e: WheelEvent, pointerPos: Position) => void;
}

const CLOSE_DISTANCE = 12;

/**
 * CM-009/014-016: Workspace-aware canvas events hook.
 * Handles panning, drawing, and selection interactions on the Konva Stage.
 * Reads/writes pan state via workspaceStore.
 */
export function useWorkspaceCanvasEvents({
  drawing,
  onMeasurementCreate,
  handleWheel,
}: UseWorkspaceCanvasEventsOptions) {
  const [isPanning, setIsPanning] = useState(false);
  const [panStart, setPanStart] = useState<Position>({ x: 0, y: 0 });
  const [panStartPos, setPanStartPos] = useState<Position>({ x: 0, y: 0 });
  const [isCloseToStart, setIsCloseToStart] = useState(false);

  const setViewport = useWorkspaceStore((s) => s.setViewport);
  const setSelectedMeasurements = useWorkspaceStore((s) => s.setSelectedMeasurements);
  const setActiveCondition = useWorkspaceStore((s) => s.setActiveCondition);

  // Global mouseup to prevent stuck panning
  useEffect(() => {
    const handleGlobalMouseUp = () => {
      if (isPanning) setIsPanning(false);
    };
    window.addEventListener('mouseup', handleGlobalMouseUp);
    return () => window.removeEventListener('mouseup', handleGlobalMouseUp);
  }, [isPanning]);

  // Reset close-to-start when not drawing polygon
  useEffect(() => {
    if (!drawing.isDrawing || drawing.tool !== 'polygon') {
      setIsCloseToStart(false);
    }
  }, [drawing.isDrawing, drawing.tool]);

  const getImagePointFromStage = useCallback((stage: Konva.Stage): Position | null => {
    const pos = stage.getRelativePointerPosition();
    return pos || null;
  }, []);

  const handleStageMouseDown = useCallback((e: Konva.KonvaEventObject<MouseEvent>) => {
    const stage = e.target.getStage();
    if (!stage) return;

    const pointerPos = stage.getPointerPosition();
    if (!pointerPos) return;

    const { viewport, activeTool, activeConditionId } = useWorkspaceStore.getState();
    const isRightClick = e.evt.button === 2;
    const isMiddleClick = e.evt.button === 1;
    const isLeftClick = e.evt.button === 0;

    // Right click or middle mouse = always pan
    if (isRightClick || isMiddleClick) {
      e.evt.preventDefault();
      setIsPanning(true);
      setPanStart({ x: pointerPos.x, y: pointerPos.y });
      setPanStartPos({ x: viewport.panX, y: viewport.panY });
      stage.draggable(false);
      return;
    }

    if (isLeftClick) {
      if (activeTool && activeTool !== 'select') {
        const point = getImagePointFromStage(stage);
        if (!point) return;

        // Check condition requirement for drawing tools
        if (activeTool !== 'measure' && !activeConditionId) {
          useWorkspaceStore.setState({ toolRejectionMessage: 'Select a condition first' });
          return;
        }

        // Point tool: immediate creation
        if (activeTool === 'point') {
          onMeasurementCreate({ tool: 'point', points: [point] });
          return;
        }

        // Rectangle/Circle: click-drag-release
        if (activeTool === 'rectangle' || activeTool === 'circle') {
          if (!drawing.isDrawing) {
            drawing.startDrawing(point);
          }
          return;
        }

        // Line/Polyline/Polygon: click-click
        if (!drawing.isDrawing) {
          drawing.startDrawing(point);
        } else {
          if (activeTool === 'line') {
            onMeasurementCreate({ tool: 'line', points: [drawing.points[0], point] });
            drawing.finishDrawing();
          } else {
            // Polyline/Polygon: skip if double-click
            if (e.evt.detail > 1) return;
            drawing.addPoint(point);
          }
        }
        return;
      }

      // Select tool: click empty stage clears selection, clicking stage starts pan
      if (activeTool === 'select') {
        if (e.target === e.target.getStage()) {
          setSelectedMeasurements([]);
          setActiveCondition(null);
          setIsPanning(true);
          setPanStart({ x: pointerPos.x, y: pointerPos.y });
          setPanStartPos({ x: viewport.panX, y: viewport.panY });
          stage.draggable(false);
        }
        return;
      }

      // Default: pan
      setIsPanning(true);
      setPanStart({ x: pointerPos.x, y: pointerPos.y });
      setPanStartPos({ x: viewport.panX, y: viewport.panY });
      stage.draggable(false);
    }
  }, [drawing, getImagePointFromStage, onMeasurementCreate, setViewport, setSelectedMeasurements, setActiveCondition]);

  const handleStageMouseMove = useCallback((e: Konva.KonvaEventObject<MouseEvent>) => {
    const stage = e.target.getStage();
    if (!stage) return;

    const pointerPos = stage.getPointerPosition();
    if (!pointerPos) return;

    if (isPanning) {
      const dx = pointerPos.x - panStart.x;
      const dy = pointerPos.y - panStart.y;
      setViewport({ panX: panStartPos.x + dx, panY: panStartPos.y + dy });
      return;
    }

    if (drawing.isDrawing) {
      const point = getImagePointFromStage(stage);
      if (point) {
        drawing.updatePreview(point);
        if (drawing.tool === 'polygon' && drawing.points.length >= 3) {
          const first = drawing.points[0];
          const distance = Math.hypot(point.x - first.x, point.y - first.y);
          setIsCloseToStart(distance <= CLOSE_DISTANCE);
        } else {
          setIsCloseToStart(false);
        }
      } else {
        setIsCloseToStart(false);
      }
    }
  }, [isPanning, panStart, panStartPos, drawing, getImagePointFromStage, setViewport]);

  const handleStageMouseUp = useCallback((e: Konva.KonvaEventObject<MouseEvent>) => {
    const stage = e.target.getStage();

    if (isPanning) {
      setIsPanning(false);
      if (stage) stage.draggable(false);
      return;
    }

    // Auto-finish for rectangle and circle on mouse up (drag-release)
    if (drawing.tool === 'rectangle' || drawing.tool === 'circle') {
      if (drawing.isDrawing && drawing.points.length > 0 && stage) {
        const endPoint = getImagePointFromStage(stage);
        if (endPoint) {
          const startPoint = drawing.points[0];
          const dx = Math.abs(endPoint.x - startPoint.x);
          const dy = Math.abs(endPoint.y - startPoint.y);
          const minSize = 5;

          if (dx >= minSize || dy >= minSize) {
            const result = drawing.finishDrawing();
            if (result.tool !== 'select' && result.previewShape) {
              onMeasurementCreate(result as unknown as MeasurementResult);
            }
          } else {
            drawing.finishDrawing(); // Too small, cancel
          }
        } else {
          drawing.finishDrawing();
        }
      }
    }
  }, [isPanning, drawing, getImagePointFromStage, onMeasurementCreate]);

  const handleStageMouseLeave = useCallback(() => {
    if (isPanning) setIsPanning(false);
    setIsCloseToStart(false);
  }, [isPanning]);

  const handleWheelEvent = useCallback((e: Konva.KonvaEventObject<WheelEvent>) => {
    const stage = e.target.getStage();
    if (!stage) return;
    const pointerPos = stage.getPointerPosition();
    if (!pointerPos) return;
    handleWheel(e.evt, pointerPos);
  }, [handleWheel]);

  const handleStageDoubleClick = useCallback((e: Konva.KonvaEventObject<MouseEvent>) => {
    const stage = e.target.getStage();
    if (!stage) return;

    // Polyline: finish if >= 2 points
    if (drawing.tool === 'polyline' && drawing.isDrawing && drawing.points.length >= 2) {
      const point = getImagePointFromStage(stage);
      const lastPoint = drawing.points[drawing.points.length - 1];
      const isNearLast =
        point && lastPoint
          ? Math.hypot(point.x - lastPoint.x, point.y - lastPoint.y) <= CLOSE_DISTANCE
          : false;
      const finalPoints = point && !isNearLast ? [...drawing.points, point] : drawing.points;
      const result = drawing.finishDrawing(finalPoints);
      if (result.tool !== 'select' && result.points.length >= 2) {
        onMeasurementCreate(result as unknown as MeasurementResult);
      }
    }

    // Polygon: finish if >= 2 points
    if (drawing.tool === 'polygon' && drawing.isDrawing && drawing.points.length >= 2) {
      const point = getImagePointFromStage(stage);
      if (!point) return;

      const first = drawing.points[0];
      const distance = Math.hypot(point.x - first.x, point.y - first.y);
      const shouldCloseToStart = drawing.points.length >= 3 && distance <= CLOSE_DISTANCE;
      const lastPoint = drawing.points[drawing.points.length - 1];
      const isNearLast =
        lastPoint && Math.hypot(point.x - lastPoint.x, point.y - lastPoint.y) <= CLOSE_DISTANCE;
      const finalPoints =
        shouldCloseToStart || isNearLast ? drawing.points : [...drawing.points, point];

      const result = drawing.finishDrawing(finalPoints);
      if (result.tool !== 'select' && result.points.length >= 3) {
        onMeasurementCreate(result as unknown as MeasurementResult);
      }
    }
  }, [drawing, getImagePointFromStage, onMeasurementCreate]);

  return {
    isPanning,
    isCloseToStart,
    handleStageMouseDown,
    handleStageMouseMove,
    handleStageMouseUp,
    handleStageMouseLeave,
    handleWheelEvent,
    handleStageDoubleClick,
  };
}
