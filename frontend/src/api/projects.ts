/**
 * API client for project-related endpoints.
 */

import { apiClient } from './client';
import { Project, CreateProjectRequest, Document } from '../types';

export const projectsApi = {
    /**
     * List all projects
     */
    list: async (): Promise<{ projects: Project[] }> => {
        const response = await apiClient.get<Project[]>('/projects/');
        return { projects: response.data };
    },

    /**
     * Get single project by ID
     */
    get: async (projectId: string): Promise<Project> => {
        const response = await apiClient.get<Project>(`/projects/${projectId}`);
        return response.data;
    },

    /**
     * Create a new project
     */
    create: async (data: CreateProjectRequest): Promise<Project> => {
        const response = await apiClient.post<Project>('/projects', data);
        return response.data;
    },

    /**
     * Update an existing project
     */
    update: async (projectId: string, data: Partial<CreateProjectRequest>): Promise<Project> => {
        const response = await apiClient.put<Project>(`/projects/${projectId}`, data);
        return response.data;
    },

    /**
     * Delete a project
     */
    delete: async (projectId: string): Promise<void> => {
        await apiClient.delete(`/projects/${projectId}`);
    },

    /**
     * Get all documents for a project
     */
    getDocuments: async (projectId: string): Promise<{ documents: Document[] }> => {
        const response = await apiClient.get<{ documents: Document[] }>(`/projects/${projectId}/documents`);
        return response.data;
    },
};
