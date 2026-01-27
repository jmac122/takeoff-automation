import { useState, useCallback } from 'react';
import type { DrawingTool } from '@/components/viewer/DrawingToolbar';

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

export function useDrawingState() {
    const [tool, setTool] = useState<DrawingTool>('select');
    const [isDrawing, setIsDrawing] = useState(false);
    const [points, setPoints] = useState<Point[]>([]);
    const [previewShape, setPreviewShape] = useState<DrawingState['previewShape']>(null);

    const [pointHistoryState, setPointHistoryState] = useState<{
        history: Point[][];
        index: number;
    }>({
        history: [],
        index: -1,
    });

    const canUndo = pointHistoryState.index > 0;
    const canRedo =
        pointHistoryState.index >= 0 &&
        pointHistoryState.index < pointHistoryState.history.length - 1;

    const startDrawing = useCallback((point: Point) => {
        setIsDrawing(true);
        const nextPoints = [point];
        setPointHistoryState({ history: [nextPoints], index: 0 });
        setPoints(nextPoints);
    }, []);

    const addPoint = useCallback((point: Point) => {
        setPointHistoryState((prev) => {
            const basePoints = prev.index >= 0 ? prev.history[prev.index] : points;
            const nextPoints = [...basePoints, point];
            const nextHistory = [...prev.history.slice(0, prev.index + 1), nextPoints];
            setPoints(nextPoints);
            return { history: nextHistory, index: nextHistory.length - 1 };
        });
    }, [points]);

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

    const finishDrawing = useCallback((overridePoints?: Point[]) => {
        const finalPoints = overridePoints ?? points;
        const result = { tool, points: finalPoints, previewShape };

        setIsDrawing(false);
        setPoints([]);
        setPreviewShape(null);
        setPointHistoryState({ history: [], index: -1 });

        return result;
    }, [tool, points, previewShape]);

    const cancelDrawing = useCallback(() => {
        setIsDrawing(false);
        setPoints([]);
        setPreviewShape(null);
        setPointHistoryState({ history: [], index: -1 });
    }, []);

    const undo = useCallback(() => {
        setPointHistoryState((prev) => {
            if (prev.index <= 0) {
                return prev;
            }
            const nextIndex = prev.index - 1;
            setPoints(prev.history[nextIndex]);
            return { ...prev, index: nextIndex };
        });
    }, []);

    const redo = useCallback(() => {
        setPointHistoryState((prev) => {
            if (prev.index < 0 || prev.index >= prev.history.length - 1) {
                return prev;
            }
            const nextIndex = prev.index + 1;
            setPoints(prev.history[nextIndex]);
            return { ...prev, index: nextIndex };
        });
    }, []);

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
    };
}
