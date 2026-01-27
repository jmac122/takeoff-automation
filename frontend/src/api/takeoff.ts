/**
 * API functions for AI Takeoff generation.
 */

import { apiClient } from './client';

// ============================================================================
// Types
// ============================================================================

export interface TakeoffTaskResponse {
    task_id: string;
    message: string;
    provider?: string;
}

export interface BatchTakeoffResponse {
    task_id: string;
    message: string;
    pages_count: number;
}

export interface TaskStatusResponse {
    task_id: string;
    status: 'PENDING' | 'STARTED' | 'SUCCESS' | 'FAILURE' | 'RETRY';
    result?: TakeoffResult;
    error?: string;
}

export interface TakeoffResult {
    page_id: string;
    condition_id?: string;
    elements_detected: number;
    measurements_created: number;
    page_description: string;
    analysis_notes: string;
    llm_provider: string;
    llm_model: string;
    llm_latency_ms: number;
}

export interface AutonomousTakeoffResult {
    page_id: string;
    autonomous: boolean;
    element_types_found: string[];
    elements_by_type: Record<string, DetectedElement[]>;
    total_elements: number;
    measurements_created: number;
    conditions_created: number;
    page_description: string;
    analysis_notes: string;
    llm_provider: string;
    llm_model: string;
    llm_latency_ms: number;
}

export interface ProviderComparisonResult {
    page_id: string;
    condition_id: string;
    providers_compared: string[];
    results: Record<string, ProviderResult>;
}

export interface ProviderResult {
    elements_detected: number;
    latency_ms: number;
    input_tokens: number;
    output_tokens: number;
    model: string;
    elements: DetectedElement[];
}

export interface DetectedElement {
    element_type: string;
    geometry_type: string;
    geometry_data: Record<string, unknown>;
    confidence: number;
    description: string;
}

export interface AvailableProvidersResponse {
    available: string[];
    default: string;
    task_config: Record<string, string>;
}

// ============================================================================
// API Functions
// ============================================================================

export const takeoffApi = {
    /**
     * Generate AI takeoff for a page with a pre-defined condition.
     */
    generateTakeoff: async (
        pageId: string,
        conditionId: string,
        provider?: string
    ): Promise<TakeoffTaskResponse> => {
        const response = await apiClient.post<TakeoffTaskResponse>(
            `/pages/${pageId}/ai-takeoff`,
            {
                condition_id: conditionId,
                provider,
            }
        );
        return response.data;
    },

    /**
     * AUTONOMOUS AI Takeoff - AI identifies ALL concrete elements on its own.
     * 
     * No pre-defined condition required. The AI will independently analyze
     * the drawing and identify all concrete elements it can find.
     */
    generateAutonomousTakeoff: async (
        pageId: string,
        projectId: string,
        provider?: string
    ): Promise<TakeoffTaskResponse> => {
        const response = await apiClient.post<TakeoffTaskResponse>(
            `/pages/${pageId}/autonomous-takeoff`,
            {
                project_id: projectId,
                provider,
            }
        );
        return response.data;
    },

    /**
     * Compare AI takeoff results across multiple providers.
     */
    compareProviders: async (
        pageId: string,
        conditionId: string,
        providers?: string[]
    ): Promise<TakeoffTaskResponse> => {
        const response = await apiClient.post<TakeoffTaskResponse>(
            `/pages/${pageId}/compare-providers`,
            {
                condition_id: conditionId,
                providers,
            }
        );
        return response.data;
    },

    /**
     * Generate AI takeoff for multiple pages.
     */
    batchTakeoff: async (
        pageIds: string[],
        conditionId: string,
        provider?: string
    ): Promise<BatchTakeoffResponse> => {
        const response = await apiClient.post<BatchTakeoffResponse>(
            '/batch-ai-takeoff',
            {
                page_ids: pageIds,
                condition_id: conditionId,
                provider,
            }
        );
        return response.data;
    },

    /**
     * Get available LLM providers for AI takeoff.
     */
    getAvailableProviders: async (): Promise<AvailableProvidersResponse> => {
        const response = await apiClient.get<AvailableProvidersResponse>(
            '/ai-takeoff/providers'
        );
        return response.data;
    },

    /**
     * Get status of a Celery task.
     */
    getTaskStatus: async (taskId: string): Promise<TaskStatusResponse> => {
        const response = await apiClient.get<TaskStatusResponse>(
            `/tasks/${taskId}/status`
        );
        return response.data;
    },

    /**
     * Poll for task completion.
     */
    pollTaskStatus: async (
        taskId: string,
        onProgress?: (status: TaskStatusResponse) => void,
        options?: {
            maxAttempts?: number;
            intervalMs?: number;
        }
    ): Promise<TaskStatusResponse> => {
        const maxAttempts = options?.maxAttempts ?? 120; // 10 minutes at 5s intervals
        const intervalMs = options?.intervalMs ?? 5000;
        
        let attempts = 0;
        
        while (attempts < maxAttempts) {
            const status = await takeoffApi.getTaskStatus(taskId);
            
            onProgress?.(status);
            
            if (status.status === 'SUCCESS' || status.status === 'FAILURE') {
                return status;
            }
            
            attempts++;
            await new Promise(resolve => setTimeout(resolve, intervalMs));
        }
        
        throw new Error('Task polling timed out');
    },
};

export default takeoffApi;
