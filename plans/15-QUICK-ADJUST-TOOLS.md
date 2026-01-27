# Quick Adjust Geometry Tools
## Precision Editing Tools for Measurement Review

> **Part of Phase 4B Enhanced**
> **Purpose**: Enable rapid, precise geometry adjustments without dialog boxes

---

## Overview

During review, estimators often need to make small adjustments to AI-detected measurements. Quick adjust tools provide keyboard-driven precision editing that's faster than mouse dragging.

### Tool Categories

| Category | Tools | Use Case |
|----------|-------|----------|
| **Nudge** | Arrow keys + modifiers | Move vertices/shapes by fixed increments |
| **Snap** | S + click | Snap to grid, intersections, or other geometry |
| **Extend** | X + direction | Extend line to intersection or boundary |
| **Trim** | T + click | Trim line at intersection |
| **Offset** | O + value | Create parallel offset of selected geometry |
| **Split** | Shift+S | Split polygon/line at point |
| **Join** | J | Join adjacent geometry |

---

## Implementation

### Task: Geometry Adjustment Service

Create `frontend/src/services/geometry-adjustment.ts`:

```typescript
import { Point, Polygon, Line, Geometry } from '@/types/geometry';

export interface NudgeOptions {
  direction: 'up' | 'down' | 'left' | 'right';
  amount: number; // in pixels
  target: 'all' | 'selected-vertices' | 'selected-shape';
}

export interface SnapOptions {
  point: Point;
  snapTargets: SnapTarget[];
  tolerance: number;
}

export interface SnapTarget {
  type: 'grid' | 'vertex' | 'edge' | 'intersection' | 'endpoint';
  point: Point;
  source?: string; // ID of source geometry
}

export interface ExtendOptions {
  line: Line;
  direction: 'start' | 'end' | 'both';
  boundary: Geometry | 'page-edge';
}

export interface TrimOptions {
  line: Line;
  trimPoint: Point;
  keepSide: 'before' | 'after';
}

export interface OffsetOptions {
  geometry: Geometry;
  distance: number; // positive = outward, negative = inward
  cornerType: 'miter' | 'round' | 'bevel';
}

/**
 * Geometry adjustment utilities for quick editing.
 */
export class GeometryAdjustmentService {
  private gridSize: number = 10; // pixels
  private snapTolerance: number = 15; // pixels

  /**
   * Nudge geometry in a direction by a fixed amount.
   */
  nudge(geometry: Geometry, options: NudgeOptions): Geometry {
    const { direction, amount, target } = options;
    
    const dx = direction === 'left' ? -amount : direction === 'right' ? amount : 0;
    const dy = direction === 'up' ? -amount : direction === 'down' ? amount : 0;

    if (geometry.type === 'polygon') {
      return {
        ...geometry,
        points: geometry.points.map((p, i) => {
          if (target === 'all' || geometry.selectedVertices?.includes(i)) {
            return { x: p.x + dx, y: p.y + dy };
          }
          return p;
        }),
      };
    }

    if (geometry.type === 'line') {
      return {
        ...geometry,
        start: { x: geometry.start.x + dx, y: geometry.start.y + dy },
        end: { x: geometry.end.x + dx, y: geometry.end.y + dy },
      };
    }

    if (geometry.type === 'point') {
      return {
        ...geometry,
        x: geometry.x + dx,
        y: geometry.y + dy,
      };
    }

    return geometry;
  }

  /**
   * Find the nearest snap target for a point.
   */
  findSnapTarget(point: Point, targets: SnapTarget[]): SnapTarget | null {
    let nearest: SnapTarget | null = null;
    let minDist = this.snapTolerance;

    for (const target of targets) {
      const dist = this.distance(point, target.point);
      if (dist < minDist) {
        minDist = dist;
        nearest = target;
      }
    }

    return nearest;
  }

  /**
   * Snap a point to the grid.
   */
  snapToGrid(point: Point): Point {
    return {
      x: Math.round(point.x / this.gridSize) * this.gridSize,
      y: Math.round(point.y / this.gridSize) * this.gridSize,
    };
  }

  /**
   * Generate grid snap targets for a viewport.
   */
  generateGridTargets(viewport: {
    x: number;
    y: number;
    width: number;
    height: number;
  }): SnapTarget[] {
    const targets: SnapTarget[] = [];
    
    for (let x = viewport.x; x <= viewport.x + viewport.width; x += this.gridSize) {
      for (let y = viewport.y; y <= viewport.y + viewport.height; y += this.gridSize) {
        targets.push({
          type: 'grid',
          point: { x, y },
        });
      }
    }

    return targets;
  }

  /**
   * Generate snap targets from existing geometry.
   */
  generateGeometryTargets(geometries: Geometry[]): SnapTarget[] {
    const targets: SnapTarget[] = [];

    for (const geom of geometries) {
      if (geom.type === 'polygon') {
        // Vertices
        for (const p of geom.points) {
          targets.push({
            type: 'vertex',
            point: p,
            source: geom.id,
          });
        }
        
        // Edge midpoints
        for (let i = 0; i < geom.points.length; i++) {
          const p1 = geom.points[i];
          const p2 = geom.points[(i + 1) % geom.points.length];
          targets.push({
            type: 'edge',
            point: { x: (p1.x + p2.x) / 2, y: (p1.y + p2.y) / 2 },
            source: geom.id,
          });
        }
      }

      if (geom.type === 'line') {
        targets.push(
          { type: 'endpoint', point: geom.start, source: geom.id },
          { type: 'endpoint', point: geom.end, source: geom.id },
          {
            type: 'edge',
            point: {
              x: (geom.start.x + geom.end.x) / 2,
              y: (geom.start.y + geom.end.y) / 2,
            },
            source: geom.id,
          }
        );
      }

      if (geom.type === 'point') {
        targets.push({
          type: 'vertex',
          point: { x: geom.x, y: geom.y },
          source: geom.id,
        });
      }
    }

    // Find intersections
    const intersections = this.findAllIntersections(geometries);
    for (const point of intersections) {
      targets.push({
        type: 'intersection',
        point,
      });
    }

    return targets;
  }

  /**
   * Extend a line to intersect with a boundary.
   */
  extendLine(options: ExtendOptions): Line {
    const { line, direction, boundary } = options;
    
    // Calculate line direction vector
    const dx = line.end.x - line.start.x;
    const dy = line.end.y - line.start.y;
    const len = Math.sqrt(dx * dx + dy * dy);
    const unitX = dx / len;
    const unitY = dy / len;

    let newStart = { ...line.start };
    let newEnd = { ...line.end };

    if (boundary === 'page-edge') {
      // Extend to page boundaries (assuming 0,0 to very large)
      const maxExtent = 10000;
      
      if (direction === 'start' || direction === 'both') {
        newStart = {
          x: line.start.x - unitX * maxExtent,
          y: line.start.y - unitY * maxExtent,
        };
      }
      
      if (direction === 'end' || direction === 'both') {
        newEnd = {
          x: line.end.x + unitX * maxExtent,
          y: line.end.y + unitY * maxExtent,
        };
      }
    } else {
      // Find intersection with boundary geometry
      const intersection = this.findLineGeometryIntersection(
        { start: line.start, end: { x: line.end.x + unitX * 10000, y: line.end.y + unitY * 10000 } },
        boundary
      );
      
      if (intersection && (direction === 'end' || direction === 'both')) {
        newEnd = intersection;
      }
    }

    return { ...line, start: newStart, end: newEnd };
  }

  /**
   * Trim a line at a point.
   */
  trimLine(options: TrimOptions): Line {
    const { line, trimPoint, keepSide } = options;
    
    // Project trim point onto line
    const projected = this.projectPointOnLine(trimPoint, line);
    
    if (keepSide === 'before') {
      return { ...line, end: projected };
    } else {
      return { ...line, start: projected };
    }
  }

  /**
   * Create an offset of a polygon.
   */
  offsetPolygon(options: OffsetOptions): Polygon | null {
    const { geometry, distance, cornerType } = options;
    
    if (geometry.type !== 'polygon') return null;
    
    const points = geometry.points;
    const newPoints: Point[] = [];

    for (let i = 0; i < points.length; i++) {
      const prev = points[(i - 1 + points.length) % points.length];
      const curr = points[i];
      const next = points[(i + 1) % points.length];

      // Calculate edge normals
      const norm1 = this.perpendicular({ x: curr.x - prev.x, y: curr.y - prev.y });
      const norm2 = this.perpendicular({ x: next.x - curr.x, y: next.y - curr.y });

      // Average normal at vertex
      const avgNorm = this.normalize({
        x: norm1.x + norm2.x,
        y: norm1.y + norm2.y,
      });

      // Calculate offset point
      const angle = Math.acos(norm1.x * norm2.x + norm1.y * norm2.y);
      const miterLength = distance / Math.cos(angle / 2);

      if (cornerType === 'miter' && miterLength < distance * 2) {
        newPoints.push({
          x: curr.x + avgNorm.x * miterLength,
          y: curr.y + avgNorm.y * miterLength,
        });
      } else {
        // Use bevel or round
        newPoints.push({
          x: curr.x + norm1.x * distance,
          y: curr.y + norm1.y * distance,
        });
        newPoints.push({
          x: curr.x + norm2.x * distance,
          y: curr.y + norm2.y * distance,
        });
      }
    }

    return {
      ...geometry,
      id: `${geometry.id}-offset`,
      points: newPoints,
    };
  }

  /**
   * Split a polygon at a point.
   */
  splitPolygon(polygon: Polygon, splitPoints: [Point, Point]): [Polygon, Polygon] | null {
    // Find which edges the split points are on
    const edge1 = this.findEdgeForPoint(polygon, splitPoints[0]);
    const edge2 = this.findEdgeForPoint(polygon, splitPoints[1]);

    if (edge1 === null || edge2 === null || edge1 === edge2) {
      return null;
    }

    // Create two new polygons
    const points = polygon.points;
    const poly1Points: Point[] = [];
    const poly2Points: Point[] = [];

    let inPoly1 = true;
    for (let i = 0; i < points.length; i++) {
      if (inPoly1) {
        poly1Points.push(points[i]);
      } else {
        poly2Points.push(points[i]);
      }

      if (i === edge1) {
        poly1Points.push(splitPoints[0]);
        poly1Points.push(splitPoints[1]);
        inPoly1 = false;
        poly2Points.push(splitPoints[1]);
        poly2Points.push(splitPoints[0]);
      } else if (i === edge2) {
        poly2Points.push(splitPoints[0]);
        poly2Points.push(splitPoints[1]);
        inPoly1 = true;
      }
    }

    return [
      { ...polygon, id: `${polygon.id}-a`, points: poly1Points },
      { ...polygon, id: `${polygon.id}-b`, points: poly2Points },
    ];
  }

  /**
   * Join two adjacent lines.
   */
  joinLines(line1: Line, line2: Line): Line | null {
    const tolerance = this.snapTolerance;

    // Check which endpoints are close
    if (this.distance(line1.end, line2.start) < tolerance) {
      return { ...line1, end: line2.end };
    }
    if (this.distance(line1.start, line2.end) < tolerance) {
      return { ...line2, end: line1.end };
    }
    if (this.distance(line1.end, line2.end) < tolerance) {
      return { ...line1, end: line2.start };
    }
    if (this.distance(line1.start, line2.start) < tolerance) {
      return { start: line2.end, end: line1.end };
    }

    return null;
  }

  // Helper methods

  private distance(p1: Point, p2: Point): number {
    return Math.sqrt((p2.x - p1.x) ** 2 + (p2.y - p1.y) ** 2);
  }

  private perpendicular(v: Point): Point {
    const len = Math.sqrt(v.x * v.x + v.y * v.y);
    return { x: -v.y / len, y: v.x / len };
  }

  private normalize(v: Point): Point {
    const len = Math.sqrt(v.x * v.x + v.y * v.y);
    return len > 0 ? { x: v.x / len, y: v.y / len } : { x: 0, y: 0 };
  }

  private projectPointOnLine(point: Point, line: Line): Point {
    const dx = line.end.x - line.start.x;
    const dy = line.end.y - line.start.y;
    const len2 = dx * dx + dy * dy;
    
    const t = Math.max(0, Math.min(1,
      ((point.x - line.start.x) * dx + (point.y - line.start.y) * dy) / len2
    ));

    return {
      x: line.start.x + t * dx,
      y: line.start.y + t * dy,
    };
  }

  private findEdgeForPoint(polygon: Polygon, point: Point): number | null {
    const tolerance = this.snapTolerance;
    
    for (let i = 0; i < polygon.points.length; i++) {
      const p1 = polygon.points[i];
      const p2 = polygon.points[(i + 1) % polygon.points.length];
      
      const projected = this.projectPointOnLine(point, { start: p1, end: p2 } as Line);
      if (this.distance(point, projected) < tolerance) {
        return i;
      }
    }

    return null;
  }

  private findAllIntersections(geometries: Geometry[]): Point[] {
    const intersections: Point[] = [];
    const lines: Line[] = [];

    // Extract all line segments
    for (const geom of geometries) {
      if (geom.type === 'line') {
        lines.push(geom);
      } else if (geom.type === 'polygon') {
        for (let i = 0; i < geom.points.length; i++) {
          lines.push({
            id: `${geom.id}-edge-${i}`,
            type: 'line',
            start: geom.points[i],
            end: geom.points[(i + 1) % geom.points.length],
          } as Line);
        }
      }
    }

    // Find pairwise intersections
    for (let i = 0; i < lines.length; i++) {
      for (let j = i + 1; j < lines.length; j++) {
        const intersection = this.lineLineIntersection(lines[i], lines[j]);
        if (intersection) {
          intersections.push(intersection);
        }
      }
    }

    return intersections;
  }

  private lineLineIntersection(line1: Line, line2: Line): Point | null {
    const x1 = line1.start.x, y1 = line1.start.y;
    const x2 = line1.end.x, y2 = line1.end.y;
    const x3 = line2.start.x, y3 = line2.start.y;
    const x4 = line2.end.x, y4 = line2.end.y;

    const denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4);
    if (Math.abs(denom) < 1e-10) return null;

    const t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom;
    const u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom;

    if (t >= 0 && t <= 1 && u >= 0 && u <= 1) {
      return {
        x: x1 + t * (x2 - x1),
        y: y1 + t * (y2 - y1),
      };
    }

    return null;
  }

  private findLineGeometryIntersection(line: Line, geometry: Geometry): Point | null {
    if (geometry.type === 'line') {
      return this.lineLineIntersection(line, geometry);
    }

    if (geometry.type === 'polygon') {
      let nearest: Point | null = null;
      let minDist = Infinity;

      for (let i = 0; i < geometry.points.length; i++) {
        const edge: Line = {
          id: 'edge',
          type: 'line',
          start: geometry.points[i],
          end: geometry.points[(i + 1) % geometry.points.length],
        };
        
        const intersection = this.lineLineIntersection(line, edge);
        if (intersection) {
          const dist = this.distance(line.start, intersection);
          if (dist < minDist) {
            minDist = dist;
            nearest = intersection;
          }
        }
      }

      return nearest;
    }

    return null;
  }

  // Configuration
  setGridSize(size: number): void {
    this.gridSize = size;
  }

  setSnapTolerance(tolerance: number): void {
    this.snapTolerance = tolerance;
  }
}

export const geometryAdjustment = new GeometryAdjustmentService();
```

---

### Task: Quick Adjust Keyboard Handler

Create `frontend/src/hooks/useQuickAdjust.ts`:

```typescript
import { useCallback, useEffect, useState } from 'react';
import { useHotkeys } from 'react-hotkeys-hook';
import { geometryAdjustment } from '@/services/geometry-adjustment';
import { Geometry, Point } from '@/types/geometry';

interface UseQuickAdjustOptions {
  enabled: boolean;
  selectedGeometry: Geometry | null;
  allGeometries: Geometry[];
  gridSize: number;
  onGeometryChange: (geometry: Geometry) => void;
  onGeometrySplit?: (geometries: Geometry[]) => void;
  onGeometryJoin?: (geometry: Geometry) => void;
}

interface QuickAdjustState {
  mode: 'normal' | 'snap' | 'extend' | 'trim' | 'offset' | 'split';
  snapTargets: any[];
  pendingAction: any | null;
}

export function useQuickAdjust(options: UseQuickAdjustOptions) {
  const {
    enabled,
    selectedGeometry,
    allGeometries,
    gridSize,
    onGeometryChange,
    onGeometrySplit,
    onGeometryJoin,
  } = options;

  const [state, setState] = useState<QuickAdjustState>({
    mode: 'normal',
    snapTargets: [],
    pendingAction: null,
  });

  // Update grid size
  useEffect(() => {
    geometryAdjustment.setGridSize(gridSize);
  }, [gridSize]);

  // Generate snap targets when geometries change
  useEffect(() => {
    if (enabled) {
      const targets = geometryAdjustment.generateGeometryTargets(allGeometries);
      setState(s => ({ ...s, snapTargets: targets }));
    }
  }, [enabled, allGeometries]);

  // Nudge with arrow keys
  const nudge = useCallback(
    (direction: 'up' | 'down' | 'left' | 'right', large: boolean) => {
      if (!selectedGeometry) return;

      const amount = large ? gridSize * 5 : gridSize;
      const newGeometry = geometryAdjustment.nudge(selectedGeometry, {
        direction,
        amount,
        target: 'all',
      });

      onGeometryChange(newGeometry);
    },
    [selectedGeometry, gridSize, onGeometryChange]
  );

  // Arrow key handlers
  useHotkeys('up', () => nudge('up', false), { enabled: enabled && !!selectedGeometry });
  useHotkeys('down', () => nudge('down', false), { enabled: enabled && !!selectedGeometry });
  useHotkeys('left', () => nudge('left', false), { enabled: enabled && !!selectedGeometry });
  useHotkeys('right', () => nudge('right', false), { enabled: enabled && !!selectedGeometry });

  // Large nudge with shift
  useHotkeys('shift+up', () => nudge('up', true), { enabled: enabled && !!selectedGeometry });
  useHotkeys('shift+down', () => nudge('down', true), { enabled: enabled && !!selectedGeometry });
  useHotkeys('shift+left', () => nudge('left', true), { enabled: enabled && !!selectedGeometry });
  useHotkeys('shift+right', () => nudge('right', true), { enabled: enabled && !!selectedGeometry });

  // Mode toggles
  useHotkeys('s', () => {
    setState(s => ({ ...s, mode: s.mode === 'snap' ? 'normal' : 'snap' }));
  }, { enabled });

  useHotkeys('x', () => {
    setState(s => ({ ...s, mode: s.mode === 'extend' ? 'normal' : 'extend' }));
  }, { enabled });

  useHotkeys('t', () => {
    setState(s => ({ ...s, mode: s.mode === 'trim' ? 'normal' : 'trim' }));
  }, { enabled });

  useHotkeys('o', () => {
    setState(s => ({ ...s, mode: s.mode === 'offset' ? 'normal' : 'offset' }));
  }, { enabled });

  useHotkeys('shift+s', () => {
    setState(s => ({ ...s, mode: s.mode === 'split' ? 'normal' : 'split' }));
  }, { enabled });

  // Escape to cancel mode
  useHotkeys('escape', () => {
    setState(s => ({ ...s, mode: 'normal', pendingAction: null }));
  }, { enabled });

  // Snap to grid
  useHotkeys('g', () => {
    if (!selectedGeometry) return;

    if (selectedGeometry.type === 'polygon') {
      const snappedPoints = selectedGeometry.points.map(p =>
        geometryAdjustment.snapToGrid(p)
      );
      onGeometryChange({ ...selectedGeometry, points: snappedPoints });
    } else if (selectedGeometry.type === 'line') {
      onGeometryChange({
        ...selectedGeometry,
        start: geometryAdjustment.snapToGrid(selectedGeometry.start),
        end: geometryAdjustment.snapToGrid(selectedGeometry.end),
      });
    }
  }, { enabled: enabled && !!selectedGeometry });

  // Handle click in different modes
  const handleCanvasClick = useCallback(
    (point: Point) => {
      if (!enabled) return;

      switch (state.mode) {
        case 'snap': {
          const target = geometryAdjustment.findSnapTarget(point, state.snapTargets);
          if (target && selectedGeometry) {
            // Move selected geometry vertex to snap target
            // Implementation depends on what's selected
            console.log('Snap to:', target);
          }
          break;
        }

        case 'extend': {
          if (selectedGeometry?.type === 'line') {
            const extended = geometryAdjustment.extendLine({
              line: selectedGeometry,
              direction: 'both',
              boundary: 'page-edge',
            });
            onGeometryChange(extended);
          }
          break;
        }

        case 'trim': {
          if (selectedGeometry?.type === 'line') {
            const trimmed = geometryAdjustment.trimLine({
              line: selectedGeometry,
              trimPoint: point,
              keepSide: 'before', // or determine from click position
            });
            onGeometryChange(trimmed);
          }
          break;
        }

        case 'offset': {
          if (selectedGeometry?.type === 'polygon') {
            const distance = prompt('Offset distance (pixels):');
            if (distance) {
              const offset = geometryAdjustment.offsetPolygon({
                geometry: selectedGeometry,
                distance: parseFloat(distance),
                cornerType: 'miter',
              });
              if (offset && onGeometrySplit) {
                onGeometrySplit([selectedGeometry, offset]);
              }
            }
          }
          break;
        }

        case 'split': {
          if (selectedGeometry?.type === 'polygon' && state.pendingAction?.point) {
            const result = geometryAdjustment.splitPolygon(
              selectedGeometry,
              [state.pendingAction.point, point]
            );
            if (result && onGeometrySplit) {
              onGeometrySplit(result);
            }
            setState(s => ({ ...s, mode: 'normal', pendingAction: null }));
          } else {
            setState(s => ({ ...s, pendingAction: { point } }));
          }
          break;
        }
      }
    },
    [enabled, state, selectedGeometry, onGeometryChange, onGeometrySplit]
  );

  return {
    mode: state.mode,
    snapTargets: state.snapTargets,
    pendingAction: state.pendingAction,
    handleCanvasClick,
  };
}
```

---

### Task: Quick Adjust Toolbar Component

Create `frontend/src/components/review/QuickAdjustToolbar.tsx`:

```tsx
import { cn } from '@/lib/utils';
import {
  Move,
  Magnet,
  ArrowUpRight,
  Scissors,
  Copy,
  Split,
  Grid3x3,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';

interface QuickAdjustToolbarProps {
  mode: 'normal' | 'snap' | 'extend' | 'trim' | 'offset' | 'split';
  onModeChange: (mode: string) => void;
  disabled?: boolean;
}

const tools = [
  {
    id: 'normal',
    icon: Move,
    label: 'Select',
    shortcut: 'Esc',
    description: 'Normal selection mode',
  },
  {
    id: 'snap',
    icon: Magnet,
    label: 'Snap',
    shortcut: 'S',
    description: 'Snap to grid/geometry',
  },
  {
    id: 'extend',
    icon: ArrowUpRight,
    label: 'Extend',
    shortcut: 'X',
    description: 'Extend line to boundary',
  },
  {
    id: 'trim',
    icon: Scissors,
    label: 'Trim',
    shortcut: 'T',
    description: 'Trim line at point',
  },
  {
    id: 'offset',
    icon: Copy,
    label: 'Offset',
    shortcut: 'O',
    description: 'Create parallel offset',
  },
  {
    id: 'split',
    icon: Split,
    label: 'Split',
    shortcut: 'Shift+S',
    description: 'Split polygon',
  },
];

export function QuickAdjustToolbar({
  mode,
  onModeChange,
  disabled,
}: QuickAdjustToolbarProps) {
  return (
    <div className="flex items-center gap-1 p-1 bg-muted/50 rounded-lg">
      {tools.map((tool) => (
        <Tooltip key={tool.id}>
          <TooltipTrigger asChild>
            <Button
              variant={mode === tool.id ? 'default' : 'ghost'}
              size="icon"
              className={cn(
                'h-8 w-8',
                mode === tool.id && 'bg-primary text-primary-foreground'
              )}
              onClick={() => onModeChange(tool.id)}
              disabled={disabled}
            >
              <tool.icon className="h-4 w-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="bottom">
            <div className="text-sm font-medium">{tool.label}</div>
            <div className="text-xs text-muted-foreground">
              {tool.description}
            </div>
            <kbd className="mt-1 px-1.5 py-0.5 text-xs bg-muted rounded">
              {tool.shortcut}
            </kbd>
          </TooltipContent>
        </Tooltip>
      ))}

      <div className="w-px h-6 bg-border mx-1" />

      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            disabled={disabled}
          >
            <Grid3x3 className="h-4 w-4" />
          </Button>
        </TooltipTrigger>
        <TooltipContent side="bottom">
          <div className="text-sm font-medium">Snap to Grid</div>
          <div className="text-xs text-muted-foreground">
            Snap all vertices to grid
          </div>
          <kbd className="mt-1 px-1.5 py-0.5 text-xs bg-muted rounded">G</kbd>
        </TooltipContent>
      </Tooltip>

      {/* Nudge hints */}
      <div className="ml-2 text-xs text-muted-foreground">
        <span className="hidden lg:inline">
          Arrow keys: nudge • Shift+Arrow: large nudge
        </span>
      </div>
    </div>
  );
}
```

---

## Keyboard Shortcut Reference

| Key | Action | Mode |
|-----|--------|------|
| **↑↓←→** | Nudge by grid size | Any |
| **Shift+↑↓←→** | Nudge by 5× grid size | Any |
| **S** | Toggle snap mode | - |
| **X** | Toggle extend mode | - |
| **T** | Toggle trim mode | - |
| **O** | Toggle offset mode | - |
| **Shift+S** | Toggle split mode | - |
| **G** | Snap all vertices to grid | Any |
| **Esc** | Return to normal mode | Any |

---

## Integration with Review Workspace

Add to `ReviewWorkspace.tsx`:

```tsx
import { QuickAdjustToolbar } from '@/components/review/QuickAdjustToolbar';
import { useQuickAdjust } from '@/hooks/useQuickAdjust';

// In component:
const {
  mode: adjustMode,
  handleCanvasClick,
} = useQuickAdjust({
  enabled: true,
  selectedGeometry: currentMeasurement?.geometry_data,
  allGeometries: measurements.map(m => m.geometry_data),
  gridSize: 10,
  onGeometryChange: (newGeometry) => {
    // Update via modify mutation
    modifyMutation.mutate({
      id: currentMeasurement.id,
      geometry: newGeometry,
    });
  },
});

// In render:
<QuickAdjustToolbar
  mode={adjustMode}
  onModeChange={setAdjustMode}
  disabled={!currentMeasurement}
/>
```
