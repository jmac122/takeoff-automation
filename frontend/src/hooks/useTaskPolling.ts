/**
 * Unified task polling hook for the async Task API.
 *
 * Polls GET /api/v1/tasks/{taskId} and provides reactive status,
 * progress, callbacks for terminal states, and a cancel helper.
 */

import { useCallback, useEffect, useRef } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';

// ============================================================================
// Types
// ============================================================================

export interface TaskProgress {
  percent: number;
  step: string | null;
}

export interface TaskStatus {
  task_id: string;
  task_type: string | null;
  task_name: string | null;
  status: string;
  progress: TaskProgress;
  result: unknown;
  error: string | null;
  traceback: string | null;
  created_at: string | null;
  started_at: string | null;
  completed_at: string | null;
  project_id: string | null;
}

const TERMINAL_STATUSES = ['SUCCESS', 'FAILURE', 'REVOKED'];

export interface UseTaskPollingOptions {
  onSuccess?: (result: unknown) => void;
  onError?: (error: string | null) => void;
  invalidateKeys?: string[][];
  interval?: number;
}

// ============================================================================
// Hook
// ============================================================================

export function useTaskPolling(
  taskId: string | null,
  options: UseTaskPollingOptions = {},
) {
  const { onSuccess, onError, invalidateKeys, interval = 2000 } = options;
  const queryClient = useQueryClient();

  // Track whether callbacks have fired for this taskId to avoid duplicates
  const firedRef = useRef<string | null>(null);

  // Reset fired ref when taskId changes
  useEffect(() => {
    firedRef.current = null;
  }, [taskId]);

  const isTerminal = (status: string) => TERMINAL_STATUSES.includes(status);

  const query = useQuery<TaskStatus>({
    queryKey: ['task', taskId],
    queryFn: async () => {
      const res = await apiClient.get<TaskStatus>(`/tasks/${taskId}`);
      return res.data;
    },
    enabled: !!taskId,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data && isTerminal(data.status)) return false;
      return interval;
    },
  });

  const taskStatus = query.data ?? null;

  // Fire callbacks on terminal state (once per taskId)
  useEffect(() => {
    if (!taskStatus || !taskId) return;
    if (firedRef.current === taskId) return;
    if (!isTerminal(taskStatus.status)) return;

    firedRef.current = taskId;

    if (taskStatus.status === 'SUCCESS') {
      onSuccess?.(taskStatus.result);
      if (invalidateKeys) {
        for (const key of invalidateKeys) {
          queryClient.invalidateQueries({ queryKey: key });
        }
      }
    } else {
      onError?.(taskStatus.error);
    }
  }, [taskStatus, taskId, onSuccess, onError, invalidateKeys, queryClient]);

  // Cancel mutation
  const cancelMutation = useMutation({
    mutationFn: async () => {
      if (!taskId) return;
      await apiClient.post(`/tasks/${taskId}/cancel`);
    },
  });

  const cancel = useCallback(() => cancelMutation.mutateAsync(), [cancelMutation]);

  return {
    taskStatus,
    isPolling: !!taskId && !!taskStatus && !isTerminal(taskStatus.status),
    progress: taskStatus?.progress ?? { percent: 0, step: null },
    isSuccess: taskStatus?.status === 'SUCCESS',
    isError: taskStatus?.status === 'FAILURE' || taskStatus?.status === 'REVOKED',
    cancel,
  };
}
