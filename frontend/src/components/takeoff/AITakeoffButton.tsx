/**
 * AI Takeoff Button Component
 * 
 * Triggers AI-powered element detection and measurement generation
 * for a specific page and condition.
 */

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from '@/components/ui/tooltip';
import { Sparkles, Loader2, Check, AlertCircle, FlaskConical } from 'lucide-react';
import { takeoffApi, type TakeoffResult, type TaskStatusResponse } from '@/api/takeoff';
import { LLMProviderSelector } from '@/components/LLMProviderSelector';

interface AITakeoffButtonProps {
    pageId: string;
    conditionId: string;
    conditionName: string;
    isPageCalibrated: boolean;
    onComplete?: (result: TakeoffResult) => void;
}

type TaskStatus = 'idle' | 'pending' | 'processing' | 'success' | 'error';

export function AITakeoffButton({
    pageId,
    conditionId,
    conditionName,
    isPageCalibrated,
    onComplete,
}: AITakeoffButtonProps) {
    const [showDialog, setShowDialog] = useState(false);
    const [taskStatus, setTaskStatus] = useState<TaskStatus>('idle');
    const [result, setResult] = useState<TakeoffResult | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [selectedProvider, setSelectedProvider] = useState<string | undefined>(undefined);
    const [showAdvanced, setShowAdvanced] = useState(false);

    const queryClient = useQueryClient();

    const generateMutation = useMutation({
        mutationFn: async () => {
            const response = await takeoffApi.generateTakeoff(
                pageId,
                conditionId,
                selectedProvider
            );
            return response;
        },
        onSuccess: async (data) => {
            setTaskStatus('processing');

            // Poll for task completion
            try {
                const finalStatus = await takeoffApi.pollTaskStatus(
                    data.task_id,
                    (status: TaskStatusResponse) => {
                        // Optional progress callback
                        if (status.status === 'STARTED') {
                            setTaskStatus('processing');
                        }
                    },
                    {
                        maxAttempts: 60, // 5 minutes max at 5s intervals
                        intervalMs: 5000,
                    }
                );

                if (finalStatus.status === 'SUCCESS' && finalStatus.result) {
                    setTaskStatus('success');
                    setResult(finalStatus.result);
                    queryClient.invalidateQueries({ queryKey: ['measurements', pageId] });
                    queryClient.invalidateQueries({ queryKey: ['conditions'] });
                    onComplete?.(finalStatus.result);
                } else if (finalStatus.status === 'FAILURE') {
                    setTaskStatus('error');
                    setError(finalStatus.error || 'Generation failed');
                }
            } catch (e) {
                setTaskStatus('error');
                setError(e instanceof Error ? e.message : 'Failed to check status');
            }
        },
        onError: (error: unknown) => {
            setTaskStatus('error');
            const errorMessage = error instanceof Error 
                ? error.message 
                : 'Failed to start generation';
            setError(errorMessage);
        },
    });

    const handleStart = () => {
        setTaskStatus('pending');
        setResult(null);
        setError(null);
        setShowDialog(true);
        generateMutation.mutate();
    };

    const handleClose = () => {
        setShowDialog(false);
        setTaskStatus('idle');
    };

    if (!isPageCalibrated) {
        return (
            <TooltipProvider>
                <Tooltip>
                    <TooltipTrigger asChild>
                        <span>
                            <Button variant="outline" size="sm" disabled>
                                <Sparkles className="h-4 w-4 mr-1" />
                                AI Takeoff
                            </Button>
                        </span>
                    </TooltipTrigger>
                    <TooltipContent>
                        <p>Calibrate page scale first</p>
                    </TooltipContent>
                </Tooltip>
            </TooltipProvider>
        );
    }

    return (
        <>
            <div className="flex items-center gap-2">
                <Button variant="outline" size="sm" onClick={handleStart}>
                    <Sparkles className="h-4 w-4 mr-1" />
                    AI Takeoff
                </Button>

                <TooltipProvider>
                    <Tooltip>
                        <TooltipTrigger asChild>
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setShowAdvanced(!showAdvanced)}
                            >
                                <FlaskConical className="h-4 w-4" />
                            </Button>
                        </TooltipTrigger>
                        <TooltipContent>
                            <p>Advanced: Select AI provider</p>
                        </TooltipContent>
                    </Tooltip>
                </TooltipProvider>
            </div>

            {showAdvanced && (
                <div className="mt-2">
                    <LLMProviderSelector
                        value={selectedProvider}
                        onChange={setSelectedProvider}
                        label="AI Provider"
                    />
                </div>
            )}

            <Dialog open={showDialog} onOpenChange={setShowDialog}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>AI Takeoff Generation</DialogTitle>
                        <DialogDescription>
                            Detecting {conditionName} elements on this page
                            {selectedProvider && ` using ${selectedProvider}`}
                        </DialogDescription>
                    </DialogHeader>

                    <div className="py-6">
                        {taskStatus === 'pending' && (
                            <div className="flex items-center gap-3">
                                <Loader2 className="h-5 w-5 animate-spin text-primary" />
                                <span>Starting analysis...</span>
                            </div>
                        )}

                        {taskStatus === 'processing' && (
                            <div className="flex items-center gap-3">
                                <Loader2 className="h-5 w-5 animate-spin text-primary" />
                                <div>
                                    <p>Analyzing page...</p>
                                    <p className="text-sm text-muted-foreground">
                                        This may take 30-60 seconds
                                    </p>
                                </div>
                            </div>
                        )}

                        {taskStatus === 'success' && result && (
                            <div className="space-y-3">
                                <div className="flex items-center gap-2 text-green-600">
                                    <Check className="h-5 w-5" />
                                    <span>Analysis complete!</span>
                                </div>
                                <div className="bg-muted p-3 rounded-lg space-y-1 text-sm">
                                    <p>
                                        <strong>Elements detected:</strong> {result.elements_detected}
                                    </p>
                                    <p>
                                        <strong>Measurements created:</strong> {result.measurements_created}
                                    </p>
                                    <p>
                                        <strong>Provider:</strong> {result.llm_provider} ({result.llm_model})
                                    </p>
                                    <p>
                                        <strong>Processing time:</strong> {Math.round(result.llm_latency_ms)}ms
                                    </p>
                                    {result.page_description && (
                                        <p className="text-muted-foreground">
                                            {result.page_description}
                                        </p>
                                    )}
                                </div>
                                {result.analysis_notes && (
                                    <p className="text-sm text-muted-foreground">
                                        {result.analysis_notes}
                                    </p>
                                )}
                            </div>
                        )}

                        {taskStatus === 'error' && (
                            <div className="flex items-center gap-2 text-destructive">
                                <AlertCircle className="h-5 w-5" />
                                <span>{error || 'An error occurred'}</span>
                            </div>
                        )}
                    </div>

                    <DialogFooter>
                        {taskStatus === 'success' || taskStatus === 'error' ? (
                            <Button onClick={handleClose}>Close</Button>
                        ) : (
                            <Button variant="outline" onClick={handleClose} disabled>
                                Cancel
                            </Button>
                        )}
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </>
    );
}

export default AITakeoffButton;
