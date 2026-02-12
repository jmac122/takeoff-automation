import { useRef, useEffect, useCallback, useMemo, useState } from 'react';
import { Stage, Layer, Image as KonvaImage } from 'react-konva';
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
import { createMeasurementGeometry, type MeasurementResult } from '@/utils/measurementUtils';
import { MeasurementLayer } from '@/components/viewer/MeasurementLayer';
import { DrawingPreviewLayer } from '@/components/viewer/DrawingPreviewLayer';
import { GhostPointLayer } from '@/components/viewer/GhostPointLayer';
import { MeasurementContextMenu } from './MeasurementContextMenu';

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

  // Filter measurements: exclude rejected, apply review mode filter, apply condition visibility
  const allMeasurements = measurementsData?.measurements ?? [];
  const visibleMeasurements = useMemo(() => {
    const filtered = filterMeasurementsForCanvas(allMeasurements, reviewMode, reviewConfidenceFilter);
    return filtered.filter((m) => {
      const condition = conditionsMap.get(m.condition_id);
      return condition?.is_visible !== false;
    });
  }, [allMeasurements, reviewMode, reviewConfidenceFilter, conditionsMap]);

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
  const undoRedo = useUndoRedo();
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

      // Push undo action
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

  // ---------------------------------------------------------------------------
  // Canvas events
  // ---------------------------------------------------------------------------
  const canvasEvents = useWorkspaceCanvasEvents({
    drawing,
    onMeasurementCreate: handleMeasurementCreate,
    handleWheel: canvasControls.handleWheel,
  });

  // ---------------------------------------------------------------------------
  // Selection & context menu handlers
  // ---------------------------------------------------------------------------
  const handleMeasurementSelect = useCallback((id: string | null) => {
    if (id) {
      setSelectedMeasurements([id]);
      // Auto-select the condition of the selected measurement
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
      // Don't fire shortcuts when typing in inputs
      const target = e.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) return;
      // Only fire when canvas is focused
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

      // Escape: cancel drawing or clear selection
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

      // Tool shortcuts (single key, no modifiers)
      if (!e.ctrlKey && !e.metaKey && !e.altKey) {
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
  }, [drawing, undoRedo, allMeasurements, handleMeasurementDelete]);

  // ---------------------------------------------------------------------------
  // Cursor management (CM-006)
  // ---------------------------------------------------------------------------
  const cursorStyle = useMemo(() => {
    if (canvasEvents.isPanning) return 'grabbing';
    if (activeTool && activeTool !== 'select') return 'crosshair';
    return 'default';
  }, [activeTool, canvasEvents.isPanning]);

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------
  const selectedMeasurementId = selectedMeasurementIds[0] ?? null;
  const isEditing = activeTool === 'select';
  const showDrawingOverlay = !!(activeTool && activeTool !== 'select' && activeConditionId);

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
            onMouseDown={canvasEvents.handleStageMouseDown}
            onMouseMove={canvasEvents.handleStageMouseMove}
            onMouseUp={canvasEvents.handleStageMouseUp}
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
              unitLabel={scaleUnit ?? undefined}
            />

            {/* Layer 3: Ghost prediction overlay */}
            <GhostPointLayer scale={viewport.zoom} />
          </Stage>

          {/* HTML overlays on top of canvas */}

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

          {/* Context menu */}
          {contextMenu && (
            <MeasurementContextMenu
              measurement={contextMenu.measurement}
              position={contextMenu.position}
              onClose={() => setContextMenu(null)}
              onDelete={(m) => void handleMeasurementDelete(m)}
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
