import { apiClient } from './client';

export interface ScaleDetectionStatus {
    status: 'processing' | 'complete';
    scale_text: string | null;
    scale_value: number | null;
    calibrated: boolean;
    detection: any | null;
}

export const scaleApi = {
    detectScale: async (pageId: string) => {
        const response = await apiClient.post(`/pages/${pageId}/detect-scale`);
        return response.data;
    },

    getDetectionStatus: async (pageId: string): Promise<ScaleDetectionStatus> => {
        const response = await apiClient.get<ScaleDetectionStatus>(
            `/pages/${pageId}/scale-detection-status`
        );
        return response.data;
    },
};
