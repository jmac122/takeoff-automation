import { ChevronLeft, Ruler, Loader2, MapPin, Crop, Eye, EyeOff } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ZoomControls } from './ZoomControls';
import { AutonomousAITakeoffButton } from '@/components/takeoff/AutonomousAITakeoffButton';
import type { Page } from '@/types';

interface ViewerHeaderProps {
    page: Page | undefined;
    pageId: string | undefined;
    projectId: string | undefined;
    zoom: number;
    isFullscreen: boolean;
    isDetectingScale: boolean;
    scaleLocationVisible: boolean;
    showTitleBlockRegion: boolean;
    isTitleBlockMode: boolean;
    isSavingTitleBlock: boolean;
    onNavigateBack: () => void;
    onZoomIn: () => void;
    onZoomOut: () => void;
    onFitToScreen: () => void;
    onActualSize: () => void;
    onToggleFullscreen: () => void;
    onDetectScale: () => void;
    onSetScale: () => void;
    onToggleScaleLocation: () => void;
    onToggleTitleBlockMode: () => void;
    onToggleTitleBlockRegion: () => void;
    onAutonomousTakeoffComplete?: () => void;
}

export function ViewerHeader({
    page,
    pageId,
    projectId,
    zoom,
    isFullscreen,
    isDetectingScale,
    scaleLocationVisible,
    showTitleBlockRegion,
    isTitleBlockMode,
    isSavingTitleBlock,
    onNavigateBack,
    onZoomIn,
    onZoomOut,
    onFitToScreen,
    onActualSize,
    onToggleFullscreen,
    onDetectScale,
    onSetScale,
    onToggleScaleLocation,
    onToggleTitleBlockMode,
    onToggleTitleBlockRegion,
    onAutonomousTakeoffComplete,
}: ViewerHeaderProps) {
    const hasScaleLocation = page?.scale_calibration_data?.best_scale?.bbox;
    const hasTitleBlockRegion = page?.document?.title_block_region;
    
    // AI Takeoff requires a calibrated scale (manual or auto-detected)
    const isPageCalibrated = Boolean(page?.scale_calibrated && page?.scale_value);
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

            {/* Scale Buttons */}
            <div className="flex items-center gap-2 flex-shrink-0">
                <Button
                    variant="outline"
                    size="sm"
                    onClick={onToggleTitleBlockMode}
                    disabled={isSavingTitleBlock}
                    className={`font-mono uppercase text-xs ${isTitleBlockMode
                        ? 'bg-sky-500/20 text-sky-300 border-sky-400/50 hover:bg-sky-500/30'
                        : 'text-white hover:bg-neutral-800 border-neutral-700'
                        }`}
                    title="Draw the title block region for OCR"
                >
                    <Crop className="h-3 w-3 mr-1" />
                    {isTitleBlockMode ? 'Exit' : 'Title Block'}
                </Button>
                {hasTitleBlockRegion && (
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={onToggleTitleBlockRegion}
                        disabled={isTitleBlockMode}
                        className={`font-mono uppercase text-xs ${showTitleBlockRegion
                            ? 'bg-emerald-500/20 text-emerald-300 border-emerald-400/50 hover:bg-emerald-500/30'
                            : 'text-white hover:bg-neutral-800 border-neutral-700'
                            }`}
                        title="Show or hide the saved title block region"
                    >
                        {showTitleBlockRegion ? <EyeOff className="h-3 w-3 mr-1" /> : <Eye className="h-3 w-3 mr-1" />}
                        {showTitleBlockRegion ? 'Hide' : 'Show'} Region
                    </Button>
                )}
                <Button
                    variant="outline"
                    size="sm"
                    onClick={onDetectScale}
                    disabled={isDetectingScale || isTitleBlockMode}
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
                    disabled={isTitleBlockMode}
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
                        disabled={isTitleBlockMode}
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

            {/* AI Takeoff Button - requires calibrated scale */}
            {pageId && projectId && (
                <AutonomousAITakeoffButton
                    pageId={pageId}
                    projectId={projectId}
                    isPageCalibrated={isPageCalibrated}
                    onComplete={onAutonomousTakeoffComplete}
                />
            )}

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
