import type { SheetInfo } from '@/api/sheets';
import { SCALE_CONFIDENCE_HIGH, SCALE_CONFIDENCE_MEDIUM } from '@/lib/constants';

interface ScaleBadgeProps {
  sheet: SheetInfo;
}

/**
 * Scale badge indicator:
 * - Green: auto-detected scale with high confidence (>= 0.85)
 * - Yellow: auto-detected scale with medium confidence (>= 0.50)
 * - Red (dot): no scale detected
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

  // Auto-detected scale — color by confidence
  const confidence = sheet.classification_confidence ?? 0;
  const isHighConfidence = confidence >= SCALE_CONFIDENCE_HIGH;
  const isMediumConfidence = confidence >= SCALE_CONFIDENCE_MEDIUM;
  const displayText = sheet.scale_text || sheet.scale_value?.toString() || 'Scaled';

  if (isHighConfidence) {
    return (
      <span
        className="inline-flex items-center rounded bg-green-600/20 px-1 py-0.5 text-[10px] text-green-400"
        title={`Scale: ${displayText} (confidence: ${(confidence * 100).toFixed(0)}%)`}
        data-testid="scale-badge-auto"
      >
        {displayText}
      </span>
    );
  }

  if (isMediumConfidence) {
    return (
      <span
        className="inline-flex items-center rounded bg-yellow-600/20 px-1 py-0.5 text-[10px] text-yellow-400"
        title={`Scale: ${displayText} (confidence: ${(confidence * 100).toFixed(0)}%)`}
        data-testid="scale-badge-medium"
      >
        {displayText}
      </span>
    );
  }

  // Low confidence auto-detected
  return (
    <span
      className="inline-flex items-center rounded bg-green-600/20 px-1 py-0.5 text-[10px] text-green-400"
      title={`Scale: ${displayText} (auto-detected)`}
      data-testid="scale-badge-auto"
    >
      {displayText}
    </span>
  );
}
