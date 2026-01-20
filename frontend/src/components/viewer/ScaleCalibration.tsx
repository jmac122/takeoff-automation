import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Ruler, Check, Copy } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import { apiClient } from '../../api/client';

interface ScaleCalibrationProps {
    pageId: string;
    currentScale: number | null;
    scaleText: string | null;
    isCalibrated: boolean;
    onCalibrationStart: () => void;
    onCalibrationEnd: () => void;
    calibrationLine: { start: { x: number; y: number }; end: { x: number; y: number } } | null;
}

export function ScaleCalibration({
    pageId,
    currentScale,
    scaleText,
    isCalibrated,
    onCalibrationStart,
    onCalibrationEnd,
    calibrationLine,
}: ScaleCalibrationProps) {
    const [isDialogOpen, setIsDialogOpen] = useState(false);
    const [realDistance, setRealDistance] = useState('');
    const [unit, setUnit] = useState('foot');
    const queryClient = useQueryClient();

    const calibrateMutation = useMutation({
        mutationFn: async (data: {
            pixelDistance: number;
            realDistance: number;
            realUnit: string;
        }) => {
            const response = await apiClient.post(`/pages/${pageId}/calibrate`, null, {
                params: {
                    pixel_distance: data.pixelDistance,
                    real_distance: data.realDistance,
                    real_unit: data.realUnit,
                },
            });
            return response.data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['page', pageId] });
            setIsDialogOpen(false);
            onCalibrationEnd();
            setRealDistance('');
        },
    });

    const handleStartCalibration = () => {
        onCalibrationStart();
    };

    const handleCalibrationComplete = () => {
        if (calibrationLine) {
            const dx = calibrationLine.end.x - calibrationLine.start.x;
            const dy = calibrationLine.end.y - calibrationLine.start.y;
            const pixelDistance = Math.sqrt(dx * dx + dy * dy);

            if (pixelDistance > 10) {
                setIsDialogOpen(true);
            }
        }
    };

    const handleSubmitCalibration = () => {
        if (!calibrationLine || !realDistance) return;

        const dx = calibrationLine.end.x - calibrationLine.start.x;
        const dy = calibrationLine.end.y - calibrationLine.start.y;
        const pixelDistance = Math.sqrt(dx * dx + dy * dy);

        calibrateMutation.mutate({
            pixelDistance,
            realDistance: parseFloat(realDistance),
            realUnit: unit,
        });
    };

    const handleCancel = () => {
        setIsDialogOpen(false);
        onCalibrationEnd();
        setRealDistance('');
    };

    return (
        <div className="flex items-center gap-2">
            {/* Current scale display */}
            <div className="flex items-center gap-2 px-3 py-1.5 bg-muted rounded-md">
                <Ruler className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm">
                    {isCalibrated ? (
                        <>
                            <span className="font-medium">{scaleText || 'Calibrated'}</span>
                            {currentScale && (
                                <span className="text-muted-foreground ml-1">
                                    ({currentScale.toFixed(1)} px/ft)
                                </span>
                            )}
                        </>
                    ) : (
                        <span className="text-amber-600">Not calibrated</span>
                    )}
                </span>
                {isCalibrated && (
                    <Check className="h-4 w-4 text-green-600" />
                )}
            </div>

            {/* Calibration button */}
            <Button
                variant="outline"
                size="sm"
                onClick={handleStartCalibration}
            >
                <Ruler className="h-4 w-4 mr-1" />
                {isCalibrated ? 'Recalibrate' : 'Calibrate'}
            </Button>

            {/* Show "Done" button when in calibration mode with a line drawn */}
            {calibrationLine && (
                <Button
                    variant="default"
                    size="sm"
                    onClick={handleCalibrationComplete}
                >
                    <Check className="h-4 w-4 mr-1" />
                    Done
                </Button>
            )}

            {/* Calibration dialog */}
            <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
                <DialogContent className="sm:max-w-[425px]">
                    <DialogHeader>
                        <DialogTitle>Calibrate Scale</DialogTitle>
                        <DialogDescription>
                            Enter the real-world distance of the line you drew.
                        </DialogDescription>
                    </DialogHeader>

                    <div className="space-y-4 py-4">
                        <div className="flex items-end gap-2">
                            <div className="flex-1">
                                <Label htmlFor="distance">Distance</Label>
                                <Input
                                    id="distance"
                                    type="number"
                                    step="0.1"
                                    min="0"
                                    value={realDistance}
                                    onChange={(e) => setRealDistance(e.target.value)}
                                    placeholder="e.g., 10"
                                />
                            </div>
                            <div className="w-32">
                                <Label htmlFor="unit">Unit</Label>
                                <Select value={unit} onValueChange={setUnit}>
                                    <SelectTrigger id="unit">
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="foot">Feet</SelectItem>
                                        <SelectItem value="inch">Inches</SelectItem>
                                        <SelectItem value="meter">Meters</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>

                        <p className="text-sm text-muted-foreground">
                            Tip: Use a dimension line or a known wall length for best accuracy.
                        </p>
                    </div>

                    <DialogFooter>
                        <Button variant="outline" onClick={handleCancel}>
                            Cancel
                        </Button>
                        <Button
                            onClick={handleSubmitCalibration}
                            disabled={!realDistance || calibrateMutation.isPending}
                        >
                            {calibrateMutation.isPending ? 'Calibrating...' : 'Apply'}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}

// Component for copying scale from another page
interface CopyScaleButtonProps {
    pageId: string;
    pages: Array<{
        id: string;
        page_number: number;
        scale_calibrated: boolean;
        scale_text: string | null;
    }>;
}

export function CopyScaleButton({ pageId, pages }: CopyScaleButtonProps) {
    const [isOpen, setIsOpen] = useState(false);
    const queryClient = useQueryClient();

    const copyMutation = useMutation({
        mutationFn: async (sourcePageId: string) => {
            const response = await apiClient.post(
                `/pages/${pageId}/copy-scale-from/${sourcePageId}`
            );
            return response.data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['page', pageId] });
            setIsOpen(false);
        },
    });

    const calibratedPages = pages.filter(
        (p) => p.scale_calibrated && p.id !== pageId
    );

    if (calibratedPages.length === 0) return null;

    return (
        <>
            <Button variant="ghost" size="sm" onClick={() => setIsOpen(true)}>
                <Copy className="h-4 w-4 mr-1" />
                Copy from...
            </Button>

            <Dialog open={isOpen} onOpenChange={setIsOpen}>
                <DialogContent className="sm:max-w-[425px]">
                    <DialogHeader>
                        <DialogTitle>Copy Scale From Page</DialogTitle>
                        <DialogDescription>
                            Select a calibrated page to copy its scale settings.
                        </DialogDescription>
                    </DialogHeader>

                    <div className="space-y-2 py-4 max-h-64 overflow-auto">
                        {calibratedPages.map((page) => (
                            <Button
                                key={page.id}
                                variant="outline"
                                onClick={() => copyMutation.mutate(page.id)}
                                disabled={copyMutation.isPending}
                                className="w-full justify-between"
                            >
                                <span>Page {page.page_number}</span>
                                <span className="text-sm text-muted-foreground">
                                    {page.scale_text || 'Calibrated'}
                                </span>
                            </Button>
                        ))}
                    </div>

                    <DialogFooter>
                        <Button variant="outline" onClick={() => setIsOpen(false)}>
                            Close
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </>
    );
}
