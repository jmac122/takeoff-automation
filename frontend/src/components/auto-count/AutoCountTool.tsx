import { useState } from 'react';
import {
  ScanSearch,
  Check,
  X,
  CheckCheck,
  Loader2,
  AlertTriangle,
  Download,
} from 'lucide-react';
import {
  useAutoCountSession,
  useBulkConfirmDetections,
  useConfirmDetection,
  useCreateMeasurementsFromDetections,
  useRejectDetection,
  useStartAutoCount,
} from '@/hooks/useAutoCount';
import type { AutoCountDetection, BBox } from '@/types';

interface AutoCountToolProps {
  pageId: string;
  conditionId: string;
}

type ToolState = 'idle' | 'selecting' | 'processing' | 'reviewing';

export function AutoCountTool({ pageId, conditionId }: AutoCountToolProps) {
  const [toolState, setToolState] = useState<ToolState>('idle');
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [thresholdSlider, setThresholdSlider] = useState(0.80);

  const startAutoCount = useStartAutoCount(pageId);
  const { data: session } =
    useAutoCountSession(activeSessionId ?? undefined);
  const confirmDetection = useConfirmDetection(activeSessionId ?? undefined);
  const rejectDetection = useRejectDetection(activeSessionId ?? undefined);
  const bulkConfirm = useBulkConfirmDetections(activeSessionId ?? undefined);
  const createMeasurements = useCreateMeasurementsFromDetections(
    activeSessionId ?? undefined,
    conditionId
  );

  // Auto-transition from processing to reviewing when session completes
  if (
    toolState === 'processing' &&
    session &&
    session.status === 'completed'
  ) {
    setToolState('reviewing');
  }

  // Called by canvas when user finishes drawing bbox in 'selecting' state
  const handleStartDetection = (templateBbox: BBox) => {
    setToolState('processing');
    startAutoCount.mutate(
      {
        condition_id: conditionId,
        template_bbox: templateBbox,
        confidence_threshold: thresholdSlider,
        detection_method: 'hybrid',
      },
      {
        onSuccess: (response) => {
          setActiveSessionId(response.session_id);
        },
        onError: () => {
          setToolState('idle');
        },
      }
    );
  };
  void handleStartDetection;

  const handleConfirm = (detectionId: string) => {
    confirmDetection.mutate(detectionId);
  };

  const handleReject = (detectionId: string) => {
    rejectDetection.mutate(detectionId);
  };

  const handleBulkConfirm = () => {
    bulkConfirm.mutate(thresholdSlider);
  };

  const handleCreateMeasurements = () => {
    createMeasurements.mutate(undefined, {
      onSuccess: () => {
        setToolState('idle');
        setActiveSessionId(null);
      },
    });
  };

  const handleCancel = () => {
    setToolState('idle');
    setActiveSessionId(null);
  };

  // Idle state — show "Start Auto Count" button
  if (toolState === 'idle') {
    return (
      <div className="flex flex-col gap-2 rounded border border-neutral-700 bg-neutral-800 p-3">
        <div className="flex items-center gap-2">
          <ScanSearch className="h-4 w-4 text-cyan-400" />
          <span className="text-xs font-medium text-neutral-200">
            Auto Count
          </span>
        </div>
        <p className="text-[10px] text-neutral-500">
          Draw a box around one instance to find all similar elements.
        </p>
        <div className="flex items-center gap-2">
          <label className="text-[10px] text-neutral-500">Threshold:</label>
          <input
            type="range"
            min={0.5}
            max={1.0}
            step={0.05}
            value={thresholdSlider}
            onChange={(e) => setThresholdSlider(Number(e.target.value))}
            className="flex-1 accent-cyan-500"
          />
          <span className="text-[10px] text-neutral-400 w-8 text-right">
            {Math.round(thresholdSlider * 100)}%
          </span>
        </div>
        <button
          className="mt-1 w-full rounded bg-cyan-600 px-2 py-1.5 text-xs font-medium text-white hover:bg-cyan-500 transition-colors"
          onClick={() => setToolState('selecting')}
        >
          Select Template Region
        </button>
      </div>
    );
  }

  // Selecting state — user draws bbox on canvas
  if (toolState === 'selecting') {
    return (
      <div className="flex flex-col gap-2 rounded border border-cyan-700 bg-cyan-900/20 p-3">
        <div className="flex items-center gap-2">
          <ScanSearch className="h-4 w-4 text-cyan-400 animate-pulse" />
          <span className="text-xs font-medium text-cyan-300">
            Draw Template Box
          </span>
        </div>
        <p className="text-[10px] text-neutral-400">
          Click and drag on the canvas to select one instance of the element
          you want to count.
        </p>
        <button
          className="mt-1 w-full rounded border border-neutral-600 px-2 py-1.5 text-xs text-neutral-400 hover:text-neutral-200 transition-colors"
          onClick={handleCancel}
        >
          Cancel
        </button>
      </div>
    );
  }

  // Processing state
  if (toolState === 'processing') {
    return (
      <div className="flex flex-col gap-2 rounded border border-neutral-700 bg-neutral-800 p-3">
        <div className="flex items-center gap-2">
          <Loader2 className="h-4 w-4 text-cyan-400 animate-spin" />
          <span className="text-xs font-medium text-neutral-200">
            Detecting...
          </span>
        </div>
        <p className="text-[10px] text-neutral-500">
          Searching for similar elements on this sheet.
        </p>
        {session && (
          <div className="text-[10px] text-neutral-500">
            Status: {session.status}
            {session.processing_time_ms && (
              <span> ({(session.processing_time_ms / 1000).toFixed(1)}s)</span>
            )}
          </div>
        )}
      </div>
    );
  }

  // Reviewing state
  if (toolState === 'reviewing' && session) {
    const pendingCount = session.detections.filter(
      (d) => d.status === 'pending'
    ).length;
    const confirmedCount = session.confirmed_count;
    const rejectedCount = session.rejected_count;

    const failed = session.status === 'failed';

    return (
      <div className="flex flex-col gap-2 rounded border border-neutral-700 bg-neutral-800 p-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ScanSearch className="h-4 w-4 text-cyan-400" />
            <span className="text-xs font-medium text-neutral-200">
              Auto Count Results
            </span>
          </div>
          <button
            className="text-neutral-500 hover:text-neutral-300 text-xs"
            onClick={handleCancel}
          >
            &times;
          </button>
        </div>

        {failed ? (
          <div className="flex items-center gap-2 text-red-400 text-xs">
            <AlertTriangle className="h-3.5 w-3.5" />
            <span>{session.error_message || 'Detection failed'}</span>
          </div>
        ) : (
          <>
            {/* Stats */}
            <div className="flex gap-3 text-[10px]">
              <span className="text-neutral-400">
                Total: <strong className="text-neutral-200">{session.total_detections}</strong>
              </span>
              <span className="text-green-400">
                Confirmed: {confirmedCount}
              </span>
              <span className="text-red-400">
                Rejected: {rejectedCount}
              </span>
              <span className="text-neutral-500">
                Pending: {pendingCount}
              </span>
            </div>

            {/* Threshold slider for bulk confirm */}
            <div className="flex items-center gap-2">
              <label className="text-[10px] text-neutral-500">Min confidence:</label>
              <input
                type="range"
                min={0.5}
                max={1.0}
                step={0.05}
                value={thresholdSlider}
                onChange={(e) => setThresholdSlider(Number(e.target.value))}
                className="flex-1 accent-cyan-500"
              />
              <span className="text-[10px] text-neutral-400 w-8 text-right">
                {Math.round(thresholdSlider * 100)}%
              </span>
            </div>

            {/* Action buttons */}
            <div className="flex gap-1.5">
              <button
                className="flex-1 flex items-center justify-center gap-1 rounded bg-green-700 px-2 py-1.5 text-xs text-white hover:bg-green-600 transition-colors"
                onClick={handleBulkConfirm}
                disabled={bulkConfirm.isPending || pendingCount === 0}
              >
                <CheckCheck className="h-3 w-3" />
                Confirm All
              </button>
              <button
                className="flex-1 flex items-center justify-center gap-1 rounded bg-cyan-700 px-2 py-1.5 text-xs text-white hover:bg-cyan-600 transition-colors"
                onClick={handleCreateMeasurements}
                disabled={createMeasurements.isPending || confirmedCount === 0}
              >
                <Download className="h-3 w-3" />
                Create ({confirmedCount})
              </button>
            </div>

            {/* Detection list */}
            <div className="max-h-[200px] overflow-y-auto border-t border-neutral-700 pt-1 mt-1">
              {session.detections.map((detection) => (
                <DetectionRow
                  key={detection.id}
                  detection={detection}
                  onConfirm={() => handleConfirm(detection.id)}
                  onReject={() => handleReject(detection.id)}
                />
              ))}
            </div>
          </>
        )}
      </div>
    );
  }

  return null;
}

// ---------------------------------------------------------------------------
// Detection row
// ---------------------------------------------------------------------------

function DetectionRow({
  detection,
  onConfirm,
  onReject,
}: {
  detection: AutoCountDetection;
  onConfirm: () => void;
  onReject: () => void;
}) {
  const confidenceColor =
    detection.confidence >= 0.9
      ? 'text-green-400'
      : detection.confidence >= 0.7
        ? 'text-yellow-400'
        : 'text-red-400';

  return (
    <div className="group flex items-center gap-2 py-0.5 text-[10px]">
      <span className={`w-8 text-right font-mono ${confidenceColor}`}>
        {Math.round(detection.confidence * 100)}%
      </span>
      <span className="text-neutral-500">
        ({Math.round(detection.center_x)}, {Math.round(detection.center_y)})
      </span>
      <span className="flex-1 text-neutral-600">{detection.detection_source}</span>
      {detection.status === 'pending' ? (
        <div className="flex gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            className="rounded p-0.5 text-green-500 hover:bg-green-900/30"
            onClick={onConfirm}
            title="Confirm"
          >
            <Check className="h-3 w-3" />
          </button>
          <button
            className="rounded p-0.5 text-red-500 hover:bg-red-900/30"
            onClick={onReject}
            title="Reject"
          >
            <X className="h-3 w-3" />
          </button>
        </div>
      ) : (
        <span
          className={`text-[9px] px-1 rounded ${
            detection.status === 'confirmed'
              ? 'bg-green-900/30 text-green-400'
              : 'bg-red-900/30 text-red-400'
          }`}
        >
          {detection.status}
        </span>
      )}
    </div>
  );
}
