import { apiClient } from './client';

// ============================================================================
// Types
// ============================================================================

export interface SheetInfo {
  id: string;
  document_id: string;
  page_number: number;
  sheet_number: string | null;
  title: string | null;
  display_name: string | null;
  display_order: number | null;
  group_name: string | null;
  discipline: string | null;
  page_type: string | null;
  classification: string | null;
  classification_confidence: number | null;
  scale_text: string | null;
  scale_value: number | null;
  scale_calibrated: boolean;
  scale_detection_method: string | null;
  measurement_count: number;
  thumbnail_url: string | null;
  image_url: string | null;
  width: number;
  height: number;
  is_relevant: boolean;
}

export interface SheetGroup {
  group_name: string;
  sheets: SheetInfo[];
}

export interface SheetsResponse {
  groups: SheetGroup[];
  total: number;
}

export interface PageDisplayUpdate {
  display_name?: string | null;
  display_order?: number | null;
  group_name?: string | null;
}

export interface PageRelevanceUpdate {
  is_relevant: boolean;
}

// ============================================================================
// API Calls
// ============================================================================

export async function getProjectSheets(projectId: string): Promise<SheetsResponse> {
  const response = await apiClient.get(`/projects/${projectId}/sheets`);
  return response.data;
}

export async function updatePageDisplay(
  pageId: string,
  data: PageDisplayUpdate,
): Promise<void> {
  await apiClient.put(`/pages/${pageId}/display`, data);
}

export async function updatePageRelevance(
  pageId: string,
  data: PageRelevanceUpdate,
): Promise<void> {
  await apiClient.put(`/pages/${pageId}/relevance`, data);
}

export async function batchUpdateScale(
  pageIds: string[],
  scaleValue: number,
  scaleText?: string,
  scaleUnit?: string,
): Promise<void> {
  await apiClient.post('/pages/batch-scale', {
    page_ids: pageIds,
    scale_value: scaleValue,
    scale_text: scaleText,
    scale_unit: scaleUnit || 'foot',
  });
}
