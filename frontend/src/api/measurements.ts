import { apiClient } from './client';
import type { JsonObject, Measurement } from '@/types';

export interface MeasurementCreateRequest {
  page_id: string;
  geometry_type: string;
  geometry_data: JsonObject;
  notes?: string | null;
}

export interface MeasurementUpdateRequest {
  geometry_data?: JsonObject;
  notes?: string | null;
}

export interface MeasurementListResponse {
  measurements: Measurement[];
  total: number;
}

/**
 * List measurements for a condition
 */
export async function listConditionMeasurements(conditionId: string): Promise<MeasurementListResponse> {
  const response = await apiClient.get<MeasurementListResponse>(`/conditions/${conditionId}/measurements`);
  return response.data;
}

/**
 * List measurements for a page
 */
export async function listPageMeasurements(pageId: string): Promise<MeasurementListResponse> {
  const response = await apiClient.get<MeasurementListResponse>(`/pages/${pageId}/measurements`);
  return response.data;
}

/**
 * Create a new measurement
 */
export async function createMeasurement(
  conditionId: string,
  data: MeasurementCreateRequest
): Promise<Measurement> {
  const response = await apiClient.post<Measurement>(`/conditions/${conditionId}/measurements`, data);
  return response.data;
}

/**
 * Get measurement details
 */
export async function getMeasurement(measurementId: string): Promise<Measurement> {
  const response = await apiClient.get<Measurement>(`/measurements/${measurementId}`);
  return response.data;
}

/**
 * Update a measurement
 */
export async function updateMeasurement(
  measurementId: string,
  data: MeasurementUpdateRequest
): Promise<Measurement> {
  const response = await apiClient.put<Measurement>(`/measurements/${measurementId}`, data);
  return response.data;
}

/**
 * Delete a measurement
 */
export async function deleteMeasurement(measurementId: string): Promise<void> {
  await apiClient.delete(`/measurements/${measurementId}`);
}

/**
 * Recalculate a measurement (after scale change)
 */
export async function recalculateMeasurement(measurementId: string): Promise<Measurement> {
  const response = await apiClient.post<Measurement>(`/measurements/${measurementId}/recalculate`);
  return response.data;
}

/**
 * Recalculate all measurements on a page
 */
export async function recalculatePageMeasurements(pageId: string): Promise<{status: string; recalculated_count: number}> {
  const response = await apiClient.post<{status: string; recalculated_count: number}>(`/pages/${pageId}/recalculate-all`);
  return response.data;
}
