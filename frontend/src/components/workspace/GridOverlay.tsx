import { useMemo } from 'react';
import { useWorkspaceStore } from '@/stores/workspaceStore';

interface GridOverlayProps {
  /** Canvas width in pixels */
  width: number;
  /** Canvas height in pixels */
  height: number;
  className?: string;
}

/**
 * SVG overlay that draws a subtle snap-to-grid pattern on the canvas.
 *
 * Grid lines are spaced by `gridSize` (in image-pixel space) and
 * scaled/translated to match the current viewport zoom & pan.
 *
 * Hidden when `showGrid` is false in the workspace store.
 */
export function GridOverlay({ width, height, className = '' }: GridOverlayProps) {
  const showGrid = useWorkspaceStore((s) => s.showGrid);
  const gridSize = useWorkspaceStore((s) => s.gridSize);
  const viewport = useWorkspaceStore((s) => s.viewport);

  // Compute grid lines visible in the current viewport
  const { verticals, horizontals } = useMemo(() => {
    if (!showGrid || gridSize <= 0) return { verticals: [], horizontals: [] };

    const { zoom, panX, panY } = viewport;
    const scaledGrid = gridSize * zoom;

    // Avoid rendering too many lines (performance guard)
    if (scaledGrid < 4) return { verticals: [], horizontals: [] };

    // Offset so grid aligns with image-pixel grid after pan
    const offsetX = (panX % scaledGrid + scaledGrid) % scaledGrid;
    const offsetY = (panY % scaledGrid + scaledGrid) % scaledGrid;

    const vLines: number[] = [];
    for (let x = offsetX; x <= width; x += scaledGrid) {
      vLines.push(x);
    }

    const hLines: number[] = [];
    for (let y = offsetY; y <= height; y += scaledGrid) {
      hLines.push(y);
    }

    return { verticals: vLines, horizontals: hLines };
  }, [showGrid, gridSize, viewport, width, height]);

  if (!showGrid) return null;

  return (
    <svg
      className={`pointer-events-none absolute inset-0 ${className}`}
      width={width}
      height={height}
      data-testid="grid-overlay"
    >
      {verticals.map((x) => (
        <line
          key={`v-${x}`}
          x1={x}
          y1={0}
          x2={x}
          y2={height}
          stroke="rgba(255,255,255,0.08)"
          strokeWidth={1}
        />
      ))}
      {horizontals.map((y) => (
        <line
          key={`h-${y}`}
          x1={0}
          y1={y}
          x2={width}
          y2={y}
          stroke="rgba(255,255,255,0.08)"
          strokeWidth={1}
        />
      ))}
    </svg>
  );
}
