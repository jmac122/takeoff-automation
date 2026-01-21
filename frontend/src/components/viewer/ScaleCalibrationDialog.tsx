import { useState } from 'react';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { parseScaleText, validateScaleText } from '@/utils/scaleParser';
import type { Page } from '@/types';

interface ScaleCalibrationDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    page: Page | undefined;
    pageId: string | undefined;
    onScaleUpdated: () => void;
}

export function ScaleCalibrationDialog({
    open,
    onOpenChange,
    page,
    pageId,
    onScaleUpdated,
}: ScaleCalibrationDialogProps) {
    const [scaleText, setScaleText] = useState<string>('');
    const [scaleError, setScaleError] = useState<string | null>(null);

    const handleOpenChange = (newOpen: boolean) => {
        if (!newOpen) {
            setScaleText('');
            setScaleError(null);
        } else {
            setScaleText((page as any)?.scale_text || '');
            setScaleError(null);
        }
        onOpenChange(newOpen);
    };

    const handleSubmit = async () => {
        const validationError = validateScaleText(scaleText);
        if (validationError) {
            setScaleError(validationError);
            return;
        }

        const parsed = parseScaleText(scaleText);
        if (!parsed) {
            setScaleError('Failed to parse scale text');
            return;
        }

        try {
            const { apiClient } = await import('@/api/client');
            await apiClient.put(`/pages/${pageId}/scale`, {
                scale_value: parsed.pixelsPerFoot,
                scale_unit: 'foot',
                scale_text: scaleText,
            });

            onScaleUpdated();
            handleOpenChange(false);
        } catch (error) {
            console.error('Scale update failed:', error);
            setScaleError('Failed to set scale. Please try again.');
        }
    };

    return (
        <Dialog open={open} onOpenChange={handleOpenChange}>
            <DialogContent className="bg-neutral-900 border-neutral-700">
                <DialogHeader>
                    <DialogTitle className="text-white uppercase tracking-tight font-mono">
                        Set Scale
                    </DialogTitle>
                    <DialogDescription className="text-neutral-400 font-mono text-sm">
                        {page?.scale_text
                            ? `Current scale: ${page.scale_text} • Enter a new scale to override`
                            : 'Enter the scale from the drawing (e.g., "3/32" = 1\'-0"" or "1/4" = 1\'-0"")'}
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-4 py-4">
                    {page?.scale_text && (
                        <div className="bg-green-900/20 border border-green-700/50 rounded p-3">
                            <div className="flex items-center gap-2">
                                <span className="text-green-400 font-mono text-xs">✓ Current Scale:</span>
                                <span className="text-white font-mono font-bold">{page.scale_text}</span>
                                {page.scale_detection_method && (
                                    <span className="text-neutral-500 font-mono text-xs">
                                        (via {page.scale_detection_method === 'vision_llm' ? 'AI Vision' : page.scale_detection_method.replace(/_/g, ' ')})
                                    </span>
                                )}
                            </div>
                        </div>
                    )}

                    <div className="space-y-2">
                        <Label htmlFor="scale-text" className="text-neutral-400 font-mono text-xs uppercase">
                            {page?.scale_text ? 'New Scale (Optional)' : 'Scale Text'}
                        </Label>
                        <Input
                            id="scale-text"
                            type="text"
                            value={scaleText}
                            onChange={(e) => {
                                setScaleText(e.target.value);
                                setScaleError(null);
                            }}
                            placeholder={page?.scale_text || "e.g., 3/32 inch = 1 foot or 1/4 inch = 1 foot"}
                            className="bg-neutral-800 border-neutral-700 text-white font-mono placeholder:text-neutral-600"
                        />
                        {scaleError && (
                            <p className="text-xs text-red-400 font-mono">{scaleError}</p>
                        )}
                        {scaleText && !scaleError && parseScaleText(scaleText) && (
                            <div className="text-xs text-neutral-400 font-mono">
                                Calculated: {parseScaleText(scaleText)?.pixelsPerFoot.toFixed(2)} pixels per foot
                            </div>
                        )}
                    </div>

                    <div className="bg-neutral-800 border border-neutral-700 rounded p-3">
                        <p className="text-xs text-neutral-400 font-mono mb-2">Supported formats:</p>
                        <ul className="text-xs text-neutral-500 font-mono space-y-1 list-disc list-inside">
                            <li>"3/32" = 1'-0""</li>
                            <li>"1/4" = 1'-0""</li>
                            <li>"1" = 10'-0"" (engineering scale)</li>
                            <li>"1:48" (ratio format)</li>
                        </ul>
                    </div>
                </div>

                <DialogFooter>
                    <Button
                        variant="outline"
                        onClick={() => handleOpenChange(false)}
                        className="border-neutral-700 text-white hover:bg-neutral-800 font-mono uppercase"
                    >
                        Cancel
                    </Button>
                    <Button
                        onClick={handleSubmit}
                        disabled={!scaleText || !!validateScaleText(scaleText)}
                        className="bg-amber-500 hover:bg-amber-400 text-black font-mono uppercase"
                    >
                        Set Scale
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
