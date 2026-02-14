import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  approveMeasurement,
  rejectMeasurement,
  modifyMeasurement,
  autoAcceptMeasurements,
  getNextUnreviewed,
} from '@/api/review';
import { useWorkspaceStore } from '@/stores/workspaceStore';
import type { JsonObject } from '@/types';

export function useReviewActions(
  pageId: string | undefined,
  projectId: string | undefined,
) {
  const queryClient = useQueryClient();
  const reviewAutoAdvance = useWorkspaceStore((s) => s.reviewAutoAdvance);
  const advanceReview = useWorkspaceStore((s) => s.advanceReview);

  const invalidateAll = () => {
    if (pageId) {
      queryClient.invalidateQueries({ queryKey: ['measurements', pageId] });
    }
    if (projectId) {
      queryClient.invalidateQueries({ queryKey: ['conditions', projectId] });
      queryClient.invalidateQueries({ queryKey: ['review-stats', projectId] });
    }
  };

  const autoAdvance = async () => {
    if (!reviewAutoAdvance || !pageId) return;
    try {
      const result = await getNextUnreviewed(pageId);
      advanceReview(result.measurement?.id ?? null);
    } catch {
      // Silently fail on auto-advance
    }
  };

  const approveMutation = useMutation({
    mutationFn: ({ measurementId, reviewer, notes }: {
      measurementId: string;
      reviewer: string;
      notes?: string | null;
    }) => approveMeasurement(measurementId, reviewer, notes),
    onSuccess: () => {
      invalidateAll();
      autoAdvance();
    },
  });

  const rejectMutation = useMutation({
    mutationFn: ({ measurementId, reviewer, reason }: {
      measurementId: string;
      reviewer: string;
      reason: string;
    }) => rejectMeasurement(measurementId, reviewer, reason),
    onSuccess: () => {
      invalidateAll();
      autoAdvance();
    },
  });

  const modifyMutation = useMutation({
    mutationFn: ({ measurementId, reviewer, geometryData, notes }: {
      measurementId: string;
      reviewer: string;
      geometryData: JsonObject;
      notes?: string | null;
    }) => modifyMeasurement(measurementId, reviewer, geometryData, notes),
    onSuccess: () => {
      invalidateAll();
      autoAdvance();
    },
  });

  const autoAcceptMutation = useMutation({
    mutationFn: ({ threshold, reviewer }: {
      threshold?: number;
      reviewer?: string | null;
    }) => {
      if (!projectId) throw new Error('Project ID required');
      return autoAcceptMeasurements(projectId, threshold, reviewer);
    },
    onSuccess: () => {
      invalidateAll();
    },
  });

  return {
    approve: approveMutation.mutate,
    reject: rejectMutation.mutate,
    modify: modifyMutation.mutate,
    autoAccept: autoAcceptMutation.mutate,
    approveAsync: approveMutation.mutateAsync,
    rejectAsync: rejectMutation.mutateAsync,
    modifyAsync: modifyMutation.mutateAsync,
    autoAcceptAsync: autoAcceptMutation.mutateAsync,
    isApproving: approveMutation.isPending,
    isRejecting: rejectMutation.isPending,
    isModifying: modifyMutation.isPending,
    isAutoAccepting: autoAcceptMutation.isPending,
  };
}
