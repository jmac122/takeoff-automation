/**
 * AI Takeoff Dialog Component
 * 
 * A dialog that triggers AI-powered element detection and measurement generation
 * for a specific page and condition. Designed to be used as a controlled component.
 */

import { useState, useEffect } from 'react';
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
import { Sparkles, Loader2, Check, AlertCircle } from 'lucide-react';
import { takeoffApi, type TakeoffResult, type TaskStatusResponse } from '@/api/takeoff';
import { LLMProviderSelector } from '@/components/LLMProviderSelector';

interface AITakeoffDialogProps {
    pageId: string;
    conditionId: string;
    conditionName: string;
    isPageCalibrated: boolean;
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onComplete?: (result: TakeoffResult) => void;
}

type TaskStatus = 'idle' | 'pending' | 'processing' | 'success' | 'error';

export function AITakeoffDialog({
    pageId,
    conditionId,
    conditionName,
    isPageCalibrated,
    open,
    onOpenChange,
    onComplete,
}: AITakeoffDialogProps) {
    const [taskStatus, setTaskStatus] = useState<TaskStatus>('idle');
    const [result, setResult] = useState<TakeoffResult | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [selectedProvider, setSelectedProvider] = useState<string | undefined>(undefined);
    const [showAdvanced, setShowAdvanced] = useState(false);

    const queryClient = useQueryClient();

    // Reset state when dialog opens
    useEffect(() => {
        if (open) {
            setTaskStatus('idle');
            setResult(null);
            setError(null);
        }
    }, [open]);

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
        generateMutation.mutate();
    };

    const handleClose = () => {
        onOpenChange(false);
    };

    const isRunning = taskStatus === 'pending' || taskStatus === 'processing';

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <Sparkles className="h-5 w-5 text-primary" />
                        AI Takeoff Generation
                    </DialogTitle>
                    <DialogDescription>
                        Automatically detect and measure {conditionName} elements on this page using AI.
                    </DialogDescription>
                </DialogHeader>

                <div className="py-4">
                    {!isPageCalibrated && (
                        <div className="flex items-center gap-2 text-amber-500 mb-4 p-3 bg-amber-500/10 rounded-lg">
                            <AlertCircle className="h-5 w-5" />
                            <span className="text-sm">Page scale must be calibrated first</span>
                        </div>
                    )}

                    {taskStatus === 'idle' && isPageCalibrated && (
                        <div className="space-y-4">
                            <p className="text-sm text-muted-foreground">
                                The AI will analyze this page and create measurements for all detected {conditionName} elements.
                            </p>
                            
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setShowAdvanced(!showAdvanced)}
                                className="text-xs"
                            >
                                {showAdvanced ? 'Hide' : 'Show'} advanced options
                            </Button>

                            {showAdvanced && (
                                <div className="p-3 border rounded-lg">
                                    <LLMProviderSelector
                                        value={selectedProvider}
                                        onChange={setSelectedProvider}
                                        label="AI Provider"
                                    />
                                </div>
                            )}
                        </div>
                    )}

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
                                    <p className="text-muted-foreground pt-2 border-t">
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
                        <div className="flex items-center gap-2 text-destructive p-3 bg-destructive/10 rounded-lg">
                            <AlertCircle className="h-5 w-5" />
                            <span>{error || 'An error occurred'}</span>
                        </div>
                    )}
                </div>

                <DialogFooter>
                    {taskStatus === 'idle' && (
                        <>
                            <Button variant="outline" onClick={handleClose}>
                                Cancel
                            </Button>
                            <Button 
                                onClick={handleStart} 
                                disabled={!isPageCalibrated}
                            >
                                <Sparkles className="h-4 w-4 mr-2" />
                                Start AI Takeoff
                            </Button>
                        </>
                    )}
                    {isRunning && (
                        <Button variant="outline" disabled>
                            Processing...
                        </Button>
                    )}
                    {(taskStatus === 'success' || taskStatus === 'error') && (
                        <Button onClick={handleClose}>Close</Button>
                    )}
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}

export default AITakeoffDialog;
