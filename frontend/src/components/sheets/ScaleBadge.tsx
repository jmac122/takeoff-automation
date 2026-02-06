import { SCALE_CONFIDENCE_HIGH, SCALE_CONFIDENCE_MEDIUM } from '@/lib/constants';
import type { SheetInfo } from '@/api/sheets';

interface ScaleBadgeProps {
  sheet: SheetInfo;
}

/**
 * Scale confidence indicator:
 * - Green (high): confidence >= 0.85
 * - Yellow (medium): confidence >= 0.50
 * - Red (none): no scale detected
 * - Blue: manually calibrated
 */
export function ScaleBadge({ sheet }: ScaleBadgeProps) {
  if (!sheet.scale_text && !sheet.scale_calibrated) {
    // No scale detected
    return (
      <span
        className="inline-flex h-2 w-2 rounded-full bg-red-500"
        title="No scale detected"
        data-testid="scale-badge-none"
      />
    );
  }

  if (sheet.scale_detection_method === 'manual_calibration') {
    // Manually calibrated
    return (
      <span
        className="inline-flex items-center rounded bg-blue-600/20 px-1 py-0.5 text-[10px] text-blue-400"
        title={`Manual: ${sheet.scale_text || 'calibrated'}`}
        data-testid="scale-badge-manual"
      >
        {sheet.scale_text || 'Cal'}
      </span>
    );
  }

  // Auto-detected — compute confidence from classification_confidence as proxy
  // In production, the sheets endpoint would include scale_confidence directly
  const confidence = sheet.classification_confidence ?? 0;

  if (confidence >= SCALE_CONFIDENCE_HIGH) {
    return (
      <span
        className="inline-flex items-center rounded bg-green-600/20 px-1 py-0.5 text-[10px] text-green-400"
        title={`Scale: ${sheet.scale_text} (${Math.round(confidence * 100)}% confidence)`}
        data-testid="scale-badge-high"
      >
        {sheet.scale_text}
      </span>
    );
  }

  if (confidence >= SCALE_CONFIDENCE_MEDIUM) {
    return (
      <span
        className="inline-flex items-center rounded bg-yellow-600/20 px-1 py-0.5 text-[10px] text-yellow-400"
        title={`Scale: ${sheet.scale_text} (${Math.round(confidence * 100)}% confidence)`}
        data-testid="scale-badge-medium"
      >
        {sheet.scale_text}
      </span>
    );
  }

  // Low confidence
  return (
    <span
      className="inline-flex items-center rounded bg-yellow-600/20 px-1 py-0.5 text-[10px] text-yellow-400"
      title={`Scale: ${sheet.scale_text} (low confidence)`}
      data-testid="scale-badge-low"
    >
      {sheet.scale_text}
    </span>
  );
}
