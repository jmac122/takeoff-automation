import { apiClient } from './client';
import type {
  AutoCountDetection,
  AutoCountSession,
  AutoCountSessionDetail,
  AutoCountStartResponse,
  BBox,
} from '@/types';

// ---------------------------------------------------------------------------
// Request types
// ---------------------------------------------------------------------------

export interface AutoCountCreateRequest {
  condition_id: string;
  template_bbox: BBox;
  confidence_threshold?: number;
  scale_tolerance?: number;
  rotation_tolerance?: number;
  detection_method?: 'template' | 'llm' | 'hybrid';
  provider?: string | null;
}

export interface BulkConfirmRequest {
  threshold: number;
}

// ---------------------------------------------------------------------------
// Start auto count
// ---------------------------------------------------------------------------

export async function startAutoCount(
  pageId: string,
  data: AutoCountCreateRequest
): Promise<AutoCountStartResponse> {
  const response = await apiClient.post<AutoCountStartResponse>(
    `/pages/${pageId}/auto-count`,
    data
  );
  return response.data;
}

// ---------------------------------------------------------------------------
// Session endpoints
// ---------------------------------------------------------------------------

export async function getAutoCountSession(
  sessionId: string
): Promise<AutoCountSessionDetail> {
  const response = await apiClient.get<AutoCountSessionDetail>(
    `/auto-count-sessions/${sessionId}`
  );
  return response.data;
}

export async function listPageAutoCountSessions(
  pageId: string,
  conditionId?: string
): Promise<AutoCountSession[]> {
  const response = await apiClient.get<AutoCountSession[]>(
    `/pages/${pageId}/auto-count-sessions`,
    { params: conditionId ? { condition_id: conditionId } : undefined }
  );
  return response.data;
}

// ---------------------------------------------------------------------------
// Detection review
// ---------------------------------------------------------------------------

export async function confirmDetection(
  detectionId: string
): Promise<AutoCountDetection> {
  const response = await apiClient.post<AutoCountDetection>(
    `/auto-count-detections/${detectionId}/confirm`
  );
  return response.data;
}

export async function rejectDetection(
  detectionId: string
): Promise<AutoCountDetection> {
  const response = await apiClient.post<AutoCountDetection>(
    `/auto-count-detections/${detectionId}/reject`
  );
  return response.data;
}

export async function bulkConfirmDetections(
  sessionId: string,
  threshold: number
): Promise<{ confirmed_count: number; threshold: number }> {
  const response = await apiClient.post(
    `/auto-count-sessions/${sessionId}/bulk-confirm`,
    { threshold }
  );
  return response.data;
}

export async function createMeasurementsFromDetections(
  sessionId: string
): Promise<{ measurements_created: number }> {
  const response = await apiClient.post(
    `/auto-count-sessions/${sessionId}/create-measurements`
  );
  return response.data;
}
