import { apiClient } from './client';
import type {
  JsonObject,
  ReviewActionResponse,
  AutoAcceptResponse,
  ReviewStatistics,
  NextUnreviewedResponse,
  MeasurementHistoryEntry,
} from '@/types';

/**
 * Approve a measurement
 */
export async function approveMeasurement(
  measurementId: string,
  reviewer: string,
  notes?: string | null,
): Promise<ReviewActionResponse> {
  const response = await apiClient.post<ReviewActionResponse>(
    `/measurements/${measurementId}/approve`,
    { reviewer, notes },
  );
  return response.data;
}

/**
 * Reject a measurement
 */
export async function rejectMeasurement(
  measurementId: string,
  reviewer: string,
  reason: string,
): Promise<ReviewActionResponse> {
  const response = await apiClient.post<ReviewActionResponse>(
    `/measurements/${measurementId}/reject`,
    { reviewer, reason },
  );
  return response.data;
}

/**
 * Modify a measurement's geometry during review
 */
export async function modifyMeasurement(
  measurementId: string,
  reviewer: string,
  geometryData: JsonObject,
  notes?: string | null,
): Promise<ReviewActionResponse> {
  const response = await apiClient.post<ReviewActionResponse>(
    `/measurements/${measurementId}/modify`,
    { reviewer, geometry_data: geometryData, notes },
  );
  return response.data;
}

/**
 * Auto-accept high-confidence AI measurements for a project
 */
export async function autoAcceptMeasurements(
  projectId: string,
  threshold: number = 0.9,
  reviewer?: string | null,
): Promise<AutoAcceptResponse> {
  const response = await apiClient.post<AutoAcceptResponse>(
    `/projects/${projectId}/measurements/auto-accept`,
    { threshold, reviewer },
  );
  return response.data;
}

/**
 * Get review statistics for a project
 */
export async function getReviewStats(projectId: string): Promise<ReviewStatistics> {
  const response = await apiClient.get<ReviewStatistics>(
    `/projects/${projectId}/review-stats`,
  );
  return response.data;
}

/**
 * Get the next unreviewed measurement on a page
 */
export async function getNextUnreviewed(
  pageId: string,
  afterId?: string | null,
): Promise<NextUnreviewedResponse> {
  const params = afterId ? { after: afterId } : {};
  const response = await apiClient.get<NextUnreviewedResponse>(
    `/pages/${pageId}/measurements/next-unreviewed`,
    { params },
  );
  return response.data;
}

/**
 * Get the audit history for a measurement
 */
export async function getMeasurementHistory(
  measurementId: string,
): Promise<MeasurementHistoryEntry[]> {
  const response = await apiClient.get<MeasurementHistoryEntry[]>(
    `/measurements/${measurementId}/history`,
  );
  return response.data;
}
