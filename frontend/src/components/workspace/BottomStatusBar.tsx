import { useWorkspaceStore } from '@/stores/workspaceStore';
import { BOTTOM_STATUS_BAR_HEIGHT } from '@/lib/constants';

export function BottomStatusBar() {
  const viewport = useWorkspaceStore((s) => s.viewport);
  const activeTool = useWorkspaceStore((s) => s.activeTool);
  const activeSheetId = useWorkspaceStore((s) => s.activeSheetId);
  const selectedMeasurementIds = useWorkspaceStore((s) => s.selectedMeasurementIds);

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
      <span className="ml-auto text-neutral-500">ForgeX Takeoffs</span>
    </div>
  );
}
