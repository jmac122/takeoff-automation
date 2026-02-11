/**
 * API client functions for export operations.
 */

import { apiClient } from './client';

// ============================================================================
// Types
// ============================================================================

export type ExportFormat = 'excel' | 'csv' | 'pdf' | 'ost';

export interface ExportOptions {
  include_unverified?: boolean;
  include_costs?: boolean;
}

export interface StartExportRequest {
  format: ExportFormat;
  options?: ExportOptions | null;
}

export interface StartExportResponse {
  task_id: string;
  export_id: string;
  message: string;
}

export interface ExportJob {
  id: string;
  project_id: string;
  format: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  file_key: string | null;
  file_size: number | null;
  error_message: string | null;
  download_url: string | null;
  options: ExportOptions | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ExportListResponse {
  exports: ExportJob[];
  total: number;
}

// ============================================================================
// API Functions
// ============================================================================

export const exportsApi = {
  /**
   * Start an export job for a project.
   * Returns a task_id for polling and an export_id for fetching results.
   */
  startExport: async (
    projectId: string,
    format: ExportFormat,
    options?: ExportOptions,
  ): Promise<StartExportResponse> => {
    const response = await apiClient.post<StartExportResponse>(
      `/projects/${projectId}/export`,
      { format, options: options ?? null },
    );
    return response.data;
  },

  /**
   * Get export job status and download URL.
   */
  getExport: async (exportId: string): Promise<ExportJob> => {
    const response = await apiClient.get<ExportJob>(`/exports/${exportId}`);
    return response.data;
  },

  /**
   * List all exports for a project, newest first.
   */
  listExports: async (projectId: string): Promise<ExportListResponse> => {
    const response = await apiClient.get<ExportListResponse>(
      `/projects/${projectId}/exports`,
    );
    return response.data;
  },

  /**
   * Delete an export job and its stored file.
   */
  deleteExport: async (exportId: string): Promise<void> => {
    await apiClient.delete(`/exports/${exportId}`);
  },
};

export default exportsApi;
