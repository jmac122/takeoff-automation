import { Layer, Line, Rect, Circle, Group, Text } from 'react-konva';
import type { DrawingState } from '@/hooks/useDrawingState';

interface DrawingPreviewLayerProps {
    previewShape: DrawingState['previewShape'];
    points: { x: number; y: number }[];
    isDrawing: boolean;
    color: string;
    scale: number;
    /** Pixels per real-world unit (e.g., pixels per foot) */
    pixelsPerUnit?: number | null;
    /** Unit label (e.g., "ft", "in", "m") */
    unitLabel?: string;
}

/** Calculate pixel distance between two points */
function getPixelDistance(start: { x: number; y: number }, end: { x: number; y: number }): number {
    return Math.sqrt(Math.pow(end.x - start.x, 2) + Math.pow(end.y - start.y, 2));
}

/** Format distance for display - shows feet and inches for ft unit */
function formatDistance(pixelDistance: number, pixelsPerUnit?: number | null, unitLabel?: string): string {
    if (pixelsPerUnit && pixelsPerUnit > 0) {
        const realDistance = pixelDistance / pixelsPerUnit;
        
        // For feet, show feet and inches format: XX' YY"
        if (unitLabel === 'ft' || unitLabel === 'foot' || unitLabel === 'feet') {
            const totalInches = realDistance * 12;
            const feet = Math.floor(totalInches / 12);
            const inches = Math.round(totalInches % 12);
            
            // Handle case where inches rounds to 12
            if (inches === 12) {
                return `${feet + 1}' 0"`;
            }
            return `${feet}' ${inches}"`;
        }
        
        // Other units - show decimal format
        const formatted = realDistance < 1 
            ? realDistance.toFixed(2) 
            : realDistance < 10 
                ? realDistance.toFixed(1) 
                : Math.round(realDistance).toString();
        return `${formatted} ${unitLabel || 'units'}`;
    }
    // No scale calibration - show pixels
    return `${Math.round(pixelDistance)} px`;
}

export function DrawingPreviewLayer({
    previewShape,
    points,
    isDrawing,
    color,
    scale,
    pixelsPerUnit,
    unitLabel = 'ft',
}: DrawingPreviewLayerProps) {
    if (!isDrawing) return null;

    const strokeWidth = 2 / scale;
    const pointRadius = 4 / scale;
    const fontSize = 14 / scale;

    return (
        <Layer listening={false}>
            {/* Render preview shape */}
            {previewShape && (
                <>
                    {previewShape.type === 'line' && (() => {
                        const start = previewShape.data.start;
                        const end = previewShape.data.end;
                        const pixelDist = getPixelDistance(start, end);
                        const midX = (start.x + end.x) / 2;
                        const midY = (start.y + end.y) / 2;
                        const distanceText = formatDistance(pixelDist, pixelsPerUnit, unitLabel);
                        console.log(`Line: start=(${start.x.toFixed(1)},${start.y.toFixed(1)}) end=(${end.x.toFixed(1)},${end.y.toFixed(1)}) pixelDist=${pixelDist.toFixed(1)} pixelsPerUnit=${pixelsPerUnit} -> ${distanceText}`);
                        
                        return (
                            <>
                                <Line
                                    points={[start.x, start.y, end.x, end.y]}
                                    stroke={color}
                                    strokeWidth={strokeWidth}
                                    dash={[10 / scale, 5 / scale]}
                                />
                                {/* Distance label */}
                                <Text
                                    x={midX}
                                    y={midY - fontSize - 4 / scale}
                                    text={distanceText}
                                    fontSize={fontSize}
                                    fontFamily="monospace"
                                    fill="#fff"
                                    stroke="#000"
                                    strokeWidth={0.5 / scale}
                                    align="center"
                                    offsetX={distanceText.length * fontSize * 0.3}
                                />
                            </>
                        );
                    })()}

                    {previewShape.type === 'polyline' && (
                        <Line
                            points={previewShape.data.points.flatMap((p: any) => [p.x, p.y])}
                            stroke={color}
                            strokeWidth={strokeWidth}
                            dash={[10 / scale, 5 / scale]}
                        />
                    )}

                    {previewShape.type === 'polygon' && (
                        <Line
                            points={previewShape.data.points.flatMap((p: any) => [p.x, p.y])}
                            stroke={color}
                            strokeWidth={strokeWidth}
                            fill={color}
                            opacity={0.2}
                            closed={true}
                            dash={[10 / scale, 5 / scale]}
                        />
                    )}

                    {previewShape.type === 'rectangle' && (
                        <Rect
                            x={previewShape.data.x}
                            y={previewShape.data.y}
                            width={previewShape.data.width}
                            height={previewShape.data.height}
                            stroke={color}
                            strokeWidth={strokeWidth}
                            fill={color}
                            opacity={0.2}
                            dash={[10 / scale, 5 / scale]}
                        />
                    )}

                    {previewShape.type === 'circle' && (
                        <Circle
                            x={previewShape.data.center.x}
                            y={previewShape.data.center.y}
                            radius={previewShape.data.radius}
                            stroke={color}
                            strokeWidth={strokeWidth}
                            fill={color}
                            opacity={0.2}
                            dash={[10 / scale, 5 / scale]}
                        />
                    )}
                </>
            )}

            {/* Render control points */}
            {points.map((point, index) => (
                <Group key={index}>
                    <Circle
                        x={point.x}
                        y={point.y}
                        radius={pointRadius}
                        fill="white"
                        stroke={color}
                        strokeWidth={strokeWidth}
                    />
                </Group>
            ))}
        </Layer>
    );
}
