import { useState, useEffect, useCallback } from 'react';

export interface Size {
    width: number;
    height: number;
}

export interface Position {
    x: number;
    y: number;
}

interface UseCanvasControlsOptions {
    image: HTMLImageElement | null;
    containerId: string;
}

export function useCanvasControls({ image, containerId }: UseCanvasControlsOptions) {
    const [zoom, setZoom] = useState(1);
    const [pan, setPan] = useState<Position>({ x: 0, y: 0 });
    const [stageSize, setStageSize] = useState<Size>({ width: 0, height: 0 });

    // Initialize stage size and fit image on load
    useEffect(() => {
        if (image && image.complete) {
            const container = document.getElementById(containerId);
            if (container) {
                const widthScale = container.clientWidth / image.width;
                const heightScale = container.clientHeight / image.height;
                const isHorizontalPlan = image.width > image.height;
                const scale = isHorizontalPlan
                    ? Math.min(widthScale, 1)
                    : Math.min(widthScale, heightScale, 1);

                setZoom(scale);
                setStageSize({
                    width: container.clientWidth,
                    height: container.clientHeight,
                });
            }
        }
    }, [image, containerId]);

    // Handle window resize
    useEffect(() => {
        const handleResize = () => {
            const container = document.getElementById(containerId);
            if (container) {
                const newWidth = container.clientWidth;
                const newHeight = container.clientHeight;

                setStageSize(prev => {
                    if (prev.width !== newWidth || prev.height !== newHeight) {
                        return { width: newWidth, height: newHeight };
                    }
                    return prev;
                });
            }
        };

        handleResize();

        const container = document.getElementById(containerId);
        if (container) {
            const resizeObserver = new ResizeObserver(handleResize);
            resizeObserver.observe(container);
            window.addEventListener('resize', handleResize);

            return () => {
                resizeObserver.disconnect();
                window.removeEventListener('resize', handleResize);
            };
        } else {
            window.addEventListener('resize', handleResize);
            return () => window.removeEventListener('resize', handleResize);
        }
    }, [containerId]);

    const handleZoomIn = useCallback(() => {
        setZoom(z => Math.min(z * 1.2, 5));
    }, []);

    const handleZoomOut = useCallback(() => {
        setZoom(z => Math.max(z / 1.2, 0.1));
    }, []);

    const handleFitToScreen = useCallback(() => {
        if (!image || !stageSize.width || !stageSize.height) return;

        const scaleX = stageSize.width / image.width;
        const scaleY = stageSize.height / image.height;
        const newZoom = Math.min(scaleX, scaleY) * 0.95;

        setZoom(newZoom);
        setPan({ x: 0, y: 0 });
    }, [image, stageSize]);

    const handleActualSize = useCallback(() => {
        setZoom(1);
        setPan({ x: 0, y: 0 });
    }, []);

    const handleWheel = useCallback((e: WheelEvent, pointerPos: Position) => {
        e.preventDefault();

        const scaleBy = 1.1;
        const oldZoom = zoom;
        const newZoom = e.deltaY > 0
            ? Math.max(0.1, oldZoom / scaleBy)
            : Math.min(5, oldZoom * scaleBy);

        const imageX = (pointerPos.x - pan.x) / oldZoom;
        const imageY = (pointerPos.y - pan.y) / oldZoom;

        const newPanX = pointerPos.x - imageX * newZoom;
        const newPanY = pointerPos.y - imageY * newZoom;

        setZoom(newZoom);
        setPan({ x: newPanX, y: newPanY });
    }, [zoom, pan]);

    return {
        zoom,
        pan,
        setPan,
        stageSize,
        handleZoomIn,
        handleZoomOut,
        handleFitToScreen,
        handleActualSize,
        handleWheel,
    };
}
