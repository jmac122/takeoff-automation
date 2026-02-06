import { useWorkspaceStore } from '@/stores/workspaceStore';

interface RightPanelProps {
  projectId: string;
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function RightPanel({ projectId }: RightPanelProps) {
  const setFocusRegion = useWorkspaceStore((s) => s.setFocusRegion);
  const activeConditionId = useWorkspaceStore((s) => s.activeConditionId);

  return (
    <div
      className="flex h-full flex-col bg-neutral-900"
      data-focus-region="conditions"
      data-testid="right-panel"
      tabIndex={0}
      onFocus={() => setFocusRegion('conditions')}
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b border-neutral-700 px-3 py-2">
        <h3 className="text-sm font-medium text-neutral-200">Conditions</h3>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-3">
        {!activeConditionId ? (
          <p className="text-xs text-neutral-500">
            Select or create a condition to start measuring.
          </p>
        ) : (
          <p className="text-xs text-neutral-400">
            Condition: {activeConditionId.slice(0, 8)}...
          </p>
        )}
      </div>
    </div>
  );
}
