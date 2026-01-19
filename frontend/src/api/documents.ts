/**
 * API client functions for document operations.
 */

import { apiClient } from "./client";

export interface Document {
  id: string;
  project_id: string;
  filename: string;
  original_filename: string;
  file_type: string;
  file_size: number;
  status: string;
  page_count: number | null;
  processing_error: string | null;
  created_at: string;
  updated_at: string;
  pages?: PageSummary[];
}

export interface PageSummary {
  id: string;
  page_number: number;
  classification: string | null;
  scale_calibrated: boolean;
  thumbnail_url: string | null;
}

export interface DocumentStatus {
  status: string;
  page_count: number | null;
  error: string | null;
}

/**
 * Upload a document to a project.
 */
export async function uploadDocument(
  projectId: string,
  file: File,
  onProgress?: (progress: number) => void
): Promise<Document> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await apiClient.post<Document>(
    `/projects/${projectId}/documents`,
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          const progress = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          onProgress(progress);
        }
      },
    }
  );

  return response.data;
}

/**
 * Get document details.
 */
export async function getDocument(documentId: string): Promise<Document> {
  const response = await apiClient.get<Document>(`/documents/${documentId}`);
  return response.data;
}

/**
 * Get document processing status.
 */
export async function getDocumentStatus(
  documentId: string
): Promise<DocumentStatus> {
  const response = await apiClient.get<DocumentStatus>(
    `/documents/${documentId}/status`
  );
  return response.data;
}

/**
 * Delete a document.
 */
export async function deleteDocument(documentId: string): Promise<void> {
  await apiClient.delete(`/documents/${documentId}`);
}

/**
 * Poll document status until processing is complete.
 */
export async function pollDocumentStatus(
  documentId: string,
  onStatusUpdate?: (status: DocumentStatus) => void,
  intervalMs: number = 2000,
  maxAttempts: number = 60
): Promise<DocumentStatus> {
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    const status = await getDocumentStatus(documentId);
    
    if (onStatusUpdate) {
      onStatusUpdate(status);
    }

    if (status.status === "ready" || status.status === "error") {
      return status;
    }

    // Wait before next poll
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }

  throw new Error("Document processing timeout");
}
