/**
 * useAiAssist — manages Batch AI Inline workflow.
 *
 * Triggers an autonomous AI takeoff for the current sheet via the
 * existing Celery pipeline, tracks progress with useTaskPolling,
 * and invalidates the measurements cache on completion.
 */

import { useCallback } from 'react';
import { useWorkspaceStore } from '@/stores/workspaceStore';
import { useTaskPolling } from '@/hooks/useTaskPolling';
import { takeoffApi } from '@/api/takeoff';

export function useAiAssist(projectId: string | null, pageId: string | null) {
  const batchAiTaskId = useWorkspaceStore((s) => s.batchAiTaskId);
  const setBatchAiTaskId = useWorkspaceStore((s) => s.setBatchAiTaskId);
  const clearBatchAiTaskId = useWorkspaceStore((s) => s.clearBatchAiTaskId);

  const { isPolling, progress, cancel } = useTaskPolling(batchAiTaskId, {
    onSuccess: () => {
      clearBatchAiTaskId();
    },
    onError: () => {
      clearBatchAiTaskId();
    },
    invalidateKeys: pageId ? [['measurements', pageId]] : undefined,
    interval: 2000,
  });

  const runBatchAi = useCallback(async () => {
    if (!projectId || !pageId) return;
    if (batchAiTaskId) return; // Already running

    try {
      const response = await takeoffApi.generateAutonomousTakeoff(
        pageId,
        projectId,
      );
      setBatchAiTaskId(response.task_id);
    } catch {
      // Fail silently — user can retry
    }
  }, [projectId, pageId, batchAiTaskId, setBatchAiTaskId]);

  return {
    runBatchAi,
    isRunning: isPolling,
    progress,
    cancel,
  };
}
