import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  bulkConfirmDetections,
  confirmDetection,
  createMeasurementsFromDetections,
  getAutoCountSession,
  listPageAutoCountSessions,
  rejectDetection,
  startAutoCount,
} from '@/api/autoCount';
import type { AutoCountCreateRequest } from '@/api/autoCount';

export function useAutoCountSession(sessionId: string | undefined) {
  return useQuery({
    queryKey: ['auto-count-session', sessionId],
    queryFn: () => getAutoCountSession(sessionId as string),
    enabled: !!sessionId,
    refetchInterval: (query) => {
      const data = query.state.data;
      // Poll while processing
      if (data && (data.status === 'pending' || data.status === 'processing')) {
        return 2000;
      }
      return false;
    },
  });
}

export function usePageAutoCountSessions(
  pageId: string | undefined,
  conditionId?: string
) {
  return useQuery({
    queryKey: ['auto-count-sessions', pageId, conditionId],
    queryFn: () => listPageAutoCountSessions(pageId as string, conditionId),
    enabled: !!pageId,
  });
}

export function useStartAutoCount(pageId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: AutoCountCreateRequest) =>
      startAutoCount(pageId as string, data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['auto-count-sessions', pageId],
      });
    },
  });
}

export function useConfirmDetection(sessionId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (detectionId: string) => confirmDetection(detectionId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['auto-count-session', sessionId],
      });
    },
  });
}

export function useRejectDetection(sessionId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (detectionId: string) => rejectDetection(detectionId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['auto-count-session', sessionId],
      });
    },
  });
}

export function useBulkConfirmDetections(sessionId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (threshold: number) =>
      bulkConfirmDetections(sessionId as string, threshold),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['auto-count-session', sessionId],
      });
    },
  });
}

export function useCreateMeasurementsFromDetections(
  sessionId: string | undefined,
  conditionId: string | undefined
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () =>
      createMeasurementsFromDetections(sessionId as string),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['auto-count-session', sessionId],
      });
      queryClient.invalidateQueries({
        queryKey: ['conditions'],
      });
      if (conditionId) {
        queryClient.invalidateQueries({
          queryKey: ['condition', conditionId],
        });
      }
    },
  });
}
