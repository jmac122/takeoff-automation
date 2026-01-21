import { ChevronLeft, Ruler, Loader2, MapPin } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ZoomControls } from './ZoomControls';
import { DrawingToolbar } from './DrawingToolbar';
import type { Page } from '@/types';
import type { DrawingTool } from './DrawingToolbar';

interface ViewerHeaderProps {
    page: Page | undefined;
    zoom: number;
    isFullscreen: boolean;
    activeTool: DrawingTool;
    canUndo: boolean;
    canRedo: boolean;
    hasSelection: boolean;
    isDetectingScale: boolean;
    scaleLocationVisible: boolean;
    onNavigateBack: () => void;
    onZoomIn: () => void;
    onZoomOut: () => void;
    onFitToScreen: () => void;
    onActualSize: () => void;
    onToggleFullscreen: () => void;
    onToolChange: (tool: DrawingTool) => void;
    onUndo: () => void;
    onRedo: () => void;
    onDelete: () => void;
    onDetectScale: () => void;
    onSetScale: () => void;
    onToggleScaleLocation: () => void;
}

export function ViewerHeader({
    page,
    zoom,
    isFullscreen,
    activeTool,
    canUndo,
    canRedo,
    hasSelection,
    isDetectingScale,
    scaleLocationVisible,
    onNavigateBack,
    onZoomIn,
    onZoomOut,
    onFitToScreen,
    onActualSize,
    onToggleFullscreen,
    onToolChange,
    onUndo,
    onRedo,
    onDelete,
    onDetectScale,
    onSetScale,
    onToggleScaleLocation,
}: ViewerHeaderProps) {
    const hasScaleLocation = page?.scale_calibration_data?.best_scale?.bbox;
    return (
        <div className="flex items-center gap-4 px-4 py-3 border-b border-neutral-700 bg-neutral-900" style={{ minHeight: '70px' }}>
            {/* Back Button */}
            <Button
                variant="ghost"
                size="sm"
                onClick={onNavigateBack}
                className="text-white hover:bg-neutral-800 flex-shrink-0"
            >
                <ChevronLeft className="w-4 h-4 mr-1" />
                Back
            </Button>

            {/* Visual Separator */}
            <div className="h-10 w-px bg-neutral-700" />

            {/* Sheet Info */}
            <div className="flex-shrink-0">
                <div className="text-base font-bold text-white font-mono">
                    {page?.sheet_number || `Page ${page?.page_number || ''}`}
                </div>
                <div className="text-xs text-neutral-400 font-mono">
                    {page?.scale_text
                        ? `Scale: ${page.scale_text}`
                        : page?.scale_calibrated
                            ? `Scale: ${page.scale_value?.toFixed(2)} px/ft`
                            : 'Scale not calibrated'}
                </div>
            </div>

            {/* Visual Separator */}
            <div className="h-10 w-px bg-neutral-700" />

            {/* Drawing Tools (CENTER) */}
            <div className="flex-1 flex items-center justify-center min-w-0">
                <DrawingToolbar
                    activeTool={activeTool}
                    onToolChange={onToolChange}
                    canUndo={canUndo}
                    canRedo={canRedo}
                    onUndo={onUndo}
                    onRedo={onRedo}
                    onDelete={onDelete}
                    hasSelection={hasSelection}
                    disabled={!page?.scale_calibrated}
                />
            </div>

            {/* Visual Separator */}
            <div className="h-10 w-px bg-neutral-700" />

            {/* Scale Buttons */}
            <div className="flex items-center gap-2 flex-shrink-0">
                <Button
                    variant="outline"
                    size="sm"
                    onClick={onDetectScale}
                    disabled={isDetectingScale}
                    className="text-white hover:bg-neutral-800 border-neutral-700 font-mono uppercase text-xs"
                >
                    {isDetectingScale ? (
                        <>
                            <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                            Detecting...
                        </>
                    ) : (
                        <>
                            <Ruler className="h-3 w-3 mr-1" />
                            Auto Detect
                        </>
                    )}
                </Button>
                <Button
                    variant="outline"
                    size="sm"
                    onClick={onSetScale}
                    className="text-white hover:bg-neutral-800 border-neutral-700 font-mono uppercase text-xs"
                >
                    <Ruler className="h-3 w-3 mr-1" />
                    Set Scale
                </Button>
                {hasScaleLocation && (
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={onToggleScaleLocation}
                        className={`font-mono uppercase text-xs ${scaleLocationVisible
                            ? 'bg-amber-500/20 text-amber-400 border-amber-500/50 hover:bg-amber-500/30'
                            : 'text-white hover:bg-neutral-800 border-neutral-700'
                            }`}
                        title="Show where the scale was detected on the drawing"
                    >
                        <MapPin className="h-3 w-3 mr-1" />
                        {scaleLocationVisible ? 'Hide' : 'Show'} Location
                    </Button>
                )}
            </div>

            {/* Visual Separator */}
            <div className="h-10 w-px bg-neutral-700" />

            {/* Zoom Controls (RIGHT) */}
            <div className="flex-shrink-0">
                <ZoomControls
                    zoom={zoom}
                    isFullscreen={isFullscreen}
                    onZoomIn={onZoomIn}
                    onZoomOut={onZoomOut}
                    onFitToScreen={onFitToScreen}
                    onActualSize={onActualSize}
                    onToggleFullscreen={onToggleFullscreen}
                />
            </div>
        </div>
    );
}
