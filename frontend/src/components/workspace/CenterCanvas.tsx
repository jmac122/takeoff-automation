import { useWorkspaceStore } from '@/stores/workspaceStore';
import { Loader2 } from 'lucide-react';
import {
  REVIEW_CONFIDENCE_HIGH,
  REVIEW_CONFIDENCE_MEDIUM,
  REVIEW_COLOR_HIGH,
  REVIEW_COLOR_MEDIUM,
  REVIEW_COLOR_LOW,
} from '@/lib/constants';
import type { Measurement } from '@/types';

interface CenterCanvasProps {
  projectId: string;
  isLoadingSheet?: boolean;
  sheetImageUrl?: string | null;
  measurements?: Measurement[];
}

/**
 * Get the review color for a measurement based on AI confidence.
 * Used when review mode is active to override condition colors.
 */
export function getReviewColor(confidence: number | null | undefined): string {
  if (confidence == null) return REVIEW_COLOR_LOW;
  if (confidence >= REVIEW_CONFIDENCE_HIGH) return REVIEW_COLOR_HIGH;
  if (confidence >= REVIEW_CONFIDENCE_MEDIUM) return REVIEW_COLOR_MEDIUM;
  return REVIEW_COLOR_LOW;
}

/**
 * Filter measurements for canvas rendering.
 * - Always: exclude rejected measurements
 * - In review mode: also apply confidence filter
 */
export function filterMeasurementsForCanvas(
  measurements: Measurement[],
  reviewMode: boolean,
  confidenceFilter: number,
): Measurement[] {
  return measurements.filter((m) => {
    // Always exclude rejected
    if (m.is_rejected) return false;
    // In review mode, apply confidence filter
    if (reviewMode && confidenceFilter > 0) {
      const confidence = m.ai_confidence ?? 0;
      if (confidence < confidenceFilter) return false;
    }
    return true;
  });
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function CenterCanvas({ projectId, isLoadingSheet, sheetImageUrl, measurements }: CenterCanvasProps) {
  const activeSheetId = useWorkspaceStore((s) => s.activeSheetId);
  const setFocusRegion = useWorkspaceStore((s) => s.setFocusRegion);
  const reviewMode = useWorkspaceStore((s) => s.reviewMode);
  const reviewCurrentId = useWorkspaceStore((s) => s.reviewCurrentId);
  const reviewConfidenceFilter = useWorkspaceStore((s) => s.reviewConfidenceFilter);

  // Filter measurements for rendering (excludes rejected, applies confidence filter in review mode)
  const visibleMeasurements = measurements
    ? filterMeasurementsForCanvas(measurements, reviewMode, reviewConfidenceFilter)
    : [];

  return (
    <div
      className="flex h-full w-full items-center justify-center bg-neutral-950"
      data-focus-region="canvas"
      data-testid="center-canvas"
      tabIndex={0}
      onFocus={() => setFocusRegion('canvas')}
    >
      {!activeSheetId ? (
        <div className="text-center text-neutral-500">
          <p className="text-lg font-medium">No sheet selected</p>
          <p className="mt-1 text-sm">Select a sheet from the left panel to begin</p>
        </div>
      ) : isLoadingSheet ? (
        <div className="flex flex-col items-center gap-2 text-neutral-400">
          <Loader2 className="h-8 w-8 animate-spin" />
          <p className="text-sm">Loading sheet...</p>
        </div>
      ) : sheetImageUrl ? (
        <div className="relative h-full w-full overflow-auto">
          <img
            src={sheetImageUrl}
            alt="Sheet plan"
            className="max-h-full max-w-full object-contain"
            draggable={false}
          />
          {/* Review mode indicator overlay */}
          {reviewMode && (
            <div className="absolute left-2 top-2 rounded bg-green-600/80 px-2 py-1 text-xs font-medium text-white">
              Review Mode ({visibleMeasurements.length} measurements)
            </div>
          )}
          {/* Current review measurement indicator */}
          {reviewMode && reviewCurrentId && (
            <div className="absolute bottom-2 left-2 rounded bg-neutral-900/80 px-2 py-1 text-xs text-neutral-300">
              Reviewing: {reviewCurrentId.slice(0, 8)}...
            </div>
          )}
        </div>
      ) : (
        <div className="text-center text-neutral-500">
          <p className="text-sm">Sheet image not available</p>
        </div>
      )}
    </div>
  );
}
