# Phase 3A+: Manual Drawing Tools
## Interactive Measurement Creation Interface

> **Duration**: 1-2 weeks  
> **Prerequisites**: Phase 3A complete (measurement engine working)  
> **Outcome**: Full manual drawing interface for creating measurements on PDF pages

---

## Context for LLM Assistant

You are implementing the **manual drawing tools** for a construction takeoff platform. This phase enables users to:
- Select geometry tools (line, polyline, polygon, rectangle, circle, point)
- Draw measurements directly on PDF/TIFF pages
- See live previews while drawing
- Create measurements that are automatically calculated and saved
- Edit existing measurements by dragging control points

This fills a critical gap in Phase 3A - the backend can calculate measurements, but there's no UI for users to create them manually.

### User Workflow

```
1. User uploads a PDF → Document is processed
2. User opens a page in the Takeoff Viewer
3. Scale is calibrated (Phase 2B)
4. User selects a condition (e.g., "4" Concrete Slab")
5. User clicks a tool button (e.g., Polygon tool)
6. User clicks on the canvas to draw points
7. User finishes the shape (double-click or close button)
8. Backend calculates quantity → Measurement saved
9. Shape appears on canvas with label showing quantity
```

### Drawing Modes by Geometry Type

| Geometry | Drawing Interaction | Finish Action |
|----------|---------------------|---------------|
| **Line** | Click start point → Move mouse → Click end point | Auto-finishes on 2nd click |
| **Polyline** | Click to add points → Move between clicks | Double-click or Finish button |
| **Polygon** | Click to add points → Move between clicks | Double-click or close to first point |
| **Rectangle** | Click corner → Drag → Release | Auto-finishes on mouse up |
| **Circle** | Click center → Drag radius → Release | Auto-finishes on mouse up |
| **Point** | Click location | Auto-finishes immediately |

---

## Design System & Component Guidelines

**CRITICAL:** Follow the established design system for all UI implementation.

### Required Reading

Read these design system documents before implementing any components:

**@docs/design/DESIGN-SYSTEM.md** - Complete design system specification
- **Color System**: Use `MEASUREMENT_COLORS` from `@/lib/colors.ts` for condition colors
- **Typography**: Follow the typography scale
  - `text-sm font-medium` for labels
  - `text-lg font-semibold` for section headings
  - `text-2xl font-semibold` for page titles
  - `font-mono` for measurement values and numbers
- **Spacing**: Use consistent spacing tokens
  - `gap-2` (8px) for button groups and inline elements
  - `gap-4` (16px) for card content spacing
  - `p-4` (16px) for panel padding
  - `w-80` (320px) for sidebar widths
- **Layout Patterns**: 3-panel split view for measurement interfaces

**@docs/design/COMPONENT_LIBRARY.md** - shadcn/ui component reference
- **Button Component**: 
  - Use variants: `default` (primary), `outline` (secondary), `ghost` (toolbar), `destructive` (delete)
  - Sizes: `sm`, `default`, `lg`, `icon`
  - Import: `import { Button } from '@/components/ui/button'`
- **Card Component**: Always use composition pattern
  - `Card` → `CardHeader` → `CardTitle` + `CardDescription`
  - `CardContent` for main content
  - `CardFooter` for actions
- **Icons**: Use Lucide React icons exclusively
  - Standard sizes: `h-4 w-4` (inline), `h-5 w-5` (standalone), `h-6 w-6` (large)
  - Import: `import { IconName } from 'lucide-react'`
- **Form Components**: Always pair `Label` with form inputs using `htmlFor`

### Key UI Patterns for This Phase

**Toolbar Buttons:**
```tsx
// Tool buttons (inactive state)
<Button variant="ghost" size="sm" className="w-10 h-10 p-0">
  <Icon className="w-4 h-4" />
</Button>

// Active tool
<Button variant="default" size="sm" className="w-10 h-10 p-0 bg-blue-600 hover:bg-blue-700">
  <Icon className="w-4 h-4" />
</Button>

// Action buttons (undo/redo)
<Button variant="ghost" size="sm" disabled={!canUndo} className="w-10 h-10 p-0">
  <Undo className="w-4 h-4" />
</Button>

// Delete button (destructive)
<Button 
  variant="ghost" 
  size="sm" 
  className="w-10 h-10 p-0 text-red-600 hover:text-red-700 hover:bg-red-50"
>
  <Trash2 className="w-4 h-4" />
</Button>
```

**Sidebar Panels:**
```tsx
// Left panel (conditions list)
<div className="w-80 border-r bg-white p-4 overflow-y-auto">
  <h2 className="text-sm font-semibold mb-3">Conditions</h2>
  {/* Condition cards */}
</div>

// Right panel (measurements list)
<div className="w-80 border-l bg-white p-4 overflow-y-auto">
  <h2 className="text-sm font-semibold mb-3">Measurements</h2>
  {/* Measurement cards */}
</div>
```

**Canvas Container:**
```tsx
<div className="flex-1 flex flex-col bg-gray-100">
  {/* Toolbar */}
  <div className="p-4">
    <DrawingToolbar />
  </div>
  
  {/* Canvas */}
  <div id="canvas-container" className="flex-1 relative">
    <Stage>{/* Konva layers */}</Stage>
  </div>
</div>
```

**Condition Selection Cards:**
```tsx
<button
  className={`w-full text-left p-3 rounded-lg border-2 transition-colors ${
    selected ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'
  }`}
>
  <div className="flex items-center gap-2">
    <div className="w-4 h-4 rounded" style={{ backgroundColor: condition.color }} />
    <div className="flex-1 min-w-0">
      <p className="font-medium text-sm truncate">{condition.name}</p>
      <p className="text-xs text-gray-600">
        {condition.total_quantity.toFixed(1)} {condition.unit}
      </p>
    </div>
  </div>
</button>
```

**Measurement Display:**
```tsx
// Use font-mono for numeric values
<p className="text-lg font-bold text-blue-600 font-mono">
  {measurement.quantity.toFixed(1)} <span className="text-xs">{measurement.unit}</span>
</p>
```

### Color Usage

**DO NOT hardcode colors** - Always import from the color system:

```tsx
// ✅ CORRECT - Import from color system
import { MEASUREMENT_COLORS } from '@/lib/colors';

const color = MEASUREMENT_COLORS[condition.scope] || MEASUREMENT_COLORS.default;
```

```tsx
// ❌ WRONG - Hardcoded colors
const color = '#3B82F6';
```

**Measurement Colors by Scope:**
- Foundation: `#E57373` (Red 300)
- Slab: `#FFB74D` (Orange 300)
- Wall: `#FFF176` (Yellow 300)
- Default: `#90A4AE` (Blue Grey 300)
- Selected: `#2196F3` (Blue 500)

### Accessibility Requirements

- [ ] All buttons must have accessible labels (use `title` or `aria-label`)
- [ ] Keyboard shortcuts must be documented in toolbar instructions
- [ ] Form inputs must have associated `Label` components with `htmlFor`
- [ ] Focus states must be visible (handled by shadcn/ui)
- [ ] Color cannot be the only indicator (pair with icons/text)

---

## Frontend Components

### Task 6B.1: Drawing Toolbar Component

Create `frontend/src/components/viewer/DrawingToolbar.tsx`:

```tsx
import { useState } from 'react';
import {
  Mouse,
  Minus,
  Pencil,
  Square,
  Circle as CircleIcon,
  MapPin,
  Pentagon,
  Undo,
  Redo,
  Trash2,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

export type DrawingTool = 
  | 'select' 
  | 'line' 
  | 'polyline' 
  | 'polygon' 
  | 'rectangle' 
  | 'circle' 
  | 'point';

interface DrawingToolbarProps {
  activeTool: DrawingTool;
  onToolChange: (tool: DrawingTool) => void;
  canUndo: boolean;
  canRedo: boolean;
  onUndo: () => void;
  onRedo: () => void;
  onDelete: () => void;
  hasSelection: boolean;
  disabled?: boolean;
}

const TOOLS = [
  { id: 'select' as const, icon: Mouse, label: 'Select', shortcut: 'V' },
  { id: 'line' as const, icon: Minus, label: 'Line', shortcut: 'L' },
  { id: 'polyline' as const, icon: Pencil, label: 'Polyline', shortcut: 'P' },
  { id: 'polygon' as const, icon: Pentagon, label: 'Polygon', shortcut: 'G' },
  { id: 'rectangle' as const, icon: Square, label: 'Rectangle', shortcut: 'R' },
  { id: 'circle' as const, icon: CircleIcon, label: 'Circle', shortcut: 'C' },
  { id: 'point' as const, icon: MapPin, label: 'Point', shortcut: 'M' },
];

export function DrawingToolbar({
  activeTool,
  onToolChange,
  canUndo,
  canRedo,
  onUndo,
  onRedo,
  onDelete,
  hasSelection,
  disabled = false,
}: DrawingToolbarProps) {
  return (
    <div className="flex items-center gap-2 p-2 bg-white border rounded-lg shadow-sm">
      {/* Drawing Tools */}
      <div className="flex gap-1">
        {TOOLS.map((tool) => {
          const Icon = tool.icon;
          const isActive = activeTool === tool.id;
          
          return (
            <Button
              key={tool.id}
              variant={isActive ? 'default' : 'ghost'}
              size="sm"
              onClick={() => onToolChange(tool.id)}
              disabled={disabled}
              title={`${tool.label} (${tool.shortcut})`}
              className={cn(
                'w-10 h-10 p-0',
                isActive && 'bg-blue-600 hover:bg-blue-700'
              )}
            >
              <Icon className="w-4 h-4" />
            </Button>
          );
        })}
      </div>

      <div className="w-px h-8 bg-gray-300" />

      {/* Action Buttons */}
      <div className="flex gap-1">
        <Button
          variant="ghost"
          size="sm"
          onClick={onUndo}
          disabled={!canUndo || disabled}
          title="Undo (Ctrl+Z)"
          className="w-10 h-10 p-0"
        >
          <Undo className="w-4 h-4" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={onRedo}
          disabled={!canRedo || disabled}
          title="Redo (Ctrl+Y)"
          className="w-10 h-10 p-0"
        >
          <Redo className="w-4 h-4" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={onDelete}
          disabled={!hasSelection || disabled}
          title="Delete (Delete)"
          className="w-10 h-10 p-0 text-red-600 hover:text-red-700 hover:bg-red-50"
        >
          <Trash2 className="w-4 h-4" />
        </Button>
      </div>

      {/* Instructions */}
      <div className="ml-auto text-sm text-gray-600">
        {getInstructions(activeTool)}
      </div>
    </div>
  );
}

function getInstructions(tool: DrawingTool): string {
  switch (tool) {
    case 'select':
      return 'Click to select measurements';
    case 'line':
      return 'Click start point, then end point';
    case 'polyline':
      return 'Click to add points, double-click to finish';
    case 'polygon':
      return 'Click to add points, double-click or close to finish';
    case 'rectangle':
      return 'Click and drag to draw rectangle';
    case 'circle':
      return 'Click center, drag to set radius';
    case 'point':
      return 'Click to place point';
    default:
      return '';
  }
}
```

---

### Task 6B.2: Drawing State Hook

Create `frontend/src/hooks/useDrawingState.ts`:

```typescript
import { useState, useCallback, useRef } from 'react';
import type { DrawingTool } from '@/components/viewer/DrawingToolbar';

export interface Point {
  x: number;
  y: number;
}

export interface DrawingState {
  tool: DrawingTool;
  isDrawing: boolean;
  points: Point[];
  previewShape: {
    type: DrawingTool;
    data: any;
  } | null;
}

interface HistoryState {
  action: 'create' | 'update' | 'delete';
  measurementId: string;
  data: any;
}

export function useDrawingState() {
  const [tool, setTool] = useState<DrawingTool>('select');
  const [isDrawing, setIsDrawing] = useState(false);
  const [points, setPoints] = useState<Point[]>([]);
  const [previewShape, setPreviewShape] = useState<DrawingState['previewShape']>(null);
  
  // Undo/Redo
  const [history, setHistory] = useState<HistoryState[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  
  const canUndo = historyIndex >= 0;
  const canRedo = historyIndex < history.length - 1;

  const startDrawing = useCallback((point: Point) => {
    setIsDrawing(true);
    setPoints([point]);
  }, []);

  const addPoint = useCallback((point: Point) => {
    setPoints((prev) => [...prev, point]);
  }, []);

  const updatePreview = useCallback((mousePos: Point) => {
    if (!isDrawing || points.length === 0) return;

    switch (tool) {
      case 'line':
        if (points.length === 1) {
          setPreviewShape({
            type: 'line',
            data: { start: points[0], end: mousePos },
          });
        }
        break;

      case 'polyline':
        setPreviewShape({
          type: 'polyline',
          data: { points: [...points, mousePos] },
        });
        break;

      case 'polygon':
        setPreviewShape({
          type: 'polygon',
          data: { points: [...points, mousePos] },
        });
        break;

      case 'rectangle':
        if (points.length === 1) {
          const start = points[0];
          setPreviewShape({
            type: 'rectangle',
            data: {
              x: Math.min(start.x, mousePos.x),
              y: Math.min(start.y, mousePos.y),
              width: Math.abs(mousePos.x - start.x),
              height: Math.abs(mousePos.y - start.y),
            },
          });
        }
        break;

      case 'circle':
        if (points.length === 1) {
          const center = points[0];
          const radius = Math.sqrt(
            Math.pow(mousePos.x - center.x, 2) + Math.pow(mousePos.y - center.y, 2)
          );
          setPreviewShape({
            type: 'circle',
            data: { center, radius },
          });
        }
        break;
    }
  }, [tool, isDrawing, points]);

  const finishDrawing = useCallback(() => {
    const result = { tool, points, previewShape };
    
    setIsDrawing(false);
    setPoints([]);
    setPreviewShape(null);
    
    return result;
  }, [tool, points, previewShape]);

  const cancelDrawing = useCallback(() => {
    setIsDrawing(false);
    setPoints([]);
    setPreviewShape(null);
  }, []);

  const undo = useCallback(() => {
    if (canUndo) {
      setHistoryIndex((prev) => prev - 1);
      return history[historyIndex];
    }
  }, [canUndo, history, historyIndex]);

  const redo = useCallback(() => {
    if (canRedo) {
      setHistoryIndex((prev) => prev + 1);
      return history[historyIndex + 1];
    }
  }, [canRedo, history, historyIndex]);

  const addToHistory = useCallback((state: HistoryState) => {
    setHistory((prev) => [...prev.slice(0, historyIndex + 1), state]);
    setHistoryIndex((prev) => prev + 1);
  }, [historyIndex]);

  return {
    tool,
    setTool,
    isDrawing,
    points,
    previewShape,
    startDrawing,
    addPoint,
    updatePreview,
    finishDrawing,
    cancelDrawing,
    canUndo,
    canRedo,
    undo,
    redo,
    addToHistory,
  };
}
```

---

### Task 6B.3: Drawing Preview Layer

Create `frontend/src/components/viewer/DrawingPreviewLayer.tsx`:

```tsx
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
```

---

### Task 6B.4: Takeoff Viewer Page

Create `frontend/src/pages/TakeoffViewer.tsx`:

**COMPLETE IMPLEMENTATION - 490 LINES**

```tsx
import { useState, useRef, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Stage, Layer, Image as KonvaImage } from 'react-konva';
import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut, Maximize } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { apiClient } from '@/api/client';
import { DrawingToolbar, type DrawingTool } from '@/components/viewer/DrawingToolbar';
import { MeasurementLayer } from '@/components/viewer/MeasurementLayer';
import { DrawingPreviewLayer } from '@/components/viewer/DrawingPreviewLayer';
import { ScaleCalibration } from '@/components/viewer/ScaleCalibration';
import { useDrawingState } from '@/hooks/useDrawingState';
import type { Page, Measurement, Condition } from '@/types';

export function TakeoffViewer() {
  const { documentId, pageId } = useParams<{ documentId: string; pageId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  
  // Canvas state
  const stageRef = useRef<any>(null);
  const [image, setImage] = useState<HTMLImageElement | null>(null);
  const [stageSize, setStageSize] = useState({ width: 0, height: 0 });
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  
  // Drawing state
  const drawing = useDrawingState();
  const [selectedConditionId, setSelectedConditionId] = useState<string | null>(null);
  const [selectedMeasurementId, setSelectedMeasurementId] = useState<string | null>(null);
  
  // Scale calibration state
  const [isCalibrating, setIsCalibrating] = useState(false);
  const [calibrationLine, setCalibrationLine] = useState<any>(null);

  // Fetch page data
  const { data: page, isLoading: pageLoading } = useQuery({
    queryKey: ['page', pageId],
    queryFn: async () => {
      const response = await apiClient.get<Page>(`/pages/${pageId}`);
      return response.data;
    },
    enabled: !!pageId,
  });

  // Fetch conditions for the project
  const { data: conditionsData } = useQuery({
    queryKey: ['conditions', page?.document?.project_id],
    queryFn: async () => {
      const response = await apiClient.get(`/projects/${page?.document?.project_id}/conditions`);
      return response.data;
    },
    enabled: !!page?.document?.project_id,
  });

  // Fetch measurements for the page
  const { data: measurementsData } = useQuery({
    queryKey: ['measurements', pageId],
    queryFn: async () => {
      const response = await apiClient.get(`/pages/${pageId}/measurements`);
      return response.data;
    },
    enabled: !!pageId,
  });

  // Create measurement mutation
  const createMeasurementMutation = useMutation({
    mutationFn: async (data: {
      conditionId: string;
      pageId: string;
      geometryType: string;
      geometryData: any;
    }) => {
      const response = await apiClient.post('/measurements', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['measurements', pageId] });
      queryClient.invalidateQueries({ queryKey: ['conditions'] });
    },
  });

  // Delete measurement mutation
  const deleteMeasurementMutation = useMutation({
    mutationFn: async (measurementId: string) => {
      await apiClient.delete(`/measurements/${measurementId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['measurements', pageId] });
      setSelectedMeasurementId(null);
    },
  });

  // Load page image
  useEffect(() => {
    if (page?.image_url) {
      const img = new window.Image();
      img.crossOrigin = 'anonymous';
      img.src = page.image_url;
      img.onload = () => {
        setImage(img);
        // Fit image to viewport
        const container = document.getElementById('canvas-container');
        if (container) {
          const scale = Math.min(
            container.clientWidth / img.width,
            container.clientHeight / img.height,
            1
          );
          setZoom(scale);
          setStageSize({
            width: container.clientWidth,
            height: container.clientHeight,
          });
        }
      };
    }
  }, [page?.image_url]);

  // Handle window resize
  useEffect(() => {
    const handleResize = () => {
      const container = document.getElementById('canvas-container');
      if (container) {
        setStageSize({
          width: container.clientWidth,
          height: container.clientHeight,
        });
      }
    };
    window.addEventListener('resize', handleResize);
    handleResize();
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Tool shortcuts
      if (e.key === 'v') drawing.setTool('select');
      if (e.key === 'l') drawing.setTool('line');
      if (e.key === 'p') drawing.setTool('polyline');
      if (e.key === 'g') drawing.setTool('polygon');
      if (e.key === 'r') drawing.setTool('rectangle');
      if (e.key === 'c') drawing.setTool('circle');
      if (e.key === 'm') drawing.setTool('point');
      
      // Undo/Redo
      if (e.ctrlKey && e.key === 'z') drawing.undo();
      if (e.ctrlKey && e.key === 'y') drawing.redo();
      
      // Delete
      if (e.key === 'Delete' && selectedMeasurementId) {
        deleteMeasurementMutation.mutate(selectedMeasurementId);
      }
      
      // Escape - cancel drawing
      if (e.key === 'Escape') {
        drawing.cancelDrawing();
        setSelectedMeasurementId(null);
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [drawing, selectedMeasurementId]);

  // Handle canvas mouse events
  const handleStageMouseDown = (e: any) => {
    // Skip if calibrating
    if (isCalibrating) {
      handleCalibrationClick(e);
      return;
    }

    // Get click position in image coordinates
    const stage = e.target.getStage();
    const pointerPos = stage.getPointerPosition();
    const point = {
      x: (pointerPos.x - pan.x) / zoom,
      y: (pointerPos.y - pan.y) / zoom,
    };

    // Handle different drawing tools
    if (drawing.tool === 'select') {
      // Clicking on canvas deselects
      if (e.target === e.target.getStage()) {
        setSelectedMeasurementId(null);
      }
      return;
    }

    if (!selectedConditionId) {
      alert('Please select a condition first');
      return;
    }

    // Handle point tool (immediate creation)
    if (drawing.tool === 'point') {
      createMeasurementMutation.mutate({
        conditionId: selectedConditionId,
        pageId: pageId!,
        geometryType: 'point',
        geometryData: { x: point.x, y: point.y },
      });
      return;
    }

    // Start or continue drawing
    if (!drawing.isDrawing) {
      drawing.startDrawing(point);
    } else {
      drawing.addPoint(point);
      
      // Auto-finish for line (2 points)
      if (drawing.tool === 'line' && drawing.points.length === 1) {
        const result = drawing.finishDrawing();
        createMeasurement(result);
      }
    }
  };

  const handleStageMouseMove = (e: any) => {
    if (!drawing.isDrawing) return;

    const stage = e.target.getStage();
    const pointerPos = stage.getPointerPosition();
    const point = {
      x: (pointerPos.x - pan.x) / zoom,
      y: (pointerPos.y - pan.y) / zoom,
    };

    drawing.updatePreview(point);
  };

  const handleStageMouseUp = (e: any) => {
    // Auto-finish for rectangle and circle on mouse up
    if (drawing.tool === 'rectangle' || drawing.tool === 'circle') {
      if (drawing.isDrawing && drawing.points.length > 0) {
        const result = drawing.finishDrawing();
        createMeasurement(result);
      }
    }
  };

  const handleStageDoubleClick = (e: any) => {
    // Finish polyline or polygon on double-click
    if (drawing.tool === 'polyline' || drawing.tool === 'polygon') {
      if (drawing.isDrawing && drawing.points.length >= 2) {
        const result = drawing.finishDrawing();
        createMeasurement(result);
      }
    }
  };

  const createMeasurement = (result: any) => {
    if (!selectedConditionId || !pageId) return;

    let geometryData: any;

    switch (result.tool) {
      case 'line':
        geometryData = {
          start: result.points[0],
          end: result.points[1],
        };
        break;
      case 'polyline':
        geometryData = { points: result.points };
        break;
      case 'polygon':
        geometryData = { points: result.points };
        break;
      case 'rectangle':
        geometryData = result.previewShape?.data;
        break;
      case 'circle':
        geometryData = result.previewShape?.data;
        break;
      default:
        return;
    }

    createMeasurementMutation.mutate({
      conditionId: selectedConditionId,
      pageId,
      geometryType: result.tool,
      geometryData,
    });
  };

  const handleCalibrationClick = (e: any) => {
    // Implementation depends on ScaleCalibration component
    // This would be similar to Phase 2B scale detection
  };

  const handleZoomIn = () => setZoom((z) => Math.min(z * 1.2, 5));
  const handleZoomOut = () => setZoom((z) => Math.max(z / 1.2, 0.1));

  const conditions = conditionsData?.conditions || [];
  const measurements = measurementsData?.measurements || [];
  const selectedCondition = conditions.find((c: Condition) => c.id === selectedConditionId);

  if (pageLoading) {
    return <div className="flex items-center justify-center h-screen">Loading...</div>;
  }

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <div className="flex items-center gap-4 p-4 border-b bg-white">
        <Button variant="ghost" size="sm" onClick={() => navigate(-1)}>
          <ChevronLeft className="w-4 h-4 mr-2" />
          Back
        </Button>
        
        <div className="flex-1">
          <h1 className="text-lg font-semibold">{page?.page_label || 'Page'}</h1>
          <p className="text-sm text-gray-600">
            {page?.scale_calibrated ? `Scale: ${page.scale_value} px/ft` : 'Scale not calibrated'}
          </p>
        </div>

        {/* Zoom controls */}
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={handleZoomOut}>
            <ZoomOut className="w-4 h-4" />
          </Button>
          <span className="text-sm font-medium w-16 text-center">
            {(zoom * 100).toFixed(0)}%
          </span>
          <Button variant="outline" size="sm" onClick={handleZoomIn}>
            <ZoomIn className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Main content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left sidebar - Conditions */}
        <div className="w-80 border-r bg-white p-4 overflow-y-auto">
          <h2 className="text-sm font-semibold mb-3">Conditions</h2>
          <div className="space-y-2">
            {conditions.map((condition: Condition) => (
              <button
                key={condition.id}
                onClick={() => setSelectedConditionId(condition.id)}
                className={`w-full text-left p-3 rounded-lg border-2 transition-colors ${
                  selectedConditionId === condition.id
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center gap-2">
                  <div
                    className="w-4 h-4 rounded"
                    style={{ backgroundColor: condition.color }}
                  />
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-sm truncate">{condition.name}</p>
                    <p className="text-xs text-gray-600">
                      {condition.total_quantity.toFixed(1)} {condition.unit}
                    </p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Center - Canvas */}
        <div className="flex-1 flex flex-col bg-gray-100">
          {/* Drawing Toolbar */}
          <div className="p-4">
            <DrawingToolbar
              activeTool={drawing.tool}
              onToolChange={drawing.setTool}
              canUndo={drawing.canUndo}
              canRedo={drawing.canRedo}
              onUndo={drawing.undo}
              onRedo={drawing.redo}
              onDelete={() => {
                if (selectedMeasurementId) {
                  deleteMeasurementMutation.mutate(selectedMeasurementId);
                }
              }}
              hasSelection={!!selectedMeasurementId}
              disabled={!page?.scale_calibrated}
            />
          </div>

          {/* Canvas */}
          <div id="canvas-container" className="flex-1 relative">
            <Stage
              ref={stageRef}
              width={stageSize.width}
              height={stageSize.height}
              scaleX={zoom}
              scaleY={zoom}
              x={pan.x}
              y={pan.y}
              onMouseDown={handleStageMouseDown}
              onMouseMove={handleStageMouseMove}
              onMouseUp={handleStageMouseUp}
              onDblClick={handleStageDoubleClick}
            >
              {/* Background image */}
              <Layer>
                {image && <KonvaImage image={image} />}
              </Layer>

              {/* Measurements */}
              {page && (
                <MeasurementLayer
                  measurements={measurements}
                  conditions={new Map(conditions.map((c: Condition) => [c.id, c]))}
                  selectedMeasurementId={selectedMeasurementId}
                  onMeasurementSelect={setSelectedMeasurementId}
                  onMeasurementUpdate={() => {}}
                  isEditing={false}
                  scale={zoom}
                />
              )}

              {/* Drawing preview */}
              <DrawingPreviewLayer
                previewShape={drawing.previewShape}
                points={drawing.points}
                isDrawing={drawing.isDrawing}
                color={selectedCondition?.color || '#3B82F6'}
                scale={zoom}
              />
            </Stage>

            {/* Scale warning */}
            {!page?.scale_calibrated && (
              <div className="absolute top-4 left-1/2 transform -translate-x-1/2 bg-yellow-100 border border-yellow-400 text-yellow-800 px-4 py-2 rounded-lg">
                ⚠️ Scale not calibrated. Measurements will not be accurate.
              </div>
            )}
          </div>
        </div>

        {/* Right sidebar - Measurement details */}
        <div className="w-80 border-l bg-white p-4 overflow-y-auto">
          <h2 className="text-sm font-semibold mb-3">Measurements</h2>
          {selectedConditionId && (
            <div className="space-y-2">
              {measurements
                .filter((m: Measurement) => m.condition_id === selectedConditionId)
                .map((measurement: Measurement) => (
                  <div
                    key={measurement.id}
                    onClick={() => setSelectedMeasurementId(measurement.id)}
                    className={`p-3 rounded-lg border cursor-pointer ${
                      selectedMeasurementId === measurement.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <p className="text-sm font-medium">{measurement.geometry_type}</p>
                    <p className="text-lg font-bold text-blue-600">
                      {measurement.quantity.toFixed(1)} {measurement.unit}
                    </p>
                  </div>
                ))}
            </div>
          )}
        </div>
      </div>

      {/* Scale Calibration Modal */}
      {page && (
        <ScaleCalibration
          pageId={page.id}
          currentScale={page.scale_value}
          scaleText={page.detected_scale}
          isCalibrated={page.scale_calibrated}
          onCalibrationStart={() => setIsCalibrating(true)}
          onCalibrationEnd={() => setIsCalibrating(false)}
          calibrationLine={calibrationLine}
        />
      )}
    </div>
  );
}
```

---

### Task 6B.5: Add Route

Update `frontend/src/App.tsx` to add the route:

```tsx
import { TakeoffViewer } from '@/pages/TakeoffViewer';

// In your Routes:
<Route path="/documents/:documentId/pages/:pageId" element={<TakeoffViewer />} />
```

---

## Verification Checklist

After completing all tasks, verify:

- [ ] Toolbar displays all drawing tools
- [ ] Clicking a tool activates it (visual highlight)
- [ ] Keyboard shortcuts work (V, L, P, G, R, C, M)
- [ ] Line tool: Click start → move mouse → see preview → click end → measurement created
- [ ] Polyline tool: Click points → see preview → double-click → measurement created
- [ ] Polygon tool: Click points → see preview → double-click → measurement created
- [ ] Rectangle tool: Click and drag → see preview → release → measurement created
- [ ] Circle tool: Click center → drag radius → see preview → release → measurement created
- [ ] Point tool: Click → measurement created immediately
- [ ] Preview shapes show dashed lines and control points
- [ ] Measurements appear on canvas with labels after creation
- [ ] Condition totals update after creating measurements
- [ ] Select tool allows clicking to select existing measurements
- [ ] Delete button/key removes selected measurements
- [ ] Undo/Redo work (Ctrl+Z, Ctrl+Y)
- [ ] Escape cancels current drawing
- [ ] Warning shows if scale not calibrated
- [ ] Cannot draw if no condition selected
- [ ] Zoom controls work
- [ ] Canvas is responsive to window resize

### Test Workflow - Using Cursor Browser

**IMPORTANT**: Use Cursor's built-in browser tools to test the implementation. Do NOT create separate test files.

1. **Start the application**:
   ```bash
   cd docker && docker compose up -d
   cd ../frontend && npm run dev
   ```

2. **Open browser and navigate**:
   - Use `browser_navigate` to open `http://localhost:5173`
   - Use `browser_snapshot` to see the Dashboard page
   
3. **Upload a test PDF** (from `tests/` folder):
   - Use `browser_click` on the upload button
   - Navigate the file picker to select a test PDF
   - Wait for processing (use `browser_wait_for` for completion message)
   
4. **Navigate to a page**:
   - Use `browser_snapshot` to see the processed document
   - Use `browser_click` to open a page in the Takeoff Viewer
   - Verify you're on `/documents/{id}/pages/{id}` route
   
5. **Verify scale calibration** (from Phase 2B):
   - Use `browser_snapshot` to check if scale is calibrated
   - If not, create a condition via API first (curl or direct API call)
   
6. **Test drawing tools**:
   - Use `browser_snapshot` to see the toolbar
   - Use `browser_click` to select Polygon tool
   - Use `browser_click` multiple times on canvas to draw points
   - Use `browser_click` with `doubleClick: true` to finish
   - Use `browser_snapshot` to verify measurement appears with quantity label
   
7. **Test other tools**:
   - Repeat for Line, Rectangle, Circle, Point tools
   - Use `browser_snapshot` after each to verify measurements appear
   
8. **Test interactions**:
   - Use `browser_click` to select tool (V key)
   - Use `browser_click` on a measurement to select it
   - Use `browser_press_key` with `key: 'Delete'` to delete
   - Use `browser_press_key` with `key: 'z'` and `modifiers: ['Control']` for undo
   
9. **Verify condition totals**:
   - Use `browser_snapshot` to check left sidebar
   - Verify total_quantity updates after creating measurements
   
10. **Take screenshots** (optional):
    - Use `browser_take_screenshot` to capture successful states
    - Save evidence of working features

**Testing Checklist**:
- [ ] Toolbar displays correctly
- [ ] Each tool button clickable and activates
- [ ] Line tool creates measurement with correct quantity
- [ ] Polygon tool works with double-click to finish
- [ ] Rectangle tool works with click-drag-release
- [ ] Circle tool works with click-drag-release
- [ ] Point tool works with single click
- [ ] Measurements appear on canvas with labels
- [ ] Condition totals update correctly
- [ ] Select tool can select existing measurements
- [ ] Delete key removes selected measurements
- [ ] Keyboard shortcuts work (V, L, P, G, R, C, M)
- [ ] Scale warning appears when not calibrated

---

## Next Phase

Once verified, proceed to **Phase 3B** (`07-CONDITION-MANAGEMENT.md`) for implementing the condition management UI with templates and organization.
