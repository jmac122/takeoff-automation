/**
 * Utility functions for measurement creation and geometry conversion
 */

export interface Point {
    x: number;
    y: number;
}

export interface RectangleData {
    x: number;
    y: number;
    width: number;
    height: number;
}

export interface CircleData {
    center: Point;
    radius: number;
}

export type GeometryData =
    | { start: Point; end: Point } // line
    | { points: Point[] } // polyline, polygon
    | RectangleData // rectangle
    | CircleData // circle
    | Point; // point

export interface MeasurementResult {
    tool: 'line' | 'polyline' | 'polygon' | 'rectangle' | 'circle' | 'point';
    points?: Point[];
    previewShape?: {
        type: string;
        data: RectangleData | CircleData;
    };
}

type GeometryType = MeasurementResult['tool'];

const hasNumber = (value: unknown): value is number => typeof value === 'number';

const isPoint = (value: unknown): value is Point =>
    typeof value === 'object' &&
    value !== null &&
    hasNumber((value as Point).x) &&
    hasNumber((value as Point).y);

const isLineData = (value: unknown): value is { start: Point; end: Point } =>
    typeof value === 'object' &&
    value !== null &&
    isPoint((value as { start?: Point }).start) &&
    isPoint((value as { end?: Point }).end);

const isPointsData = (value: unknown): value is { points: Point[] } =>
    typeof value === 'object' &&
    value !== null &&
    Array.isArray((value as { points?: Point[] }).points) &&
    (value as { points: Point[] }).points.every(isPoint);

const isRectangleData = (value: unknown): value is RectangleData =>
    typeof value === 'object' &&
    value !== null &&
    hasNumber((value as RectangleData).x) &&
    hasNumber((value as RectangleData).y) &&
    hasNumber((value as RectangleData).width) &&
    hasNumber((value as RectangleData).height);

const isCircleData = (value: unknown): value is CircleData =>
    typeof value === 'object' &&
    value !== null &&
    isPoint((value as CircleData).center) &&
    hasNumber((value as CircleData).radius);

export function offsetGeometryData(
    geometryType: GeometryType,
    geometryData: import('@/types').JsonObject,
    dx: number,
    dy: number
): import('@/types').JsonObject {
    switch (geometryType) {
        case 'line': {
            if (!isLineData(geometryData)) {
                return geometryData;
            }
            const data = geometryData;
            return {
                start: { x: data.start.x + dx, y: data.start.y + dy },
                end: { x: data.end.x + dx, y: data.end.y + dy },
            };
        }
        case 'polyline':
        case 'polygon': {
            if (!isPointsData(geometryData)) {
                return geometryData;
            }
            const data = geometryData;
            return {
                points: data.points.map((point) => ({
                    x: point.x + dx,
                    y: point.y + dy,
                })),
            };
        }
        case 'rectangle': {
            if (!isRectangleData(geometryData)) {
                return geometryData;
            }
            const data = geometryData;
            return {
                x: data.x + dx,
                y: data.y + dy,
                width: data.width,
                height: data.height,
            };
        }
        case 'circle': {
            if (!isCircleData(geometryData)) {
                return geometryData;
            }
            const data = geometryData;
            return {
                center: { x: data.center.x + dx, y: data.center.y + dy },
                radius: data.radius,
            };
        }
        case 'point': {
            if (!isPoint(geometryData)) {
                return geometryData;
            }
            const data = geometryData;
            return {
                x: data.x + dx,
                y: data.y + dy,
            };
        }
        default:
            return geometryData;
    }
}

export function createMeasurementGeometry(result: MeasurementResult | { tool: string; points?: Point[]; previewShape?: { type: string; data: unknown } | null }): {
    geometryType: MeasurementResult['tool'];
    geometryData: GeometryData;
} | null {
    if (!result.tool || result.tool === 'select') return null;

    // Type guard to ensure tool is a valid measurement tool
    const validTools: MeasurementResult['tool'][] = ['line', 'polyline', 'polygon', 'rectangle', 'circle', 'point'];
    if (!validTools.includes(result.tool as MeasurementResult['tool'])) return null;

    const measurementResult = result as MeasurementResult;

    let geometryData: GeometryData | null = null;

    switch (result.tool) {
        case 'line':
            if (!result.points || result.points.length < 2) return null;
            geometryData = {
                start: result.points[0],
                end: result.points[1],
            };
            break;
        case 'polyline':
            if (!result.points || result.points.length < 2) return null;
            geometryData = { points: result.points };
            break;
        case 'polygon':
            if (!result.points || result.points.length < 3) return null;
            geometryData = { points: result.points };
            break;
        case 'rectangle':
            if (!measurementResult.previewShape?.data) return null;
            geometryData = measurementResult.previewShape.data as RectangleData;
            break;
        case 'circle':
            if (!measurementResult.previewShape?.data) return null;
            geometryData = measurementResult.previewShape.data as CircleData;
            break;
        case 'point':
            if (!result.points || result.points.length < 1) return null;
            geometryData = { x: result.points[0].x, y: result.points[0].y };
            break;
        default:
            return null;
    }

    if (!geometryData) return null;

    return {
        geometryType: result.tool,
        geometryData,
    };
}
