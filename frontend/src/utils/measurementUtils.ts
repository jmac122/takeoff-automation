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

export function offsetGeometryData(
    geometryType: GeometryType,
    geometryData: import('@/types').JsonObject,
    dx: number,
    dy: number
): import('@/types').JsonObject {
    switch (geometryType) {
        case 'line': {
            const data = geometryData as unknown as { start: Point; end: Point };
            return {
                start: { x: data.start.x + dx, y: data.start.y + dy },
                end: { x: data.end.x + dx, y: data.end.y + dy },
            };
        }
        case 'polyline':
        case 'polygon': {
            const data = geometryData as unknown as { points: Point[] };
            return {
                points: data.points.map((point) => ({
                    x: point.x + dx,
                    y: point.y + dy,
                })),
            };
        }
        case 'rectangle': {
            const data = geometryData as unknown as RectangleData;
            return {
                x: data.x + dx,
                y: data.y + dy,
                width: data.width,
                height: data.height,
            };
        }
        case 'circle': {
            const data = geometryData as unknown as CircleData;
            return {
                center: { x: data.center.x + dx, y: data.center.y + dy },
                radius: data.radius,
            };
        }
        case 'point': {
            const data = geometryData as unknown as Point;
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
