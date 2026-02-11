import { useState, useEffect } from 'react';
import { useWorkspaceStore } from '@/stores/workspaceStore';
import { ConditionPanel } from '@/components/conditions/ConditionPanel';
import { ReviewMeasurementPanel } from '@/components/workspace/ReviewMeasurementPanel';

interface RightPanelProps {
  projectId: string;
  pageId?: string;
}

type RightPanelTab = 'conditions' | 'review';

export function RightPanel({ projectId, pageId }: RightPanelProps) {
  const setFocusRegion = useWorkspaceStore((s) => s.setFocusRegion);
  const reviewMode = useWorkspaceStore((s) => s.reviewMode);
  const [activeTab, setActiveTab] = useState<RightPanelTab>('conditions');

  // Auto-switch to review tab when review mode activates
  useEffect(() => {
    if (reviewMode) {
      setActiveTab('review');
    }
  }, [reviewMode]);

  return (
    <div
      className="flex h-full flex-col bg-neutral-900"
      data-focus-region="conditions"
      data-testid="right-panel"
      tabIndex={0}
      onFocus={() => setFocusRegion('conditions')}
    >
      {/* Header with tabs */}
      <div className="border-b border-neutral-700">
        {reviewMode ? (
          <div className="flex">
            <button
              className={`flex-1 px-3 py-2 text-sm font-medium transition-colors ${
                activeTab === 'conditions'
                  ? 'border-b-2 border-blue-500 text-neutral-200'
                  : 'text-neutral-500 hover:text-neutral-300'
              }`}
              onClick={() => setActiveTab('conditions')}
            >
              Conditions
            </button>
            <button
              className={`flex-1 px-3 py-2 text-sm font-medium transition-colors ${
                activeTab === 'review'
                  ? 'border-b-2 border-green-500 text-neutral-200'
                  : 'text-neutral-500 hover:text-neutral-300'
              }`}
              onClick={() => setActiveTab('review')}
            >
              Review
            </button>
          </div>
        ) : (
          <div className="flex items-center justify-between px-3 py-2">
            <h3 className="text-sm font-medium text-neutral-200">Conditions</h3>
          </div>
        )}
      </div>

      {/* Content */}
      {activeTab === 'conditions' || !reviewMode ? (
        <ConditionPanel projectId={projectId} />
      ) : (
        <ReviewMeasurementPanel projectId={projectId} pageId={pageId} />
      )}
    </div>
  );
}
