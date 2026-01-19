import { apiClient } from './client';
import type { Document } from '../types';

export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}

export async function uploadDocument(
  projectId: string,
  file: File,
  onProgress?: (progress: UploadProgress) => void
): Promise<Document> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post<Document>(
    `/projects/${projectId}/documents`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          onProgress({
            loaded: progressEvent.loaded,
            total: progressEvent.total,
            percentage: Math.round((progressEvent.loaded * 100) / progressEvent.total),
          });
        }
      },
    }
  );

  return response.data;
}

export async function getDocument(documentId: string): Promise<Document> {
  const response = await apiClient.get<Document>(`/documents/${documentId}`);
  return response.data;
}

export async function getDocumentStatus(
  documentId: string
): Promise<{ status: string; page_count: number | null; error: string | null }> {
  const response = await apiClient.get(`/documents/${documentId}/status`);
  return response.data;
}

export async function deleteDocument(documentId: string): Promise<void> {
  await apiClient.delete(`/documents/${documentId}`);
}