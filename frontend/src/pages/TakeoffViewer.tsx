import { useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Stage, Layer, Image as KonvaImage, Rect } from 'react-konva';
import Konva from 'konva';

import { apiClient } from '@/api/client';
import { MeasurementLayer } from '@/components/viewer/MeasurementLayer';
import { DrawingPreviewLayer } from '@/components/viewer/DrawingPreviewLayer';
import { ScaleDetectionBanner } from '@/components/viewer/ScaleDetectionBanner';
import { ConditionsPanel } from '@/components/viewer/ConditionsPanel';
import { MeasurementsPanel } from '@/components/viewer/MeasurementsPanel';
import { ScaleCalibrationDialog } from '@/components/viewer/ScaleCalibrationDialog';
import { ViewerHeader } from '@/components/viewer/ViewerHeader';
import { ClassificationSidebar } from '@/components/viewer/ClassificationSidebar';
import { useDrawingState } from '@/hooks/useDrawingState';
import { useCanvasControls } from '@/hooks/useCanvasControls';
import { useScaleDetection } from '@/hooks/useScaleDetection';
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts';
import { useMeasurements } from '@/hooks/useMeasurements';
import { useCanvasEvents } from '@/hooks/useCanvasEvents';
import { usePageImage } from '@/hooks/usePageImage';
import { useNotificationContext } from '@/contexts/NotificationContext';
import { createMeasurementGeometry } from '@/utils/measurementUtils';
import type { Page, Measurement, Condition } from '@/types';

export function TakeoffViewer() {
    const { pageId } = useParams<{ documentId: string; pageId: string }>();
    const navigate = useNavigate();
    const queryClient = useQueryClient();
    const { addNotification } = useNotificationContext();
    const stageRef = useRef<Konva.Stage | null>(null);

    // State
    const [selectedConditionId, setSelectedConditionId] = useState<string | null>(null);
    const [selectedMeasurementId, setSelectedMeasurementId] = useState<string | null>(null);
    const [showCalibrationDialog, setShowCalibrationDialog] = useState(false);
    const [isFullscreen, setIsFullscreen] = useState(false);
    const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
    const [showScaleLocation, setShowScaleLocation] = useState(false);

    // Drawing state
    const drawing = useDrawingState();

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

    // Load page image
    const image = usePageImage(page?.image_url);

    // Custom hooks
    const canvasControls = useCanvasControls({
        image,
        containerId: 'canvas-container',
    });

    const scaleDetection = useScaleDetection(pageId, page);

    const measurements = useMeasurements(pageId);

    const canvasEvents = useCanvasEvents({
        zoom: canvasControls.zoom,
        pan: canvasControls.pan,
        setPan: canvasControls.setPan,
        drawing: {
            tool: drawing.tool,
            isDrawing: drawing.isDrawing,
            points: drawing.points,
            startDrawing: drawing.startDrawing,
            addPoint: drawing.addPoint,
            updatePreview: drawing.updatePreview,
            finishDrawing: drawing.finishDrawing,
        },
        onMeasurementCreate: (result: import('@/utils/measurementUtils').MeasurementResult) => {
            if (!selectedConditionId || !pageId) return;

            const geometry = createMeasurementGeometry(result);
            if (!geometry) return;

            measurements.createMeasurement({
                conditionId: selectedConditionId,
                pageId,
                geometryType: geometry.geometryType,
                geometryData: geometry.geometryData,
            });
        },
        onMeasurementSelect: setSelectedMeasurementId,
        onConditionRequired: () => {
            // TODO: Re-enable condition requirement when condition management is implemented
            // if (!selectedConditionId) {
            //     addNotification('warning', 'Condition Required', 'Please select a condition first before drawing measurements.');
            //     return false;
            // }
            return true;
        },
        handleWheel: canvasControls.handleWheel,
    });

    useKeyboardShortcuts({
        drawing,
        selectedMeasurementId,
        onDeleteMeasurement: (id: string) => {
            measurements.deleteMeasurement(id);
            setSelectedMeasurementId(null);
        },
        onToggleFullscreen: () => setIsFullscreen(!isFullscreen),
        onDeselectMeasurement: () => setSelectedMeasurementId(null),
    });

    // Derived data
    const conditions = conditionsData?.conditions || [];
    const measurementsList = measurementsData?.measurements || [];
    const selectedCondition = conditions.find((c: Condition) => c.id === selectedConditionId);
    const filteredMeasurements = selectedConditionId
        ? measurementsList.filter((m: Measurement) => m.condition_id === selectedConditionId)
        : [];

    const handleScaleUpdated = () => {
        queryClient.invalidateQueries({ queryKey: ['page', pageId] });
    };

    if (pageLoading) {
        return (
            <div className="flex items-center justify-center h-screen bg-neutral-950 text-white font-mono">
                LOADING...
            </div>
        );
    }

    return (
        <div
            className={`flex flex-col bg-neutral-950 ${isFullscreen
                ? 'fixed inset-0 z-50 w-full h-screen'
                : 'h-screen'
                }`}
        >
            {/* Consolidated Header with all controls */}
            <ViewerHeader
                page={page}
                zoom={canvasControls.zoom}
                isFullscreen={isFullscreen}
                activeTool={drawing.tool}
                canUndo={drawing.canUndo}
                canRedo={drawing.canRedo}
                hasSelection={!!selectedMeasurementId}
                isDetectingScale={scaleDetection.isDetecting}
                scaleLocationVisible={showScaleLocation}
                onNavigateBack={() => navigate(-1)}
                onZoomIn={canvasControls.handleZoomIn}
                onZoomOut={canvasControls.handleZoomOut}
                onFitToScreen={canvasControls.handleFitToScreen}
                onActualSize={canvasControls.handleActualSize}
                onToggleFullscreen={() => setIsFullscreen(!isFullscreen)}
                onToolChange={drawing.setTool}
                onUndo={drawing.undo}
                onRedo={drawing.redo}
                onDelete={() => {
                    if (selectedMeasurementId) {
                        measurements.deleteMeasurement(selectedMeasurementId);
                        setSelectedMeasurementId(null);
                    }
                }}
                onDetectScale={scaleDetection.detectScale}
                onSetScale={() => setShowCalibrationDialog(true)}
                onToggleScaleLocation={() => setShowScaleLocation(!showScaleLocation)}
            />

            {/* Main content area with canvas and sidebar */}
            <div className="flex flex-1 overflow-hidden bg-neutral-900">
                {/* Canvas Area */}
                <div className="flex-1 flex flex-col min-w-0">
                    {/* Detection Result Display */}
                    <ScaleDetectionBanner
                        result={scaleDetection.detectionResult}
                        onDismiss={scaleDetection.dismissResult}
                    />

                    {/* Canvas */}
                    <div
                        id="canvas-container"
                        className="flex-1 relative flex items-center justify-center"
                        style={{
                            minWidth: 0,
                            minHeight: 0,
                            cursor: canvasEvents.isPanning
                                ? 'grabbing'
                                : (drawing.tool && drawing.tool !== 'select')
                                    ? 'crosshair'
                                    : 'grab',
                        }}
                        onContextMenu={(e) => e.preventDefault()}
                    >
                        <Stage
                            ref={stageRef}
                            width={canvasControls.stageSize.width}
                            height={canvasControls.stageSize.height}
                            scaleX={canvasControls.zoom}
                            scaleY={canvasControls.zoom}
                            x={canvasControls.pan.x}
                            y={canvasControls.pan.y}
                            draggable={false}
                            onMouseDown={canvasEvents.handleStageMouseDown}
                            onMouseMove={canvasEvents.handleStageMouseMove}
                            onMouseUp={canvasEvents.handleStageMouseUp}
                            onMouseLeave={canvasEvents.handleStageMouseLeave}
                            onDblClick={canvasEvents.handleStageDoubleClick}
                            onWheel={canvasEvents.handleWheelEvent}
                        >
                            {/* Background image */}
                            <Layer>
                                {image && <KonvaImage image={image} />}
                            </Layer>

                            {/* Measurements */}
                            {page && (
                                <MeasurementLayer
                                    measurements={measurementsList}
                                    conditions={new Map(conditions.map((c: Condition) => [c.id, c]))}
                                    selectedMeasurementId={selectedMeasurementId}
                                    onMeasurementSelect={setSelectedMeasurementId}
                                    onMeasurementUpdate={() => { }}
                                    isEditing={false}
                                    scale={canvasControls.zoom}
                                />
                            )}

                            {/* Drawing preview */}
                            {/* Use scale_value when calibrated (auto or manual) for real-world measurements.
                                Auto-detection now uses PDF physical dimensions for accurate calculation. */}
                            <DrawingPreviewLayer
                                previewShape={drawing.previewShape}
                                points={drawing.points}
                                isDrawing={drawing.isDrawing}
                                color={selectedCondition?.color || '#3B82F6'}
                                scale={canvasControls.zoom}
                                pixelsPerUnit={page?.scale_calibrated ? page?.scale_value : null}
                                unitLabel={page?.scale_unit || 'ft'}
                            />

                            {/* Scale detection highlight overlay */}
                            {scaleDetection.scaleHighlightBox && (
                                <Layer>
                                    <Rect
                                        x={scaleDetection.scaleHighlightBox.x}
                                        y={scaleDetection.scaleHighlightBox.y}
                                        width={scaleDetection.scaleHighlightBox.width}
                                        height={scaleDetection.scaleHighlightBox.height}
                                        fill="rgba(251, 191, 36, 0.15)"
                                        stroke="rgb(251, 191, 36)"
                                        strokeWidth={3 / canvasControls.zoom}
                                        listening={false}
                                    />
                                </Layer>
                            )}

                            {/* Historical scale location overlay (from calibration data) */}
                            {showScaleLocation && page?.scale_calibration_data?.best_scale?.bbox && (
                                <Layer>
                                    <Rect
                                        x={page.scale_calibration_data.best_scale.bbox.x}
                                        y={page.scale_calibration_data.best_scale.bbox.y}
                                        width={page.scale_calibration_data.best_scale.bbox.width}
                                        height={page.scale_calibration_data.best_scale.bbox.height}
                                        fill="rgba(34, 197, 94, 0.15)"
                                        stroke="rgb(34, 197, 94)"
                                        strokeWidth={3 / canvasControls.zoom}
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

                        {/* Conditions overlay */}
                        <ConditionsPanel
                            conditions={conditions}
                            selectedConditionId={selectedConditionId}
                            onSelectCondition={setSelectedConditionId}
                        />

                        {/* Measurements overlay */}
                        <MeasurementsPanel
                            measurements={filteredMeasurements}
                            selectedMeasurementId={selectedMeasurementId}
                            onSelectMeasurement={setSelectedMeasurementId}
                        />
                    </div>
                </div>

                {/* Classification Sidebar */}
                {!isFullscreen && (
                    <ClassificationSidebar
                        page={page}
                        isCollapsed={isSidebarCollapsed}
                        onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
                    />
                )}
            </div>

            {/* Set Scale Dialog */}
            <ScaleCalibrationDialog
                open={showCalibrationDialog}
                onOpenChange={setShowCalibrationDialog}
                page={page}
                pageId={pageId}
                onScaleUpdated={handleScaleUpdated}
            />
        </div>
    );
}
