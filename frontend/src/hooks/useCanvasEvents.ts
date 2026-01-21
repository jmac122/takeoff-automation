import { useState, useCallback, useEffect } from 'react';
import Konva from 'konva';
import type { DrawingTool } from '@/components/viewer/DrawingToolbar';
import type { Position } from './useCanvasControls';

interface UseCanvasEventsOptions {
    zoom: number;
    pan: Position;
    setPan: (pan: Position | ((prev: Position) => Position)) => void;
    drawing: {
        tool: DrawingTool | null;
        isDrawing: boolean;
        points: Position[];
        startDrawing: (point: Position) => void;
        addPoint: (point: Position) => void;
        updatePreview: (point: Position) => void;
        finishDrawing: () => {
            tool: DrawingTool;
            points: Position[];
            previewShape: {
                type: DrawingTool;
                data: unknown;
            } | null;
        };
    };
    onMeasurementCreate: (result: import('@/utils/measurementUtils').MeasurementResult) => void;
    onMeasurementSelect: (id: string | null) => void;
    onConditionRequired: () => boolean;
    handleWheel: (e: WheelEvent, pointerPos: Position) => void;
}

export function useCanvasEvents({
    zoom,
    pan,
    setPan,
    drawing,
    onMeasurementCreate,
    onMeasurementSelect,
    onConditionRequired,
    handleWheel,
}: UseCanvasEventsOptions) {
    const [isPanning, setIsPanning] = useState(false);
    const [panStart, setPanStart] = useState<Position>({ x: 0, y: 0 });
    const [panStartPos, setPanStartPos] = useState<Position>({ x: 0, y: 0 });

    // Global mouseup listener to prevent stuck panning state
    useEffect(() => {
        const handleGlobalMouseUp = () => {
            if (isPanning) {
                setIsPanning(false);
            }
        };

        window.addEventListener('mouseup', handleGlobalMouseUp);
        return () => window.removeEventListener('mouseup', handleGlobalMouseUp);
    }, [isPanning]);

    const getImagePoint = useCallback((pointerPos: Position): Position => {
        return {
            x: (pointerPos.x - pan.x) / zoom,
            y: (pointerPos.y - pan.y) / zoom,
        };
    }, [zoom, pan]);

    const handleStageMouseDown = useCallback((e: Konva.KonvaEventObject<MouseEvent>) => {
        const stage = e.target.getStage();
        if (!stage) return;

        const pointerPos = stage.getPointerPosition();
        if (!pointerPos) return;

        const isRightClick = e.evt.button === 2;
        const isMiddleClick = e.evt.button === 1;
        const isLeftClick = e.evt.button === 0;

        // Right click or middle mouse = always pan
        if (isRightClick || isMiddleClick) {
            e.evt.preventDefault();
            setIsPanning(true);
            setPanStart({ x: pointerPos.x, y: pointerPos.y });
            setPanStartPos({ x: pan.x, y: pan.y });
            stage.draggable(false);
            return;
        }

        // Left click: pan if no drawing tool, or draw if tool is active
        if (isLeftClick) {
            if (drawing.tool && drawing.tool !== 'select') {
                const point = getImagePoint(pointerPos);

                if (!onConditionRequired()) {
                    return;
                }

                // Handle point tool (immediate creation)
                if (drawing.tool === 'point') {
                    onMeasurementCreate({
                        tool: 'point',
                        points: [point],
                    });
                    return;
                }

                // Start or continue drawing
                if (!drawing.isDrawing) {
                    drawing.startDrawing(point);
                } else {
                    drawing.addPoint(point);

                    // Auto-finish for line (2 points)
                    if (drawing.tool === 'line' && drawing.points.length === 1) {
                        const result = drawing.finishDrawing();
                        // Type guard: only create measurement if tool is not 'select'
                        if (result.tool !== 'select') {
                            onMeasurementCreate(result as import('@/utils/measurementUtils').MeasurementResult);
                        }
                    }
                }
                return;
            }

            // If select tool or no tool, allow panning with left click
            setIsPanning(true);
            setPanStart({ x: pointerPos.x, y: pointerPos.y });
            setPanStartPos({ x: pan.x, y: pan.y });
            stage.draggable(false);

            // If select tool, handle selection
            if (drawing.tool === 'select') {
                if (e.target === e.target.getStage()) {
                    onMeasurementSelect(null);
                }
            }
        }
    }, [zoom, pan, drawing, getImagePoint, onMeasurementCreate, onMeasurementSelect, onConditionRequired]);

    const handleStageMouseMove = useCallback((e: Konva.KonvaEventObject<MouseEvent>) => {
        const stage = e.target.getStage();
        if (!stage) return;

        const pointerPos = stage.getPointerPosition();
        if (!pointerPos) return;

        // Handle panning
        if (isPanning) {
            const dx = pointerPos.x - panStart.x;
            const dy = pointerPos.y - panStart.y;
            setPan({
                x: panStartPos.x + dx,
                y: panStartPos.y + dy,
            });
            return;
        }

        // Handle drawing preview
        if (drawing.isDrawing) {
            const point = getImagePoint(pointerPos);
            drawing.updatePreview(point);
        }
    }, [isPanning, panStart, panStartPos, drawing, getImagePoint, setPan]);

    const handleStageMouseUp = useCallback((e: Konva.KonvaEventObject<MouseEvent>) => {
        const stage = e.target.getStage();

        if (isPanning) {
            setIsPanning(false);
            if (stage) {
                stage.draggable(false);
            }
            return;
        }

        // Auto-finish for rectangle and circle on mouse up
        if (drawing.tool === 'rectangle' || drawing.tool === 'circle') {
            if (drawing.isDrawing && drawing.points.length > 0) {
                const result = drawing.finishDrawing();
                // Type guard: only create measurement if tool is not 'select'
                if (result.tool !== 'select') {
                    onMeasurementCreate(result as import('@/utils/measurementUtils').MeasurementResult);
                }
            }
        }
    }, [isPanning, drawing, onMeasurementCreate]);

    const handleStageMouseLeave = useCallback(() => {
        if (isPanning) {
            setIsPanning(false);
        }
    }, [isPanning]);

    const handleWheelEvent = useCallback((e: Konva.KonvaEventObject<WheelEvent>) => {
        const stage = e.target.getStage();
        if (!stage) return;

        const pointerPos = stage.getPointerPosition();
        if (!pointerPos) return;

        handleWheel(e.evt, pointerPos);
    }, [handleWheel]);

    const handleStageDoubleClick = useCallback(() => {
        if (drawing.tool === 'polyline' || drawing.tool === 'polygon') {
            if (drawing.isDrawing && drawing.points.length >= 2) {
                const result = drawing.finishDrawing();
                // Type guard: only create measurement if tool is not 'select'
                if (result.tool !== 'select') {
                    onMeasurementCreate(result as import('@/utils/measurementUtils').MeasurementResult);
                }
            }
        }
    }, [drawing, onMeasurementCreate]);

    return {
        isPanning,
        handleStageMouseDown,
        handleStageMouseMove,
        handleStageMouseUp,
        handleStageMouseLeave,
        handleWheelEvent,
        handleStageDoubleClick,
    };
}
