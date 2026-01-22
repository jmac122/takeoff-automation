import { QueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type { Page } from '@/types';

export interface PollOptions {
    maxAttempts?: number;
    intervalMs?: number;
}

/**
 * Polls for page updates until a condition is met or max attempts reached.
 * Updates the query cache with each poll response.
 * 
 * @param pageId - The page ID to poll
 * @param queryClient - React Query client for cache updates
 * @param checkComplete - Predicate that returns true when polling should stop
 * @param options - Polling options (maxAttempts, intervalMs)
 */
export async function pollForPageUpdate(
    pageId: string,
    queryClient: QueryClient,
    checkComplete: (page: Page) => boolean,
    options: PollOptions = {}
): Promise<void> {
    const { maxAttempts = 10, intervalMs = 500 } = options;

    for (let attempt = 0; attempt < maxAttempts; attempt++) {
        await new Promise(resolve => setTimeout(resolve, intervalMs));
        const response = await apiClient.get<Page>(`/pages/${pageId}`);
        const updatedPage = response.data;

        queryClient.setQueryData(['page', pageId], updatedPage);

        if (checkComplete(updatedPage)) {
            return;
        }
    }
}
