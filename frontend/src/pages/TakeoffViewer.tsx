import { useState, useRef, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Stage, Layer, Image as KonvaImage, Rect } from 'react-konva';
import { ChevronLeft, ZoomIn, ZoomOut, Ruler, Maximize, Minimize, Loader2 } from 'lucide-react';
import Konva from 'konva';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import { apiClient } from '@/api/client';
import { scaleApi } from '@/api/scale';
import { DrawingToolbar } from '@/components/viewer/DrawingToolbar';
import { MeasurementLayer } from '@/components/viewer/MeasurementLayer';
import { DrawingPreviewLayer } from '@/components/viewer/DrawingPreviewLayer';
import { useDrawingState } from '@/hooks/useDrawingState';
import type { Page, Measurement, Condition } from '@/types';
import { parseScaleText, validateScaleText } from '@/utils/scaleParser';

export function TakeoffViewer() {
    const { pageId } = useParams<{ documentId: string; pageId: string }>();
    const navigate = useNavigate();
    const queryClient = useQueryClient();

    // Canvas state
    const stageRef = useRef<any>(null);
    const [image, setImage] = useState<HTMLImageElement | null>(null);
    const [stageSize, setStageSize] = useState({ width: 0, height: 0 });
    const [zoom, setZoom] = useState(1);
    const [pan, setPan] = useState({ x: 0, y: 0 });

    // Pan state
    const [isPanning, setIsPanning] = useState(false);
    const [panStart, setPanStart] = useState({ x: 0, y: 0 });
    const [panStartPos, setPanStartPos] = useState({ x: 0, y: 0 });

    // Drawing state
    const drawing = useDrawingState();
    const [selectedConditionId, setSelectedConditionId] = useState<string | null>(null);
    const [selectedMeasurementId, setSelectedMeasurementId] = useState<string | null>(null);

    // Scale calibration state
    const [showCalibrationDialog, setShowCalibrationDialog] = useState(false);
    const [scaleText, setScaleText] = useState<string>('');
    const [scaleError, setScaleError] = useState<string | null>(null);

    // Auto-detection state
    const [isDetecting, setIsDetecting] = useState(false);
    const [detectionResult, setDetectionResult] = useState<any>(null);
    const [scaleHighlightBox, setScaleHighlightBox] = useState<{
        x: number;
        y: number;
        width: number;
        height: number;
    } | null>(null);

    // Fullscreen state
    const [isFullscreen, setIsFullscreen] = useState(false);

    // Fetch page data
    const { data: page, isLoading: pageLoading } = useQuery({
        queryKey: ['page', pageId],
        queryFn: async () => {
            const response = await apiClient.get<Page>(`/pages/${pageId}`);
            return response.data;
        },
        enabled: !!pageId,
    });

    // Fetch conditions for the project
    const { data: conditionsData } = useQuery({
        queryKey: ['conditions', page?.document?.project_id],
        queryFn: async () => {
            const response = await apiClient.get(`/projects/${page?.document?.project_id}/conditions`);
            return response.data;
        },
        enabled: !!page?.document?.project_id,
    });

    // Fetch measurements for the page
    const { data: measurementsData } = useQuery({
        queryKey: ['measurements', pageId],
        queryFn: async () => {
            const response = await apiClient.get(`/pages/${pageId}/measurements`);
            return response.data;
        },
        enabled: !!pageId,
    });

    // Create measurement mutation
    const createMeasurementMutation = useMutation({
        mutationFn: async (data: {
            conditionId: string;
            pageId: string;
            geometryType: string;
            geometryData: any;
        }) => {
            const response = await apiClient.post('/measurements', data);
            return response.data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['measurements', pageId] });
            queryClient.invalidateQueries({ queryKey: ['conditions'] });
        },
    });

    // Delete measurement mutation
    const deleteMeasurementMutation = useMutation({
        mutationFn: async (measurementId: string) => {
            await apiClient.delete(`/measurements/${measurementId}`);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['measurements', pageId] });
            setSelectedMeasurementId(null);
        },
    });

    // Load page image
    useEffect(() => {
        if (page?.image_url) {
            const img = new window.Image();
            img.crossOrigin = 'anonymous';
            img.src = page.image_url;
            img.onload = () => {
                setImage(img);
                // Fit image to viewport - prioritize width for plan sets
                const container = document.getElementById('canvas-container');
                if (container) {
                    // For wide plan sets, fit to width first
                    const widthScale = container.clientWidth / img.width;
                    const heightScale = container.clientHeight / img.height;

                    // Use width scale if image is wider than tall (typical for plan sets)
                    const isHorizontalPlan = img.width > img.height;
                    const scale = isHorizontalPlan
                        ? Math.min(widthScale, 1)  // Fit to width, max 100%
                        : Math.min(widthScale, heightScale, 1);  // Fit to container

                    setZoom(scale);
                    setStageSize({
                        width: container.clientWidth,
                        height: container.clientHeight,
                    });
                }
            };
        }
    }, [page?.image_url]);

    // Handle window resize
    useEffect(() => {
        const handleResize = () => {
            const container = document.getElementById('canvas-container');
            if (container) {
                const newWidth = container.clientWidth;
                const newHeight = container.clientHeight;

                // Only update if size actually changed to avoid unnecessary re-renders
                setStageSize(prev => {
                    if (prev.width !== newWidth || prev.height !== newHeight) {
                        return {
                            width: newWidth,
                            height: newHeight,
                        };
                    }
                    return prev;
                });
            }
        };

        // Initial size calculation
        handleResize();

        // Use ResizeObserver for more accurate container size tracking
        const container = document.getElementById('canvas-container');
        if (container) {
            const resizeObserver = new ResizeObserver(() => {
                handleResize();
            });
            resizeObserver.observe(container);

            // Also listen to window resize as fallback
            window.addEventListener('resize', handleResize);

            return () => {
                resizeObserver.disconnect();
                window.removeEventListener('resize', handleResize);
            };
        } else {
            // Fallback to window resize only if container not found
            window.addEventListener('resize', handleResize);
            return () => window.removeEventListener('resize', handleResize);
        }
    }, []);

    // Fullscreen handlers
    const toggleFullscreen = async () => {
        try {
            if (!document.fullscreenElement) {
                await document.documentElement.requestFullscreen();
                setIsFullscreen(true);
            } else {
                await document.exitFullscreen();
                setIsFullscreen(false);
            }
        } catch (error) {
            console.error('Error toggling fullscreen:', error);
        }
    };

    // Listen for fullscreen changes (user might exit via ESC key)
    useEffect(() => {
        const handleFullscreenChange = () => {
            setIsFullscreen(!!document.fullscreenElement);
        };

        document.addEventListener('fullscreenchange', handleFullscreenChange);
        return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
    }, []);

    // Keyboard shortcuts
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            // Fullscreen toggle (F11)
            if (e.key === 'F11') {
                e.preventDefault();
                toggleFullscreen();
                return;
            }

            // Tool shortcuts
            if (e.key === 'v') drawing.setTool('select');
            if (e.key === 'l') drawing.setTool('line');
            if (e.key === 'p') drawing.setTool('polyline');
            if (e.key === 'g') drawing.setTool('polygon');
            if (e.key === 'r') drawing.setTool('rectangle');
            if (e.key === 'c') drawing.setTool('circle');
            if (e.key === 'm') drawing.setTool('point');

            // Undo/Redo
            if (e.ctrlKey && e.key === 'z') drawing.undo();
            if (e.ctrlKey && e.key === 'y') drawing.redo();

            // Delete
            if (e.key === 'Delete' && selectedMeasurementId) {
                deleteMeasurementMutation.mutate(selectedMeasurementId);
            }

            // Escape - cancel drawing
            if (e.key === 'Escape') {
                drawing.cancelDrawing();
                setSelectedMeasurementId(null);
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [drawing, selectedMeasurementId]);

    // Handle canvas mouse events
    const handleStageMouseDown = (e: Konva.KonvaEventObject<MouseEvent>) => {
        const stage = e.target.getStage();
        if (!stage) return;

        const pointerPos = stage.getPointerPosition();
        if (!pointerPos) return;

        // Check mouse button: right click (2) or middle mouse (1) = pan
        // Left click (0) = pan if no drawing tool active, or draw if tool is active
        const isRightClick = e.evt.button === 2;
        const isMiddleClick = e.evt.button === 1;
        const isLeftClick = e.evt.button === 0;

        // Right click or middle mouse = always pan
        if (isRightClick || isMiddleClick) {
            e.evt.preventDefault(); // Prevent context menu
            setIsPanning(true);
            setPanStart({ x: pointerPos.x, y: pointerPos.y });
            setPanStartPos({ x: pan.x, y: pan.y });
            stage.draggable(false); // Disable Konva's built-in drag
            return;
        }

        // Left click: pan if no drawing tool, or draw if tool is active
        if (isLeftClick) {
            // If drawing tool is active (not select, not null), handle drawing
            if (drawing.tool && drawing.tool !== 'select') {
                const point = {
                    x: (pointerPos.x - pan.x) / zoom,
                    y: (pointerPos.y - pan.y) / zoom,
                };

                if (!selectedConditionId) {
                    alert('Please select a condition first');
                    return;
                }

                // Handle point tool (immediate creation)
                if (drawing.tool === 'point') {
                    createMeasurementMutation.mutate({
                        conditionId: selectedConditionId,
                        pageId: pageId!,
                        geometryType: 'point',
                        geometryData: { x: point.x, y: point.y },
                    });
                    return;
                }

                // Start or continue drawing
                if (!drawing.isDrawing) {
                    drawing.startDrawing(point);
                } else {
                    drawing.addPoint(point);

                    // Auto-finish for line (2 points)
                    if (drawing.tool === 'line' && drawing.points.length === 1) {
                        const result = drawing.finishDrawing();
                        createMeasurement(result);
                    }
                }
                return;
            }

            // If select tool or no tool, allow panning with left click
            setIsPanning(true);
            setPanStart({ x: pointerPos.x, y: pointerPos.y });
            setPanStartPos({ x: pan.x, y: pan.y });
            stage.draggable(false);

            // If select tool, handle selection
            if (drawing.tool === 'select') {
                if (e.target === e.target.getStage()) {
                    setSelectedMeasurementId(null);
                }
            }
        }
    };

    const handleStageMouseMove = (e: Konva.KonvaEventObject<MouseEvent>) => {
        const stage = e.target.getStage();
        if (!stage) return;

        const pointerPos = stage.getPointerPosition();
        if (!pointerPos) return;

        // Handle panning
        if (isPanning) {
            const dx = pointerPos.x - panStart.x;
            const dy = pointerPos.y - panStart.y;
            setPan({
                x: panStartPos.x + dx,
                y: panStartPos.y + dy,
            });
            return;
        }

        // Handle drawing preview
        if (drawing.isDrawing) {
            const point = {
                x: (pointerPos.x - pan.x) / zoom,
                y: (pointerPos.y - pan.y) / zoom,
            };
            drawing.updatePreview(point);
        }
    };

    const handleStageMouseUp = (e: Konva.KonvaEventObject<MouseEvent>) => {
        const stage = e.target.getStage();

        // End panning
        if (isPanning) {
            setIsPanning(false);
            if (stage) {
                stage.draggable(false); // Keep disabled, we handle panning manually
            }
        }

        // Auto-finish for rectangle and circle on mouse up
        if (drawing.tool === 'rectangle' || drawing.tool === 'circle') {
            if (drawing.isDrawing && drawing.points.length > 0) {
                const result = drawing.finishDrawing();
                createMeasurement(result);
            }
        }
    };

    // Stop panning if mouse leaves the stage
    const handleStageMouseLeave = () => {
        if (isPanning) {
            setIsPanning(false);
        }
    };

    // Handle mouse wheel zoom
    const handleWheel = (e: Konva.KonvaEventObject<WheelEvent>) => {
        e.evt.preventDefault();

        const stage = e.target.getStage();
        if (!stage) return;

        const pointerPos = stage.getPointerPosition();
        if (!pointerPos) return;

        // Get mouse position relative to stage
        const mouseX = pointerPos.x;
        const mouseY = pointerPos.y;

        // Calculate zoom factor
        const scaleBy = 1.1;
        const oldZoom = zoom;
        const newZoom = e.evt.deltaY > 0
            ? Math.max(0.1, oldZoom / scaleBy)  // Zoom out
            : Math.min(5, oldZoom * scaleBy);     // Zoom in

        // Calculate zoom point in image coordinates
        const imageX = (mouseX - pan.x) / oldZoom;
        const imageY = (mouseY - pan.y) / oldZoom;

        // Adjust pan to zoom towards mouse position
        const newPanX = mouseX - imageX * newZoom;
        const newPanY = mouseY - imageY * newZoom;

        setZoom(newZoom);
        setPan({ x: newPanX, y: newPanY });
    };

    const handleStageDoubleClick = () => {
        // Finish polyline or polygon on double-click
        if (drawing.tool === 'polyline' || drawing.tool === 'polygon') {
            if (drawing.isDrawing && drawing.points.length >= 2) {
                const result = drawing.finishDrawing();
                createMeasurement(result);
            }
        }
    };

    const createMeasurement = (result: any) => {
        if (!selectedConditionId || !pageId) return;

        let geometryData: any;

        switch (result.tool) {
            case 'line':
                geometryData = {
                    start: result.points[0],
                    end: result.points[1],
                };
                break;
            case 'polyline':
                geometryData = { points: result.points };
                break;
            case 'polygon':
                geometryData = { points: result.points };
                break;
            case 'rectangle':
                geometryData = result.previewShape?.data;
                break;
            case 'circle':
                geometryData = result.previewShape?.data;
                break;
            default:
                return;
        }

        createMeasurementMutation.mutate({
            conditionId: selectedConditionId,
            pageId,
            geometryType: result.tool,
            geometryData,
        });
    };

    const handleScaleSubmit = async () => {
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
            await apiClient.put(`/pages/${pageId}/scale`, {
                scale_value: parsed.pixelsPerFoot,
                scale_unit: 'foot',
                scale_text: scaleText,
            });

            // Refetch page data
            queryClient.invalidateQueries({ queryKey: ['page', pageId] });

            // Reset state
            setShowCalibrationDialog(false);
            setScaleText('');
            setScaleError(null);
        } catch (error) {
            console.error('Scale update failed:', error);
            setScaleError('Failed to set scale. Please try again.');
        }
    };

    const handleZoomIn = () => setZoom((z) => Math.min(z * 1.2, 5));
    const handleZoomOut = () => setZoom((z) => Math.max(z / 1.2, 0.1));

    // Auto-detect scale function
    const detectScale = async () => {
        setIsDetecting(true);
        setDetectionResult(null);
        setScaleHighlightBox(null);

        try {
            // Trigger detection
            await scaleApi.detectScale(pageId!);

            // Poll for completion
            let attempts = 0;
            const maxAttempts = 10; // 5 seconds max (500ms * 10)

            while (attempts < maxAttempts) {
                await new Promise(resolve => setTimeout(resolve, 500));

                const status = await scaleApi.getDetectionStatus(pageId!);

                if (status.status === 'complete') {
                    setIsDetecting(false);

                    // Set detection result
                    if (status.detection) {
                        setDetectionResult(status.detection);

                        // Find bounding box for highlight
                        if (status.detection.best_scale && (page as any)?.ocr_blocks?.blocks) {
                            const scaleText = status.detection.best_scale.text;
                            const matchingBlock = (page as any).ocr_blocks.blocks.find(
                                (block: any) => block.text && block.text.includes(scaleText)
                            );

                            if (matchingBlock?.bbox) {
                                setScaleHighlightBox({
                                    x: matchingBlock.bbox.x0,
                                    y: matchingBlock.bbox.y0,
                                    width: matchingBlock.bbox.x1 - matchingBlock.bbox.x0,
                                    height: matchingBlock.bbox.y1 - matchingBlock.bbox.y0,
                                });
                            }
                        }
                    }

                    // Refetch page to update UI
                    queryClient.invalidateQueries({ queryKey: ['page', pageId] });

                    return;
                }

                attempts++;
            }

            // Timeout
            setIsDetecting(false);
            alert('Scale detection timed out. Please try again.');

        } catch (error) {
            console.error('Scale detection failed:', error);
            setIsDetecting(false);
            alert('Scale detection failed. Please try again.');
        }
    };

    const conditions = conditionsData?.conditions || [];
    const measurements = measurementsData?.measurements || [];
    const selectedCondition = conditions.find((c: Condition) => c.id === selectedConditionId);

    if (pageLoading) {
        return <div className="flex items-center justify-center h-screen bg-neutral-950 text-white font-mono">LOADING...</div>;
    }

    return (
        <div className="flex flex-col h-screen bg-neutral-950 w-full" style={{ width: '100vw', maxWidth: 'none', margin: 0, padding: 0 }}>
            {/* Header */}
            <div className="flex items-center gap-4 p-4 border-b border-neutral-700 bg-neutral-900">
                <Button variant="ghost" size="sm" onClick={() => navigate(-1)} className="text-white hover:bg-neutral-800">
                    <ChevronLeft className="w-4 h-4 mr-2" />
                    Back
                </Button>

                <div className="flex-1">
                    <h1 className="text-lg font-semibold text-white">{page?.page_label || 'Page'}</h1>
                    <p className="text-sm text-neutral-400 font-mono">
                        {page?.scale_calibrated ? `Scale: ${page.scale_value} px/ft` : 'Scale not calibrated'}
                    </p>
                </div>

                {/* Zoom controls */}
                <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm" onClick={handleZoomOut} className="border-neutral-700 text-white hover:bg-neutral-800">
                        <ZoomOut className="w-4 h-4" />
                    </Button>
                    <span className="text-sm font-medium w-16 text-center text-white font-mono">
                        {(zoom * 100).toFixed(0)}%
                    </span>
                    <Button variant="outline" size="sm" onClick={handleZoomIn} className="border-neutral-700 text-white hover:bg-neutral-800">
                        <ZoomIn className="w-4 h-4" />
                    </Button>

                    {/* Fullscreen toggle */}
                    <div className="h-6 w-px bg-neutral-700 mx-1" />
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={toggleFullscreen}
                        className="border-neutral-700 text-white hover:bg-neutral-800"
                        title={isFullscreen ? 'Exit Fullscreen (F11)' : 'Enter Fullscreen (F11)'}
                    >
                        {isFullscreen ? (
                            <Minimize className="w-4 h-4" />
                        ) : (
                            <Maximize className="w-4 h-4" />
                        )}
                    </Button>
                </div>
            </div>

            {/* Main content - Full width canvas */}
            <div className="flex flex-1 overflow-hidden bg-neutral-900 w-full">
                {/* Canvas - Full width */}
                <div className="flex-1 flex flex-col w-full min-w-0">
                    {/* Drawing Toolbar */}
                    <div className="p-4 bg-neutral-800 border-b border-neutral-700">
                        <div className="flex items-center gap-2">
                            <DrawingToolbar
                                activeTool={drawing.tool}
                                onToolChange={(tool) => {
                                    drawing.setTool(tool);
                                }}
                                canUndo={drawing.canUndo}
                                canRedo={drawing.canRedo}
                                onUndo={drawing.undo}
                                onRedo={drawing.redo}
                                onDelete={() => {
                                    if (selectedMeasurementId) {
                                        deleteMeasurementMutation.mutate(selectedMeasurementId);
                                    }
                                }}
                                hasSelection={!!selectedMeasurementId}
                                disabled={!page?.scale_calibrated}
                            />

                            {/* Scale Buttons */}
                            <div className="h-6 w-px bg-neutral-700" />
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={detectScale}
                                disabled={isDetecting}
                                className="text-white hover:bg-neutral-800 border-neutral-700 font-mono uppercase"
                            >
                                {isDetecting ? (
                                    <>
                                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                        Detecting...
                                    </>
                                ) : (
                                    <>
                                        <Ruler className="h-4 w-4 mr-2" />
                                        Auto Detect Scale
                                    </>
                                )}
                            </Button>
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => {
                                    setShowCalibrationDialog(true);
                                    setScaleText((page as any)?.scale_text || '');
                                    setScaleError(null);
                                }}
                                className="text-white hover:bg-neutral-800 border-neutral-700 font-mono uppercase"
                            >
                                <Ruler className="h-4 w-4 mr-2" />
                                Set Scale
                            </Button>
                        </div>
                    </div>

                    {/* Detection Result Display */}
                    {detectionResult && detectionResult.best_scale && (
                        <div className="px-4 py-2 bg-neutral-800 border-b border-neutral-700">
                            <div className="flex items-center gap-3">
                                <div className="text-xs font-mono text-amber-500 uppercase tracking-wider">
                                    Detected:
                                </div>
                                <div className="text-sm font-mono text-white font-bold">
                                    {detectionResult.best_scale.text}
                                </div>
                                <div className="text-xs font-mono text-neutral-400">
                                    ({(detectionResult.best_scale.confidence * 100).toFixed(0)}% confidence)
                                </div>
                                <div className="flex-1" />
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => {
                                        setDetectionResult(null);
                                        setScaleHighlightBox(null);
                                    }}
                                    className="text-neutral-500 hover:text-white h-6 w-6 p-0"
                                >
                                    ✕
                                </Button>
                            </div>
                        </div>
                    )}

                    {/* Canvas */}
                    <div
                        id="canvas-container"
                        className="flex-1 relative flex items-center justify-center w-full h-full"
                        style={{ minWidth: 0, minHeight: 0 }}
                        onContextMenu={(e) => e.preventDefault()} // Prevent context menu on right click
                    >
                        <Stage
                            ref={stageRef}
                            width={stageSize.width}
                            height={stageSize.height}
                            scaleX={zoom}
                            scaleY={zoom}
                            x={pan.x}
                            y={pan.y}
                            draggable={false}
                            onClick={handleStageMouseDown}
                            onMouseDown={handleStageMouseDown}
                            onMouseMove={handleStageMouseMove}
                            onMouseUp={handleStageMouseUp}
                            onMouseLeave={handleStageMouseLeave}
                            onDblClick={handleStageDoubleClick}
                            onWheel={handleWheel}
                            style={{
                                cursor: isPanning
                                    ? 'grabbing'
                                    : drawing.isDrawing
                                        ? 'crosshair'
                                        : 'grab'
                            }}
                        >
                            {/* Background image */}
                            <Layer>
                                {image && <KonvaImage image={image} />}
                            </Layer>

                            {/* Measurements */}
                            {page && (
                                <MeasurementLayer
                                    measurements={measurements}
                                    conditions={new Map(conditions.map((c: Condition) => [c.id, c]))}
                                    selectedMeasurementId={selectedMeasurementId}
                                    onMeasurementSelect={setSelectedMeasurementId}
                                    onMeasurementUpdate={() => { }}
                                    isEditing={false}
                                    scale={zoom}
                                />
                            )}

                            {/* Drawing preview */}
                            <DrawingPreviewLayer
                                previewShape={drawing.previewShape}
                                points={drawing.points}
                                isDrawing={drawing.isDrawing}
                                color={selectedCondition?.color || '#3B82F6'}
                                scale={zoom}
                            />

                            {/* Scale detection highlight overlay */}
                            {scaleHighlightBox && (
                                <Layer>
                                    <Rect
                                        x={scaleHighlightBox.x}
                                        y={scaleHighlightBox.y}
                                        width={scaleHighlightBox.width}
                                        height={scaleHighlightBox.height}
                                        fill="rgba(251, 191, 36, 0.15)"
                                        stroke="rgb(251, 191, 36)"
                                        strokeWidth={3 / zoom}
                                        listening={false}
                                    />
                                </Layer>
                            )}
                        </Stage>

                        {/* Scale warning */}
                        {!page?.scale_calibrated && (
                            <div className="absolute top-4 left-1/2 transform -translate-x-1/2 bg-amber-500/20 border border-amber-500/50 text-amber-400 px-4 py-2 rounded-lg shadow-lg z-10 font-mono text-sm">
                                ⚠️ Scale not calibrated. Measurements will not be accurate.
                            </div>
                        )}

                        {/* Conditions overlay - Bottom left */}
                        {conditions.length > 0 && (
                            <div className="absolute bottom-4 left-4 bg-neutral-900/95 backdrop-blur border border-neutral-700 rounded-lg shadow-xl p-3 max-w-xs max-h-96 overflow-y-auto z-10">
                                <h2 className="text-sm font-semibold mb-2 text-white font-mono uppercase tracking-wider">Conditions</h2>
                                <div className="space-y-1">
                                    {conditions.map((condition: Condition) => (
                                        <button
                                            key={condition.id}
                                            onClick={() => setSelectedConditionId(condition.id)}
                                            className={`w-full text-left px-3 py-2 rounded transition-colors border ${selectedConditionId === condition.id
                                                ? 'bg-amber-500/20 border-amber-500/50 text-amber-400'
                                                : 'text-neutral-300 hover:bg-neutral-800 border-transparent'
                                                }`}
                                        >
                                            <div className="flex items-center gap-2">
                                                <div
                                                    className="w-3 h-3 rounded flex-shrink-0 border border-neutral-600"
                                                    style={{ backgroundColor: condition.color }}
                                                />
                                                <div className="flex-1 min-w-0">
                                                    <p className="text-sm truncate font-mono">{condition.name}</p>
                                                    <p className="text-xs opacity-75 font-mono">
                                                        {condition.total_quantity.toFixed(1)} {condition.unit}
                                                    </p>
                                                </div>
                                            </div>
                                        </button>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Measurements overlay - Bottom right */}
                        {selectedConditionId && measurements.filter((m: Measurement) => m.condition_id === selectedConditionId).length > 0 && (
                            <div className="absolute bottom-4 right-4 bg-neutral-900/95 backdrop-blur border border-neutral-700 rounded-lg shadow-xl p-3 max-w-xs max-h-96 overflow-y-auto z-10">
                                <h2 className="text-sm font-semibold mb-2 text-white font-mono uppercase tracking-wider">Measurements</h2>
                                <div className="space-y-1">
                                    {measurements
                                        .filter((m: Measurement) => m.condition_id === selectedConditionId)
                                        .map((measurement: Measurement) => (
                                            <div
                                                key={measurement.id}
                                                onClick={() => setSelectedMeasurementId(measurement.id)}
                                                className={`px-3 py-2 rounded cursor-pointer transition-colors border ${selectedMeasurementId === measurement.id
                                                    ? 'bg-amber-500/20 border-amber-500/50 text-amber-400'
                                                    : 'text-neutral-300 hover:bg-neutral-800 border-transparent'
                                                    }`}
                                            >
                                                <p className="text-xs opacity-75 font-mono uppercase">{measurement.geometry_type}</p>
                                                <p className="text-sm font-bold font-mono">
                                                    {measurement.quantity.toFixed(1)} {measurement.unit}
                                                </p>
                                            </div>
                                        ))}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Set Scale Dialog */}
            <Dialog open={showCalibrationDialog} onOpenChange={setShowCalibrationDialog}>
                <DialogContent className="bg-neutral-900 border-neutral-700">
                    <DialogHeader>
                        <DialogTitle className="text-white uppercase tracking-tight font-mono">
                            Set Scale
                        </DialogTitle>
                        <DialogDescription className="text-neutral-400 font-mono text-sm">
                            Enter the scale from the drawing (e.g., "3/32" = 1'-0"" or "1/4" = 1'-0"")
                        </DialogDescription>
                    </DialogHeader>

                    <div className="space-y-4 py-4">
                        <div className="space-y-2">
                            <Label htmlFor="scale-text" className="text-neutral-400 font-mono text-xs uppercase">
                                Scale Text
                            </Label>
                            <Input
                                id="scale-text"
                                type="text"
                                value={scaleText}
                                onChange={(e) => {
                                    setScaleText(e.target.value);
                                    setScaleError(null);
                                }}
                                placeholder="e.g., 3/32 inch = 1 foot or 1/4 inch = 1 foot"
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
                            onClick={() => {
                                setShowCalibrationDialog(false);
                                setScaleText('');
                                setScaleError(null);
                            }}
                            className="border-neutral-700 text-white hover:bg-neutral-800 font-mono uppercase"
                        >
                            Cancel
                        </Button>
                        <Button
                            onClick={handleScaleSubmit}
                            disabled={!scaleText || !!validateScaleText(scaleText)}
                            className="bg-amber-500 hover:bg-amber-400 text-black font-mono uppercase"
                        >
                            Set Scale
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}
