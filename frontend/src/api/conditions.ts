import { apiClient } from './client';
import type { Condition } from '@/types';

export interface ConditionCreateRequest {
  name: string;
  description?: string | null;
  scope?: string;
  category?: string | null;
  measurement_type: "linear" | "area" | "volume" | "count";
  color?: string;
  line_width?: number;
  fill_opacity?: number;
  unit?: string;
  depth?: number | null;
  thickness?: number | null;
  sort_order?: number;
  extra_metadata?: Record<string, any> | null;
}

export interface ConditionUpdateRequest {
  name?: string;
  description?: string | null;
  scope?: string;
  category?: string | null;
  measurement_type?: "linear" | "area" | "volume" | "count";
  color?: string;
  line_width?: number;
  fill_opacity?: number;
  unit?: string;
  depth?: number | null;
  thickness?: number | null;
  sort_order?: number;
  extra_metadata?: Record<string, any> | null;
}

export interface ConditionListResponse {
  conditions: Condition[];
  total: number;
}

/**
 * List conditions for a project
 */
export async function listProjectConditions(projectId: string): Promise<ConditionListResponse> {
  const response = await apiClient.get<ConditionListResponse>(`/projects/${projectId}/conditions`);
  return response.data;
}

/**
 * Create a new condition
 */
export async function createCondition(
  projectId: string,
  data: ConditionCreateRequest
): Promise<Condition> {
  const response = await apiClient.post<Condition>(`/projects/${projectId}/conditions`, data);
  return response.data;
}

/**
 * Get condition details
 */
export async function getCondition(conditionId: string): Promise<Condition> {
  const response = await apiClient.get<Condition>(`/conditions/${conditionId}`);
  return response.data;
}

/**
 * Update a condition
 */
export async function updateCondition(
  conditionId: string,
  data: ConditionUpdateRequest
): Promise<Condition> {
  const response = await apiClient.put<Condition>(`/conditions/${conditionId}`, data);
  return response.data;
}

/**
 * Delete a condition
 */
export async function deleteCondition(conditionId: string): Promise<void> {
  await apiClient.delete(`/conditions/${conditionId}`);
}
