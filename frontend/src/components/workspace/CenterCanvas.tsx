import { useWorkspaceStore } from '@/stores/workspaceStore';
import { Loader2 } from 'lucide-react';

interface CenterCanvasProps {
  projectId: string;
  isLoadingSheet?: boolean;
  sheetImageUrl?: string | null;
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function CenterCanvas({ projectId, isLoadingSheet, sheetImageUrl }: CenterCanvasProps) {
  const activeSheetId = useWorkspaceStore((s) => s.activeSheetId);
  const setFocusRegion = useWorkspaceStore((s) => s.setFocusRegion);

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
        <div className="h-full w-full overflow-auto">
          <img
            src={sheetImageUrl}
            alt="Sheet plan"
            className="max-h-full max-w-full object-contain"
            draggable={false}
          />
        </div>
      ) : (
        <div className="text-center text-neutral-500">
          <p className="text-sm">Sheet image not available</p>
        </div>
      )}
    </div>
  );
}
