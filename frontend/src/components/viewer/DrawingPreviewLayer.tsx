import { Layer, Line, Rect, Circle, Group } from 'react-konva';
import type { DrawingState } from '@/hooks/useDrawingState';

interface DrawingPreviewLayerProps {
    previewShape: DrawingState['previewShape'];
    points: { x: number; y: number }[];
    isDrawing: boolean;
    color: string;
    scale: number;
}

export function DrawingPreviewLayer({
    previewShape,
    points,
    isDrawing,
    color,
    scale,
}: DrawingPreviewLayerProps) {
    if (!isDrawing) return null;

    const strokeWidth = 2 / scale;
    const pointRadius = 4 / scale;

    return (
        <Layer listening={false}>
            {/* Render preview shape */}
            {previewShape && (
                <>
                    {previewShape.type === 'line' && (
                        <Line
                            points={[
                                previewShape.data.start.x,
                                previewShape.data.start.y,
                                previewShape.data.end.x,
                                previewShape.data.end.y,
                            ]}
                            stroke={color}
                            strokeWidth={strokeWidth}
                            dash={[10 / scale, 5 / scale]}
                        />
                    )}

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
