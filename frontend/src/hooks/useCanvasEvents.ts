import { useState, useCallback, useEffect } from 'react';
import Konva from 'konva';
import type { DrawingTool } from '@/components/viewer/DrawingToolbar';
import type { Position } from './useCanvasControls';

interface UseCanvasEventsOptions {
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

    // Convert screen coordinates to image coordinates
    // Note: We no longer need zoom/pan since getRelativePointerPosition handles it
    const getImagePointFromStage = useCallback((stage: Konva.Stage): Position | null => {
        // getRelativePointerPosition returns coordinates in the stage's local space
        // which accounts for scaleX/scaleY and x/y transforms
        const pos = stage.getRelativePointerPosition();
        if (!pos) return null;
        console.log(`getImagePointFromStage: relativePos=(${pos.x.toFixed(1)},${pos.y.toFixed(1)})`);
        return pos;
    }, []);

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
                // Use getRelativePointerPosition for accurate image coordinates
                const point = getImagePointFromStage(stage);
                if (!point) return;

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

                // Rectangle and Circle: click-drag-release behavior
                if (drawing.tool === 'rectangle' || drawing.tool === 'circle') {
                    if (!drawing.isDrawing) {
                        drawing.startDrawing(point);
                    }
                    // Don't add points on subsequent clicks for drag tools
                    // Preview updates on mousemove, finish on mouseup
                    return;
                }

                // Line, Polyline, Polygon: click-click behavior
                if (!drawing.isDrawing) {
                    // First click - start drawing
                    drawing.startDrawing(point);
                } else {
                    // Subsequent clicks - add point
                    // For line tool: auto-finish after second point
                    if (drawing.tool === 'line') {
                        // We have 1 point (start), add the end point and finish immediately
                        // Create the measurement directly with both points
                        onMeasurementCreate({
                            tool: 'line',
                            points: [drawing.points[0], point],
                        });
                        drawing.finishDrawing(); // Reset state
                    } else {
                        // For polyline/polygon: just add points, finish on double-click
                        drawing.addPoint(point);
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
    }, [pan, drawing, getImagePointFromStage, onMeasurementCreate, onMeasurementSelect, onConditionRequired]);

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
            const point = getImagePointFromStage(stage);
            if (point) {
                drawing.updatePreview(point);
            }
        }
    }, [isPanning, panStart, panStartPos, drawing, getImagePointFromStage, setPan]);

    const handleStageMouseUp = useCallback((e: Konva.KonvaEventObject<MouseEvent>) => {
        const stage = e.target.getStage();

        if (isPanning) {
            setIsPanning(false);
            if (stage) {
                stage.draggable(false);
            }
            return;
        }

        // Auto-finish for rectangle and circle on mouse up (drag-release)
        if (drawing.tool === 'rectangle' || drawing.tool === 'circle') {
            if (drawing.isDrawing && drawing.points.length > 0 && stage) {
                // Get final mouse position for the end point
                const endPoint = getImagePointFromStage(stage);
                if (endPoint) {
                    // Check minimum size to avoid accidental clicks creating tiny shapes
                    const startPoint = drawing.points[0];
                    const dx = Math.abs(endPoint.x - startPoint.x);
                    const dy = Math.abs(endPoint.y - startPoint.y);
                    const minSize = 5; // Minimum 5 pixels
                    
                    if (dx >= minSize || dy >= minSize) {
                        const result = drawing.finishDrawing();
                        if (result.tool !== 'select' && result.previewShape) {
                            onMeasurementCreate(result as import('@/utils/measurementUtils').MeasurementResult);
                        }
                    } else {
                        // Too small, cancel the drawing
                        drawing.finishDrawing(); // Just reset state without creating
                    }
                } else {
                    drawing.finishDrawing(); // Reset state
                }
            }
        }
    }, [isPanning, drawing, getImagePointFromStage, onMeasurementCreate]);

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
        // Double-click finishes drawing for polyline and polygon
        // (Line tool auto-finishes after 2 points, so no double-click needed)
        if (drawing.tool === 'polyline' || drawing.tool === 'polygon') {
            if (drawing.isDrawing && drawing.points.length >= 2) {
                const result = drawing.finishDrawing();
                if (result.tool !== 'select' && result.points.length >= 2) {
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
