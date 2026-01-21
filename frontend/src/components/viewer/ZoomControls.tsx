import { ZoomIn, ZoomOut, Maximize2, Minimize, Maximize } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface ZoomControlsProps {
    zoom: number;
    isFullscreen: boolean;
    onZoomIn: () => void;
    onZoomOut: () => void;
    onFitToScreen: () => void;
    onActualSize: () => void;
    onToggleFullscreen: () => void;
}

export function ZoomControls({
    zoom,
    isFullscreen,
    onZoomIn,
    onZoomOut,
    onFitToScreen,
    onActualSize,
    onToggleFullscreen,
}: ZoomControlsProps) {
    return (
        <div className="flex items-center gap-2">
            <Button
                variant="outline"
                size="sm"
                onClick={onZoomOut}
                className="border-neutral-700 text-white hover:bg-neutral-800"
                title="Zoom Out"
            >
                <ZoomOut className="w-4 h-4" />
            </Button>
            <span className="text-sm font-medium w-16 text-center text-white font-mono">
                {(zoom * 100).toFixed(0)}%
            </span>
            <Button
                variant="outline"
                size="sm"
                onClick={onZoomIn}
                className="border-neutral-700 text-white hover:bg-neutral-800"
                title="Zoom In"
            >
                <ZoomIn className="w-4 h-4" />
            </Button>

            <div className="h-6 w-px bg-neutral-700 mx-1" />

            <Button
                variant="outline"
                size="sm"
                onClick={onFitToScreen}
                className="border-neutral-700 text-white hover:bg-neutral-800"
                title="Fit to Screen"
            >
                <Maximize2 className="w-4 h-4" />
            </Button>
            <Button
                variant="outline"
                size="sm"
                onClick={onActualSize}
                className="border-neutral-700 text-white hover:bg-neutral-800 text-xs px-2"
                title="Actual Size (100%)"
            >
                1:1
            </Button>

            <div className="h-6 w-px bg-neutral-700 mx-1" />
            <Button
                variant="outline"
                size="sm"
                onClick={onToggleFullscreen}
                className="border-neutral-700 text-white hover:bg-neutral-800"
                title={isFullscreen ? 'Exit Maximize' : 'Maximize'}
            >
                {isFullscreen ? (
                    <Minimize className="w-4 h-4" />
                ) : (
                    <Maximize className="w-4 h-4" />
                )}
            </Button>
        </div>
    );
}
