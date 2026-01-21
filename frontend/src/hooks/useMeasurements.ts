import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';

interface CreateMeasurementData {
    conditionId: string;
    pageId: string;
    geometryType: string;
    geometryData: any;
}

export function useMeasurements(pageId: string | undefined) {
    const queryClient = useQueryClient();

    const createMeasurementMutation = useMutation({
        mutationFn: async (data: CreateMeasurementData) => {
            const response = await apiClient.post('/measurements', data);
            return response.data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['measurements', pageId] });
            queryClient.invalidateQueries({ queryKey: ['conditions'] });
        },
    });

    const deleteMeasurementMutation = useMutation({
        mutationFn: async (measurementId: string) => {
            await apiClient.delete(`/measurements/${measurementId}`);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['measurements', pageId] });
        },
    });

    const createMeasurement = (data: CreateMeasurementData) => {
        createMeasurementMutation.mutate(data);
    };

    const deleteMeasurement = (measurementId: string) => {
        deleteMeasurementMutation.mutate(measurementId);
    };

    return {
        createMeasurement,
        deleteMeasurement,
        isCreating: createMeasurementMutation.isPending,
        isDeleting: deleteMeasurementMutation.isPending,
    };
}
