/**
 * Classification API client for LLM analytics and history
 */

import { apiClient } from './client';

export interface ClassificationHistoryEntry {
    id: string;
    page_id: string;
    page_number?: number;
    sheet_number?: string;
    document_id?: string;
    classification: string | null;
    classification_confidence: number | null;
    discipline?: string | null;
    discipline_confidence?: number | null;
    page_type?: string | null;
    page_type_confidence?: number | null;
    concrete_relevance: string | null;
    concrete_elements?: string[] | null;
    description?: string | null;
    llm_provider: string;
    llm_model: string;
    llm_latency_ms: number | null;
    input_tokens: number | null;
    output_tokens: number | null;
    status: string;
    created_at: string;
}

export interface ProviderStats {
    provider: string;
    model: string;
    total_runs: number;
    avg_latency_ms: number | null;
    min_latency_ms: number | null;
    max_latency_ms: number | null;
    avg_confidence: number | null;
    relevance_distribution: Record<string, number>;
}

export interface ClassificationStats {
    by_provider: ProviderStats[];
    total_classifications: number;
}

export interface ClassificationHistory {
    total: number;
    history: ClassificationHistoryEntry[];
}

export const classificationApi = {
    getStats: async (): Promise<ClassificationStats> => {
        const response = await apiClient.get<ClassificationStats>('/classification/stats');
        return response.data;
    },

    getHistory: async (limit: number = 100): Promise<ClassificationHistory> => {
        const response = await apiClient.get<ClassificationHistory>(
            `/classification/history?limit=${limit}`
        );
        return response.data;
    },

    getPageHistory: async (pageId: string, limit: number = 50): Promise<ClassificationHistory> => {
        const response = await apiClient.get<ClassificationHistory>(
            `/pages/${pageId}/classification/history?limit=${limit}`
        );
        return response.data;
    },
};
