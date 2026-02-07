import { useWorkspaceStore } from '@/stores/workspaceStore';
import { ConditionPanel } from '@/components/conditions/ConditionPanel';

interface RightPanelProps {
  projectId: string;
}

export function RightPanel({ projectId }: RightPanelProps) {
  const setFocusRegion = useWorkspaceStore((s) => s.setFocusRegion);

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
      <ConditionPanel projectId={projectId} />
    </div>
  );
}
