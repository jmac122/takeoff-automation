import { useRef, useEffect, useCallback, useMemo, useState } from 'react';
import { Stage, Layer, Image as KonvaImage, Rect } from 'react-konva';
import type Konva from 'konva';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Loader2 } from 'lucide-react';

import { useWorkspaceStore } from '@/stores/workspaceStore';
import {
  REVIEW_CONFIDENCE_HIGH,
  REVIEW_CONFIDENCE_MEDIUM,
  REVIEW_COLOR_HIGH,
  REVIEW_COLOR_MEDIUM,
  REVIEW_COLOR_LOW,
} from '@/lib/constants';
import type { Condition, JsonObject, Measurement } from '@/types';
import { listPageMeasurements, createMeasurement, updateMeasurement, deleteMeasurement } from '@/api/measurements';
import { useConditions } from '@/hooks/useConditions';
import { usePageImage } from '@/hooks/usePageImage';
import { useStageSize } from '@/hooks/useStageSize';
import { useWorkspaceCanvasControls } from '@/hooks/useWorkspaceCanvasControls';
import { useWorkspaceDrawingState } from '@/hooks/useWorkspaceDrawingState';
import { useWorkspaceCanvasEvents } from '@/hooks/useWorkspaceCanvasEvents';
import { useUndoRedo } from '@/hooks/useUndoRedo';
import { createMeasurementGeometry, offsetGeometryData, type MeasurementResult } from '@/utils/measurementUtils';
import { MeasurementLayer } from '@/components/viewer/MeasurementLayer';
import { DrawingPreviewLayer } from '@/components/viewer/DrawingPreviewLayer';
import { GhostPointLayer } from '@/components/viewer/GhostPointLayer';
import { CalibrationOverlay } from '@/components/viewer/CalibrationOverlay';
import { ScaleDetectionBanner } from '@/components/viewer/ScaleDetectionBanner';
import { MeasurementsPanel } from '@/components/viewer/MeasurementsPanel';
import { MeasurementContextMenu } from './MeasurementContextMenu';
import type { CalibrationState } from '@/hooks/useScaleCalibration';
import type { ScaleDetectionResult } from '@/types';

// ============================================================================
// Props & Helpers
// ============================================================================

interface CenterCanvasProps {
  projectId: string;
  pageId?: string;
  isLoadingSheet?: boolean;
  sheetImageUrl?: string | null;
  scaleValue?: number | null;
  scaleUnit?: string | null;
  pixelsPerUnit?: number | null;
  // Scale calibration
  calibrationState?: CalibrationState;
  calibrationCurrentPoint?: { x: number; y: number } | null;
  onCalibrationClick?: (e: Konva.KonvaEventObject<MouseEvent>) => void;
  onCalibrationMouseMove?: (e: Konva.KonvaEventObject<MouseEvent>) => void;
  // Scale detection
  scaleDetectionResult?: ScaleDetectionResult | null;
  scaleHighlightBox?: { x: number; y: number; width: number; height: number } | null;
  onDismissDetection?: () => void;
  // Scale location display
  showScaleLocation?: boolean;
  scaleLocationBbox?: { x: number; y: number; width: number; height: number } | null;
  // Title block mode
  isTitleBlockMode?: boolean;
  showTitleBlockRegion?: boolean;
  titleBlockRegion?: { x: number; y: number; width: number; height: number } | null;
  onTitleBlockClick?: (e: Konva.KonvaEventObject<MouseEvent>) => void;
  onTitleBlockMouseMove?: (e: Konva.KonvaEventObject<MouseEvent>) => void;
  titleBlockDraftRect?: { x: number; y: number; width: number; height: number } | null;
  // Scale calibrated flag
  isScaleCalibrated?: boolean;
  // Undo/redo
  undoRedo?: ReturnType<typeof useUndoRedo>;
  // Active sheet info
  activeSheetScaleUnit?: string | null;
}

/** Get the review color for a measurement based on AI confidence. */
export function getReviewColor(confidence: number | null | undefined): string {
  if (confidence == null) return REVIEW_COLOR_LOW;
  if (confidence >= REVIEW_CONFIDENCE_HIGH) return REVIEW_COLOR_HIGH;
  if (confidence >= REVIEW_CONFIDENCE_MEDIUM) return REVIEW_COLOR_MEDIUM;
  return REVIEW_COLOR_LOW;
}

/** Filter measurements for canvas rendering. */
export function filterMeasurementsForCanvas(
  measurements: Measurement[],
  reviewMode: boolean,
  confidenceFilter: number,
): Measurement[] {
  return measurements.filter((m) => {
    if (m.is_rejected) return false;
    if (reviewMode && confidenceFilter > 0) {
      const confidence = m.ai_confidence ?? 0;
      if (confidence < confidenceFilter) return false;
    }
    return true;
  });
}

// Tool instructions for overlay
const TOOL_INSTRUCTIONS: Record<string, string> = {
  select: 'Click to select measurements',
  line: 'Click start point, then end point',
  polyline: 'Click to add points, double-click to finish',
  polygon: 'Click to add points, double-click to close',
  rectangle: 'Click and drag to draw rectangle',
  circle: 'Click center, drag to set radius',
  point: 'Click to place point',
  measure: 'Click two points to measure distance',
};

const TOOL_LABELS: Record<string, string> = {
  select: 'Select',
  line: 'Line',
  polyline: 'Polyline',
  polygon: 'Polygon',
  rectangle: 'Rectangle',
  circle: 'Circle',
  point: 'Point',
  measure: 'Measure',
};

// ============================================================================
// Component
// ============================================================================

export function CenterCanvas({
  projectId,
  pageId,
  isLoadingSheet,
  sheetImageUrl,
  pixelsPerUnit,
  scaleUnit,
  calibrationState,
  calibrationCurrentPoint,
  onCalibrationClick,
  onCalibrationMouseMove,
  scaleDetectionResult,
  scaleHighlightBox,
  onDismissDetection,
  showScaleLocation,
  scaleLocationBbox,
  isTitleBlockMode,
  showTitleBlockRegion,
  titleBlockRegion,
  onTitleBlockClick,
  onTitleBlockMouseMove,
  titleBlockDraftRect,
  isScaleCalibrated,
  undoRedo: externalUndoRedo,
  activeSheetScaleUnit,
}: CenterCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const stageRef = useRef<Konva.Stage>(null);
  const hasInitialFitRef = useRef<string | null>(null);

  // ---------------------------------------------------------------------------
  // Store subscriptions
  // ---------------------------------------------------------------------------
  const activeSheetId = useWorkspaceStore((s) => s.activeSheetId);
  const setFocusRegion = useWorkspaceStore((s) => s.setFocusRegion);
  const activeTool = useWorkspaceStore((s) => s.activeTool);
  const activeConditionId = useWorkspaceStore((s) => s.activeConditionId);
  const reviewMode = useWorkspaceStore((s) => s.reviewMode);
  const reviewCurrentId = useWorkspaceStore((s) => s.reviewCurrentId);
  const reviewConfidenceFilter = useWorkspaceStore((s) => s.reviewConfidenceFilter);
  const aiConfidenceOverlay = useWorkspaceStore((s) => s.aiConfidenceOverlay);
  const selectedMeasurementIds = useWorkspaceStore((s) => s.selectedMeasurementIds);
  const setSelectedMeasurements = useWorkspaceStore((s) => s.setSelectedMeasurements);
  const setActiveCondition = useWorkspaceStore((s) => s.setActiveCondition);
  const setViewport = useWorkspaceStore((s) => s.setViewport);

  // Context menu state
  const [contextMenu, setContextMenu] = useState<{
    measurement: Measurement;
    position: { x: number; y: number };
  } | null>(null);

  // Hidden measurements & ordering (local state, like TakeoffViewer)
  const [hiddenMeasurementIds, setHiddenMeasurementIds] = useState<Set<string>>(new Set());
  const [measurementOrder, setMeasurementOrder] = useState<string[]>([]);

  // ---------------------------------------------------------------------------
  // Data fetching: measurements & conditions
  // ---------------------------------------------------------------------------
  const effectivePageId = pageId ?? activeSheetId;

  // CM-021: Fetch page measurements
  const queryClient = useQueryClient();
  const { data: measurementsData } = useQuery({
    queryKey: ['measurements', effectivePageId],
    queryFn: () => listPageMeasurements(effectivePageId!),
    enabled: !!effectivePageId,
  });

  // CM-022: Fetch conditions for color-coding
  const { data: conditionsData } = useConditions(projectId);

  const conditionsMap = useMemo(() => {
    const map = new Map<string, Condition>();
    if (conditionsData?.conditions) {
      for (const c of conditionsData.conditions) {
        map.set(c.id, c);
      }
    }
    return map;
  }, [conditionsData]);

  // All measurements (unfiltered)
  const allMeasurements = measurementsData?.measurements ?? [];

  // Sync measurement order when measurements change
  useEffect(() => {
    if (allMeasurements.length === 0) {
      setMeasurementOrder((prev) => (prev.length === 0 ? prev : []));
      return;
    }
    setMeasurementOrder((prev) => {
      const availableIds = new Set(allMeasurements.map((m) => m.id));
      const filtered = prev.filter((id) => availableIds.has(id));
      const missing = allMeasurements.map((m) => m.id).filter((id) => !filtered.includes(id));
      return [...filtered, ...missing];
    });
  }, [allMeasurements]);

  // Clean up hidden IDs when measurements change
  useEffect(() => {
    if (allMeasurements.length === 0) {
      setHiddenMeasurementIds((prev) => (prev.size === 0 ? prev : new Set()));
      return;
    }
    setHiddenMeasurementIds((prev) => {
      const availableIds = new Set(allMeasurements.map((m) => m.id));
      const next = new Set<string>();
      prev.forEach((id) => { if (availableIds.has(id)) next.add(id); });
      return next;
    });
  }, [allMeasurements]);

  // Order and filter measurements
  const orderedMeasurements = useMemo(() => {
    if (measurementOrder.length === 0) return allMeasurements;
    const orderIndex = new Map(measurementOrder.map((id, i) => [id, i]));
    return [...allMeasurements].sort((a, b) => {
      const ai = orderIndex.get(a.id) ?? 0;
      const bi = orderIndex.get(b.id) ?? 0;
      return ai - bi;
    });
  }, [measurementOrder, allMeasurements]);

  const visibleMeasurements = useMemo(() => {
    const filtered = filterMeasurementsForCanvas(orderedMeasurements, reviewMode, reviewConfidenceFilter);
    return filtered.filter((m) => {
      if (hiddenMeasurementIds.has(m.id)) return false;
      const condition = conditionsMap.get(m.condition_id);
      return condition?.is_visible !== false;
    });
  }, [orderedMeasurements, reviewMode, reviewConfidenceFilter, conditionsMap, hiddenMeasurementIds]);

  // Measurements filtered by selected condition (for MeasurementsPanel)
  const filteredMeasurements = activeConditionId
    ? visibleMeasurements.filter((m) => m.condition_id === activeConditionId)
    : [];

  // ---------------------------------------------------------------------------
  // Image loading & stage sizing
  // ---------------------------------------------------------------------------
  const image = usePageImage(sheetImageUrl);
  const stageSize = useStageSize(containerRef);

  const isImageReady = !!(image && image.complete && image.width > 0 && image.height > 0);

  // ---------------------------------------------------------------------------
  // Canvas controls (zoom, pan)
  // ---------------------------------------------------------------------------
  const canvasControls = useWorkspaceCanvasControls(image, stageSize);
  const { viewport } = canvasControls;

  // CM-011: Fit-to-page on first sheet load
  const { handleFitToScreen } = canvasControls;
  useEffect(() => {
    if (isImageReady && stageSize.width > 0 && stageSize.height > 0) {
      if (hasInitialFitRef.current !== effectivePageId) {
        // Check for saved viewport first (CM-038)
        const saved = useWorkspaceStore.getState().sheetViewports?.[effectivePageId ?? ''];
        if (saved) {
          setViewport(saved);
        } else {
          handleFitToScreen();
        }
        hasInitialFitRef.current = effectivePageId ?? null;
      }
    }
  }, [isImageReady, stageSize, effectivePageId, handleFitToScreen, setViewport]);

  // CM-039: Clear undo stack & reset drawing on sheet switch
  const undoRedo = externalUndoRedo ?? useUndoRedo();
  useEffect(() => {
    undoRedo.clear();
    useWorkspaceStore.getState().resetDrawingState();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [effectivePageId]);

  // ---------------------------------------------------------------------------
  // Drawing state
  // ---------------------------------------------------------------------------
  const drawing = useWorkspaceDrawingState();
  const activeCondition = activeConditionId ? conditionsMap.get(activeConditionId) : undefined;

  // ---------------------------------------------------------------------------
  // Measurement CRUD callbacks
  // ---------------------------------------------------------------------------

  const invalidateMeasurements = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['measurements', effectivePageId] });
    queryClient.invalidateQueries({ queryKey: ['conditions', projectId] });
  }, [queryClient, effectivePageId, projectId]);

  // CM-017/032: Create measurement and push to undo stack
  const handleMeasurementCreate = useCallback(async (result: MeasurementResult) => {
    const geometry = createMeasurementGeometry(result);
    if (!geometry) return;
    if (!activeConditionId || !effectivePageId) return;

    try {
      const created = await createMeasurement(activeConditionId, {
        page_id: effectivePageId,
        geometry_type: geometry.geometryType,
        geometry_data: geometry.geometryData as unknown as JsonObject,
      });

      invalidateMeasurements();
      setSelectedMeasurements([created.id]);

      const capturedConditionId = activeConditionId;
      const capturedPageId = effectivePageId;
      const capturedGeometry = geometry;
      let currentId = created.id;

      undoRedo.push({
        label: `Create ${geometry.geometryType}`,
        undo: async () => {
          await deleteMeasurement(currentId);
          setSelectedMeasurements([]);
          invalidateMeasurements();
        },
        redo: async () => {
          const recreated = await createMeasurement(capturedConditionId, {
            page_id: capturedPageId,
            geometry_type: capturedGeometry.geometryType,
            geometry_data: capturedGeometry.geometryData as unknown as JsonObject,
          });
          currentId = recreated.id;
          setSelectedMeasurements([recreated.id]);
          invalidateMeasurements();
        },
      });
    } catch (err) {
      console.error('Failed to create measurement:', err);
    }
  }, [activeConditionId, effectivePageId, invalidateMeasurements, setSelectedMeasurements, undoRedo]);

  // CM-034: Update measurement (move/edit) and push to undo stack
  const handleMeasurementUpdate = useCallback(async (
    measurementId: string,
    geometryData: JsonObject,
    previousGeometryData?: JsonObject,
  ) => {
    try {
      await updateMeasurement(measurementId, { geometry_data: geometryData });
      invalidateMeasurements();

      if (previousGeometryData) {
        undoRedo.push({
          label: 'Move/edit measurement',
          undo: async () => {
            await updateMeasurement(measurementId, { geometry_data: previousGeometryData });
            invalidateMeasurements();
          },
          redo: async () => {
            await updateMeasurement(measurementId, { geometry_data: geometryData });
            invalidateMeasurements();
          },
        });
      }
    } catch (err) {
      console.error('Failed to update measurement:', err);
    }
  }, [invalidateMeasurements, undoRedo]);

  // CM-033: Delete measurement and push to undo stack
  const handleMeasurementDelete = useCallback(async (measurement: Measurement) => {
    try {
      await deleteMeasurement(measurement.id);
      setSelectedMeasurements([]);
      invalidateMeasurements();

      const capturedData = {
        conditionId: measurement.condition_id,
        pageId: measurement.page_id,
        geometryType: measurement.geometry_type,
        geometryData: measurement.geometry_data,
      };
      let currentId = measurement.id;

      undoRedo.push({
        label: `Delete ${measurement.geometry_type}`,
        undo: async () => {
          const recreated = await createMeasurement(capturedData.conditionId, {
            page_id: capturedData.pageId,
            geometry_type: capturedData.geometryType,
            geometry_data: capturedData.geometryData,
          });
          currentId = recreated.id;
          setSelectedMeasurements([recreated.id]);
          invalidateMeasurements();
        },
        redo: async () => {
          await deleteMeasurement(currentId);
          setSelectedMeasurements([]);
          invalidateMeasurements();
        },
      });
    } catch (err) {
      console.error('Failed to delete measurement:', err);
    }
  }, [invalidateMeasurements, setSelectedMeasurements, undoRedo]);

  // Duplicate measurement (offset by 12px)
  const handleMeasurementDuplicate = useCallback(async (measurement: Measurement) => {
    if (!effectivePageId) return;
    const offset = 12;
    const duplicatedGeometry = offsetGeometryData(
      measurement.geometry_type,
      measurement.geometry_data as JsonObject,
      offset,
      offset,
    );

    try {
      const created = await createMeasurement(measurement.condition_id, {
        page_id: effectivePageId,
        geometry_type: measurement.geometry_type,
        geometry_data: duplicatedGeometry as JsonObject,
      });
      if (!created?.id) return;
      let currentId = created.id;

      invalidateMeasurements();
      setSelectedMeasurements([currentId]);
      setActiveCondition(measurement.condition_id);

      undoRedo.push({
        label: 'Duplicate measurement',
        undo: async () => {
          await deleteMeasurement(currentId);
          setSelectedMeasurements([]);
          invalidateMeasurements();
        },
        redo: async () => {
          const recreated = await createMeasurement(measurement.condition_id, {
            page_id: effectivePageId,
            geometry_type: measurement.geometry_type,
            geometry_data: duplicatedGeometry as JsonObject,
          });
          if (recreated?.id) {
            currentId = recreated.id;
            setSelectedMeasurements([currentId]);
            invalidateMeasurements();
          }
        },
      });
    } catch (err) {
      console.error('Failed to duplicate measurement:', err);
    }
  }, [effectivePageId, invalidateMeasurements, setSelectedMeasurements, setActiveCondition, undoRedo]);

  // Bring measurement to front / send to back
  const bringMeasurementToFront = useCallback((measurement: Measurement) => {
    setMeasurementOrder((prev) => {
      const filtered = prev.filter((id) => id !== measurement.id);
      return [...filtered, measurement.id];
    });
  }, []);

  const sendMeasurementToBack = useCallback((measurement: Measurement) => {
    setMeasurementOrder((prev) => {
      const filtered = prev.filter((id) => id !== measurement.id);
      return [measurement.id, ...filtered];
    });
  }, []);

  // Toggle measurement visibility
  const toggleMeasurementHidden = useCallback((measurement: Measurement) => {
    setHiddenMeasurementIds((prev) => {
      const next = new Set(prev);
      if (next.has(measurement.id)) {
        next.delete(measurement.id);
      } else {
        next.add(measurement.id);
      }
      return next;
    });
  }, []);

  // ---------------------------------------------------------------------------
  // Canvas events
  // ---------------------------------------------------------------------------
  const canvasEvents = useWorkspaceCanvasEvents({
    drawing,
    onMeasurementCreate: handleMeasurementCreate,
    handleWheel: canvasControls.handleWheel,
  });

  // Wrapped event handlers for calibration/title block mode
  const isCalibrating = calibrationState?.isCalibrating ?? false;

  const handleStageMouseDown = useCallback((e: Konva.KonvaEventObject<MouseEvent>) => {
    if (isCalibrating || isTitleBlockMode) {
      // In calibration/title block mode, only allow panning with right/middle click
      if (e.evt.button !== 0) {
        canvasEvents.handleStageMouseDown(e);
      }
      return;
    }
    canvasEvents.handleStageMouseDown(e);
  }, [canvasEvents, isCalibrating, isTitleBlockMode]);

  const handleStageMouseMove = useCallback((e: Konva.KonvaEventObject<MouseEvent>) => {
    if (isTitleBlockMode) {
      onTitleBlockMouseMove?.(e);
      canvasEvents.handleStageMouseMove(e);
      return;
    }
    if (isCalibrating) {
      onCalibrationMouseMove?.(e);
      canvasEvents.handleStageMouseMove(e);
    } else {
      canvasEvents.handleStageMouseMove(e);
    }
  }, [canvasEvents, isCalibrating, isTitleBlockMode, onCalibrationMouseMove, onTitleBlockMouseMove]);

  const handleStageMouseUp = useCallback((e: Konva.KonvaEventObject<MouseEvent>) => {
    if (isCalibrating || isTitleBlockMode) {
      if (e.evt.button !== 0) {
        canvasEvents.handleStageMouseUp(e);
      }
      return;
    }
    canvasEvents.handleStageMouseUp(e);
  }, [canvasEvents, isCalibrating, isTitleBlockMode]);

  const handleStageClick = useCallback((e: Konva.KonvaEventObject<MouseEvent>) => {
    if (isTitleBlockMode) {
      onTitleBlockClick?.(e);
      return;
    }
    if (isCalibrating) {
      onCalibrationClick?.(e);
    }
  }, [isCalibrating, isTitleBlockMode, onCalibrationClick, onTitleBlockClick]);

  // ---------------------------------------------------------------------------
  // Selection & context menu handlers
  // ---------------------------------------------------------------------------
  const handleMeasurementSelect = useCallback((id: string | null) => {
    if (id) {
      setSelectedMeasurements([id]);
      const measurement = allMeasurements.find((m) => m.id === id);
      if (measurement) {
        setActiveCondition(measurement.condition_id);
      }
    } else {
      setSelectedMeasurements([]);
    }
  }, [allMeasurements, setSelectedMeasurements, setActiveCondition]);

  const handleMeasurementContextMenu = useCallback((
    measurement: Measurement,
    event: Konva.KonvaEventObject<PointerEvent | MouseEvent>,
  ) => {
    event.evt.preventDefault();
    setContextMenu({
      measurement,
      position: { x: event.evt.clientX, y: event.evt.clientY },
    });
    setSelectedMeasurements([measurement.id]);
    setActiveCondition(measurement.condition_id);
  }, [setSelectedMeasurements, setActiveCondition]);

  // ---------------------------------------------------------------------------
  // Keyboard shortcuts (CM-019, CM-035)
  // ---------------------------------------------------------------------------
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) return;
      if (useWorkspaceStore.getState().focusRegion !== 'canvas') return;

      // Undo/Redo (CM-035)
      if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
        e.preventDefault();
        if (drawing.isDrawing && drawing.canUndo) {
          drawing.undo();
        } else {
          void undoRedo.undo();
        }
        return;
      }
      if ((e.ctrlKey || e.metaKey) && (e.key === 'Z' || (e.key === 'z' && e.shiftKey))) {
        e.preventDefault();
        if (drawing.isDrawing && drawing.canRedo) {
          drawing.redo();
        } else {
          void undoRedo.redo();
        }
        return;
      }

      // Escape: cancel drawing, calibration, title block, or clear selection
      if (e.key === 'Escape') {
        e.preventDefault();
        if (drawing.isDrawing) {
          drawing.cancelDrawing();
        } else {
          useWorkspaceStore.getState().escapeAll();
        }
        return;
      }

      // Delete selected measurement
      if (e.key === 'Delete' || e.key === 'Backspace') {
        const ids = useWorkspaceStore.getState().selectedMeasurementIds;
        if (ids.length > 0 && !drawing.isDrawing) {
          e.preventDefault();
          const m = allMeasurements.find((m) => m.id === ids[0]);
          if (m) void handleMeasurementDelete(m);
        }
        return;
      }

      // Tool shortcuts (single key, no modifiers) — disabled during calibration/title block
      if (!e.ctrlKey && !e.metaKey && !e.altKey && !isCalibrating && !isTitleBlockMode) {
        const setActiveTool = useWorkspaceStore.getState().setActiveTool;
        switch (e.key.toLowerCase()) {
          case 'v': setActiveTool('select'); break;
          case 'l': setActiveTool('line'); break;
          case 'p': setActiveTool('polyline'); break;
          case 'a': setActiveTool('polygon'); break;
          case 'r': setActiveTool('rectangle'); break;
          case 'c': setActiveTool('circle'); break;
          case 'm': setActiveTool('measure'); break;
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [drawing, undoRedo, allMeasurements, handleMeasurementDelete, isCalibrating, isTitleBlockMode]);

  // ---------------------------------------------------------------------------
  // Cursor management (CM-006)
  // ---------------------------------------------------------------------------
  const cursorStyle = useMemo(() => {
    if (isCalibrating || isTitleBlockMode) return 'crosshair';
    if (canvasEvents.isPanning) return 'grabbing';
    if (activeTool && activeTool !== 'select') return 'crosshair';
    return 'default';
  }, [activeTool, canvasEvents.isPanning, isCalibrating, isTitleBlockMode]);

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------
  const selectedMeasurementId = selectedMeasurementIds[0] ?? null;
  const isEditing = activeTool === 'select';
  const showDrawingOverlay = !!(
    activeTool && activeTool !== 'select' && activeConditionId &&
    !isCalibrating && !isTitleBlockMode
  );

  return (
    <div
      ref={containerRef}
      className="relative h-full w-full bg-neutral-950"
      data-focus-region="canvas"
      data-testid="center-canvas"
      tabIndex={0}
      onFocus={() => setFocusRegion('canvas')}
      style={{ cursor: cursorStyle }}
      onContextMenu={(e) => e.preventDefault()}
    >
      {!activeSheetId ? (
        <div className="flex h-full w-full items-center justify-center text-neutral-500">
          <div className="text-center">
            <p className="text-lg font-medium">No sheet selected</p>
            <p className="mt-1 text-sm">Select a sheet from the left panel to begin</p>
          </div>
        </div>
      ) : isLoadingSheet ? (
        <div className="flex h-full w-full items-center justify-center text-neutral-400">
          <div className="flex flex-col items-center gap-2">
            <Loader2 className="h-8 w-8 animate-spin" />
            <p className="text-sm">Loading sheet...</p>
          </div>
        </div>
      ) : sheetImageUrl && stageSize.width > 0 && stageSize.height > 0 ? (
        <>
          {/* Scale detection banner */}
          {scaleDetectionResult && onDismissDetection && (
            <div className="absolute top-0 left-0 right-0 z-20">
              <ScaleDetectionBanner
                result={scaleDetectionResult}
                onDismiss={onDismissDetection}
              />
            </div>
          )}

          {/* Calibration mode banner */}
          {isCalibrating && (
            <div className="absolute top-0 left-0 right-0 z-20 bg-amber-500 text-black px-4 py-2 font-mono text-sm flex items-center justify-between">
              <span className="font-bold">
                CALIBRATION MODE: Draw a line over a known dimension
              </span>
            </div>
          )}

          {/* Title block mode banner */}
          {isTitleBlockMode && (
            <div className="absolute top-0 left-0 right-0 z-20 bg-sky-500 text-black px-4 py-2 font-mono text-sm flex items-center justify-between">
              <span className="font-bold">
                TITLE BLOCK MODE: Click two corners to set the title block region
              </span>
            </div>
          )}

          {/* CM-001/CM-012: Konva Stage with viewport transform */}
          <Stage
            ref={stageRef}
            width={stageSize.width}
            height={stageSize.height}
            scaleX={viewport.zoom}
            scaleY={viewport.zoom}
            x={viewport.panX}
            y={viewport.panY}
            draggable={false}
            pixelRatio={1}
            onMouseDown={handleStageMouseDown}
            onMouseMove={handleStageMouseMove}
            onMouseUp={handleStageMouseUp}
            onClick={handleStageClick}
            onMouseLeave={canvasEvents.handleStageMouseLeave}
            onWheel={canvasEvents.handleWheelEvent}
            onDblClick={canvasEvents.handleStageDoubleClick}
            onContextMenu={(e) => e.evt.preventDefault()}
          >
            {/* Layer 0: Background image (CM-003) */}
            {isImageReady && (
              <Layer>
                <KonvaImage image={image!} />
              </Layer>
            )}

            {/* Layer 1: Measurement layer (CM-023) */}
            <MeasurementLayer
              measurements={visibleMeasurements}
              conditions={conditionsMap}
              selectedMeasurementId={selectedMeasurementId}
              onMeasurementSelect={handleMeasurementSelect}
              onConditionSelect={setActiveCondition}
              onMeasurementUpdate={handleMeasurementUpdate}
              onMeasurementContextMenu={handleMeasurementContextMenu}
              isEditing={isEditing}
              scale={viewport.zoom}
            />

            {/* Layer 2: Drawing preview (CM-018) */}
            <DrawingPreviewLayer
              previewShape={drawing.previewShape}
              points={drawing.points}
              isDrawing={drawing.isDrawing}
              color={activeCondition?.color ?? '#3B82F6'}
              scale={viewport.zoom}
              isCloseToStart={canvasEvents.isCloseToStart}
              pixelsPerUnit={pixelsPerUnit}
              unitLabel={activeSheetScaleUnit ?? scaleUnit ?? undefined}
            />

            {/* Layer 3: Ghost prediction overlay */}
            <GhostPointLayer scale={viewport.zoom} />

            {/* Title block region overlay (existing saved region) */}
            {showTitleBlockRegion && titleBlockRegion && (
              <Layer>
                <Rect
                  x={titleBlockRegion.x}
                  y={titleBlockRegion.y}
                  width={titleBlockRegion.width}
                  height={titleBlockRegion.height}
                  fill="rgba(34, 197, 94, 0.12)"
                  stroke="rgb(34, 197, 94)"
                  strokeWidth={2 / viewport.zoom}
                  listening={false}
                />
              </Layer>
            )}

            {/* Title block draft rect (being drawn) */}
            {titleBlockDraftRect && (
              <Layer>
                <Rect
                  x={titleBlockDraftRect.x}
                  y={titleBlockDraftRect.y}
                  width={titleBlockDraftRect.width}
                  height={titleBlockDraftRect.height}
                  fill="rgba(59, 130, 246, 0.15)"
                  stroke="rgb(59, 130, 246)"
                  strokeWidth={2 / viewport.zoom}
                  dash={[8 / viewport.zoom, 4 / viewport.zoom]}
                  listening={false}
                />
              </Layer>
            )}

            {/* Scale detection highlight overlay */}
            {scaleHighlightBox && (
              <Layer>
                <Rect
                  x={scaleHighlightBox.x}
                  y={scaleHighlightBox.y}
                  width={scaleHighlightBox.width}
                  height={scaleHighlightBox.height}
                  fill="rgba(251, 191, 36, 0.15)"
                  stroke="rgb(251, 191, 36)"
                  strokeWidth={3 / viewport.zoom}
                  listening={false}
                />
              </Layer>
            )}

            {/* Scale location overlay (historical, from calibration data) */}
            {showScaleLocation && scaleLocationBbox && (
              <Layer>
                <Rect
                  x={scaleLocationBbox.x}
                  y={scaleLocationBbox.y}
                  width={scaleLocationBbox.width}
                  height={scaleLocationBbox.height}
                  fill="rgba(34, 197, 94, 0.15)"
                  stroke="rgb(34, 197, 94)"
                  strokeWidth={3 / viewport.zoom}
                  listening={false}
                />
              </Layer>
            )}

            {/* Calibration overlay */}
            {isCalibrating && calibrationState && (
              <CalibrationOverlay
                calibrationLine={calibrationState.calibrationLine}
                startPoint={calibrationState.startPoint}
                isDrawing={calibrationState.isDrawing}
                currentPoint={calibrationCurrentPoint ?? null}
                pixelDistance={calibrationState.pixelDistance}
                scale={viewport.zoom}
              />
            )}
          </Stage>

          {/* HTML overlays on top of canvas */}

          {/* Scale warning */}
          {isScaleCalibrated === false && activeSheetId && (
            <div className="absolute top-4 left-1/2 z-10 -translate-x-1/2 rounded-lg border border-amber-500/50 bg-amber-500/20 px-4 py-2 text-sm text-amber-400 shadow-lg">
              Scale not calibrated. Measurements will not be accurate.
            </div>
          )}

          {/* Review mode indicator */}
          {reviewMode && (
            <div className="absolute left-2 top-2 z-10 rounded bg-green-600/80 px-2 py-1 text-xs font-medium text-white">
              Review Mode ({visibleMeasurements.length} measurements)
            </div>
          )}

          {/* Current review measurement indicator */}
          {reviewMode && reviewCurrentId && (
            <div className="absolute bottom-2 left-2 z-10 rounded bg-neutral-900/80 px-2 py-1 text-xs text-neutral-300">
              Reviewing: {reviewCurrentId.slice(0, 8)}...
            </div>
          )}

          {/* Drawing instructions overlay (CM-020) */}
          {showDrawingOverlay && (
            <div className="absolute right-4 top-4 z-10 rounded-lg border border-neutral-700 bg-neutral-900/90 px-3 py-2 text-xs text-neutral-200 shadow-lg backdrop-blur">
              <div className="flex items-center justify-between gap-3 text-[10px] uppercase tracking-widest text-neutral-400">
                <span>Drawing mode</span>
                <span>{drawing.isDrawing ? 'Drawing' : 'Ready'}</span>
              </div>
              <div className="mt-1 text-sm font-semibold text-white">
                {TOOL_LABELS[activeTool ?? ''] ?? activeTool}
                {activeCondition ? ` - ${activeCondition.name}` : ''}
              </div>
              <div className="mt-1 text-xs text-neutral-300">
                {TOOL_INSTRUCTIONS[activeTool ?? ''] ?? ''}
              </div>
              {canvasEvents.isCloseToStart && activeTool === 'polygon' && (
                <div className="mt-1 text-xs text-amber-300">Click the first point to close.</div>
              )}
              <div className="mt-1 text-[10px] uppercase text-neutral-500">Esc cancels</div>
            </div>
          )}

          {/* AI Confidence Overlay indicator */}
          {aiConfidenceOverlay && (
            <div className="absolute left-2 bottom-8 z-10 rounded bg-neutral-900/80 px-2 py-1 text-xs text-neutral-300">
              AI Confidence Colors Active
            </div>
          )}

          {/* Measurements panel (per-condition list) */}
          {filteredMeasurements.length > 0 && !isCalibrating && !isTitleBlockMode && (
            <MeasurementsPanel
              measurements={filteredMeasurements}
              selectedMeasurementId={selectedMeasurementId}
              onSelectMeasurement={(id) => {
                const measurement = allMeasurements.find((m) => m.id === id);
                handleMeasurementSelect(id);
                if (measurement) {
                  setActiveCondition(measurement.condition_id);
                }
              }}
            />
          )}

          {/* Context menu */}
          {contextMenu && (
            <MeasurementContextMenu
              measurement={contextMenu.measurement}
              position={contextMenu.position}
              onClose={() => setContextMenu(null)}
              onDelete={(m) => void handleMeasurementDelete(m)}
              onDuplicate={(m) => void handleMeasurementDuplicate(m)}
              onBringToFront={bringMeasurementToFront}
              onSendToBack={sendMeasurementToBack}
              onToggleHidden={toggleMeasurementHidden}
              isHidden={hiddenMeasurementIds.has(contextMenu.measurement.id)}
            />
          )}
        </>
      ) : (
        <div className="flex h-full w-full items-center justify-center text-neutral-500">
          <p className="text-sm">Sheet image not available</p>
        </div>
      )}
    </div>
  );
}
