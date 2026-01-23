/**
 * Provider Comparison Component
 * 
 * Compares AI takeoff results across multiple LLM providers.
 * Useful for benchmarking which provider works best for specific content.
 */

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Loader2, FlaskConical, Clock, Hash, DollarSign, AlertCircle } from 'lucide-react';
import { takeoffApi, type ProviderResult, type TaskStatusResponse } from '@/api/takeoff';

interface ProviderComparisonProps {
    pageId: string;
    conditionId: string;
    conditionName: string;
    isPageCalibrated: boolean;
}

// Rough cost estimates per 1M tokens
const PROVIDER_COSTS: Record<string, { input: number; output: number }> = {
    anthropic: { input: 3, output: 15 },
    openai: { input: 2.5, output: 10 },
    google: { input: 1.25, output: 5 },
    xai: { input: 5, output: 15 },
};

function estimateCost(result: ProviderResult, provider: string): string {
    const rate = PROVIDER_COSTS[provider] || { input: 3, output: 15 };
    const cost = (result.input_tokens * rate.input + result.output_tokens * rate.output) / 1_000_000;
    return `$${cost.toFixed(4)}`;
}

export function ProviderComparison({
    pageId,
    conditionId,
    conditionName,
    isPageCalibrated,
}: ProviderComparisonProps) {
    const [results, setResults] = useState<Record<string, ProviderResult> | null>(null);
    const [error, setError] = useState<string | null>(null);

    const compareMutation = useMutation({
        mutationFn: async () => {
            const response = await takeoffApi.compareProviders(pageId, conditionId);
            
            // Poll for results
            const finalStatus = await takeoffApi.pollTaskStatus(
                response.task_id,
                (_status: TaskStatusResponse) => {
                    // Progress callback - status available for future use
                },
                {
                    maxAttempts: 120, // 10 minutes max
                    intervalMs: 5000,
                }
            );

            if (finalStatus.status === 'SUCCESS' && finalStatus.result) {
                // The result has a different shape for comparison
                return (finalStatus.result as unknown as { results: Record<string, ProviderResult> }).results;
            } else if (finalStatus.status === 'FAILURE') {
                throw new Error(finalStatus.error || 'Comparison failed');
            }
            
            throw new Error('Comparison timed out');
        },
        onSuccess: (data) => {
            setResults(data);
            setError(null);
        },
        onError: (err: Error) => {
            setError(err.message);
        },
    });

    if (!isPageCalibrated) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <FlaskConical className="h-5 w-5" />
                        Provider Comparison
                    </CardTitle>
                    <CardDescription>
                        Page must be calibrated before running comparison
                    </CardDescription>
                </CardHeader>
            </Card>
        );
    }

    return (
        <Card>
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <FlaskConical className="h-5 w-5" />
                    Provider Comparison
                </CardTitle>
                <CardDescription>
                    Compare AI takeoff results across different providers for {conditionName}
                </CardDescription>
            </CardHeader>
            <CardContent>
                {error && (
                    <div className="flex items-center gap-2 text-destructive mb-4">
                        <AlertCircle className="h-4 w-4" />
                        <span className="text-sm">{error}</span>
                    </div>
                )}

                {!results && (
                    <Button
                        onClick={() => compareMutation.mutate()}
                        disabled={compareMutation.isPending}
                    >
                        {compareMutation.isPending ? (
                            <>
                                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                Running comparison...
                            </>
                        ) : (
                            <>
                                <FlaskConical className="h-4 w-4 mr-2" />
                                Compare All Providers
                            </>
                        )}
                    </Button>
                )}

                {results && (
                    <div className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                            {Object.entries(results).map(([provider, result]) => (
                                <Card key={provider}>
                                    <CardHeader className="pb-2">
                                        <CardTitle className="text-lg capitalize">{provider}</CardTitle>
                                        <CardDescription className="text-xs">{result.model}</CardDescription>
                                    </CardHeader>
                                    <CardContent className="space-y-2">
                                        <div className="flex items-center justify-between">
                                            <span className="text-sm text-muted-foreground flex items-center gap-1">
                                                <Hash className="h-3 w-3" />
                                                Elements
                                            </span>
                                            <Badge variant="secondary">{result.elements_detected}</Badge>
                                        </div>
                                        <div className="flex items-center justify-between">
                                            <span className="text-sm text-muted-foreground flex items-center gap-1">
                                                <Clock className="h-3 w-3" />
                                                Latency
                                            </span>
                                            <Badge variant="outline">{Math.round(result.latency_ms)}ms</Badge>
                                        </div>
                                        <div className="flex items-center justify-between">
                                            <span className="text-sm text-muted-foreground flex items-center gap-1">
                                                <DollarSign className="h-3 w-3" />
                                                Est. Cost
                                            </span>
                                            <Badge variant="outline">{estimateCost(result, provider)}</Badge>
                                        </div>
                                        <div className="text-xs text-muted-foreground pt-2 border-t">
                                            Tokens: {result.input_tokens} in / {result.output_tokens} out
                                        </div>
                                    </CardContent>
                                </Card>
                            ))}
                        </div>

                        <Button variant="outline" onClick={() => setResults(null)}>
                            Run Again
                        </Button>
                    </div>
                )}
            </CardContent>
        </Card>
    );
}

export default ProviderComparison;
