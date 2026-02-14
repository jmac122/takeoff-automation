/**
 * AutoTab hook — triggers AI prediction of the next measurement point
 * after the user completes a measurement, and provides accept/dismiss.
 *
 * Silent failure: errors are swallowed and never shown to the user.
 */

import { useCallback, useRef } from 'react';
import { useWorkspaceStore } from '@/stores/workspaceStore';
import { takeoffApi } from '@/api/takeoff';
import { AUTOTAB_TIMEOUT_MS } from '@/lib/constants';

export function useAutoTab(pageId: string | null, conditionId: string | null) {
  const abortRef = useRef<AbortController | null>(null);

  const autoTabEnabled = useWorkspaceStore((s) => s.autoTabEnabled);
  const pendingPrediction = useWorkspaceStore((s) => s.pendingPrediction);
  const ghostPrediction = useWorkspaceStore((s) => s.ghostPrediction);
  const setPendingPrediction = useWorkspaceStore((s) => s.setPendingPrediction);
  const setGhostPrediction = useWorkspaceStore((s) => s.setGhostPrediction);
  const clearGhostPrediction = useWorkspaceStore((s) => s.clearGhostPrediction);

  const triggerPrediction = useCallback(
    async (lastGeometryType: string, lastGeometryData: Record<string, unknown>) => {
      if (!autoTabEnabled || !pageId || !conditionId) return;

      // Cancel any in-flight prediction
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      setPendingPrediction(true);
      clearGhostPrediction();

      try {
        // Race against timeout
        const result = await Promise.race([
          takeoffApi.predictNextPoint(pageId, {
            condition_id: conditionId,
            last_geometry_type: lastGeometryType,
            last_geometry_data: lastGeometryData,
          }),
          new Promise<never>((_, reject) => {
            const timer = setTimeout(
              () => reject(new Error('AutoTab timeout')),
              AUTOTAB_TIMEOUT_MS,
            );
            controller.signal.addEventListener('abort', () => {
              clearTimeout(timer);
              reject(new Error('AutoTab aborted'));
            });
          }),
        ]);

        // Check if this request was superseded
        if (controller.signal.aborted) return;

        if (result.prediction) {
          setGhostPrediction(result.prediction);
        }
      } catch {
        // Silent failure — never block drawing
      } finally {
        if (!controller.signal.aborted) {
          setPendingPrediction(false);
        }
      }
    },
    [autoTabEnabled, pageId, conditionId, setPendingPrediction, setGhostPrediction, clearGhostPrediction],
  );

  const acceptPrediction = useCallback(() => {
    const prediction = useWorkspaceStore.getState().ghostPrediction;
    if (!prediction) return null;
    clearGhostPrediction();
    return prediction;
  }, [clearGhostPrediction]);

  const dismissPrediction = useCallback(() => {
    abortRef.current?.abort();
    clearGhostPrediction();
    setPendingPrediction(false);
  }, [clearGhostPrediction, setPendingPrediction]);

  return {
    triggerPrediction,
    isPredicting: pendingPrediction,
    ghostPrediction,
    acceptPrediction,
    dismissPrediction,
  };
}
