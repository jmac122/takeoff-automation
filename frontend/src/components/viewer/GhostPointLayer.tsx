/**
 * GhostPointLayer — renders the AutoTab AI prediction as a dashed
 * ghost shape on the Konva canvas.  The user can accept with Tab
 * or dismiss with Esc.
 */

import { useEffect, useRef } from 'react';
import { Circle, Group, Line, Rect, Text } from 'react-konva';
import type Konva from 'konva';

import { useWorkspaceStore, selectGhostPrediction } from '@/stores/workspaceStore';

// Cyan ghost colour to distinguish from real measurements
const GHOST_COLOR = '#06B6D4';
const PULSE_MIN = 0.3;
const PULSE_MAX = 0.7;
const PULSE_DURATION_MS = 1500;

type Point = { x: number; y: number };

interface GhostPointLayerProps {
  scale: number;
}

export function GhostPointLayer({ scale }: GhostPointLayerProps) {
  const prediction = useWorkspaceStore(selectGhostPrediction);
  const groupRef = useRef<Konva.Group>(null);

  // Pulsing opacity animation
  useEffect(() => {
    const node = groupRef.current;
    if (!node || !prediction) return;

    let animFrame: number;
    const animate = () => {
      const t = (Date.now() % PULSE_DURATION_MS) / PULSE_DURATION_MS;
      // Sine wave between PULSE_MIN and PULSE_MAX
      const opacity = PULSE_MIN + (PULSE_MAX - PULSE_MIN) * (0.5 + 0.5 * Math.sin(t * Math.PI * 2));
      node.opacity(opacity);
      node.getLayer()?.batchDraw();
      animFrame = requestAnimationFrame(animate);
    };

    animFrame = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(animFrame);
  }, [prediction]);

  if (!prediction) return null;

  const { geometry_type, geometry_data } = prediction;
  const dash = [8 / scale, 6 / scale];
  const strokeWidth = 2 / scale;
  const labelFontSize = 11 / scale;

  const renderShape = () => {
    switch (geometry_type) {
      case 'line':
      case 'polyline': {
        const points = (geometry_data as { points: Point[] }).points ?? [];
        if (points.length < 2) return null;
        const flatPoints = points.flatMap((p) => [p.x, p.y]);
        return (
          <Line
            points={flatPoints}
            stroke={GHOST_COLOR}
            strokeWidth={strokeWidth}
            dash={dash}
            hitStrokeWidth={0}
            listening={false}
          />
        );
      }
      case 'polygon': {
        const points = (geometry_data as { points: Point[] }).points ?? [];
        if (points.length < 3) return null;
        const flatPoints = points.flatMap((p) => [p.x, p.y]);
        return (
          <Line
            points={flatPoints}
            stroke={GHOST_COLOR}
            strokeWidth={strokeWidth}
            dash={dash}
            closed
            fill={GHOST_COLOR}
            opacity={0.1}
            hitStrokeWidth={0}
            listening={false}
          />
        );
      }
      case 'rectangle': {
        const data = geometry_data as { x: number; y: number; width: number; height: number };
        return (
          <Rect
            x={data.x}
            y={data.y}
            width={data.width}
            height={data.height}
            stroke={GHOST_COLOR}
            strokeWidth={strokeWidth}
            dash={dash}
            fill={GHOST_COLOR}
            opacity={0.1}
            hitStrokeWidth={0}
            listening={false}
          />
        );
      }
      case 'circle': {
        const data = geometry_data as { center: Point; radius: number };
        return (
          <Circle
            x={data.center.x}
            y={data.center.y}
            radius={data.radius}
            stroke={GHOST_COLOR}
            strokeWidth={strokeWidth}
            dash={dash}
            fill={GHOST_COLOR}
            opacity={0.1}
            hitStrokeWidth={0}
            listening={false}
          />
        );
      }
      case 'point': {
        const data = geometry_data as { x: number; y: number };
        const marker = 8 / scale;
        return (
          <>
            <Line
              points={[data.x - marker, data.y - marker, data.x + marker, data.y + marker]}
              stroke={GHOST_COLOR}
              strokeWidth={strokeWidth}
              dash={dash}
              listening={false}
            />
            <Line
              points={[data.x + marker, data.y - marker, data.x - marker, data.y + marker]}
              stroke={GHOST_COLOR}
              strokeWidth={strokeWidth}
              dash={dash}
              listening={false}
            />
            <Circle
              x={data.x}
              y={data.y}
              radius={marker * 1.5}
              stroke={GHOST_COLOR}
              strokeWidth={1 / scale}
              dash={dash}
              listening={false}
            />
          </>
        );
      }
      default:
        return null;
    }
  };

  // Calculate label position — near the first point of the shape
  const getLabelPosition = (): Point => {
    if (geometry_type === 'point') {
      const data = geometry_data as { x: number; y: number };
      return { x: data.x + 12 / scale, y: data.y - 20 / scale };
    }
    if (geometry_type === 'rectangle') {
      const data = geometry_data as { x: number; y: number };
      return { x: data.x, y: data.y - 16 / scale };
    }
    if (geometry_type === 'circle') {
      const data = geometry_data as { center: Point; radius: number };
      return { x: data.center.x, y: data.center.y - data.radius - 16 / scale };
    }
    // polyline / polygon / line
    const points = (geometry_data as { points: Point[] }).points ?? [];
    if (points.length > 0) {
      return { x: points[0].x, y: points[0].y - 16 / scale };
    }
    return { x: 0, y: 0 };
  };

  const labelPos = getLabelPosition();

  return (
    <Group ref={groupRef} listening={false}>
      {renderShape()}
      <Text
        x={labelPos.x}
        y={labelPos.y}
        text="Tab to accept \u00B7 Esc to dismiss"
        fontSize={labelFontSize}
        fill={GHOST_COLOR}
        listening={false}
      />
    </Group>
  );
}
