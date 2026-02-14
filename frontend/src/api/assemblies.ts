import { apiClient } from './client';
import type {
  AssemblyComponent,
  AssemblyDetail,
  AssemblyTemplate,
  FormulaValidateResponse,
  ProjectCostSummary,
} from '@/types';

// ---------------------------------------------------------------------------
// Request types
// ---------------------------------------------------------------------------

export interface AssemblyCreateRequest {
  name?: string | null;
  template_id?: string | null;
  description?: string | null;
}

export interface AssemblyUpdateRequest {
  name?: string;
  description?: string | null;
  csi_code?: string | null;
  csi_description?: string | null;
  default_waste_percent?: number;
  overhead_percent?: number;
  profit_percent?: number;
  productivity_rate?: number | null;
  productivity_unit?: string | null;
  crew_size?: number | null;
  notes?: string | null;
}

export interface ComponentCreateRequest {
  name: string;
  description?: string | null;
  component_type?: string;
  quantity_formula?: string;
  unit: string;
  unit_cost?: number;
  waste_percent?: number;
  cost_item_id?: string | null;
  sort_order?: number;
  labor_hours?: number | null;
  labor_rate?: number | null;
  crew_size?: number | null;
  duration_hours?: number | null;
  hourly_rate?: number | null;
  daily_rate?: number | null;
  is_included?: boolean;
  is_optional?: boolean;
  notes?: string | null;
}

export interface ComponentUpdateRequest {
  name?: string;
  description?: string | null;
  component_type?: string;
  quantity_formula?: string;
  unit?: string;
  unit_cost?: number;
  waste_percent?: number;
  cost_item_id?: string | null;
  sort_order?: number;
  labor_hours?: number | null;
  labor_rate?: number | null;
  crew_size?: number | null;
  duration_hours?: number | null;
  hourly_rate?: number | null;
  daily_rate?: number | null;
  is_included?: boolean;
  is_optional?: boolean;
  notes?: string | null;
}

export interface FormulaValidateRequest {
  formula: string;
  test_qty?: number;
  test_depth?: number;
  test_thickness?: number;
  test_perimeter?: number;
  test_count?: number;
}

// ---------------------------------------------------------------------------
// Assembly CRUD
// ---------------------------------------------------------------------------

export async function getConditionAssembly(conditionId: string): Promise<AssemblyDetail | null> {
  const response = await apiClient.get<AssemblyDetail | null>(
    `/conditions/${conditionId}/assembly`
  );
  return response.data;
}

export async function createAssembly(
  conditionId: string,
  data: AssemblyCreateRequest
): Promise<AssemblyDetail> {
  const response = await apiClient.post<AssemblyDetail>(
    `/conditions/${conditionId}/assembly`,
    data
  );
  return response.data;
}

export async function getAssembly(assemblyId: string): Promise<AssemblyDetail> {
  const response = await apiClient.get<AssemblyDetail>(`/assemblies/${assemblyId}`);
  return response.data;
}

export async function updateAssembly(
  assemblyId: string,
  data: AssemblyUpdateRequest
): Promise<AssemblyDetail> {
  const response = await apiClient.put<AssemblyDetail>(`/assemblies/${assemblyId}`, data);
  return response.data;
}

export async function deleteAssembly(assemblyId: string): Promise<void> {
  await apiClient.delete(`/assemblies/${assemblyId}`);
}

export async function calculateAssembly(assemblyId: string): Promise<AssemblyDetail> {
  const response = await apiClient.post<AssemblyDetail>(`/assemblies/${assemblyId}/calculate`);
  return response.data;
}

export async function lockAssembly(
  assemblyId: string,
  lockedBy: string
): Promise<AssemblyDetail> {
  const response = await apiClient.post<AssemblyDetail>(
    `/assemblies/${assemblyId}/lock`,
    null,
    { params: { locked_by: lockedBy } }
  );
  return response.data;
}

export async function unlockAssembly(assemblyId: string): Promise<AssemblyDetail> {
  const response = await apiClient.post<AssemblyDetail>(`/assemblies/${assemblyId}/unlock`);
  return response.data;
}

// ---------------------------------------------------------------------------
// Component CRUD
// ---------------------------------------------------------------------------

export async function addComponent(
  assemblyId: string,
  data: ComponentCreateRequest
): Promise<AssemblyComponent> {
  const response = await apiClient.post<AssemblyComponent>(
    `/assemblies/${assemblyId}/components`,
    data
  );
  return response.data;
}

export async function updateComponent(
  componentId: string,
  data: ComponentUpdateRequest
): Promise<AssemblyComponent> {
  const response = await apiClient.put<AssemblyComponent>(
    `/components/${componentId}`,
    data
  );
  return response.data;
}

export async function deleteComponent(componentId: string): Promise<void> {
  await apiClient.delete(`/components/${componentId}`);
}

export async function reorderComponents(
  assemblyId: string,
  componentIds: string[]
): Promise<void> {
  await apiClient.put(`/assemblies/${assemblyId}/components/reorder`, componentIds);
}

// ---------------------------------------------------------------------------
// Templates
// ---------------------------------------------------------------------------

export async function listAssemblyTemplates(filters?: {
  scope?: string;
  category?: string;
  measurement_type?: string;
}): Promise<AssemblyTemplate[]> {
  const response = await apiClient.get<AssemblyTemplate[]>('/assembly-templates', {
    params: filters,
  });
  return response.data;
}

export async function getAssemblyTemplate(templateId: string): Promise<AssemblyTemplate> {
  const response = await apiClient.get<AssemblyTemplate>(
    `/assembly-templates/${templateId}`
  );
  return response.data;
}

// ---------------------------------------------------------------------------
// Formula utilities
// ---------------------------------------------------------------------------

export async function validateFormula(
  data: FormulaValidateRequest
): Promise<FormulaValidateResponse> {
  const response = await apiClient.post<FormulaValidateResponse>('/formulas/validate', data);
  return response.data;
}

export async function getFormulaPresets(): Promise<Record<string, {
  name: string;
  formula: string;
  description: string;
}>> {
  const response = await apiClient.get('/formulas/presets');
  return response.data;
}

export async function getFormulaHelp(): Promise<Record<string, unknown>> {
  const response = await apiClient.get('/formulas/help');
  return response.data;
}

// ---------------------------------------------------------------------------
// Project cost summary
// ---------------------------------------------------------------------------

export async function getProjectCostSummary(projectId: string): Promise<ProjectCostSummary> {
  const response = await apiClient.get<ProjectCostSummary>(
    `/projects/${projectId}/cost-summary`
  );
  return response.data;
}
