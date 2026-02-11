import { useWorkspaceStore } from '@/stores/workspaceStore';
import { useReviewStats } from '@/hooks/useReviewStats';
import { BOTTOM_STATUS_BAR_HEIGHT } from '@/lib/constants';

interface BottomStatusBarProps {
  projectId?: string;
}

export function BottomStatusBar({ projectId }: BottomStatusBarProps) {
  const viewport = useWorkspaceStore((s) => s.viewport);
  const activeTool = useWorkspaceStore((s) => s.activeTool);
  const activeSheetId = useWorkspaceStore((s) => s.activeSheetId);
  const selectedMeasurementIds = useWorkspaceStore((s) => s.selectedMeasurementIds);
  const reviewMode = useWorkspaceStore((s) => s.reviewMode);
  const { data: reviewStats } = useReviewStats(projectId);

  return (
    <div
      className="flex items-center gap-4 border-t border-neutral-700 bg-neutral-900 px-3 text-xs text-neutral-400"
      style={{ height: BOTTOM_STATUS_BAR_HEIGHT }}
      data-testid="bottom-status-bar"
    >
      <span>Zoom: {Math.round(viewport.zoom * 100)}%</span>
      <span>Tool: {activeTool ?? 'none'}</span>
      {activeSheetId && <span>Sheet: {activeSheetId.slice(0, 8)}...</span>}
      {selectedMeasurementIds.length > 0 && (
        <span>{selectedMeasurementIds.length} selected</span>
      )}

      {/* Review stats in review mode */}
      {reviewMode && reviewStats && (
        <span className="flex items-center gap-2">
          Review:
          <span className="text-green-400">{reviewStats.approved} approved</span>
          <span className="text-yellow-400">{reviewStats.pending} pending</span>
          <span className="text-red-400">{reviewStats.rejected} rejected</span>
        </span>
      )}

      <span className="ml-auto text-neutral-500">ForgeX Takeoffs</span>
    </div>
  );
}
