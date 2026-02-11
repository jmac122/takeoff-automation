/**
 * API client functions for document revision and plan overlay operations.
 */

import { apiClient } from './client';

// ============================================================================
// Types
// ============================================================================

export interface LinkRevisionRequest {
  supersedes_document_id: string;
  revision_number?: string | null;
  revision_date?: string | null;
  revision_label?: string | null;
}

export interface RevisionChainItem {
  id: string;
  original_filename: string;
  revision_number: string | null;
  revision_date: string | null;
  revision_label: string | null;
  is_latest_revision: boolean;
  page_count: number | null;
  created_at: string;
}

export interface RevisionChainResponse {
  chain: RevisionChainItem[];
  current_document_id: string;
}

export interface PageComparisonRequest {
  old_document_id: string;
  new_document_id: string;
  page_number: number;
}

export interface PageComparisonResponse {
  old_page_id: string | null;
  new_page_id: string | null;
  old_image_url: string | null;
  new_image_url: string | null;
  page_number: number;
  has_both: boolean;
}

// ============================================================================
// API Functions
// ============================================================================

export const revisionsApi = {
  /**
   * Link a document as a revision of another.
   */
  linkRevision: async (
    documentId: string,
    data: LinkRevisionRequest,
  ) => {
    const response = await apiClient.put(`/documents/${documentId}/revision`, data);
    return response.data;
  },

  /**
   * Get the full revision chain for a document.
   */
  getRevisionChain: async (documentId: string): Promise<RevisionChainResponse> => {
    const response = await apiClient.get<RevisionChainResponse>(
      `/documents/${documentId}/revisions`,
    );
    return response.data;
  },

  /**
   * Compare a specific page between two document revisions.
   */
  comparePages: async (
    data: PageComparisonRequest,
  ): Promise<PageComparisonResponse> => {
    const response = await apiClient.post<PageComparisonResponse>(
      '/documents/compare-pages',
      data,
    );
    return response.data;
  },
};

export default revisionsApi;
