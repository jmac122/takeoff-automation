import { useState, useRef, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Stage, Layer, Image as KonvaImage } from 'react-konva';
import { ChevronLeft, ZoomIn, ZoomOut } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { apiClient } from '@/api/client';
import { DrawingToolbar } from '@/components/viewer/DrawingToolbar';
import { MeasurementLayer } from '@/components/viewer/MeasurementLayer';
import { DrawingPreviewLayer } from '@/components/viewer/DrawingPreviewLayer';
import { ScaleCalibration } from '@/components/viewer/ScaleCalibration';
import { useDrawingState } from '@/hooks/useDrawingState';
import type { Page, Measurement, Condition } from '@/types';

export function TakeoffViewer() {
    const { pageId } = useParams<{ documentId: string; pageId: string }>();
    const navigate = useNavigate();
    const queryClient = useQueryClient();

    // Canvas state
    const stageRef = useRef<any>(null);
    const [image, setImage] = useState<HTMLImageElement | null>(null);
    const [stageSize, setStageSize] = useState({ width: 0, height: 0 });
    const [zoom, setZoom] = useState(1);
    const [pan] = useState({ x: 0, y: 0 });

    // Drawing state
    const drawing = useDrawingState();
    const [selectedConditionId, setSelectedConditionId] = useState<string | null>(null);
    const [selectedMeasurementId, setSelectedMeasurementId] = useState<string | null>(null);

    // Scale calibration state
    const [isCalibrating, setIsCalibrating] = useState(false);
    const [calibrationLine] = useState<any>(null);

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
                // Fit image to viewport
                const container = document.getElementById('canvas-container');
                if (container) {
                    const scale = Math.min(
                        container.clientWidth / img.width,
                        container.clientHeight / img.height,
                        1
                    );
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
                setStageSize({
                    width: container.clientWidth,
                    height: container.clientHeight,
                });
            }
        };
        window.addEventListener('resize', handleResize);
        handleResize();
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    // Keyboard shortcuts
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
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
    const handleStageMouseDown = (e: any) => {
        // Skip if calibrating
        if (isCalibrating) {
            handleCalibrationClick(e);
            return;
        }

        // Get click position in image coordinates
        const stage = e.target.getStage();
        const pointerPos = stage.getPointerPosition();
        const point = {
            x: (pointerPos.x - pan.x) / zoom,
            y: (pointerPos.y - pan.y) / zoom,
        };

        // Handle different drawing tools
        if (drawing.tool === 'select') {
            // Clicking on canvas deselects
            if (e.target === e.target.getStage()) {
                setSelectedMeasurementId(null);
            }
            return;
        }

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
    };

    const handleStageMouseMove = (e: any) => {
        if (!drawing.isDrawing) return;

        const stage = e.target.getStage();
        const pointerPos = stage.getPointerPosition();
        const point = {
            x: (pointerPos.x - pan.x) / zoom,
            y: (pointerPos.y - pan.y) / zoom,
        };

        drawing.updatePreview(point);
    };

    const handleStageMouseUp = () => {
        // Auto-finish for rectangle and circle on mouse up
        if (drawing.tool === 'rectangle' || drawing.tool === 'circle') {
            if (drawing.isDrawing && drawing.points.length > 0) {
                const result = drawing.finishDrawing();
                createMeasurement(result);
            }
        }
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

    const handleCalibrationClick = (_e: any) => {
        // Implementation depends on ScaleCalibration component
        // This would be similar to Phase 2B scale detection
    };

    const handleZoomIn = () => setZoom((z) => Math.min(z * 1.2, 5));
    const handleZoomOut = () => setZoom((z) => Math.max(z / 1.2, 0.1));

    const conditions = conditionsData?.conditions || [];
    const measurements = measurementsData?.measurements || [];
    const selectedCondition = conditions.find((c: Condition) => c.id === selectedConditionId);

    if (pageLoading) {
        return <div className="flex items-center justify-center h-screen">Loading...</div>;
    }

    return (
        <div className="flex flex-col h-screen">
            {/* Header */}
            <div className="flex items-center gap-4 p-4 border-b bg-white">
                <Button variant="ghost" size="sm" onClick={() => navigate(-1)}>
                    <ChevronLeft className="w-4 h-4 mr-2" />
                    Back
                </Button>

                <div className="flex-1">
                    <h1 className="text-lg font-semibold">{page?.page_label || 'Page'}</h1>
                    <p className="text-sm text-gray-600">
                        {page?.scale_calibrated ? `Scale: ${page.scale_value} px/ft` : 'Scale not calibrated'}
                    </p>
                </div>

                {/* Zoom controls */}
                <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm" onClick={handleZoomOut}>
                        <ZoomOut className="w-4 h-4" />
                    </Button>
                    <span className="text-sm font-medium w-16 text-center">
                        {(zoom * 100).toFixed(0)}%
                    </span>
                    <Button variant="outline" size="sm" onClick={handleZoomIn}>
                        <ZoomIn className="w-4 h-4" />
                    </Button>
                </div>
            </div>

            {/* Main content */}
            <div className="flex flex-1 overflow-hidden">
                {/* Left sidebar - Conditions */}
                <div className="w-80 border-r bg-white p-4 overflow-y-auto">
                    <h2 className="text-sm font-semibold mb-3">Conditions</h2>
                    <div className="space-y-2">
                        {conditions.map((condition: Condition) => (
                            <button
                                key={condition.id}
                                onClick={() => setSelectedConditionId(condition.id)}
                                className={`w-full text-left p-3 rounded-lg border-2 transition-colors ${selectedConditionId === condition.id
                                    ? 'border-blue-500 bg-blue-50'
                                    : 'border-gray-200 hover:border-gray-300'
                                    }`}
                            >
                                <div className="flex items-center gap-2">
                                    <div
                                        className="w-4 h-4 rounded"
                                        style={{ backgroundColor: condition.color }}
                                    />
                                    <div className="flex-1 min-w-0">
                                        <p className="font-medium text-sm truncate">{condition.name}</p>
                                        <p className="text-xs text-gray-600">
                                            {condition.total_quantity.toFixed(1)} {condition.unit}
                                        </p>
                                    </div>
                                </div>
                            </button>
                        ))}
                    </div>
                </div>

                {/* Center - Canvas */}
                <div className="flex-1 flex flex-col bg-gray-100">
                    {/* Drawing Toolbar */}
                    <div className="p-4">
                        <DrawingToolbar
                            activeTool={drawing.tool}
                            onToolChange={drawing.setTool}
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
                    </div>

                    {/* Canvas */}
                    <div id="canvas-container" className="flex-1 relative">
                        <Stage
                            ref={stageRef}
                            width={stageSize.width}
                            height={stageSize.height}
                            scaleX={zoom}
                            scaleY={zoom}
                            x={pan.x}
                            y={pan.y}
                            onMouseDown={handleStageMouseDown}
                            onMouseMove={handleStageMouseMove}
                            onMouseUp={handleStageMouseUp}
                            onDblClick={handleStageDoubleClick}
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
                        </Stage>

                        {/* Scale warning */}
                        {!page?.scale_calibrated && (
                            <div className="absolute top-4 left-1/2 transform -translate-x-1/2 bg-yellow-100 border border-yellow-400 text-yellow-800 px-4 py-2 rounded-lg">
                                ⚠️ Scale not calibrated. Measurements will not be accurate.
                            </div>
                        )}
                    </div>
                </div>

                {/* Right sidebar - Measurement details */}
                <div className="w-80 border-l bg-white p-4 overflow-y-auto">
                    <h2 className="text-sm font-semibold mb-3">Measurements</h2>
                    {selectedConditionId && (
                        <div className="space-y-2">
                            {measurements
                                .filter((m: Measurement) => m.condition_id === selectedConditionId)
                                .map((measurement: Measurement) => (
                                    <div
                                        key={measurement.id}
                                        onClick={() => setSelectedMeasurementId(measurement.id)}
                                        className={`p-3 rounded-lg border cursor-pointer ${selectedMeasurementId === measurement.id
                                            ? 'border-blue-500 bg-blue-50'
                                            : 'border-gray-200 hover:border-gray-300'
                                            }`}
                                    >
                                        <p className="text-sm font-medium">{measurement.geometry_type}</p>
                                        <p className="text-lg font-bold text-blue-600">
                                            {measurement.quantity.toFixed(1)} {measurement.unit}
                                        </p>
                                    </div>
                                ))}
                        </div>
                    )}
                </div>
            </div>

            {/* Scale Calibration Modal */}
            {page && (
                <ScaleCalibration
                    pageId={page.id}
                    currentScale={page.scale_value ?? null}
                    scaleText={page.detected_scale ?? null}
                    isCalibrated={page.scale_calibrated}
                    onCalibrationStart={() => setIsCalibrating(true)}
                    onCalibrationEnd={() => setIsCalibrating(false)}
                    calibrationLine={calibrationLine}
                />
            )}
        </div>
    );
}
