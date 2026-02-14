import { useEffect, useCallback } from 'react';
import { useWorkspaceStore } from '@/stores/workspaceStore';
import { useFocusContext } from '@/contexts/FocusContext';
import { getNextUnreviewed } from '@/api/review';

interface UseReviewKeyboardShortcutsOptions {
  pageId: string | undefined;
  onApprove: () => void;
  onReject: () => void;
  onEdit: () => void;
}

export function useReviewKeyboardShortcuts({
  pageId,
  onApprove,
  onReject,
  onEdit,
}: UseReviewKeyboardShortcutsOptions) {
  const reviewMode = useWorkspaceStore((s) => s.reviewMode);
  const reviewCurrentId = useWorkspaceStore((s) => s.reviewCurrentId);
  const setReviewMode = useWorkspaceStore((s) => s.setReviewMode);
  const advanceReview = useWorkspaceStore((s) => s.advanceReview);
  const { shouldFireShortcut } = useFocusContext();

  const handleSkipForward = useCallback(async () => {
    if (!pageId) return;
    try {
      const result = await getNextUnreviewed(pageId, reviewCurrentId);
      advanceReview(result.measurement?.id ?? null);
    } catch {
      // Silently fail
    }
  }, [pageId, reviewCurrentId, advanceReview]);

  useEffect(() => {
    if (!reviewMode) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (!shouldFireShortcut(e)) return;

      switch (e.key.toLowerCase()) {
        case 'a':
          e.preventDefault();
          if (reviewCurrentId) onApprove();
          break;
        case 'r':
          e.preventDefault();
          if (reviewCurrentId) onReject();
          break;
        case 's':
        case 'n':
          e.preventDefault();
          handleSkipForward();
          break;
        case 'arrowright':
          e.preventDefault();
          handleSkipForward();
          break;
        case 'e':
          e.preventDefault();
          if (reviewCurrentId) onEdit();
          break;
        case 'escape':
          e.preventDefault();
          setReviewMode(false);
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [
    reviewMode,
    reviewCurrentId,
    shouldFireShortcut,
    onApprove,
    onReject,
    onEdit,
    handleSkipForward,
    setReviewMode,
  ]);
}
