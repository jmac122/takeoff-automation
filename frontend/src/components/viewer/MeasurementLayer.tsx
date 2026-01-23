import { Layer, Line, Rect, Circle, Group, Text } from 'react-konva';

import type { Condition, JsonObject, Measurement } from '@/types';

type Point = { x: number; y: number };
type LineData = { start: Point; end: Point };
type PolylineData = { points: Point[] };
type PolygonData = { points: Point[] };
type RectangleData = { x: number; y: number; width: number; height: number };
type CircleData = { center: Point; radius: number };
type PointData = { x: number; y: number };

interface MeasurementLayerProps {
    measurements: Measurement[];
    conditions: Map<string, Condition>;
    selectedMeasurementId: string | null;
    onMeasurementSelect: (id: string | null) => void;
    onMeasurementUpdate: (id: string, geometryData: JsonObject) => void;
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
    onUpdate: (geometryData: JsonObject) => void;
}

function MeasurementShape({
    measurement,
    condition,
    isSelected,
    scale,
    onClick,
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
        case 'line': {
            const lineData = geometry_data as unknown as LineData;
            return (
                <LineShape
                    start={lineData.start}
                    end={lineData.end}
                    {...commonProps}
                    quantity={measurement.quantity}
                    unit={measurement.unit}
                    scale={scale}
                />
            );
        }

        case 'polyline': {
            const polylineData = geometry_data as unknown as PolylineData;
            return (
                <PolylineShape
                    points={polylineData.points}
                    {...commonProps}
                    quantity={measurement.quantity}
                    unit={measurement.unit}
                    scale={scale}
                />
            );
        }

        case 'polygon': {
            const polygonData = geometry_data as unknown as PolygonData;
            return (
                <PolygonShape
                    points={polygonData.points}
                    fill={color}
                    fillOpacity={fillOpacity}
                    {...commonProps}
                    quantity={measurement.quantity}
                    unit={measurement.unit}
                    scale={scale}
                />
            );
        }

        case 'rectangle': {
            const rectangleData = geometry_data as unknown as RectangleData;
            return (
                <RectangleShape
                    x={rectangleData.x}
                    y={rectangleData.y}
                    width={rectangleData.width}
                    height={rectangleData.height}
                    fill={color}
                    fillOpacity={fillOpacity}
                    {...commonProps}
                    quantity={measurement.quantity}
                    unit={measurement.unit}
                    scale={scale}
                />
            );
        }

        case 'circle': {
            const circleData = geometry_data as unknown as CircleData;
            return (
                <CircleShape
                    center={circleData.center}
                    radius={circleData.radius}
                    fill={color}
                    fillOpacity={fillOpacity}
                    {...commonProps}
                    quantity={measurement.quantity}
                    unit={measurement.unit}
                    scale={scale}
                />
            );
        }

        case 'point': {
            const pointData = geometry_data as unknown as PointData;
            return (
                <PointShape
                    x={pointData.x}
                    y={pointData.y}
                    color={color}
                    {...commonProps}
                    scale={scale}
                />
            );
        }

        default:
            return null;
    }
}

// Individual shape components
interface CommonShapeProps {
    stroke: string;
    strokeWidth: number;
    onClick: () => void;
    onTap: () => void;
    quantity: number;
    unit: string;
    scale: number;
}

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
}: { start: Point; end: Point } & CommonShapeProps) {
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
}: { points: Point[] } & CommonShapeProps) {
    const flatPoints = points.flatMap((point) => [point.x, point.y]);
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
}: {
    points: Point[];
    fill: string;
    fillOpacity: number;
} & CommonShapeProps) {
    const flatPoints = points.flatMap((point) => [point.x, point.y]);

    // Calculate centroid for label
    const centroidX = points.reduce((sum, point) => sum + point.x, 0) / points.length;
    const centroidY = points.reduce((sum, point) => sum + point.y, 0) / points.length;

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
}: {
    x: number;
    y: number;
    width: number;
    height: number;
    fill: string;
    fillOpacity: number;
} & CommonShapeProps) {
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
}: {
    center: Point;
    radius: number;
    fill: string;
    fillOpacity: number;
} & CommonShapeProps) {
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
}: {
    x: number;
    y: number;
    color: string;
    onClick: () => void;
    onTap: () => void;
    scale: number;
}) {
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
