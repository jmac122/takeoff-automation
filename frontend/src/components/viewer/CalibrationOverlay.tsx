import { Layer, Line, Circle, Text, Group } from 'react-konva';
import type { CalibrationLine, CalibrationPoint } from '@/hooks/useScaleCalibration';

interface CalibrationOverlayProps {
    calibrationLine: CalibrationLine | null;
    startPoint: CalibrationPoint | null;
    isDrawing: boolean;
    currentPoint: CalibrationPoint | null;
    pixelDistance: number | null;
    scale: number;
}

export function CalibrationOverlay({
    calibrationLine,
    startPoint,
    isDrawing,
    currentPoint,
    pixelDistance,
    scale,
}: CalibrationOverlayProps) {
    // Safety check for scale
    const safeScale = scale > 0 && Number.isFinite(scale) ? scale : 1;
    
    // Determine what line to render (either completed or in-progress)
    let line: CalibrationLine | null = null;
    
    if (calibrationLine) {
        line = calibrationLine;
    } else if (isDrawing && startPoint && currentPoint) {
        line = {
            start: startPoint,
            end: currentPoint,
        };
    }

    // Don't render if no line
    if (!line) return null;

    // Safety check: ensure line has valid, finite coordinates
    if (typeof line.start?.x !== 'number' || typeof line.start?.y !== 'number' ||
        typeof line.end?.x !== 'number' || typeof line.end?.y !== 'number' ||
        !Number.isFinite(line.start.x) || !Number.isFinite(line.start.y) ||
        !Number.isFinite(line.end.x) || !Number.isFinite(line.end.y)) {
        return null;
    }

    const strokeWidth = 2 / safeScale;
    const fontSize = 12 / safeScale;
    const circleRadius = 4 / safeScale;

    // Calculate distance from line coordinates
    const dx = line.end.x - line.start.x;
    const dy = line.end.y - line.start.y;
    const calculatedDistance = Math.sqrt(dx * dx + dy * dy);
    
    // Use passed pixelDistance if available, otherwise calculated
    const displayDistance = pixelDistance ?? calculatedDistance;

    // Calculate midpoint for label
    const midX = (line.start.x + line.end.x) / 2;
    const midY = (line.start.y + line.end.y) / 2;

    // Calculate angle for label positioning
    const angle = Math.atan2(dy, dx);
    const labelOffset = 20 / safeScale;
    const labelX = midX + Math.sin(angle) * labelOffset;
    const labelY = midY - Math.cos(angle) * labelOffset;

    // Only show distance label if line is long enough
    const showLabel = displayDistance > 20;

    return (
        <Layer>
            {/* Main calibration line */}
            <Line
                points={[line.start.x, line.start.y, line.end.x, line.end.y]}
                stroke="#f59e0b"
                strokeWidth={strokeWidth}
                dash={[10 / safeScale, 5 / safeScale]}
                lineCap="round"
            />

            {/* Start point */}
            <Circle
                x={line.start.x}
                y={line.start.y}
                radius={circleRadius}
                fill="#f59e0b"
                stroke="#000"
                strokeWidth={1 / safeScale}
            />

            {/* End point */}
            <Circle
                x={line.end.x}
                y={line.end.y}
                radius={circleRadius}
                fill="#f59e0b"
                stroke="#000"
                strokeWidth={1 / safeScale}
            />

            {/* Distance label - only show when line is long enough */}
            {showLabel && (
                <Group x={labelX} y={labelY}>
                    {/* Background for readability */}
                    <Text
                        text={`${Math.round(displayDistance)} px`}
                        fontSize={fontSize}
                        fontFamily="monospace"
                        fill="#000"
                        offsetX={fontSize * 2}
                        offsetY={fontSize / 2}
                        stroke="#000"
                        strokeWidth={3 / safeScale}
                    />
                    {/* Foreground text */}
                    <Text
                        text={`${Math.round(displayDistance)} px`}
                        fontSize={fontSize}
                        fontFamily="monospace"
                        fill="#f59e0b"
                        offsetX={fontSize * 2}
                        offsetY={fontSize / 2}
                    />
                </Group>
            )}
        </Layer>
    );
}
