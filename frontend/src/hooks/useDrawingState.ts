import { useState, useCallback } from 'react';
import type { DrawingTool } from '@/components/viewer/DrawingToolbar';
import type { JsonObject } from '@/types';

export interface Point {
    x: number;
    y: number;
}

export interface DrawingState {
    tool: DrawingTool;
    isDrawing: boolean;
    points: Point[];
    previewShape: PreviewShape | null;
}

export type LinePreviewData = { start: Point; end: Point };
export type PolylinePreviewData = { points: Point[] };
export type PolygonPreviewData = { points: Point[] };
export type RectanglePreviewData = { x: number; y: number; width: number; height: number };
export type CirclePreviewData = { center: Point; radius: number };

export type PreviewShape =
    | { type: 'line'; data: LinePreviewData }
    | { type: 'polyline'; data: PolylinePreviewData }
    | { type: 'polygon'; data: PolygonPreviewData }
    | { type: 'rectangle'; data: RectanglePreviewData }
    | { type: 'circle'; data: CirclePreviewData };

interface HistoryState {
    action: 'create' | 'update' | 'delete';
    measurementId: string;
    data: JsonObject | null;
}

export function useDrawingState() {
    const [tool, setTool] = useState<DrawingTool>('select');
    const [isDrawing, setIsDrawing] = useState(false);
    const [points, setPoints] = useState<Point[]>([]);
    const [previewShape, setPreviewShape] = useState<DrawingState['previewShape']>(null);

    // Undo/Redo
    const [history, setHistory] = useState<HistoryState[]>([]);
    const [historyIndex, setHistoryIndex] = useState(-1);

    const canUndo = historyIndex >= 0;
    const canRedo = historyIndex < history.length - 1;

    const startDrawing = useCallback((point: Point) => {
        setIsDrawing(true);
        setPoints([point]);
    }, []);

    const addPoint = useCallback((point: Point) => {
        setPoints((prev) => [...prev, point]);
    }, []);

    const updatePreview = useCallback((mousePos: Point) => {
        if (!isDrawing || points.length === 0) return;

        switch (tool) {
            case 'line':
                if (points.length === 1) {
                    setPreviewShape({
                        type: 'line',
                        data: { start: points[0], end: mousePos },
                    });
                }
                break;

            case 'polyline':
                setPreviewShape({
                    type: 'polyline',
                    data: { points: [...points, mousePos] },
                });
                break;

            case 'polygon':
                setPreviewShape({
                    type: 'polygon',
                    data: { points: [...points, mousePos] },
                });
                break;

            case 'rectangle':
                if (points.length === 1) {
                    const start = points[0];
                    setPreviewShape({
                        type: 'rectangle',
                        data: {
                            x: Math.min(start.x, mousePos.x),
                            y: Math.min(start.y, mousePos.y),
                            width: Math.abs(mousePos.x - start.x),
                            height: Math.abs(mousePos.y - start.y),
                        },
                    });
                }
                break;

            case 'circle':
                if (points.length === 1) {
                    const center = points[0];
                    const radius = Math.sqrt(
                        Math.pow(mousePos.x - center.x, 2) + Math.pow(mousePos.y - center.y, 2)
                    );
                    setPreviewShape({
                        type: 'circle',
                        data: { center, radius },
                    });
                }
                break;
        }
    }, [tool, isDrawing, points]);

    const finishDrawing = useCallback(() => {
        const result = { tool, points, previewShape };

        setIsDrawing(false);
        setPoints([]);
        setPreviewShape(null);

        return result;
    }, [tool, points, previewShape]);

    const cancelDrawing = useCallback(() => {
        setIsDrawing(false);
        setPoints([]);
        setPreviewShape(null);
    }, []);

    const undo = useCallback(() => {
        if (canUndo) {
            setHistoryIndex((prev) => prev - 1);
            return history[historyIndex];
        }
    }, [canUndo, history, historyIndex]);

    const redo = useCallback(() => {
        if (canRedo) {
            setHistoryIndex((prev) => prev + 1);
            return history[historyIndex + 1];
        }
    }, [canRedo, history, historyIndex]);

    const addToHistory = useCallback((state: HistoryState) => {
        setHistory((prev) => [...prev.slice(0, historyIndex + 1), state]);
        setHistoryIndex((prev) => prev + 1);
    }, [historyIndex]);

    return {
        tool,
        setTool,
        isDrawing,
        points,
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
        addToHistory,
    };
}
