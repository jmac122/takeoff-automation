/**
 * Hook for managing export operations with task polling and download handling.
 */

import { useState, useCallback } from 'react';
import { exportsApi, type ExportFormat, type ExportOptions } from '@/api/exports';
import { useTaskPolling } from './useTaskPolling';

export interface UseExportOptions {
  projectId: string | null;
  onSuccess?: () => void;
  onError?: (error: string) => void;
}

export function useExport({ projectId, onSuccess, onError }: UseExportOptions) {
  const [taskId, setTaskId] = useState<string | null>(null);
  const [exportId, setExportId] = useState<string | null>(null);
  const [isStarting, setIsStarting] = useState(false);

  const handleSuccess = useCallback(async () => {
    if (!exportId) return;
    try {
      const exportJob = await exportsApi.getExport(exportId);
      if (exportJob.download_url) {
        // Trigger browser download
        const link = document.createElement('a');
        link.href = exportJob.download_url;
        link.download = '';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }
      onSuccess?.();
    } catch {
      onError?.('Failed to get download URL');
    } finally {
      setTaskId(null);
      setExportId(null);
    }
  }, [exportId, onSuccess, onError]);

  const handleError = useCallback((error: string | null) => {
    onError?.(error ?? 'Export failed');
    setTaskId(null);
    setExportId(null);
  }, [onError]);

  const { isPolling, progress } = useTaskPolling(taskId, {
    onSuccess: handleSuccess,
    onError: handleError,
    interval: 2000,
  });

  const startExport = useCallback(async (
    format: ExportFormat,
    options?: ExportOptions,
  ) => {
    if (!projectId) return;
    setIsStarting(true);
    try {
      const response = await exportsApi.startExport(projectId, format, options);
      setTaskId(response.task_id);
      setExportId(response.export_id);
    } catch {
      onError?.('Failed to start export');
    } finally {
      setIsStarting(false);
    }
  }, [projectId, onError]);

  return {
    startExport,
    isExporting: isStarting || isPolling,
    progress,
  };
}
