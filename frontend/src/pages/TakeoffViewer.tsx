import { useState, useRef, useCallback, useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Stage, Layer, Image as KonvaImage, Rect } from 'react-konva';
import Konva from 'konva';

import { apiClient } from '@/api/client';
import { updateTitleBlockRegion } from '@/api/documents';
import { MeasurementLayer } from '@/components/viewer/MeasurementLayer';
import { DrawingPreviewLayer } from '@/components/viewer/DrawingPreviewLayer';
import { DrawingInstructions } from '@/components/viewer/DrawingInstructions';
import { ShapeContextMenu } from '@/components/viewer/ShapeContextMenu';
import { ScaleDetectionBanner } from '@/components/viewer/ScaleDetectionBanner';
import { ConditionsPanel } from '@/components/viewer/ConditionsPanel';
import { MeasurementsPanel } from '@/components/viewer/MeasurementsPanel';
import { ScaleCalibrationDialog } from '@/components/viewer/ScaleCalibrationDialog';
import { CalibrationOverlay } from '@/components/viewer/CalibrationOverlay';
import { ViewerHeader } from '@/components/viewer/ViewerHeader';
import { MeasurementToolbarSidebar } from '@/components/viewer/MeasurementToolbarSidebar';
import { ClassificationSidebar } from '@/components/viewer/ClassificationSidebar';
import { useDrawingState } from '@/hooks/useDrawingState';
import { useUndoRedo } from '@/hooks/useUndoRedo';
import { useCanvasControls } from '@/hooks/useCanvasControls';
import { useScaleDetection } from '@/hooks/useScaleDetection';
import { useScaleCalibration } from '@/hooks/useScaleCalibration';
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts';
import { useConditions } from '@/hooks/useConditions';
import { useMeasurements } from '@/hooks/useMeasurements';
import { useCanvasEvents } from '@/hooks/useCanvasEvents';
import { usePageImage } from '@/hooks/usePageImage';
import { useNotificationContext } from '@/contexts/NotificationContext';
import { createMeasurementGeometry, offsetGeometryData } from '@/utils/measurementUtils';
import { pollUntil } from '@/utils/polling';
import { AITakeoffDialog } from '@/components/takeoff/AITakeoffDialog';
import type { Page, Measurement, Condition, JsonObject } from '@/types';

export function TakeoffViewer() {
    const { pageId } = useParams<{ documentId: string; pageId: string }>();
    const navigate = useNavigate();
    const queryClient = useQueryClient();
    const { addNotification } = useNotificationContext();
    const stageRef = useRef<Konva.Stage | null>(null);

    // State
    const [selectedConditionId, setSelectedConditionId] = useState<string | null>(null);
    const [selectedMeasurementId, setSelectedMeasurementId] = useState<string | null>(null);
    const [shapeContextMenu, setShapeContextMenu] = useState<{
        measurement: Measurement;
        position: { x: number; y: number };
    } | null>(null);
    const [isConditionsCollapsed, setIsConditionsCollapsed] = useState(false);
    const [hiddenMeasurementIds, setHiddenMeasurementIds] = useState<Set<string>>(new Set());
    const [measurementOrder, setMeasurementOrder] = useState<string[]>([]);
    const [showCalibrationDialog, setShowCalibrationDialog] = useState(false);
    const [isFullscreen, setIsFullscreen] = useState(false);
    const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
    const [showScaleLocation, setShowScaleLocation] = useState(false);
    const [showTitleBlockRegion, setShowTitleBlockRegion] = useState(true);
    const [isTitleBlockMode, setIsTitleBlockMode] = useState(false);
    const [isToolsCollapsed, setIsToolsCollapsed] = useState(false);
    const [aiTakeoffCondition, setAiTakeoffCondition] = useState<{ id: string; name: string } | null>(null);
    const [titleBlockStart, setTitleBlockStart] = useState<{ x: number; y: number } | null>(null);
    const [titleBlockCurrent, setTitleBlockCurrent] = useState<{ x: number; y: number } | null>(null);
    const [pendingTitleBlock, setPendingTitleBlock] = useState<{ x: number; y: number; width: number; height: number } | null>(null);
    const [isSavingTitleBlock, setIsSavingTitleBlock] = useState(false);

    // Drawing state
    const drawing = useDrawingState();
    const undoRedo = useUndoRedo();

    // Fetch page data
    const { data: page, isLoading: pageLoading } = useQuery({
        queryKey: ['page', pageId],
        queryFn: async () => {
            const response = await apiClient.get<Page>(`/pages/${pageId}`);
            return response.data;
        },
        enabled: !!pageId,
    });

    const projectId = page?.document?.project_id;
    const { data: conditionsData } = useConditions(projectId);

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
    const isImageReady = Boolean(image && image.complete && image.width > 0 && image.height > 0);
    // Custom hooks
    const canvasControls = useCanvasControls({
        image,
        containerId: 'canvas-container',
    });

    const scaleDetection = useScaleDetection(pageId, page);

    const scaleCalibration = useScaleCalibration();

    // Track current mouse position for calibration preview
    const [calibrationCurrentPoint, setCalibrationCurrentPoint] = useState<{ x: number; y: number } | null>(null);

    const measurements = useMeasurements(pageId, projectId);

    const clearSelection = useCallback(() => {
        setSelectedMeasurementId(null);
        setSelectedConditionId(null);
        setShapeContextMenu(null);
    }, []);

    const handleConditionSelect = useCallback((id: string | null) => {
        setSelectedConditionId(id);
        if (id === null) {
            setSelectedMeasurementId(null);
        }
    }, []);
    const handleMeasurementSelect = useCallback((id: string | null, conditionId?: string | null) => {
        setSelectedMeasurementId(id);
        if (conditionId) {
            setSelectedConditionId(conditionId);
        }
    }, []);

    const handleMeasurementCreate = useCallback(
        (result: import('@/utils/measurementUtils').MeasurementResult) => {
            void (async () => {
                if (!selectedConditionId || !pageId) return;

                const geometry = createMeasurementGeometry(result);
                if (!geometry) return;

                try {
                    const created = await measurements.createMeasurementAsync({
                        conditionId: selectedConditionId,
                        pageId,
                        geometryType: geometry.geometryType,
                        geometryData: geometry.geometryData as unknown as JsonObject,
                    });

                    if (!created?.id) return;
                    let measurementId = created.id as string;

                    undoRedo.push({
                        undo: async () => {
                            try {
                                await measurements.deleteMeasurementAsync(measurementId);
                                setSelectedMeasurementId((prev) =>
                                    prev === measurementId ? null : prev
                                );
                            } catch (error) {
                                const message =
                                    error instanceof Error
                                        ? error.message
                                        : 'Failed to undo measurement creation.';
                                addNotification('error', 'Undo failed', message);
                            }
                        },
                        redo: async () => {
                                try {
                                    const recreated = await measurements.createMeasurementAsync({
                                        conditionId: selectedConditionId,
                                        pageId,
                                        geometryType: geometry.geometryType,
                                        geometryData: geometry.geometryData as unknown as JsonObject,
                                    });
                                    if (!recreated?.id) {
                                        throw new Error('Failed to recreate measurement during redo.');
                                    }
                                    measurementId = recreated.id as string;
                                    setSelectedMeasurementId(measurementId);
                                    setSelectedConditionId(selectedConditionId);
                                } catch (error) {
                                    const message =
                                        error instanceof Error
                                            ? error.message
                                            : 'Failed to redo measurement creation.';
                                    addNotification('error', 'Redo failed', message);
                                }
                        },
                    });

                    setSelectedMeasurementId(measurementId);
                    setSelectedConditionId(selectedConditionId);
                } catch (error) {
                    const message =
                        error instanceof Error ? error.message : 'Failed to create measurement.';
                    addNotification('error', 'Create failed', message);
                }
            })();
        },
        [addNotification, measurements, pageId, selectedConditionId, undoRedo]
    );

    const canvasEvents = useCanvasEvents({
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
        onMeasurementCreate: handleMeasurementCreate,
        onMeasurementSelect: (id) => handleMeasurementSelect(id),
        onConditionSelect: handleConditionSelect,
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

    // Derived data
    const conditions = conditionsData?.conditions || [];
    const measurementsList = measurementsData?.measurements || [];
    const selectedCondition = conditions.find((c: Condition) => c.id === selectedConditionId);
    const orderedMeasurements = useMemo(() => {
        if (measurementOrder.length === 0) return measurementsList;
        const orderIndex = new Map(measurementOrder.map((id, index) => [id, index]));
        return [...measurementsList].sort((a, b) => {
            const aIndex = orderIndex.get(a.id) ?? 0;
            const bIndex = orderIndex.get(b.id) ?? 0;
            return aIndex - bIndex;
        });
    }, [measurementOrder, measurementsList]);
    const visibleMeasurements = orderedMeasurements.filter(
        (measurement: Measurement) => !hiddenMeasurementIds.has(measurement.id)
    );
    const filteredMeasurements = selectedConditionId
        ? visibleMeasurements.filter((m: Measurement) => m.condition_id === selectedConditionId)
        : [];

    useEffect(() => {
        if (measurementsList.length === 0) {
            setMeasurementOrder((prev) => (prev.length === 0 ? prev : []));
            return;
        }
        setMeasurementOrder((prev) => {
            const availableIds = new Set(
                measurementsList.map((measurement: Measurement) => measurement.id)
            );
            const filtered = prev.filter((id: string) => availableIds.has(id));
            const missing = measurementsList
                .map((measurement: Measurement) => measurement.id)
                .filter((id: string) => !filtered.includes(id));
            return [...filtered, ...missing];
        });
    }, [measurementsList]);

    useEffect(() => {
        if (measurementsList.length === 0) {
            setHiddenMeasurementIds((prev) => (prev.size === 0 ? prev : new Set()));
            return;
        }
        setHiddenMeasurementIds((prev) => {
            const availableIds = new Set(
                measurementsList.map((measurement: Measurement) => measurement.id)
            );
            const next = new Set<string>();
            prev.forEach((id) => {
                if (availableIds.has(id)) {
                    next.add(id);
                }
            });
            return next;
        });
    }, [measurementsList]);

    const handleDeleteMeasurement = useCallback(
        (id: string) => {
            void (async () => {
                if (!pageId) return;
                const measurement = measurementsList.find((item: Measurement) => item.id === id);
                if (!measurement) return;

                let measurementId = id;
                try {
                    await measurements.deleteMeasurementAsync(measurementId);
                    setSelectedMeasurementId((prev) => (prev === measurementId ? null : prev));

                    undoRedo.push({
                        undo: async () => {
                            try {
                                const recreated = await measurements.createMeasurementAsync({
                                    conditionId: measurement.condition_id,
                                    pageId,
                                    geometryType: measurement.geometry_type,
                                    geometryData: measurement.geometry_data as unknown as JsonObject,
                                });
                                if (!recreated?.id) {
                                    throw new Error('Failed to recreate measurement during undo.');
                                }
                                measurementId = recreated.id as string;
                                setSelectedMeasurementId(measurementId);
                                setSelectedConditionId(measurement.condition_id);
                            } catch (error) {
                                const message =
                                    error instanceof Error
                                        ? error.message
                                        : 'Failed to undo measurement deletion.';
                                addNotification('error', 'Undo failed', message);
                            }
                        },
                        redo: async () => {
                            try {
                                await measurements.deleteMeasurementAsync(measurementId);
                                setSelectedMeasurementId((prev) =>
                                    prev === measurementId ? null : prev
                                );
                            } catch (error) {
                                const message =
                                    error instanceof Error
                                        ? error.message
                                        : 'Failed to redo measurement deletion.';
                                addNotification('error', 'Redo failed', message);
                            }
                        },
                    });
                } catch (error) {
                    const message =
                        error instanceof Error ? error.message : 'Failed to delete measurement.';
                    addNotification('error', 'Delete failed', message);
                }
            })();
        },
        [addNotification, measurements, measurementsList, pageId, undoRedo]
    );

    const handleMeasurementUpdate = useCallback(
        (id: string, geometryData: JsonObject, previousGeometryData?: JsonObject) => {
            void (async () => {
                if (!pageId) return;
                const measurement = measurementsList.find((item: Measurement) => item.id === id);
                if (!measurement) return;
                const before = previousGeometryData ?? (measurement.geometry_data as JsonObject);
                try {
                    await measurements.updateMeasurementAsync({
                        measurementId: id,
                        geometryData,
                    });
                    undoRedo.push({
                        undo: async () => {
                            try {
                                await measurements.updateMeasurementAsync({
                                    measurementId: id,
                                    geometryData: before,
                                });
                            } catch (error) {
                                const message =
                                    error instanceof Error
                                        ? error.message
                                        : 'Failed to undo measurement update.';
                                addNotification('error', 'Undo failed', message);
                            }
                        },
                        redo: async () => {
                            try {
                                await measurements.updateMeasurementAsync({
                                    measurementId: id,
                                    geometryData,
                                });
                            } catch (error) {
                                const message =
                                    error instanceof Error
                                        ? error.message
                                        : 'Failed to redo measurement update.';
                                addNotification('error', 'Redo failed', message);
                            }
                        },
                    });
                } catch (error) {
                    const message =
                        error instanceof Error ? error.message : 'Failed to update measurement.';
                    addNotification('error', 'Update failed', message);
                }
            })();
        },
        [addNotification, measurements, measurementsList, pageId, undoRedo]
    );

    const handleDuplicateMeasurement = useCallback(
        (id: string) => {
            void (async () => {
                if (!pageId) return;
                const measurement = measurementsList.find((item: Measurement) => item.id === id);
                if (!measurement) return;
                const offset = 12;
                const duplicatedGeometry = offsetGeometryData(
                    measurement.geometry_type,
                    measurement.geometry_data as JsonObject,
                    offset,
                    offset
                );

                try {
                    const created = await measurements.createMeasurementAsync({
                        conditionId: measurement.condition_id,
                        pageId,
                        geometryType: measurement.geometry_type,
                        geometryData: duplicatedGeometry as JsonObject,
                    });
                    if (!created?.id) return;
                    let measurementId = created.id as string;

                    undoRedo.push({
                        undo: async () => {
                            try {
                                await measurements.deleteMeasurementAsync(measurementId);
                            } catch (error) {
                                const message =
                                    error instanceof Error
                                        ? error.message
                                        : 'Failed to undo measurement duplication.';
                                addNotification('error', 'Undo failed', message);
                            }
                        },
                        redo: async () => {
                            try {
                                const recreated = await measurements.createMeasurementAsync({
                                    conditionId: measurement.condition_id,
                                    pageId,
                                    geometryType: measurement.geometry_type,
                                    geometryData: duplicatedGeometry as JsonObject,
                                });
                                if (!recreated?.id) {
                                    throw new Error('Failed to recreate measurement during redo.');
                                }
                                measurementId = recreated.id as string;
                                setSelectedMeasurementId(measurementId);
                                setSelectedConditionId(measurement.condition_id);
                            } catch (error) {
                                const message =
                                    error instanceof Error
                                        ? error.message
                                        : 'Failed to redo measurement duplication.';
                                addNotification('error', 'Redo failed', message);
                            }
                        },
                    });

                    setSelectedMeasurementId(measurementId);
                    setSelectedConditionId(measurement.condition_id);
                } catch (error) {
                    const message =
                        error instanceof Error ? error.message : 'Failed to duplicate measurement.';
                    addNotification('error', 'Duplicate failed', message);
                }
            })();
        },
        [addNotification, measurements, measurementsList, pageId, undoRedo]
    );

    const bringMeasurementToFront = useCallback((id: string) => {
        setMeasurementOrder((prev) => {
            const filtered = prev.filter((item) => item !== id);
            return [...filtered, id];
        });
    }, []);

    const sendMeasurementToBack = useCallback((id: string) => {
        setMeasurementOrder((prev) => {
            const filtered = prev.filter((item) => item !== id);
            return [id, ...filtered];
        });
    }, []);

    const toggleMeasurementHidden = useCallback((id: string) => {
        setHiddenMeasurementIds((prev) => {
            const next = new Set(prev);
            if (next.has(id)) {
                next.delete(id);
            } else {
                next.add(id);
            }
            return next;
        });
    }, []);

    const openShapeContextMenu = useCallback(
        (measurement: Measurement, event: Konva.KonvaEventObject<PointerEvent | MouseEvent>) => {
            event.evt.preventDefault();
            setShapeContextMenu({
                measurement,
                position: { x: event.evt.clientX, y: event.evt.clientY },
            });
            setSelectedMeasurementId(measurement.id);
            setSelectedConditionId(measurement.condition_id);
        },
        []
    );

    const closeShapeContextMenu = useCallback(() => {
        setShapeContextMenu(null);
    }, []);

    const handleUndo = useCallback(() => {
        if (drawing.isDrawing && drawing.canUndo) {
            drawing.undo();
            return;
        }
        void undoRedo.undo();
    }, [drawing, undoRedo]);

    const handleRedo = useCallback(() => {
        if (drawing.isDrawing && drawing.canRedo) {
            drawing.redo();
            return;
        }
        void undoRedo.redo();
    }, [drawing, undoRedo]);

    const canUndo = drawing.canUndo || undoRedo.canUndo;
    const canRedo = drawing.canRedo || undoRedo.canRedo;
    const showDrawingInstructions =
        drawing.tool !== 'select' &&
        Boolean(selectedConditionId) &&
        !scaleCalibration.state.isCalibrating &&
        !isTitleBlockMode;

    useKeyboardShortcuts({
        drawing,
        selectedMeasurementId,
        onDeleteMeasurement: handleDeleteMeasurement,
        onToggleFullscreen: () => setIsFullscreen(!isFullscreen),
        onClearSelection: clearSelection,
        onUndo: handleUndo,
        onRedo: handleRedo,
    });

    const handleScaleUpdated = () => {
        queryClient.invalidateQueries({ queryKey: ['page', pageId] });
        queryClient.refetchQueries({ queryKey: ['page', pageId] });
    };

    const MIN_TITLE_BLOCK_SIZE = 10;

    const resetTitleBlockSelection = useCallback(() => {
        setTitleBlockStart(null);
        setTitleBlockCurrent(null);
        setPendingTitleBlock(null);
    }, []);

    const getRectFromPoints = useCallback(
        (start: { x: number; y: number }, end: { x: number; y: number }) => ({
            x: Math.min(start.x, end.x),
            y: Math.min(start.y, end.y),
            width: Math.abs(end.x - start.x),
            height: Math.abs(end.y - start.y),
        }),
        []
    );

    const fetchPage = useCallback(async () => {
        const response = await apiClient.get<Page>(`/pages/${pageId}`);
        return response.data;
    }, [pageId]);

    const pollForTitleBlockUpdate = useCallback(
        async (previousSheetNumber: string | null, previousTitle: string | null) => {
            if (!pageId) return;

            await pollUntil<Page>({
                fetcher: fetchPage,
                shouldStop: (updatedPage) => {
                    const hasRegion = !!updatedPage.document?.title_block_region;
                    const sheetNumberChanged = updatedPage.sheet_number !== previousSheetNumber;
                    const titleChanged = updatedPage.title !== previousTitle;
                    const hasSheetOrTitle = !!updatedPage.sheet_number || !!updatedPage.title;
                    return hasRegion && (sheetNumberChanged || titleChanged || hasSheetOrTitle);
                },
                onTick: (updatedPage) => queryClient.setQueryData(['page', pageId], updatedPage),
                intervalMs: 2000,
                maxAttempts: 15,
                initialDelayMs: 2000,
            });
        },
        [fetchPage, pageId, queryClient]
    );

    const handleToggleTitleBlockMode = useCallback(() => {
        if (isSavingTitleBlock) return;

        if (isTitleBlockMode) {
            setIsTitleBlockMode(false);
            resetTitleBlockSelection();
            return;
        }

        if (scaleCalibration.state.isCalibrating) {
            scaleCalibration.cancelCalibration();
        }

        drawing.cancelDrawing();
        setIsTitleBlockMode(true);
        resetTitleBlockSelection();
    }, [
        isSavingTitleBlock,
        isTitleBlockMode,
        resetTitleBlockSelection,
        scaleCalibration,
        drawing,
    ]);

    const handleTitleBlockClick = useCallback(
        (e: Konva.KonvaEventObject<MouseEvent>) => {
            if (!isTitleBlockMode) return;
            if (e.evt.button !== 0) return;

            const stage = e.target.getStage();
            if (!stage) return;

            const pos = stage.getRelativePointerPosition();
            if (!pos) return;

            if (!titleBlockStart) {
                setTitleBlockStart({ x: pos.x, y: pos.y });
                setTitleBlockCurrent({ x: pos.x, y: pos.y });
                setPendingTitleBlock(null);
                return;
            }

            const rect = getRectFromPoints(titleBlockStart, pos);
            if (rect.width < MIN_TITLE_BLOCK_SIZE || rect.height < MIN_TITLE_BLOCK_SIZE) {
                addNotification(
                    'warning',
                    'Selection too small',
                    'Title block region must be at least 10x10 pixels.'
                );
                resetTitleBlockSelection();
                return;
            }

            setPendingTitleBlock(rect);
            setTitleBlockStart(null);
            setTitleBlockCurrent(null);
        },
        [
            addNotification,
            getRectFromPoints,
            isTitleBlockMode,
            resetTitleBlockSelection,
            titleBlockStart,
        ]
    );

    const handleTitleBlockMouseMove = useCallback(
        (e: Konva.KonvaEventObject<MouseEvent>) => {
            if (!isTitleBlockMode || !titleBlockStart) return;

            const stage = e.target.getStage();
            if (!stage) return;

            const pos = stage.getRelativePointerPosition();
            if (!pos) return;

            setTitleBlockCurrent({ x: pos.x, y: pos.y });
        },
        [isTitleBlockMode, titleBlockStart]
    );

    const handleSaveTitleBlockRegion = useCallback(async () => {
        if (!pendingTitleBlock || !page || !page.width || !page.height) return;

        const clamp = (value: number, min: number, max: number) =>
            Math.max(min, Math.min(value, max));

        const normalized = {
            x: clamp(pendingTitleBlock.x / page.width, 0, 1),
            y: clamp(pendingTitleBlock.y / page.height, 0, 1),
            width: clamp(pendingTitleBlock.width / page.width, 0, 1),
            height: clamp(pendingTitleBlock.height / page.height, 0, 1),
            source_page_id: page.id,
        };
        normalized.width = Math.min(normalized.width, 1 - normalized.x);
        normalized.height = Math.min(normalized.height, 1 - normalized.y);
        if (normalized.width <= 0 || normalized.height <= 0) {
            addNotification(
                'warning',
                'Invalid selection',
                'Title block region must stay within the page bounds.'
            );
            return;
        }

        const previousSheetNumber = page.sheet_number ?? null;
        const previousTitle = page.title ?? null;

        setIsSavingTitleBlock(true);
        try {
            const result = await updateTitleBlockRegion(page.document_id, normalized);
            addNotification(
                'success',
                'Title block region saved',
                `OCR queued for ${result.pages_queued} pages.`
            );
            await pollForTitleBlockUpdate(previousSheetNumber, previousTitle);
            queryClient.invalidateQueries({ queryKey: ['page', pageId] });
            queryClient.refetchQueries({ queryKey: ['page', pageId] });
            queryClient.invalidateQueries({ queryKey: ['pages', page.document_id] });
            queryClient.refetchQueries({ queryKey: ['pages', page.document_id] });
            setShowTitleBlockRegion(true);
            setIsTitleBlockMode(false);
            resetTitleBlockSelection();
        } catch (error) {
            const message =
                error instanceof Error ? error.message : 'Failed to save title block region.';
            addNotification('error', 'Save failed', message);
        } finally {
            setIsSavingTitleBlock(false);
        }
    }, [
        addNotification,
        page,
        pageId,
        pendingTitleBlock,
        pollForTitleBlockUpdate,
        queryClient,
        resetTitleBlockSelection,
    ]);

    // Calibration mouse handlers - click-to-start, click-to-finish (left-click only)
    const handleCalibrationClick = useCallback((e: Konva.KonvaEventObject<MouseEvent>) => {
        if (!scaleCalibration.state.isCalibrating) return;
        
        // Only respond to left-click (button 0)
        // Right-click (1) and middle-click (2) should be ignored for calibration
        if (e.evt.button !== 0) return;
        
        const stage = e.target.getStage();
        if (!stage) return;
        
        const pos = stage.getRelativePointerPosition();
        if (!pos) return;
        
        if (!scaleCalibration.state.isDrawing) {
            // First click: start drawing
            scaleCalibration.startDrawing({ x: pos.x, y: pos.y });
        } else {
            // Second click: finish drawing
            scaleCalibration.finishDrawing({ x: pos.x, y: pos.y });
            setShowCalibrationDialog(true);
        }
    }, [scaleCalibration]);

    const handleCalibrationMouseMove = useCallback((e: Konva.KonvaEventObject<MouseEvent>) => {
        if (!scaleCalibration.state.isCalibrating) return;
        
        const stage = e.target.getStage();
        if (!stage) return;
        
        const pos = stage.getRelativePointerPosition();
        if (!pos) return;
        
        setCalibrationCurrentPoint({ x: pos.x, y: pos.y });
        
        if (scaleCalibration.state.isDrawing) {
            scaleCalibration.updateDrawing({ x: pos.x, y: pos.y });
        }
    }, [scaleCalibration]);

    // Wrapped event handlers that check for calibration mode
    const handleStageMouseDown = useCallback((e: Konva.KonvaEventObject<MouseEvent>) => {
        if (scaleCalibration.state.isCalibrating || isTitleBlockMode) {
            // In calibration/title block mode, only allow panning with right/middle click
            if (e.evt.button !== 0) {
                canvasEvents.handleStageMouseDown(e);
            }
            return;
        }
        canvasEvents.handleStageMouseDown(e);
    }, [canvasEvents, isTitleBlockMode, scaleCalibration.state.isCalibrating]);

    const handleStageMouseMove = useCallback((e: Konva.KonvaEventObject<MouseEvent>) => {
        if (isTitleBlockMode) {
            handleTitleBlockMouseMove(e);
            // Also allow panning movement (for right/middle drag)
            canvasEvents.handleStageMouseMove(e);
            return;
        }
        if (scaleCalibration.state.isCalibrating) {
            handleCalibrationMouseMove(e);
            // Also allow panning movement (for right/middle drag)
            canvasEvents.handleStageMouseMove(e);
        } else {
            canvasEvents.handleStageMouseMove(e);
        }
    }, [canvasEvents, handleCalibrationMouseMove, handleTitleBlockMouseMove, isTitleBlockMode, scaleCalibration.state.isCalibrating]);

    const handleStageMouseUp = useCallback((e: Konva.KonvaEventObject<MouseEvent>) => {
        if (scaleCalibration.state.isCalibrating || isTitleBlockMode) {
            // In calibration/title block mode, only allow panning release with right/middle click
            if (e.evt.button !== 0) {
                canvasEvents.handleStageMouseUp(e);
            }
            return;
        }
        canvasEvents.handleStageMouseUp(e);
    }, [canvasEvents, isTitleBlockMode, scaleCalibration.state.isCalibrating]);

    const handleStageClick = useCallback((e: Konva.KonvaEventObject<MouseEvent>) => {
        if (isTitleBlockMode) {
            handleTitleBlockClick(e);
            return;
        }
        if (scaleCalibration.state.isCalibrating) {
            handleCalibrationClick(e);
        }
        // Normal mode doesn't use click events
    }, [handleCalibrationClick, handleTitleBlockClick, isTitleBlockMode, scaleCalibration.state.isCalibrating]);

    const existingTitleBlockRegion = page?.document?.title_block_region;
    const existingTitleBlockRect =
        existingTitleBlockRegion && page?.width && page?.height
            ? {
                x: existingTitleBlockRegion.x * page.width,
                y: existingTitleBlockRegion.y * page.height,
                width: existingTitleBlockRegion.width * page.width,
                height: existingTitleBlockRegion.height * page.height,
            }
            : null;

    const titleBlockDraftRect =
        titleBlockStart && titleBlockCurrent
            ? getRectFromPoints(titleBlockStart, titleBlockCurrent)
            : null;
    const activeTitleBlockRect = pendingTitleBlock ?? titleBlockDraftRect;

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
            {/* Deprecation banner */}
            {projectId && (
                <div className="flex items-center justify-between bg-amber-600/90 px-4 py-1.5 text-xs text-white">
                    <span>This viewer is deprecated. Use the new workspace for the full experience.</span>
                    <button
                        className="rounded bg-white/20 px-3 py-0.5 font-medium hover:bg-white/30"
                        onClick={() => navigate(`/projects/${projectId}/workspace`)}
                    >
                        Open Workspace
                    </button>
                </div>
            )}
            {/* Consolidated Header with all controls */}
            <ViewerHeader
                page={page}
                pageId={pageId}
                projectId={projectId}
                zoom={canvasControls.zoom}
                isFullscreen={isFullscreen}
                isDetectingScale={scaleDetection.isDetecting}
                scaleLocationVisible={showScaleLocation}
                showTitleBlockRegion={showTitleBlockRegion}
                isTitleBlockMode={isTitleBlockMode}
                isSavingTitleBlock={isSavingTitleBlock}
                onNavigateBack={() => navigate(-1)}
                onZoomIn={canvasControls.handleZoomIn}
                onZoomOut={canvasControls.handleZoomOut}
                onFitToScreen={canvasControls.handleFitToScreen}
                onActualSize={canvasControls.handleActualSize}
                onToggleFullscreen={() => setIsFullscreen(!isFullscreen)}
                onDetectScale={scaleDetection.detectScale}
                onSetScale={() => setShowCalibrationDialog(true)}
                onToggleScaleLocation={() => setShowScaleLocation(!showScaleLocation)}
                onToggleTitleBlockMode={handleToggleTitleBlockMode}
                onToggleTitleBlockRegion={() => setShowTitleBlockRegion((prev) => !prev)}
                onAutonomousTakeoffComplete={() => {
                    queryClient.invalidateQueries({ queryKey: ['measurements', pageId] });
                    queryClient.invalidateQueries({ queryKey: ['conditions'] });
                    addNotification('success', 'Autonomous Takeoff Complete', 'AI has identified concrete elements and created measurements.');
                }}
            />

            {/* Main content area with canvas and sidebar */}
            <div className="flex flex-1 overflow-hidden bg-neutral-900">
                <MeasurementToolbarSidebar
                    activeTool={drawing.tool}
                    onToolChange={drawing.setTool}
                    canUndo={canUndo}
                    canRedo={canRedo}
                    onUndo={handleUndo}
                    onRedo={handleRedo}
                    onDelete={() => {
                        if (selectedMeasurementId) {
                            handleDeleteMeasurement(selectedMeasurementId);
                        }
                    }}
                    hasSelection={!!selectedMeasurementId}
                    disabled={!page?.scale_calibrated || isTitleBlockMode}
                    isCollapsed={isToolsCollapsed}
                    onToggleCollapse={() => setIsToolsCollapsed((prev) => !prev)}
                />
                {/* Canvas Area */}
                <div className="flex-1 flex flex-col min-w-0">
                    {/* Detection Result Display */}
                    {scaleDetection.detectionResult && (
                        <div className="relative z-10 flex-shrink-0">
                            <ScaleDetectionBanner
                                result={scaleDetection.detectionResult}
                                onDismiss={scaleDetection.dismissResult}
                            />
                        </div>
                    )}

                    {/* Calibration Banner */}
                    {scaleCalibration.state.isCalibrating && (
                        <div className="relative z-10 flex-shrink-0 bg-amber-500 text-black px-4 py-2 font-mono text-sm flex items-center justify-between">
                            <span className="font-bold">
                                CALIBRATION MODE: Draw a line over a known dimension
                            </span>
                            <button
                                onClick={() => {
                                    scaleCalibration.cancelCalibration();
                                }}
                                className="bg-black/20 hover:bg-black/30 px-3 py-1 rounded text-xs uppercase"
                            >
                                Cancel
                            </button>
                        </div>
                    )}

                    {isTitleBlockMode && (
                        <div className="relative z-10 flex-shrink-0 bg-sky-500 text-black px-4 py-2 font-mono text-sm flex items-center justify-between">
                            <span className="font-bold">
                                TITLE BLOCK MODE: Click two corners to set the title block region
                            </span>
                            <div className="flex items-center gap-2">
                                {pendingTitleBlock && (
                                    <button
                                        onClick={handleSaveTitleBlockRegion}
                                        disabled={isSavingTitleBlock}
                                        className="bg-black/20 hover:bg-black/30 px-3 py-1 rounded text-xs uppercase disabled:opacity-60"
                                    >
                                        {isSavingTitleBlock ? 'Saving...' : 'Save & Re-run OCR'}
                                    </button>
                                )}
                                {pendingTitleBlock && (
                                    <button
                                        onClick={resetTitleBlockSelection}
                                        className="bg-black/20 hover:bg-black/30 px-3 py-1 rounded text-xs uppercase"
                                    >
                                        Reset
                                    </button>
                                )}
                                <button
                                    onClick={() => {
                                        setIsTitleBlockMode(false);
                                        resetTitleBlockSelection();
                                    }}
                                    className="bg-black/20 hover:bg-black/30 px-3 py-1 rounded text-xs uppercase"
                                >
                                    Cancel
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Canvas */}
                    <div
                        id="canvas-container"
                        className="flex-1 relative z-0 flex items-center justify-center"
                        style={{
                            minWidth: 0,
                            minHeight: 0,
                            cursor: scaleCalibration.state.isCalibrating || isTitleBlockMode
                                ? 'crosshair'
                                : canvasEvents.isPanning
                                    ? 'grabbing'
                                    : drawing.tool && drawing.tool !== 'select'
                                        ? 'crosshair'
                                        : 'pointer',
                        }}
                        onContextMenu={(e) => e.preventDefault()}
                    >
                        <Stage
                            ref={stageRef}
                            width={canvasControls.stageSize.width}
                            height={canvasControls.stageSize.height}
                            pixelRatio={1}
                            scaleX={canvasControls.zoom}
                            scaleY={canvasControls.zoom}
                            x={canvasControls.pan.x}
                            y={canvasControls.pan.y}
                            draggable={false}
                            onMouseDown={handleStageMouseDown}
                            onMouseMove={handleStageMouseMove}
                            onMouseUp={handleStageMouseUp}
                            onClick={handleStageClick}
                            onMouseLeave={canvasEvents.handleStageMouseLeave}
                            onDblClick={canvasEvents.handleStageDoubleClick}
                            onWheel={canvasEvents.handleWheelEvent}
                        >
                            {/* Background image */}
                            <Layer>
                                {isImageReady && image && <KonvaImage image={image} />}
                            </Layer>

                            {/* Measurements */}
                            {page && (
                                <MeasurementLayer
                                    measurements={visibleMeasurements}
                                    conditions={new Map(conditions.map((c: Condition) => [c.id, c]))}
                                    selectedMeasurementId={selectedMeasurementId}
                                    onMeasurementSelect={(id) => handleMeasurementSelect(id)}
                                    onConditionSelect={handleConditionSelect}
                                    onMeasurementUpdate={handleMeasurementUpdate}
                                    onMeasurementContextMenu={openShapeContextMenu}
                                    isEditing={drawing.tool === 'select'}
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
                                isCloseToStart={canvasEvents.isCloseToStart}
                                pixelsPerUnit={page?.scale_calibrated ? page?.scale_value : null}
                                unitLabel={page?.scale_unit || 'ft'}
                            />

                            {/* Title block region overlay */}
                            {showTitleBlockRegion && existingTitleBlockRect && (
                                <Layer>
                                    <Rect
                                        x={existingTitleBlockRect.x}
                                        y={existingTitleBlockRect.y}
                                        width={existingTitleBlockRect.width}
                                        height={existingTitleBlockRect.height}
                                        fill="rgba(34, 197, 94, 0.12)"
                                        stroke="rgb(34, 197, 94)"
                                        strokeWidth={2 / canvasControls.zoom}
                                        listening={false}
                                    />
                                </Layer>
                            )}
                            {activeTitleBlockRect && (
                                <Layer>
                                    <Rect
                                        x={activeTitleBlockRect.x}
                                        y={activeTitleBlockRect.y}
                                        width={activeTitleBlockRect.width}
                                        height={activeTitleBlockRect.height}
                                        fill="rgba(59, 130, 246, 0.15)"
                                        stroke="rgb(59, 130, 246)"
                                        strokeWidth={2 / canvasControls.zoom}
                                        dash={[8 / canvasControls.zoom, 4 / canvasControls.zoom]}
                                        listening={false}
                                    />
                                </Layer>
                            )}

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

                            {/* Calibration overlay */}
                            {scaleCalibration.state.isCalibrating && (
                                <CalibrationOverlay
                                    calibrationLine={scaleCalibration.state.calibrationLine}
                                    startPoint={scaleCalibration.state.startPoint}
                                    isDrawing={scaleCalibration.state.isDrawing}
                                    currentPoint={calibrationCurrentPoint}
                                    pixelDistance={scaleCalibration.state.pixelDistance}
                                    scale={canvasControls.zoom}
                                />
                            )}
                        </Stage>

                        {showDrawingInstructions && (
                            <DrawingInstructions
                                isVisible={showDrawingInstructions}
                                tool={drawing.tool}
                                conditionName={selectedCondition?.name}
                                isDrawing={drawing.isDrawing}
                                isCloseToStart={canvasEvents.isCloseToStart}
                            />
                        )}

                        {/* Scale warning */}
                        {!page?.scale_calibrated && (
                            <div className="absolute top-4 left-1/2 transform -translate-x-1/2 bg-amber-500/20 border border-amber-500/50 text-amber-400 px-4 py-2 rounded-lg shadow-lg z-10 font-mono text-sm">
                                ⚠️ Scale not calibrated. Measurements will not be accurate.
                            </div>
                        )}

                        {/* Conditions overlay */}
                        {page?.document?.project_id && (
                            <ConditionsPanel
                                projectId={page.document.project_id}
                                selectedConditionId={selectedConditionId}
                                onConditionSelect={handleConditionSelect}
                                pageId={pageId}
                                isCollapsed={isConditionsCollapsed}
                                onToggleCollapse={() =>
                                    setIsConditionsCollapsed((prev) => !prev)
                                }
                                isPageCalibrated={Boolean(
                                    page?.scale_calibrated && (
                                        page?.scale_detection_method === 'manual_calibration' ||
                                        page?.scale_calibration_data?.manual_calibration ||
                                        page?.scale_calibration_data?.calibration
                                    )
                                )}
                                onAITakeoff={(conditionId, conditionName) => {
                                    setAiTakeoffCondition({ id: conditionId, name: conditionName });
                                }}
                            />
                        )}

                        {/* Measurements overlay */}
                        <MeasurementsPanel
                            measurements={filteredMeasurements}
                            selectedMeasurementId={selectedMeasurementId}
                            onSelectMeasurement={(id) => {
                                const measurement = measurementsList.find((item: Measurement) => item.id === id);
                                handleMeasurementSelect(id, measurement?.condition_id);
                            }}
                        />

                        {shapeContextMenu && (
                            <ShapeContextMenu
                                position={shapeContextMenu.position}
                                isHidden={hiddenMeasurementIds.has(shapeContextMenu.measurement.id)}
                                onEdit={() => {
                                    setSelectedMeasurementId(shapeContextMenu.measurement.id);
                                    setSelectedConditionId(shapeContextMenu.measurement.condition_id);
                                }}
                                onDuplicate={() => handleDuplicateMeasurement(shapeContextMenu.measurement.id)}
                                onDelete={() => handleDeleteMeasurement(shapeContextMenu.measurement.id)}
                                onBringToFront={() =>
                                    bringMeasurementToFront(shapeContextMenu.measurement.id)
                                }
                                onSendToBack={() => sendMeasurementToBack(shapeContextMenu.measurement.id)}
                                onToggleHidden={() =>
                                    toggleMeasurementHidden(shapeContextMenu.measurement.id)
                                }
                                onClose={closeShapeContextMenu}
                            />
                        )}
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
                calibrationState={scaleCalibration.state}
                onStartCalibration={scaleCalibration.startCalibration}
                onCancelCalibration={scaleCalibration.cancelCalibration}
                onClearLine={scaleCalibration.clearLine}
                onSubmitCalibration={scaleCalibration.submitCalibration}
            />

            {/* AI Takeoff Dialog */}
            {aiTakeoffCondition && pageId && (
                <AITakeoffDialog
                    pageId={pageId}
                    conditionId={aiTakeoffCondition.id}
                    conditionName={aiTakeoffCondition.name}
                    isPageCalibrated={page?.scale_calibrated ?? false}
                    open={!!aiTakeoffCondition}
                    onOpenChange={(open) => !open && setAiTakeoffCondition(null)}
                    onComplete={() => {
                        queryClient.invalidateQueries({ queryKey: ['measurements', pageId] });
                        queryClient.invalidateQueries({ queryKey: ['conditions'] });
                        addNotification('success', 'AI Takeoff Complete', 'Measurements have been generated.');
                    }}
                />
            )}
        </div>
    );
}
