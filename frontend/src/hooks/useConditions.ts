import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  createCondition,
  createConditionFromTemplate,
  deleteCondition,
  duplicateCondition,
  listConditionTemplates,
  listProjectConditions,
  reorderConditions,
  updateCondition,
} from '@/api/conditions';
import type { Condition } from '@/types';

export function useConditions(
  projectId: string | undefined,
  filters?: { scope?: string; category?: string }
) {
  return useQuery({
    queryKey: ['conditions', projectId, filters?.scope, filters?.category],
    queryFn: () => listProjectConditions(projectId as string, filters),
    enabled: !!projectId,
  });
}

export function useConditionTemplates(filters?: { scope?: string; category?: string }) {
  return useQuery({
    queryKey: ['condition-templates', filters?.scope, filters?.category],
    queryFn: () => listConditionTemplates(filters),
  });
}

export function useCreateCondition(projectId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Parameters<typeof createCondition>[1]) =>
      createCondition(projectId as string, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conditions', projectId] });
    },
  });
}

export function useCreateConditionFromTemplate(projectId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (templateName: string) =>
      createConditionFromTemplate(projectId as string, templateName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conditions', projectId] });
    },
  });
}

export function useUpdateCondition(projectId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      conditionId,
      data,
    }: {
      conditionId: string;
      data: Parameters<typeof updateCondition>[2];
    }) => updateCondition(projectId as string, conditionId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['conditions', projectId] });
      queryClient.invalidateQueries({ queryKey: ['condition', variables.conditionId] });
    },
  });
}

export function useDeleteCondition(projectId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (conditionId: string) => deleteCondition(projectId as string, conditionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conditions', projectId] });
    },
  });
}

export function useDuplicateCondition(projectId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (conditionId: string) => duplicateCondition(projectId as string, conditionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conditions', projectId] });
    },
  });
}

export function useReorderConditions(projectId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (conditionIds: string[]) =>
      reorderConditions(projectId as string, conditionIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conditions', projectId] });
    },
  });
}

export function getConditionDisplayName(condition: Condition) {
  return condition.name.trim() || 'Untitled Condition';
}
