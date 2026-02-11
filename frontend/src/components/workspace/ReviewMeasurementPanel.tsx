import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useWorkspaceStore } from '@/stores/workspaceStore';
import { useReviewActions } from '@/hooks/useReviewActions';
import { getMeasurementHistory } from '@/api/review';
import { listPageMeasurements } from '@/api/measurements';
import {
  REVIEW_CONFIDENCE_HIGH,
  REVIEW_CONFIDENCE_MEDIUM,
  REVIEW_COLOR_HIGH,
  REVIEW_COLOR_MEDIUM,
  REVIEW_COLOR_LOW,
} from '@/lib/constants';
import {
  Check,
  X,
  SkipForward,
  ChevronDown,
  ChevronUp,
  Clock,
  AlertCircle,
} from 'lucide-react';
import type { Measurement, MeasurementHistoryEntry } from '@/types';

interface ReviewMeasurementPanelProps {
  projectId: string;
  pageId: string | undefined;
}

function getConfidenceBadge(confidence: number | null | undefined) {
  if (confidence == null) {
    return { color: REVIEW_COLOR_LOW, label: 'N/A', bg: 'bg-red-900/50' };
  }
  if (confidence >= REVIEW_CONFIDENCE_HIGH) {
    return { color: REVIEW_COLOR_HIGH, label: `${Math.round(confidence * 100)}%`, bg: 'bg-green-900/50' };
  }
  if (confidence >= REVIEW_CONFIDENCE_MEDIUM) {
    return { color: REVIEW_COLOR_MEDIUM, label: `${Math.round(confidence * 100)}%`, bg: 'bg-yellow-900/50' };
  }
  return { color: REVIEW_COLOR_LOW, label: `${Math.round(confidence * 100)}%`, bg: 'bg-red-900/50' };
}

function getStatusLabel(m: Measurement): string {
  if (m.is_rejected) return 'Rejected';
  if (m.is_verified && m.is_modified) return 'Modified';
  if (m.is_verified) return 'Approved';
  return 'Pending';
}

function getStatusColor(m: Measurement): string {
  if (m.is_rejected) return 'text-red-400';
  if (m.is_verified) return 'text-green-400';
  return 'text-yellow-400';
}

export function ReviewMeasurementPanel({ projectId, pageId }: ReviewMeasurementPanelProps) {
  const reviewCurrentId = useWorkspaceStore((s) => s.reviewCurrentId);
  const { approve, reject, isApproving, isRejecting } = useReviewActions(pageId, projectId);
  const [rejectReason, setRejectReason] = useState('');
  const [showRejectForm, setShowRejectForm] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [reviewNotes, setReviewNotes] = useState('');
  const advanceReview = useWorkspaceStore((s) => s.advanceReview);

  // Get current measurement from page measurements
  const { data: measurementsData } = useQuery({
    queryKey: ['measurements', pageId],
    queryFn: () => listPageMeasurements(pageId!),
    enabled: !!pageId,
  });

  const currentMeasurement = measurementsData?.measurements.find(
    (m) => m.id === reviewCurrentId,
  );

  // Get history for current measurement
  const { data: historyData } = useQuery({
    queryKey: ['measurement-history', reviewCurrentId],
    queryFn: () => getMeasurementHistory(reviewCurrentId!),
    enabled: !!reviewCurrentId && showHistory,
  });

  const handleApprove = () => {
    if (!reviewCurrentId) return;
    approve({
      measurementId: reviewCurrentId,
      reviewer: 'user',
      notes: reviewNotes || undefined,
    });
    setReviewNotes('');
    setShowRejectForm(false);
  };

  const handleReject = () => {
    if (!reviewCurrentId || !rejectReason.trim()) return;
    reject({
      measurementId: reviewCurrentId,
      reviewer: 'user',
      reason: rejectReason,
    });
    setRejectReason('');
    setShowRejectForm(false);
    setReviewNotes('');
  };

  const handleSkip = async () => {
    if (!pageId) return;
    const { getNextUnreviewed } = await import('@/api/review');
    try {
      const result = await getNextUnreviewed(pageId, reviewCurrentId);
      advanceReview(result.measurement?.id ?? null);
    } catch {
      // Silently fail
    }
  };

  if (!reviewCurrentId || !currentMeasurement) {
    return (
      <div className="flex flex-col items-center justify-center p-4 text-neutral-500">
        <AlertCircle size={24} className="mb-2" />
        <p className="text-sm text-center">
          {!pageId
            ? 'Select a sheet to start reviewing'
            : 'No measurement selected for review'}
        </p>
      </div>
    );
  }

  const confidence = getConfidenceBadge(currentMeasurement.ai_confidence);

  return (
    <div className="flex flex-col gap-3 p-3 text-sm">
      {/* Measurement info */}
      <div className="rounded-lg bg-neutral-800 p-3">
        <div className="flex items-center justify-between mb-2">
          <span className="font-medium text-neutral-200 capitalize">
            {currentMeasurement.geometry_type}
          </span>
          <span className={getStatusColor(currentMeasurement)}>
            {getStatusLabel(currentMeasurement)}
          </span>
        </div>

        <div className="grid grid-cols-2 gap-2 text-xs text-neutral-400">
          <div>
            <span className="text-neutral-500">Quantity:</span>{' '}
            <span className="text-neutral-200">{currentMeasurement.quantity.toFixed(2)} {currentMeasurement.unit}</span>
          </div>
          {currentMeasurement.is_ai_generated && (
            <div>
              <span className="text-neutral-500">AI Model:</span>{' '}
              <span className="text-neutral-200">{currentMeasurement.ai_model ?? 'Unknown'}</span>
            </div>
          )}
        </div>

        {/* Confidence badge */}
        {currentMeasurement.is_ai_generated && (
          <div className="mt-2 flex items-center gap-2">
            <span className="text-xs text-neutral-500">Confidence:</span>
            <span
              className={`inline-flex items-center rounded px-2 py-0.5 text-xs font-medium ${confidence.bg}`}
              style={{ color: confidence.color }}
            >
              {confidence.label}
            </span>
          </div>
        )}
      </div>

      {/* Notes input */}
      <div>
        <label className="mb-1 block text-xs text-neutral-500">Review Notes</label>
        <textarea
          className="w-full rounded bg-neutral-800 px-2 py-1.5 text-xs text-neutral-200 border border-neutral-700 focus:border-blue-500 focus:outline-none resize-none"
          rows={2}
          value={reviewNotes}
          onChange={(e) => setReviewNotes(e.target.value)}
          placeholder="Optional notes..."
        />
      </div>

      {/* Reject reason form */}
      {showRejectForm && (
        <div>
          <label className="mb-1 block text-xs text-red-400">Rejection Reason (required)</label>
          <textarea
            className="w-full rounded bg-neutral-800 px-2 py-1.5 text-xs text-neutral-200 border border-red-700 focus:border-red-500 focus:outline-none resize-none"
            rows={2}
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            placeholder="Why is this measurement incorrect?"
            autoFocus
          />
          <div className="mt-2 flex gap-2">
            <button
              className="flex-1 rounded bg-red-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-red-500 disabled:opacity-50"
              onClick={handleReject}
              disabled={!rejectReason.trim() || isRejecting}
            >
              {isRejecting ? 'Rejecting...' : 'Confirm Reject'}
            </button>
            <button
              className="rounded bg-neutral-700 px-3 py-1.5 text-xs text-neutral-300 hover:bg-neutral-600"
              onClick={() => setShowRejectForm(false)}
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Action buttons */}
      {!showRejectForm && (
        <div className="flex gap-2">
          <button
            className="flex flex-1 items-center justify-center gap-1 rounded bg-green-600 px-3 py-2 text-xs font-medium text-white hover:bg-green-500 disabled:opacity-50"
            onClick={handleApprove}
            disabled={isApproving}
            title="Approve (A)"
          >
            <Check size={14} />
            {isApproving ? 'Approving...' : 'Approve'}
          </button>
          <button
            className="flex flex-1 items-center justify-center gap-1 rounded bg-red-600 px-3 py-2 text-xs font-medium text-white hover:bg-red-500"
            onClick={() => setShowRejectForm(true)}
            title="Reject (R)"
          >
            <X size={14} />
            Reject
          </button>
          <button
            className="flex items-center justify-center gap-1 rounded bg-neutral-700 px-3 py-2 text-xs text-neutral-300 hover:bg-neutral-600"
            onClick={handleSkip}
            title="Skip (S)"
          >
            <SkipForward size={14} />
          </button>
        </div>
      )}

      {/* History toggle */}
      <button
        className="flex items-center gap-1 text-xs text-neutral-500 hover:text-neutral-300"
        onClick={() => setShowHistory(!showHistory)}
      >
        {showHistory ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        History
      </button>

      {/* History entries */}
      {showHistory && historyData && (
        <div className="max-h-48 overflow-y-auto space-y-2">
          {historyData.length === 0 ? (
            <p className="text-xs text-neutral-500">No history entries</p>
          ) : (
            historyData.map((entry: MeasurementHistoryEntry) => (
              <div
                key={entry.id}
                className="rounded bg-neutral-800 p-2 text-xs"
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium text-neutral-300 capitalize">{entry.action.replace('_', ' ')}</span>
                  <span className="text-neutral-500 flex items-center gap-1">
                    <Clock size={10} />
                    {new Date(entry.created_at).toLocaleString()}
                  </span>
                </div>
                <div className="mt-1 text-neutral-400">
                  by {entry.actor} ({entry.actor_type})
                </div>
                {entry.change_description && (
                  <div className="mt-1 text-neutral-500">{entry.change_description}</div>
                )}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
