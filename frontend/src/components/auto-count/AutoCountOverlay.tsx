import type { AutoCountDetection } from '@/types';

interface AutoCountOverlayProps {
  detections: AutoCountDetection[];
  zoom: number;
  panX: number;
  panY: number;
  onDetectionClick?: (detection: AutoCountDetection) => void;
}

function getDetectionColor(detection: AutoCountDetection): string {
  if (detection.status === 'confirmed') return '#22C55E'; // green-500
  if (detection.status === 'rejected') return '#EF4444'; // red-500

  // Pending — color by confidence
  if (detection.confidence >= 0.9) return '#22C55E'; // green-500
  if (detection.confidence >= 0.7) return '#EAB308'; // yellow-500
  return '#EF4444'; // red-500
}

function getDetectionOpacity(detection: AutoCountDetection): number {
  if (detection.status === 'rejected') return 0.2;
  return 0.6;
}

export function AutoCountOverlay({
  detections,
  zoom,
  panX,
  panY,
  onDetectionClick,
}: AutoCountOverlayProps) {
  if (!detections || detections.length === 0) return null;

  return (
    <svg
      className="pointer-events-none absolute inset-0 h-full w-full"
      style={{ zIndex: 20 }}
    >
      {detections
        .filter((d) => d.status !== 'rejected')
        .map((detection) => {
          const color = getDetectionColor(detection);
          const opacity = getDetectionOpacity(detection);

          // Transform coordinates to viewport
          const x = detection.bbox.x * zoom + panX;
          const y = detection.bbox.y * zoom + panY;
          const w = detection.bbox.w * zoom;
          const h = detection.bbox.h * zoom;
          const centerX = detection.center_x * zoom + panX;
          const centerY = detection.center_y * zoom + panY;

          return (
            <g key={detection.id}>
              {/* Bounding box */}
              <rect
                x={x}
                y={y}
                width={w}
                height={h}
                fill={color}
                fillOpacity={opacity * 0.15}
                stroke={color}
                strokeWidth={1.5}
                strokeOpacity={opacity}
                strokeDasharray={detection.status === 'pending' ? '4 2' : 'none'}
                className="pointer-events-auto cursor-pointer"
                onClick={(e) => {
                  e.stopPropagation();
                  onDetectionClick?.(detection);
                }}
              />

              {/* Center point marker */}
              <circle
                cx={centerX}
                cy={centerY}
                r={3}
                fill={color}
                fillOpacity={opacity}
              />

              {/* Confidence label */}
              <text
                x={x + 2}
                y={y - 3}
                fill={color}
                fontSize={10}
                fontFamily="monospace"
                opacity={opacity}
              >
                {Math.round(detection.confidence * 100)}%
              </text>

              {/* Status badge for confirmed */}
              {detection.status === 'confirmed' && (
                <circle
                  cx={x + w - 4}
                  cy={y + 4}
                  r={4}
                  fill="#22C55E"
                  fillOpacity={0.9}
                />
              )}
            </g>
          );
        })}
    </svg>
  );
}
