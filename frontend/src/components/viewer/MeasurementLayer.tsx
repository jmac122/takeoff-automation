import { Layer, Line, Rect, Circle, Group, Text } from 'react-konva';
import type { KonvaEventObject } from 'konva/lib/Node';

import type { Measurement, Condition } from '@/types';

interface MeasurementLayerProps {
    measurements: Measurement[];
    conditions: Map<string, Condition>;
    selectedMeasurementId: string | null;
    onMeasurementSelect: (id: string | null) => void;
    onMeasurementUpdate: (id: string, geometryData: any) => void;
    isEditing: boolean;
    scale: number; // Viewer zoom scale
}

export function MeasurementLayer({
    measurements,
    conditions,
    selectedMeasurementId,
    onMeasurementSelect,
    onMeasurementUpdate,
    isEditing,
    scale,
}: MeasurementLayerProps) {
    return (
        <Layer>
            {measurements.map((measurement) => {
                const condition = conditions.get(measurement.condition_id);
                if (!condition) return null;

                const isSelected = measurement.id === selectedMeasurementId;

                return (
                    <MeasurementShape
                        key={measurement.id}
                        measurement={measurement}
                        condition={condition}
                        isSelected={isSelected}
                        isEditing={isEditing && isSelected}
                        scale={scale}
                        onClick={() => onMeasurementSelect(measurement.id)}
                        onUpdate={(geometryData) =>
                            onMeasurementUpdate(measurement.id, geometryData)
                        }
                    />
                );
            })}
        </Layer>
    );
}

interface MeasurementShapeProps {
    measurement: Measurement;
    condition: Condition;
    isSelected: boolean;
    isEditing: boolean;
    scale: number;
    onClick: () => void;
    onUpdate: (geometryData: any) => void;
}

function MeasurementShape({
    measurement,
    condition,
    isSelected,
    isEditing,
    scale,
    onClick,
    onUpdate,
}: MeasurementShapeProps) {
    const { geometry_type, geometry_data } = measurement;
    const color = condition.color;
    const strokeWidth = (condition.line_width || 2) / scale;
    const fillOpacity = condition.fill_opacity || 0.3;

    const commonProps = {
        stroke: color,
        strokeWidth: isSelected ? strokeWidth * 1.5 : strokeWidth,
        onClick,
        onTap: onClick,
    };

    switch (geometry_type) {
        case 'line':
            return (
                <LineShape
                    start={geometry_data.start}
                    end={geometry_data.end}
                    {...commonProps}
                    quantity={measurement.quantity}
                    unit={measurement.unit}
                    scale={scale}
                />
            );

        case 'polyline':
            return (
                <PolylineShape
                    points={geometry_data.points}
                    {...commonProps}
                    quantity={measurement.quantity}
                    unit={measurement.unit}
                    scale={scale}
                />
            );

        case 'polygon':
            return (
                <PolygonShape
                    points={geometry_data.points}
                    fill={color}
                    fillOpacity={fillOpacity}
                    {...commonProps}
                    quantity={measurement.quantity}
                    unit={measurement.unit}
                    scale={scale}
                />
            );

        case 'rectangle':
            return (
                <RectangleShape
                    x={geometry_data.x}
                    y={geometry_data.y}
                    width={geometry_data.width}
                    height={geometry_data.height}
                    fill={color}
                    fillOpacity={fillOpacity}
                    {...commonProps}
                    quantity={measurement.quantity}
                    unit={measurement.unit}
                    scale={scale}
                />
            );

        case 'circle':
            return (
                <CircleShape
                    center={geometry_data.center}
                    radius={geometry_data.radius}
                    fill={color}
                    fillOpacity={fillOpacity}
                    {...commonProps}
                    quantity={measurement.quantity}
                    unit={measurement.unit}
                    scale={scale}
                />
            );

        case 'point':
            return (
                <PointShape
                    x={geometry_data.x}
                    y={geometry_data.y}
                    color={color}
                    {...commonProps}
                    scale={scale}
                />
            );

        default:
            return null;
    }
}

// Individual shape components
function LineShape({
    start,
    end,
    stroke,
    strokeWidth,
    onClick,
    onTap,
    quantity,
    unit,
    scale,
}: any) {
    const midX = (start.x + end.x) / 2;
    const midY = (start.y + end.y) / 2;

    return (
        <Group>
            <Line
                points={[start.x, start.y, end.x, end.y]}
                stroke={stroke}
                strokeWidth={strokeWidth}
                onClick={onClick}
                onTap={onTap}
                hitStrokeWidth={20}
            />
            <Text
                x={midX}
                y={midY - 10 / scale}
                text={`${quantity.toFixed(1)} ${unit}`}
                fontSize={12 / scale}
                fill={stroke}
                offsetX={20}
            />
        </Group>
    );
}

function PolylineShape({
    points,
    stroke,
    strokeWidth,
    onClick,
    onTap,
    quantity,
    unit,
    scale,
}: any) {
    const flatPoints = points.flatMap((p: any) => [p.x, p.y]);
    const firstPoint = points[0];

    return (
        <Group>
            <Line
                points={flatPoints}
                stroke={stroke}
                strokeWidth={strokeWidth}
                onClick={onClick}
                onTap={onTap}
                hitStrokeWidth={20}
            />
            <Text
                x={firstPoint.x}
                y={firstPoint.y - 15 / scale}
                text={`${quantity.toFixed(1)} ${unit}`}
                fontSize={12 / scale}
                fill={stroke}
            />
        </Group>
    );
}

function PolygonShape({
    points,
    stroke,
    strokeWidth,
    fill,
    fillOpacity,
    onClick,
    onTap,
    quantity,
    unit,
    scale,
}: any) {
    const flatPoints = points.flatMap((p: any) => [p.x, p.y]);

    // Calculate centroid for label
    const centroidX = points.reduce((sum: number, p: any) => sum + p.x, 0) / points.length;
    const centroidY = points.reduce((sum: number, p: any) => sum + p.y, 0) / points.length;

    return (
        <Group>
            <Line
                points={flatPoints}
                stroke={stroke}
                strokeWidth={strokeWidth}
                fill={fill}
                opacity={fillOpacity}
                closed={true}
                onClick={onClick}
                onTap={onTap}
            />
            <Text
                x={centroidX}
                y={centroidY}
                text={`${quantity.toFixed(1)} ${unit}`}
                fontSize={14 / scale}
                fill={stroke}
                align="center"
                offsetX={30}
                offsetY={7}
            />
        </Group>
    );
}

function RectangleShape({
    x,
    y,
    width,
    height,
    stroke,
    strokeWidth,
    fill,
    fillOpacity,
    onClick,
    onTap,
    quantity,
    unit,
    scale,
}: any) {
    return (
        <Group>
            <Rect
                x={x}
                y={y}
                width={width}
                height={height}
                stroke={stroke}
                strokeWidth={strokeWidth}
                fill={fill}
                opacity={fillOpacity}
                onClick={onClick}
                onTap={onTap}
            />
            <Text
                x={x + width / 2}
                y={y + height / 2}
                text={`${quantity.toFixed(1)} ${unit}`}
                fontSize={14 / scale}
                fill={stroke}
                align="center"
                offsetX={30}
                offsetY={7}
            />
        </Group>
    );
}

function CircleShape({
    center,
    radius,
    stroke,
    strokeWidth,
    fill,
    fillOpacity,
    onClick,
    onTap,
    quantity,
    unit,
    scale,
}: any) {
    return (
        <Group>
            <Circle
                x={center.x}
                y={center.y}
                radius={radius}
                stroke={stroke}
                strokeWidth={strokeWidth}
                fill={fill}
                opacity={fillOpacity}
                onClick={onClick}
                onTap={onTap}
            />
            <Text
                x={center.x}
                y={center.y}
                text={`${quantity.toFixed(1)} ${unit}`}
                fontSize={14 / scale}
                fill={stroke}
                align="center"
                offsetX={30}
                offsetY={7}
            />
        </Group>
    );
}

function PointShape({
    x,
    y,
    color,
    onClick,
    onTap,
    scale,
}: any) {
    const markerSize = 8 / scale;

    return (
        <Group onClick={onClick} onTap={onTap}>
            {/* X marker */}
            <Line
                points={[
                    x - markerSize, y - markerSize,
                    x + markerSize, y + markerSize,
                ]}
                stroke={color}
                strokeWidth={2 / scale}
            />
            <Line
                points={[
                    x + markerSize, y - markerSize,
                    x - markerSize, y + markerSize,
                ]}
                stroke={color}
                strokeWidth={2 / scale}
            />
            <Circle
                x={x}
                y={y}
                radius={markerSize * 1.5}
                stroke={color}
                strokeWidth={1 / scale}
            />
        </Group>
    );
}
