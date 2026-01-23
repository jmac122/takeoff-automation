import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Circle, Group, Line, Rect, Text } from 'react-konva';
import type Konva from 'konva';

import type { Condition, JsonObject, Measurement } from '@/types';
import { offsetGeometryData } from '@/utils/measurementUtils';
import { ShapeTransformer } from './ShapeTransformer';

type Point = { x: number; y: number };
type LineData = { start: Point; end: Point };
type PolylineData = { points: Point[] };
type PolygonData = { points: Point[] };
type RectangleData = { x: number; y: number; width: number; height: number };
type CircleData = { center: Point; radius: number };
type PointData = { x: number; y: number };

interface MeasurementShapeProps {
    measurement: Measurement;
    condition: Condition;
    isSelected: boolean;
    isEditing: boolean;
    scale: number;
    onSelect: () => void;
    onUpdate: (geometryData: JsonObject, previousGeometryData?: JsonObject) => void;
    onContextMenu?: (event: Konva.KonvaEventObject<PointerEvent | MouseEvent>) => void;
}

export function MeasurementShape({
    measurement,
    condition,
    isSelected,
    isEditing,
    scale,
    onSelect,
    onUpdate,
    onContextMenu,
}: MeasurementShapeProps) {
    const [isHovered, setIsHovered] = useState(false);
    const [localGeometry, setLocalGeometry] = useState<JsonObject>(
        measurement.geometry_data as JsonObject
    );
    const geometryBeforeDragRef = useRef<JsonObject | null>(null);
    const rectRef = useRef<Konva.Rect>(null);
    const circleRef = useRef<Konva.Circle>(null);

    useEffect(() => {
        setLocalGeometry(measurement.geometry_data as JsonObject);
    }, [measurement.geometry_data]);

    const strokeWidth = (condition.line_width || 2) / scale;
    const fillOpacity = condition.fill_opacity || 0.3;
    const dash = isSelected ? [6 / scale, 4 / scale] : undefined;
    const baseStrokeWidth = isSelected ? strokeWidth * 1.5 : strokeWidth;
    const displayStrokeWidth = isHovered ? baseStrokeWidth * 1.2 : baseStrokeWidth;

    const handleMouseEnter = useCallback(() => {
        setIsHovered(true);
        document.body.style.cursor = isEditing ? 'move' : 'pointer';
    }, [isEditing]);

    const handleMouseLeave = useCallback(() => {
        setIsHovered(false);
        document.body.style.cursor = '';
    }, []);

    const handleGroupDragStart = useCallback(() => {
        geometryBeforeDragRef.current = localGeometry;
    }, [localGeometry]);

    const handleGroupDragEnd = useCallback(
        (e: Konva.KonvaEventObject<DragEvent>) => {
            const dx = e.target.x();
            const dy = e.target.y();
            if (dx === 0 && dy === 0) {
                geometryBeforeDragRef.current = null;
                return;
            }

            const previous = geometryBeforeDragRef.current ?? localGeometry;
            const next = offsetGeometryData(measurement.geometry_type, localGeometry, dx, dy);
            setLocalGeometry(next);
            e.target.position({ x: 0, y: 0 });
            onUpdate(next, previous);
            geometryBeforeDragRef.current = null;
        },
        [localGeometry, measurement.geometry_type, onUpdate]
    );

    const handleVertexDragStart = useCallback(() => {
        geometryBeforeDragRef.current = localGeometry;
    }, [localGeometry]);

    const handleVertexDragMove = useCallback((index: number, point: Point) => {
        const data = localGeometry as unknown as PolylineData;
        const nextPoints = data.points.map((value, idx) =>
            idx === index ? point : value
        );
        setLocalGeometry({ points: nextPoints });
    }, [localGeometry]);

    const handleVertexDragEnd = useCallback(
        (index: number, point: Point) => {
            const previous = geometryBeforeDragRef.current ?? localGeometry;
            const data = localGeometry as unknown as PolylineData;
            const nextPoints = data.points.map((value, idx) =>
                idx === index ? point : value
            );
            const next = { points: nextPoints };
            setLocalGeometry(next);
            onUpdate(next, previous as JsonObject);
            geometryBeforeDragRef.current = null;
        },
        [localGeometry, onUpdate]
    );

    const handleRectTransformEnd = useCallback(() => {
        const node = rectRef.current;
        if (!node) return;
        const previous = localGeometry;
        const scaleX = node.scaleX();
        const scaleY = node.scaleY();

        node.scaleX(1);
        node.scaleY(1);

        const width = Math.max(2, node.width() * scaleX);
        const height = Math.max(2, node.height() * scaleY);
        const next: RectangleData = {
            x: node.x(),
            y: node.y(),
            width,
            height,
        };
        setLocalGeometry(next as unknown as JsonObject);
        onUpdate(next as unknown as JsonObject, previous);
    }, [localGeometry, onUpdate]);

    const handleCircleTransformEnd = useCallback(() => {
        const node = circleRef.current;
        if (!node) return;
        const previous = localGeometry;
        const scaleX = node.scaleX();
        const scaleY = node.scaleY();
        const radiusScale = Math.max(scaleX, scaleY);

        node.scaleX(1);
        node.scaleY(1);

        const next: CircleData = {
            center: { x: node.x(), y: node.y() },
            radius: Math.max(2, node.radius() * radiusScale),
        };
        setLocalGeometry(next as unknown as JsonObject);
        onUpdate(next as unknown as JsonObject, previous);
    }, [localGeometry, onUpdate]);

    const commonGroupProps = {
        onClick: onSelect,
        onTap: onSelect,
        onMouseEnter: handleMouseEnter,
        onMouseLeave: handleMouseLeave,
        onContextMenu: (e: Konva.KonvaEventObject<PointerEvent | MouseEvent>) => {
            e.evt.preventDefault();
            e.cancelBubble = true;
            onContextMenu?.(e);
        },
        draggable: isSelected && isEditing,
        onDragStart: handleGroupDragStart,
        onDragEnd: handleGroupDragEnd,
    };

    const labelText = useMemo(
        () => `${measurement.quantity.toFixed(1)} ${measurement.unit}`,
        [measurement.quantity, measurement.unit]
    );

    const vertexHandles = useMemo(() => {
        if (!isSelected || !isEditing) return null;
        if (measurement.geometry_type !== 'polyline' && measurement.geometry_type !== 'polygon') {
            return null;
        }
        const data = localGeometry as unknown as PolylineData;
        return data.points.map((point, index) => (
            <Circle
                key={`vertex-${index}`}
                x={point.x}
                y={point.y}
                radius={5 / scale}
                fill="#fff"
                stroke={condition.color}
                strokeWidth={2 / scale}
                draggable
                onDragStart={handleVertexDragStart}
                onDragMove={(e) =>
                    handleVertexDragMove(index, { x: e.target.x(), y: e.target.y() })
                }
                onDragEnd={(e) =>
                    handleVertexDragEnd(index, { x: e.target.x(), y: e.target.y() })
                }
                onMouseEnter={() => {
                    document.body.style.cursor = 'crosshair';
                }}
                onMouseLeave={() => {
                    document.body.style.cursor = '';
                }}
            />
        ));
    }, [
        condition.color,
        handleVertexDragEnd,
        handleVertexDragMove,
        handleVertexDragStart,
        isEditing,
        isSelected,
        localGeometry,
        measurement.geometry_type,
        scale,
    ]);

    switch (measurement.geometry_type) {
        case 'line': {
            const data = localGeometry as unknown as LineData;
            const midX = (data.start.x + data.end.x) / 2;
            const midY = (data.start.y + data.end.y) / 2;
            return (
                <Group {...commonGroupProps}>
                    <Line
                        points={[data.start.x, data.start.y, data.end.x, data.end.y]}
                        stroke={condition.color}
                        strokeWidth={displayStrokeWidth}
                        dash={dash}
                        hitStrokeWidth={20}
                    />
                    <Text
                        x={midX}
                        y={midY - 10 / scale}
                        text={labelText}
                        fontSize={12 / scale}
                        fill={condition.color}
                        offsetX={20}
                    />
                </Group>
            );
        }
        case 'polyline': {
            const data = localGeometry as unknown as PolylineData;
            const flatPoints = data.points.flatMap((point) => [point.x, point.y]);
            const first = data.points[0];
            return (
                <Group {...commonGroupProps}>
                    <Line
                        points={flatPoints}
                        stroke={condition.color}
                        strokeWidth={displayStrokeWidth}
                        dash={dash}
                        hitStrokeWidth={20}
                    />
                    <Text
                        x={first.x}
                        y={first.y - 15 / scale}
                        text={labelText}
                        fontSize={12 / scale}
                        fill={condition.color}
                    />
                    {vertexHandles}
                </Group>
            );
        }
        case 'polygon': {
            const data = localGeometry as unknown as PolygonData;
            const flatPoints = data.points.flatMap((point) => [point.x, point.y]);
            const centroidX = data.points.reduce((sum, point) => sum + point.x, 0) / data.points.length;
            const centroidY = data.points.reduce((sum, point) => sum + point.y, 0) / data.points.length;
            return (
                <Group {...commonGroupProps}>
                    <Line
                        points={flatPoints}
                        stroke={condition.color}
                        strokeWidth={displayStrokeWidth}
                        fill={condition.color}
                        opacity={fillOpacity}
                        closed
                        dash={dash}
                        hitStrokeWidth={20}
                    />
                    <Text
                        x={centroidX}
                        y={centroidY}
                        text={labelText}
                        fontSize={14 / scale}
                        fill={condition.color}
                        align="center"
                        offsetX={30}
                        offsetY={7}
                    />
                    {vertexHandles}
                </Group>
            );
        }
        case 'rectangle': {
            const data = localGeometry as unknown as RectangleData;
            return (
                <Group {...commonGroupProps}>
                    <Rect
                        ref={rectRef}
                        x={data.x}
                        y={data.y}
                        width={data.width}
                        height={data.height}
                        stroke={condition.color}
                        strokeWidth={displayStrokeWidth}
                        fill={condition.color}
                        opacity={fillOpacity}
                        dash={dash}
                        onTransformEnd={handleRectTransformEnd}
                    />
                    <Text
                        x={data.x + data.width / 2}
                        y={data.y + data.height / 2}
                        text={labelText}
                        fontSize={14 / scale}
                        fill={condition.color}
                        align="center"
                        offsetX={30}
                        offsetY={7}
                    />
                    <ShapeTransformer
                        node={rectRef.current}
                        enabled={isSelected && isEditing}
                        scale={scale}
                    />
                    {isSelected && isEditing && (
                        <Rect
                            x={data.x}
                            y={data.y}
                            width={data.width}
                            height={data.height}
                            stroke={condition.color}
                            strokeWidth={1 / scale}
                            dash={[4 / scale, 4 / scale]}
                            listening={false}
                        />
                    )}
                </Group>
            );
        }
        case 'circle': {
            const data = localGeometry as unknown as CircleData;
            return (
                <Group {...commonGroupProps}>
                    <Circle
                        ref={circleRef}
                        x={data.center.x}
                        y={data.center.y}
                        radius={data.radius}
                        stroke={condition.color}
                        strokeWidth={displayStrokeWidth}
                        fill={condition.color}
                        opacity={fillOpacity}
                        dash={dash}
                        onTransformEnd={handleCircleTransformEnd}
                    />
                    <Text
                        x={data.center.x}
                        y={data.center.y}
                        text={labelText}
                        fontSize={14 / scale}
                        fill={condition.color}
                        align="center"
                        offsetX={30}
                        offsetY={7}
                    />
                    <ShapeTransformer
                        node={circleRef.current}
                        enabled={isSelected && isEditing}
                        scale={scale}
                    />
                    {isSelected && isEditing && (
                        <Circle
                            x={data.center.x}
                            y={data.center.y}
                            radius={data.radius}
                            stroke={condition.color}
                            strokeWidth={1 / scale}
                            dash={[4 / scale, 4 / scale]}
                            listening={false}
                        />
                    )}
                </Group>
            );
        }
        case 'point': {
            const data = localGeometry as unknown as PointData;
            const markerSize = 8 / scale;
            return (
                <Group {...commonGroupProps}>
                    <Line
                        points={[data.x - markerSize, data.y - markerSize, data.x + markerSize, data.y + markerSize]}
                        stroke={condition.color}
                        strokeWidth={2 / scale}
                    />
                    <Line
                        points={[data.x + markerSize, data.y - markerSize, data.x - markerSize, data.y + markerSize]}
                        stroke={condition.color}
                        strokeWidth={2 / scale}
                    />
                    <Circle
                        x={data.x}
                        y={data.y}
                        radius={markerSize * 1.5}
                        stroke={condition.color}
                        strokeWidth={1 / scale}
                    />
                </Group>
            );
        }
        default:
            return null;
    }
}
