import { useQuery } from '@tanstack/react-query';
import { getReviewStats } from '@/api/review';
import { useWorkspaceStore } from '@/stores/workspaceStore';

export function useReviewStats(projectId: string | undefined) {
  const reviewMode = useWorkspaceStore((s) => s.reviewMode);

  return useQuery({
    queryKey: ['review-stats', projectId],
    queryFn: () => {
      if (!projectId) throw new Error('Project ID required');
      return getReviewStats(projectId);
    },
    enabled: !!projectId && reviewMode,
    refetchInterval: 10_000,
  });
}
