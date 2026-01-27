import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type { JsonObject } from '@/types';

interface CreateMeasurementData {
    conditionId: string;
    pageId: string;
    geometryType: string;
    geometryData: JsonObject;
}

interface UpdateMeasurementData {
    measurementId: string;
    geometryData: JsonObject;
    notes?: string | null;
}

export function useMeasurements(pageId: string | undefined, projectId?: string) {
    const queryClient = useQueryClient();

    const createMeasurementMutation = useMutation({
        mutationFn: async (data: CreateMeasurementData) => {
            // Backend expects: POST /conditions/{conditionId}/measurements
            const response = await apiClient.post(`/conditions/${data.conditionId}/measurements`, {
                page_id: data.pageId,
                geometry_type: data.geometryType,
                geometry_data: data.geometryData,
            });
            return response.data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['measurements', pageId] });
            if (projectId) {
                queryClient.invalidateQueries({ queryKey: ['conditions', projectId] });
            } else {
                queryClient.invalidateQueries({ queryKey: ['conditions'] });
            }
        },
    });

    const deleteMeasurementMutation = useMutation({
        mutationFn: async (measurementId: string) => {
            await apiClient.delete(`/measurements/${measurementId}`);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['measurements', pageId] });
            // Also invalidate conditions to refresh total_quantity and measurement_count
            if (projectId) {
                queryClient.invalidateQueries({ queryKey: ['conditions', projectId] });
            } else {
                queryClient.invalidateQueries({ queryKey: ['conditions'] });
            }
        },
    });

    const updateMeasurementMutation = useMutation({
        mutationFn: async (data: UpdateMeasurementData) => {
            const response = await apiClient.put(`/measurements/${data.measurementId}`, {
                geometry_data: data.geometryData,
                notes: data.notes ?? null,
            });
            return response.data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['measurements', pageId] });
            if (projectId) {
                queryClient.invalidateQueries({ queryKey: ['conditions', projectId] });
            } else {
                queryClient.invalidateQueries({ queryKey: ['conditions'] });
            }
        },
    });

    const createMeasurement = (data: CreateMeasurementData) => {
        createMeasurementMutation.mutate(data);
    };

    const deleteMeasurement = (measurementId: string) => {
        deleteMeasurementMutation.mutate(measurementId);
    };

    const updateMeasurement = (data: UpdateMeasurementData) => {
        updateMeasurementMutation.mutate(data);
    };

    const createMeasurementAsync = (data: CreateMeasurementData) => {
        return createMeasurementMutation.mutateAsync(data);
    };

    const deleteMeasurementAsync = (measurementId: string) => {
        return deleteMeasurementMutation.mutateAsync(measurementId);
    };

    const updateMeasurementAsync = (data: UpdateMeasurementData) => {
        return updateMeasurementMutation.mutateAsync(data);
    };

    return {
        createMeasurement,
        deleteMeasurement,
        updateMeasurement,
        createMeasurementAsync,
        deleteMeasurementAsync,
        updateMeasurementAsync,
        isCreating: createMeasurementMutation.isPending,
        isDeleting: deleteMeasurementMutation.isPending,
        isUpdating: updateMeasurementMutation.isPending,
    };
}
