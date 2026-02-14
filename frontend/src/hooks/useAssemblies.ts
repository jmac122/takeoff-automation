import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  addComponent,
  calculateAssembly,
  createAssembly,
  deleteAssembly,
  deleteComponent,
  getConditionAssembly,
  getProjectCostSummary,
  listAssemblyTemplates,
  lockAssembly,
  reorderComponents,
  unlockAssembly,
  updateAssembly,
  updateComponent,
} from '@/api/assemblies';
import type {
  AssemblyCreateRequest,
  AssemblyUpdateRequest,
  ComponentCreateRequest,
  ComponentUpdateRequest,
} from '@/api/assemblies';

export function useConditionAssembly(conditionId: string | undefined) {
  return useQuery({
    queryKey: ['assembly', conditionId],
    queryFn: () => getConditionAssembly(conditionId as string),
    enabled: !!conditionId,
  });
}

export function useCreateAssembly(conditionId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: AssemblyCreateRequest) =>
      createAssembly(conditionId as string, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assembly', conditionId] });
    },
  });
}

export function useUpdateAssembly(conditionId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      assemblyId,
      data,
    }: {
      assemblyId: string;
      data: AssemblyUpdateRequest;
    }) => updateAssembly(assemblyId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assembly', conditionId] });
    },
  });
}

export function useDeleteAssembly(conditionId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (assemblyId: string) => deleteAssembly(assemblyId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assembly', conditionId] });
    },
  });
}

export function useCalculateAssembly(
  conditionId: string | undefined,
  projectId: string | undefined
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (assemblyId: string) => calculateAssembly(assemblyId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assembly', conditionId] });
      queryClient.invalidateQueries({ queryKey: ['project-cost-summary', projectId] });
    },
  });
}

export function useLockAssembly(conditionId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ assemblyId, lockedBy }: { assemblyId: string; lockedBy: string }) =>
      lockAssembly(assemblyId, lockedBy),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assembly', conditionId] });
    },
  });
}

export function useUnlockAssembly(conditionId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (assemblyId: string) => unlockAssembly(assemblyId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assembly', conditionId] });
    },
  });
}

// ---------------------------------------------------------------------------
// Component mutations
// ---------------------------------------------------------------------------

export function useAddComponent(conditionId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      assemblyId,
      data,
    }: {
      assemblyId: string;
      data: ComponentCreateRequest;
    }) => addComponent(assemblyId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assembly', conditionId] });
    },
  });
}

export function useUpdateComponent(conditionId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      componentId,
      data,
    }: {
      componentId: string;
      data: ComponentUpdateRequest;
    }) => updateComponent(componentId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assembly', conditionId] });
    },
  });
}

export function useDeleteComponent(conditionId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (componentId: string) => deleteComponent(componentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assembly', conditionId] });
    },
  });
}

export function useReorderComponents(conditionId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      assemblyId,
      componentIds,
    }: {
      assemblyId: string;
      componentIds: string[];
    }) => reorderComponents(assemblyId, componentIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assembly', conditionId] });
    },
  });
}

// ---------------------------------------------------------------------------
// Templates & project cost
// ---------------------------------------------------------------------------

export function useAssemblyTemplates(filters?: {
  scope?: string;
  category?: string;
  measurement_type?: string;
}) {
  return useQuery({
    queryKey: ['assembly-templates', filters?.scope, filters?.category, filters?.measurement_type],
    queryFn: () => listAssemblyTemplates(filters),
  });
}

export function useProjectCostSummary(projectId: string | undefined) {
  return useQuery({
    queryKey: ['project-cost-summary', projectId],
    queryFn: () => getProjectCostSummary(projectId as string),
    enabled: !!projectId,
  });
}
