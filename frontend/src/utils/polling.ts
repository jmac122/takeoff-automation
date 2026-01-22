export interface PollUntilOptions<T> {
    fetcher: () => Promise<T>;
    shouldStop: (value: T) => boolean;
    onTick?: (value: T) => void;
    intervalMs?: number;
    maxAttempts?: number;
    initialDelayMs?: number;
}

const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export async function pollUntil<T>({
    fetcher,
    shouldStop,
    onTick,
    intervalMs = 500,
    maxAttempts = 10,
    initialDelayMs = intervalMs,
}: PollUntilOptions<T>): Promise<T | null> {
    if (initialDelayMs > 0) {
        await sleep(initialDelayMs);
    }

    for (let attempt = 0; attempt < maxAttempts; attempt++) {
        const value = await fetcher();
        onTick?.(value);

        if (shouldStop(value)) {
            return value;
        }

        if (attempt < maxAttempts - 1) {
            await sleep(intervalMs);
        }
    }

    return null;
}
