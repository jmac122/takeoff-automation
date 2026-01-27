/**
 * Tests for AI Takeoff API functions.
 * 
 * Run with: npx vitest run src/api/takeoff.test.ts
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { takeoffApi } from './takeoff';
import { apiClient } from './client';

// Mock the API client
vi.mock('./client', () => ({
    apiClient: {
        post: vi.fn(),
        get: vi.fn(),
    },
}));

describe('takeoffApi', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    describe('generateTakeoff', () => {
        it('should call POST /pages/{pageId}/ai-takeoff with correct payload', async () => {
            const mockResponse = {
                data: {
                    task_id: 'task-123',
                    message: 'AI takeoff started',
                    provider: 'anthropic',
                },
            };
            vi.mocked(apiClient.post).mockResolvedValue(mockResponse);

            const result = await takeoffApi.generateTakeoff('page-1', 'condition-1', 'anthropic');

            expect(apiClient.post).toHaveBeenCalledWith(
                '/pages/page-1/ai-takeoff',
                {
                    condition_id: 'condition-1',
                    provider: 'anthropic',
                }
            );
            expect(result.task_id).toBe('task-123');
        });

        it('should work without provider override', async () => {
            const mockResponse = {
                data: {
                    task_id: 'task-456',
                    message: 'AI takeoff started',
                },
            };
            vi.mocked(apiClient.post).mockResolvedValue(mockResponse);

            await takeoffApi.generateTakeoff('page-1', 'condition-1');

            expect(apiClient.post).toHaveBeenCalledWith(
                '/pages/page-1/ai-takeoff',
                {
                    condition_id: 'condition-1',
                    provider: undefined,
                }
            );
        });
    });

    describe('compareProviders', () => {
        it('should call POST /pages/{pageId}/compare-providers', async () => {
            const mockResponse = {
                data: {
                    task_id: 'compare-task-123',
                    message: 'Comparison started',
                },
            };
            vi.mocked(apiClient.post).mockResolvedValue(mockResponse);

            const result = await takeoffApi.compareProviders(
                'page-1',
                'condition-1',
                ['anthropic', 'openai']
            );

            expect(apiClient.post).toHaveBeenCalledWith(
                '/pages/page-1/compare-providers',
                {
                    condition_id: 'condition-1',
                    providers: ['anthropic', 'openai'],
                }
            );
            expect(result.task_id).toBe('compare-task-123');
        });
    });

    describe('batchTakeoff', () => {
        it('should call POST /batch-ai-takeoff with multiple pages', async () => {
            const mockResponse = {
                data: {
                    task_id: 'batch-task-123',
                    message: 'Batch queued',
                    pages_count: 3,
                },
            };
            vi.mocked(apiClient.post).mockResolvedValue(mockResponse);

            const result = await takeoffApi.batchTakeoff(
                ['page-1', 'page-2', 'page-3'],
                'condition-1',
                'openai'
            );

            expect(apiClient.post).toHaveBeenCalledWith(
                '/batch-ai-takeoff',
                {
                    page_ids: ['page-1', 'page-2', 'page-3'],
                    condition_id: 'condition-1',
                    provider: 'openai',
                }
            );
            expect(result.pages_count).toBe(3);
        });
    });

    describe('getAvailableProviders', () => {
        it('should call GET /ai-takeoff/providers', async () => {
            const mockResponse = {
                data: {
                    available: ['anthropic', 'openai', 'google'],
                    default: 'anthropic',
                    task_config: {
                        element_detection: 'anthropic',
                    },
                },
            };
            vi.mocked(apiClient.get).mockResolvedValue(mockResponse);

            const result = await takeoffApi.getAvailableProviders();

            expect(apiClient.get).toHaveBeenCalledWith('/ai-takeoff/providers');
            expect(result.available).toContain('anthropic');
            expect(result.default).toBe('anthropic');
        });
    });

    describe('getTaskStatus', () => {
        it('should call GET /tasks/{taskId}/status', async () => {
            const mockResponse = {
                data: {
                    task_id: 'task-123',
                    status: 'SUCCESS',
                    result: {
                        elements_detected: 5,
                        measurements_created: 5,
                    },
                },
            };
            vi.mocked(apiClient.get).mockResolvedValue(mockResponse);

            const result = await takeoffApi.getTaskStatus('task-123');

            expect(apiClient.get).toHaveBeenCalledWith('/tasks/task-123/status');
            expect(result.status).toBe('SUCCESS');
            expect(result.result?.elements_detected).toBe(5);
        });
    });

    describe('pollTaskStatus', () => {
        it('should poll until SUCCESS status', async () => {
            const pendingResponse = {
                data: { task_id: 'task-123', status: 'PENDING' },
            };
            const successResponse = {
                data: {
                    task_id: 'task-123',
                    status: 'SUCCESS',
                    result: { elements_detected: 3 },
                },
            };

            vi.mocked(apiClient.get)
                .mockResolvedValueOnce(pendingResponse)
                .mockResolvedValueOnce(pendingResponse)
                .mockResolvedValueOnce(successResponse);

            const onProgress = vi.fn();
            const result = await takeoffApi.pollTaskStatus(
                'task-123',
                onProgress,
                { maxAttempts: 10, intervalMs: 10 }
            );

            expect(result.status).toBe('SUCCESS');
            expect(onProgress).toHaveBeenCalledTimes(3);
        });

        it('should return on FAILURE status', async () => {
            const failureResponse = {
                data: {
                    task_id: 'task-123',
                    status: 'FAILURE',
                    error: 'Task failed',
                },
            };
            vi.mocked(apiClient.get).mockResolvedValue(failureResponse);

            const result = await takeoffApi.pollTaskStatus('task-123', undefined, {
                maxAttempts: 5,
                intervalMs: 10,
            });

            expect(result.status).toBe('FAILURE');
            expect(result.error).toBe('Task failed');
        });

        it('should throw on timeout', async () => {
            const pendingResponse = {
                data: { task_id: 'task-123', status: 'PENDING' },
            };
            vi.mocked(apiClient.get).mockResolvedValue(pendingResponse);

            await expect(
                takeoffApi.pollTaskStatus('task-123', undefined, {
                    maxAttempts: 2,
                    intervalMs: 10,
                })
            ).rejects.toThrow('Task polling timed out');
        });
    });
});
