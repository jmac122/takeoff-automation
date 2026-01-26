/**
 * Autonomous AI Takeoff Button
 * 
 * Triggers AI-powered AUTONOMOUS element detection - the AI identifies
 * ALL concrete elements on its own without pre-defined conditions.
 * This is the real AI takeoff capability.
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
import { Sparkles, Loader2, Check, AlertCircle, Brain } from 'lucide-react';
import { takeoffApi, type AutonomousTakeoffResult, type TaskStatusResponse } from '@/api/takeoff';
import { LLMProviderSelector } from '@/components/LLMProviderSelector';

interface AutonomousAITakeoffButtonProps {
    pageId: string;
    projectId: string;
    isPageCalibrated: boolean;
    onComplete?: (result: AutonomousTakeoffResult) => void;
}

type TaskStatus = 'idle' | 'pending' | 'processing' | 'success' | 'error';

export function AutonomousAITakeoffButton({
    pageId,
    projectId,
    isPageCalibrated,
    onComplete,
}: AutonomousAITakeoffButtonProps) {
    const [showDialog, setShowDialog] = useState(false);
    const [taskStatus, setTaskStatus] = useState<TaskStatus>('idle');
    const [result, setResult] = useState<AutonomousTakeoffResult | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [selectedProvider, setSelectedProvider] = useState<string | undefined>(undefined);
    const [showAdvanced, setShowAdvanced] = useState(false);

    const queryClient = useQueryClient();

    const generateMutation = useMutation({
        mutationFn: async () => {
            const response = await takeoffApi.generateAutonomousTakeoff(
                pageId,
                projectId,
                selectedProvider
            );
            return response;
        },
        onSuccess: async (data) => {
            setTaskStatus('processing');

            try {
                const finalStatus = await takeoffApi.pollTaskStatus(
                    data.task_id,
                    (status: TaskStatusResponse) => {
                        if (status.status === 'STARTED') {
                            setTaskStatus('processing');
                        }
                    },
                    {
                        maxAttempts: 90, // 7.5 minutes max
                        intervalMs: 5000,
                    }
                );

                if (finalStatus.status === 'SUCCESS' && finalStatus.result) {
                    setTaskStatus('success');
                    const autonomousResult = finalStatus.result as unknown as AutonomousTakeoffResult;
                    setResult(autonomousResult);
                    queryClient.invalidateQueries({ queryKey: ['measurements', pageId] });
                    queryClient.invalidateQueries({ queryKey: ['conditions'] });
                    onComplete?.(autonomousResult);
                } else if (finalStatus.status === 'FAILURE') {
                    setTaskStatus('error');
                    setError(finalStatus.error || 'Autonomous takeoff failed');
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
                : 'Failed to start autonomous takeoff';
            setError(errorMessage);
        },
    });

    const handleOpenDialog = () => {
        setShowDialog(true);
        setTaskStatus('idle');
        setResult(null);
        setError(null);
    };

    const handleStart = () => {
        setTaskStatus('pending');
        generateMutation.mutate();
    };

    const handleClose = () => {
        setShowDialog(false);
    };

    const isRunning = taskStatus === 'pending' || taskStatus === 'processing';

    // #region agent log
    fetch('http://127.0.0.1:7244/ingest/c2908297-06df-40fb-a71a-4f158024ffa0',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sessionId:'debug-session',runId:'run2',hypothesisId:'H2',location:'AutonomousAITakeoffButton.tsx:124',message:'auto detect render state',data:{isPageCalibrated,taskStatus,showDialog},timestamp:Date.now()})}).catch(()=>{});
    // #endregion
    if (!isPageCalibrated) {
        return (
            <TooltipProvider>
                <Tooltip>
                    <TooltipTrigger asChild>
                        <span>
                            <Button 
                                variant="default" 
                                size="sm" 
                                disabled
                                className="bg-gradient-to-r from-purple-600 to-blue-600 opacity-50"
                            >
                                <Brain className="h-4 w-4 mr-2" />
                                AUTO DETECT
                            </Button>
                        </span>
                    </TooltipTrigger>
                    <TooltipContent>
                        <p>Scale calibration required. Use "Set Scale" to calibrate.</p>
                    </TooltipContent>
                </Tooltip>
            </TooltipProvider>
        );
    }

    return (
        <>
            <Button 
                variant="default" 
                size="sm" 
                onClick={handleOpenDialog}
                className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-semibold"
            >
                <Brain className="h-4 w-4 mr-2" />
                AUTO DETECT
            </Button>

            <Dialog open={showDialog} onOpenChange={setShowDialog}>
                <DialogContent className="sm:max-w-[500px]">
                    <DialogHeader>
                        <DialogTitle className="flex items-center gap-2">
                            <Brain className="h-5 w-5 text-purple-500" />
                            Autonomous AI Takeoff
                        </DialogTitle>
                        <DialogDescription>
                            AI will independently identify ALL concrete elements on this page.
                            No pre-defined conditions required.
                        </DialogDescription>
                    </DialogHeader>

                    <div className="py-4">
                        {taskStatus === 'idle' && (
                            <div className="space-y-4">
                                <div className="bg-purple-500/10 border border-purple-500/30 p-4 rounded-lg">
                                    <h4 className="font-medium text-purple-400 mb-2">What the AI will do:</h4>
                                    <ul className="text-sm text-muted-foreground space-y-1">
                                        <li>• Analyze the drawing independently</li>
                                        <li>• Identify concrete elements (slabs, footings, walls, etc.)</li>
                                        <li>• Draw boundaries around each element</li>
                                        <li>• Calculate SF and CY quantities</li>
                                        <li>• Auto-create conditions for each element type</li>
                                    </ul>
                                </div>
                                
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
                                <Loader2 className="h-5 w-5 animate-spin text-purple-500" />
                                <span>Starting autonomous analysis...</span>
                            </div>
                        )}

                        {taskStatus === 'processing' && (
                            <div className="flex items-center gap-3">
                                <Loader2 className="h-5 w-5 animate-spin text-purple-500" />
                                <div>
                                    <p>AI is analyzing the drawing...</p>
                                    <p className="text-sm text-muted-foreground">
                                        Identifying concrete elements. This may take 30-90 seconds.
                                    </p>
                                </div>
                            </div>
                        )}

                        {taskStatus === 'success' && result && (
                            <div className="space-y-4">
                                <div className="flex items-center gap-2 text-green-500">
                                    <Check className="h-5 w-5" />
                                    <span className="font-medium">Analysis Complete!</span>
                                </div>
                                
                                <div className="bg-muted p-4 rounded-lg space-y-3">
                                    <div className="grid grid-cols-2 gap-4 text-sm">
                                        <div>
                                            <p className="text-muted-foreground">Total Elements</p>
                                            <p className="text-2xl font-bold text-purple-400">{result.total_elements}</p>
                                        </div>
                                        <div>
                                            <p className="text-muted-foreground">Measurements</p>
                                            <p className="text-2xl font-bold text-blue-400">{result.measurements_created}</p>
                                        </div>
                                    </div>

                                    {result.element_types_found.length > 0 && (
                                        <div>
                                            <p className="text-sm text-muted-foreground mb-2">Element Types Found:</p>
                                            <div className="flex flex-wrap gap-2">
                                                {result.element_types_found.map((type) => (
                                                    <span 
                                                        key={type}
                                                        className="px-2 py-1 bg-purple-500/20 text-purple-300 rounded text-xs"
                                                    >
                                                        {type.replace(/_/g, ' ')}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {result.conditions_created > 0 && (
                                        <p className="text-sm text-green-400">
                                            ✓ Created {result.conditions_created} new conditions
                                        </p>
                                    )}

                                    <div className="text-xs text-muted-foreground pt-2 border-t">
                                        <p>Provider: {result.llm_provider} ({result.llm_model})</p>
                                        <p>Processing time: {Math.round(result.llm_latency_ms)}ms</p>
                                    </div>
                                </div>

                                {result.page_description && (
                                    <p className="text-sm text-muted-foreground">
                                        {result.page_description}
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
                                    className="bg-gradient-to-r from-purple-600 to-blue-600"
                                >
                                    <Sparkles className="h-4 w-4 mr-2" />
                                    Start Autonomous Takeoff
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
        </>
    );
}

export default AutonomousAITakeoffButton;
