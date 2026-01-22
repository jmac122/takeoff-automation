import { useState, useEffect } from 'react';
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
import type { Page } from '@/types';
import type { CalibrationState } from '@/hooks/useScaleCalibration';

interface ScaleCalibrationDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    page: Page | undefined;
    pageId: string | undefined;
    onScaleUpdated: () => void;
    // Calibration props
    calibrationState: CalibrationState;
    onStartCalibration: () => void;
    onCancelCalibration: () => void;
    onClearLine: () => void;
    onSubmitCalibration: (pageId: string, realDistance: number, unit: string, pixelDistance?: number) => Promise<void>;
}

type CalibrationStep = 'choose' | 'drawing' | 'enter-distance';

export function ScaleCalibrationDialog({
    open,
    onOpenChange,
    page,
    pageId,
    onScaleUpdated,
    calibrationState,
    onStartCalibration,
    onCancelCalibration,
    onClearLine,
    onSubmitCalibration,
}: ScaleCalibrationDialogProps) {
    const [step, setStep] = useState<CalibrationStep>('choose');
    const [realDistance, setRealDistance] = useState<string>('');
    const [distanceError, setDistanceError] = useState<string | null>(null);
    const [isSubmitting, setIsSubmitting] = useState(false);

    // Reset state when dialog opens/closes
    // Note: Don't cancel calibration when closing - user might be drawing
    useEffect(() => {
        if (!open) {
            // Only reset internal dialog state, not calibration state
            setRealDistance('');
            setDistanceError(null);
            setIsSubmitting(false);
            // Reset step to 'choose' only if not actively calibrating
            if (!calibrationState.isCalibrating) {
                setStep('choose');
            }
        }
    }, [open, calibrationState.isCalibrating]);

    // Move to enter-distance step when line is drawn
    useEffect(() => {
        if (calibrationState.calibrationLine && !calibrationState.isDrawing && step === 'drawing') {
            setStep('enter-distance');
        }
    }, [calibrationState.calibrationLine, calibrationState.isDrawing, step]);

    const handleStartDrawing = () => {
        setStep('drawing');
        onStartCalibration();
        // Close dialog so user can draw on canvas
        onOpenChange(false);
    };

    const handleOpenChange = (newOpen: boolean) => {
        if (!newOpen && calibrationState.isCalibrating && !calibrationState.calibrationLine) {
            // User closed dialog while calibrating but before drawing - cancel
            onCancelCalibration();
        }
        onOpenChange(newOpen);
    };

    const parseDistance = (value: string): number | null => {
        if (!value || !value.trim()) return null;
        
        const trimmed = value.trim();
        
        // Try feet with optional inches: "21'-6"", "21' 6"", "21-6", "21'", "21'-0""
        const feetInchesMatch = trimmed.match(/^(\d+)[''\-]?\s*(\d+)?["'"]?$/);
        if (feetInchesMatch) {
            const feet = parseInt(feetInchesMatch[1]);
            const inches = feetInchesMatch[2] ? parseInt(feetInchesMatch[2]) : 0;
            return feet + inches / 12;
        }

        // Try just a number (feet): "21" or "21.5"
        const numberMatch = trimmed.match(/^(\d+\.?\d*)$/);
        if (numberMatch) {
            return parseFloat(numberMatch[1]);
        }

        return null;
    };
    
    // Calculate pixel distance from calibration line (more reliable than state)
    const calculatedPixelDistance = calibrationState.calibrationLine 
        ? Math.sqrt(
            Math.pow(calibrationState.calibrationLine.end.x - calibrationState.calibrationLine.start.x, 2) +
            Math.pow(calibrationState.calibrationLine.end.y - calibrationState.calibrationLine.start.y, 2)
        )
        : calibrationState.pixelDistance ?? 0;

    const handleSubmit = async () => {
        if (!pageId) return;

        const distance = parseDistance(realDistance);
        if (!distance || distance <= 0) {
            setDistanceError('Please enter a valid distance (e.g., "21" or "21\'-6"")');
            return;
        }

        if (calculatedPixelDistance <= 0) {
            setDistanceError('No calibration line drawn. Please redraw.');
            return;
        }

        setIsSubmitting(true);
        setDistanceError(null);

        try {
            await onSubmitCalibration(pageId, distance, 'foot', calculatedPixelDistance);
            onScaleUpdated();
            handleOpenChange(false);
        } catch (error) {
            console.error('Calibration failed:', error);
            setDistanceError('Calibration failed. Please try again.');
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleRedraw = () => {
        onClearLine();
        setStep('drawing');
        onStartCalibration();
        onOpenChange(false);
    };

    // If we have a calibration line and dialog is being opened, go to enter-distance
    useEffect(() => {
        if (open && calibrationState.calibrationLine && !calibrationState.isDrawing) {
            setStep('enter-distance');
        }
    }, [open, calibrationState.calibrationLine, calibrationState.isDrawing]);

    return (
        <Dialog open={open} onOpenChange={handleOpenChange}>
            <DialogContent className="bg-neutral-900 border-neutral-700 max-w-md">
                <DialogHeader>
                    <DialogTitle className="text-white uppercase tracking-tight font-mono">
                        {step === 'choose' && 'Calibrate Scale'}
                        {step === 'drawing' && 'Draw Calibration Line'}
                        {step === 'enter-distance' && 'Enter Distance'}
                    </DialogTitle>
                    <DialogDescription className="text-neutral-400 font-mono text-sm">
                        {step === 'choose' && 'Draw a line over a known dimension to calibrate the scale.'}
                        {step === 'drawing' && 'Click and drag to draw a line over a dimension with a known length.'}
                        {step === 'enter-distance' && 'Enter the real-world distance of the line you drew.'}
                    </DialogDescription>
                </DialogHeader>

                {/* Step: Choose */}
                {step === 'choose' && (
                    <div className="space-y-4 py-4">
                        {page?.scale_text && (
                            <div className="bg-amber-900/20 border border-amber-700/50 rounded p-3">
                                <div className="flex items-center gap-2 flex-wrap">
                                    <span className="text-amber-400 font-mono text-xs">Current Scale:</span>
                                    <span className="text-white font-mono font-bold">{page.scale_text}</span>
                                    {page.scale_value && (
                                        <span className="text-neutral-500 font-mono text-xs">
                                            ({page.scale_value.toFixed(2)} px/ft)
                                        </span>
                                    )}
                                </div>
                            </div>
                        )}

                        <div className="bg-neutral-800 border border-neutral-700 rounded p-4 space-y-3">
                            <div className="flex items-start gap-3">
                                <div className="bg-amber-500 text-black font-mono font-bold w-6 h-6 rounded flex items-center justify-center text-sm flex-shrink-0">
                                    1
                                </div>
                                <div>
                                    <p className="text-white font-mono text-sm">Draw a line</p>
                                    <p className="text-neutral-500 font-mono text-xs">
                                        Click "Start" then draw a line over any dimension with a known length
                                    </p>
                                </div>
                            </div>
                            <div className="flex items-start gap-3">
                                <div className="bg-amber-500 text-black font-mono font-bold w-6 h-6 rounded flex items-center justify-center text-sm flex-shrink-0">
                                    2
                                </div>
                                <div>
                                    <p className="text-white font-mono text-sm">Enter the distance</p>
                                    <p className="text-neutral-500 font-mono text-xs">
                                        Tell us the real-world length (e.g., "21'-0"")
                                    </p>
                                </div>
                            </div>
                            <div className="flex items-start gap-3">
                                <div className="bg-green-500 text-black font-mono font-bold w-6 h-6 rounded flex items-center justify-center text-sm flex-shrink-0">
                                    ✓
                                </div>
                                <div>
                                    <p className="text-white font-mono text-sm">Scale calibrated</p>
                                    <p className="text-neutral-500 font-mono text-xs">
                                        All measurements will now be accurate
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Step: Enter Distance */}
                {step === 'enter-distance' && (
                    <div className="space-y-4 py-4">
                        <div className="bg-green-900/20 border border-green-700/50 rounded p-3">
                            <div className="flex items-center gap-2">
                                <span className="text-green-400 font-mono text-xs">✓ Line drawn:</span>
                                <span className="text-white font-mono font-bold">
                                    {calculatedPixelDistance.toFixed(1)} pixels
                                </span>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="real-distance" className="text-neutral-400 font-mono text-xs uppercase">
                                Real-World Distance (feet)
                            </Label>
                            <Input
                                id="real-distance"
                                type="text"
                                value={realDistance}
                                onChange={(e) => {
                                    setRealDistance(e.target.value);
                                    setDistanceError(null);
                                }}
                                placeholder="e.g., 21 or 21'-6&quot;"
                                className="bg-neutral-800 border-neutral-700 text-white font-mono placeholder:text-neutral-600 text-lg"
                                autoFocus
                            />
                            {distanceError && (
                                <p className="text-xs text-red-400 font-mono">{distanceError}</p>
                            )}
                            {realDistance && parseDistance(realDistance) && calculatedPixelDistance > 0 && (
                                <div className="text-xs text-neutral-400 font-mono">
                                    = {parseDistance(realDistance)?.toFixed(2)} feet
                                    <span className="text-green-400 ml-2">
                                        → {(calculatedPixelDistance / parseDistance(realDistance)!).toFixed(2)} px/ft
                                    </span>
                                </div>
                            )}
                        </div>

                        <div className="bg-neutral-800 border border-neutral-700 rounded p-3">
                            <p className="text-xs text-neutral-400 font-mono mb-2">Supported formats:</p>
                            <ul className="text-xs text-neutral-500 font-mono space-y-1 list-disc list-inside">
                                <li>21 (feet)</li>
                                <li>21'-6" (feet and inches)</li>
                                <li>21.5 (decimal feet)</li>
                            </ul>
                        </div>
                    </div>
                )}

                <DialogFooter className="gap-2">
                    {step === 'choose' && (
                        <>
                            <Button
                                variant="outline"
                                onClick={() => handleOpenChange(false)}
                                className="border-neutral-700 text-white hover:bg-neutral-800 font-mono uppercase"
                            >
                                Cancel
                            </Button>
                            <Button
                                onClick={handleStartDrawing}
                                className="bg-amber-500 hover:bg-amber-400 text-black font-mono uppercase"
                            >
                                Start Drawing
                            </Button>
                        </>
                    )}
                    {step === 'enter-distance' && (
                        <>
                            <Button
                                variant="outline"
                                onClick={handleRedraw}
                                className="border-neutral-700 text-white hover:bg-neutral-800 font-mono uppercase"
                            >
                                Redraw Line
                            </Button>
                            <Button
                                onClick={handleSubmit}
                                disabled={!realDistance || !parseDistance(realDistance) || isSubmitting}
                                className="bg-green-500 hover:bg-green-400 text-black font-mono uppercase"
                            >
                                {isSubmitting ? 'Calibrating...' : 'Set Scale'}
                            </Button>
                        </>
                    )}
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
