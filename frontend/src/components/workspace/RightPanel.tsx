import { useState, useEffect } from 'react';
import { useWorkspaceStore } from '@/stores/workspaceStore';
import { ConditionPanel } from '@/components/conditions/ConditionPanel';
import { ReviewMeasurementPanel } from '@/components/workspace/ReviewMeasurementPanel';
import { AssemblyPanel } from '@/components/assembly/AssemblyPanel';
import { RevisionChainPanel } from '@/components/document/RevisionChainPanel';
import { LinkRevisionDialog } from '@/components/document/LinkRevisionDialog';

interface RightPanelProps {
  projectId: string;
  pageId?: string;
  documentId?: string;
  onCompare?: (oldDocId: string, newDocId: string) => void;
}

type RightPanelTab = 'conditions' | 'cost' | 'review' | 'revisions';

export function RightPanel({ projectId, pageId, documentId, onCompare }: RightPanelProps) {
  const setFocusRegion = useWorkspaceStore((s) => s.setFocusRegion);
  const reviewMode = useWorkspaceStore((s) => s.reviewMode);
  const activeConditionId = useWorkspaceStore((s) => s.activeConditionId);
  const [activeTab, setActiveTab] = useState<RightPanelTab>('conditions');
  const [linkDialogOpen, setLinkDialogOpen] = useState(false);

  // Auto-switch to review tab when review mode activates
  useEffect(() => {
    if (reviewMode) {
      setActiveTab('review');
    }
  }, [reviewMode]);

  const showTabs = reviewMode || activeConditionId || documentId;

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
        {showTabs ? (
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
            {activeConditionId && (
              <button
                className={`flex-1 px-3 py-2 text-sm font-medium transition-colors ${
                  activeTab === 'cost'
                    ? 'border-b-2 border-amber-500 text-neutral-200'
                    : 'text-neutral-500 hover:text-neutral-300'
                }`}
                onClick={() => setActiveTab('cost')}
              >
                Cost
              </button>
            )}
            {reviewMode && (
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
            )}
            {documentId && (
              <button
                className={`flex-1 px-3 py-2 text-sm font-medium transition-colors ${
                  activeTab === 'revisions'
                    ? 'border-b-2 border-purple-500 text-neutral-200'
                    : 'text-neutral-500 hover:text-neutral-300'
                }`}
                onClick={() => setActiveTab('revisions')}
              >
                Revisions
              </button>
            )}
          </div>
        ) : (
          <div className="flex items-center justify-between px-3 py-2">
            <h3 className="text-sm font-medium text-neutral-200">Conditions</h3>
          </div>
        )}
      </div>

      {/* Content */}
      {activeTab === 'cost' && activeConditionId ? (
        <AssemblyPanel conditionId={activeConditionId} projectId={projectId} />
      ) : activeTab === 'review' && reviewMode ? (
        <ReviewMeasurementPanel projectId={projectId} pageId={pageId} />
      ) : activeTab === 'revisions' && documentId ? (
        <div className="flex-1 overflow-y-auto">
          <RevisionChainPanel
            documentId={documentId}
            onCompare={onCompare}
            onLinkRevision={() => setLinkDialogOpen(true)}
          />
          <LinkRevisionDialog
            open={linkDialogOpen}
            onOpenChange={setLinkDialogOpen}
            documentId={documentId}
            projectId={projectId}
          />
        </div>
      ) : (
        <ConditionPanel projectId={projectId} />
      )}
    </div>
  );
}
