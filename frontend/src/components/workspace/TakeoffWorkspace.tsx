import { useEffect, useMemo, useState, useCallback } from 'react';
import { useParams, Navigate } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Panel, Group, Separator } from 'react-resizable-panels';
import type Konva from 'konva';
import { useWorkspaceStore, selectToolRejectionMessage } from '@/stores/workspaceStore';
import { FocusProvider } from '@/contexts/FocusContext';
import { useNotificationContext } from '@/contexts/NotificationContext';
import {
  ENABLE_NEW_WORKSPACE,
  TOP_TOOLBAR_HEIGHT,
  BOTTOM_STATUS_BAR_HEIGHT,
} from '@/lib/constants';
import { apiClient } from '@/api/client';
import { getProjectSheets, type SheetInfo } from '@/api/sheets';
import { projectsApi } from '@/api/projects';
import { updateTitleBlockRegion } from '@/api/documents';
import { useReviewActions } from '@/hooks/useReviewActions';
import { useReviewKeyboardShortcuts } from '@/hooks/useReviewKeyboardShortcuts';
import { useAiAssist } from '@/hooks/useAiAssist';
import { useUndoRedo } from '@/hooks/useUndoRedo';
import { useScaleCalibration } from '@/hooks/useScaleCalibration';
import { useScaleDetection } from '@/hooks/useScaleDetection';
import { pollUntil } from '@/utils/polling';
import { TopToolbar } from './TopToolbar';
import { BottomStatusBar } from './BottomStatusBar';
import { CenterCanvas } from './CenterCanvas';
import { RightPanel } from './RightPanel';
import { SheetTree } from '@/components/sheets/SheetTree';
import { PlanOverlayView } from '@/components/document/PlanOverlayView';
import { ScaleCalibrationDialog } from '@/components/viewer/ScaleCalibrationDialog';
import { Loader2 } from 'lucide-react';
import type { Page } from '@/types';

export function TakeoffWorkspace() {
  const { id: projectId } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const { addNotification } = useNotificationContext();
  const activeSheetId = useWorkspaceStore((s) => s.activeSheetId);
  const leftPanelCollapsed = useWorkspaceStore((s) => s.leftPanelCollapsed);
  const rightPanelCollapsed = useWorkspaceStore((s) => s.rightPanelCollapsed);
  const toolRejectionMessage = useWorkspaceStore(selectToolRejectionMessage);
  const clearToolRejection = useWorkspaceStore((s) => s.clearToolRejection);

  const [toastVisible, setToastVisible] = useState(false);
  const [toastText, setToastText] = useState('');
  const [compareState, setCompareState] = useState<{
    oldDocId: string;
    newDocId: string;
    maxPages: number;
  } | null>(null);

  useEffect(() => {
    if (toolRejectionMessage) {
      setToastText(toolRejectionMessage);
      setToastVisible(true);
      clearToolRejection();
    }
  }, [toolRejectionMessage, clearToolRejection]);

  useEffect(() => {
    if (toastVisible) {
      const timer = setTimeout(() => setToastVisible(false), 3000);
      return () => clearTimeout(timer);
    }
  }, [toastVisible]);

  // All hooks must be called before any early returns
  const {
    isLoading: isLoadingProject,
    error: projectError,
  } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => projectsApi.get(projectId!),
    enabled: !!projectId,
  });

  const {
    data: sheetsData,
    isLoading: isLoadingSheets,
  } = useQuery({
    queryKey: ['project-sheets', projectId],
    queryFn: () => getProjectSheets(projectId!),
    enabled: !!projectId,
  });

  const activeSheet: SheetInfo | null = useMemo(() => {
    if (!sheetsData || !activeSheetId) return null;
    for (const group of sheetsData.groups) {
      const found = group.sheets.find((s) => s.id === activeSheetId);
      if (found) return found;
    }
    return null;
  }, [sheetsData, activeSheetId]);

  const [isLoadingSheetImage, setIsLoadingSheetImage] = useState(false);

  useEffect(() => {
    if (activeSheet?.image_url) {
      setIsLoadingSheetImage(true);
      let stale = false;
      const img = new Image();
      img.onload = () => { if (!stale) setIsLoadingSheetImage(false); };
      img.onerror = () => { if (!stale) setIsLoadingSheetImage(false); };
      img.src = activeSheet.image_url;
      return () => {
        stale = true;
        img.onload = null;
        img.onerror = null;
      };
    } else {
      setIsLoadingSheetImage(false);
    }
  }, [activeSheet?.image_url]);

  // ---------------------------------------------------------------------------
  // Fetch full Page data for scale_calibration_data and title_block_region
  // ---------------------------------------------------------------------------
  const { data: pageData } = useQuery({
    queryKey: ['page', activeSheetId],
    queryFn: async () => {
      const response = await apiClient.get<Page>(`/pages/${activeSheetId}`);
      return response.data;
    },
    enabled: !!activeSheetId,
  });

  // ---------------------------------------------------------------------------
  // Undo/Redo (lifted to workspace so TopToolbar can access)
  // ---------------------------------------------------------------------------
  const undoRedo = useUndoRedo();

  const handleUndo = useCallback(() => {
    void undoRedo.undo();
  }, [undoRedo]);

  const handleRedo = useCallback(() => {
    void undoRedo.redo();
  }, [undoRedo]);

  // ---------------------------------------------------------------------------
  // Scale Calibration
  // ---------------------------------------------------------------------------
  const scaleCalibration = useScaleCalibration();
  const [showCalibrationDialog, setShowCalibrationDialog] = useState(false);
  const [calibrationCurrentPoint, setCalibrationCurrentPoint] = useState<{ x: number; y: number } | null>(null);

  const handleScaleUpdated = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['page', activeSheetId] });
    queryClient.refetchQueries({ queryKey: ['page', activeSheetId] });
    queryClient.invalidateQueries({ queryKey: ['project-sheets', projectId] });
  }, [queryClient, activeSheetId, projectId]);

  const handleCalibrationClick = useCallback((e: Konva.KonvaEventObject<MouseEvent>) => {
    if (!scaleCalibration.state.isCalibrating) return;
    if (e.evt.button !== 0) return;

    const stage = e.target.getStage();
    if (!stage) return;
    const pos = stage.getRelativePointerPosition();
    if (!pos) return;

    if (!scaleCalibration.state.isDrawing) {
      scaleCalibration.startDrawing({ x: pos.x, y: pos.y });
    } else {
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

  const handleSetScale = useCallback(() => {
    setShowCalibrationDialog(true);
  }, []);

  // ---------------------------------------------------------------------------
  // Scale Detection
  // ---------------------------------------------------------------------------
  const scaleDetection = useScaleDetection(activeSheetId ?? undefined, pageData);

  // ---------------------------------------------------------------------------
  // Scale Location Display
  // ---------------------------------------------------------------------------
  const [showScaleLocation, setShowScaleLocation] = useState(false);

  const scaleLocationBbox = useMemo(() => {
    return pageData?.scale_calibration_data?.best_scale?.bbox ?? null;
  }, [pageData]);

  // ---------------------------------------------------------------------------
  // Title Block Mode
  // ---------------------------------------------------------------------------
  const [isTitleBlockMode, setIsTitleBlockMode] = useState(false);
  const [showTitleBlockRegion, setShowTitleBlockRegion] = useState(true);
  const [titleBlockStart, setTitleBlockStart] = useState<{ x: number; y: number } | null>(null);
  const [titleBlockCurrent, setTitleBlockCurrent] = useState<{ x: number; y: number } | null>(null);
  const [pendingTitleBlock, setPendingTitleBlock] = useState<{ x: number; y: number; width: number; height: number } | null>(null);
  const [isSavingTitleBlock, setIsSavingTitleBlock] = useState(false);

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

    useWorkspaceStore.getState().resetDrawingState();
    setIsTitleBlockMode(true);
    resetTitleBlockSelection();
  }, [isSavingTitleBlock, isTitleBlockMode, resetTitleBlockSelection, scaleCalibration]);

  const handleTitleBlockClick = useCallback((e: Konva.KonvaEventObject<MouseEvent>) => {
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
    if (rect.width < 10 || rect.height < 10) {
      addNotification('warning', 'Selection too small', 'Title block region must be at least 10x10 pixels.');
      resetTitleBlockSelection();
      return;
    }

    setPendingTitleBlock(rect);
    setTitleBlockStart(null);
    setTitleBlockCurrent(null);
  }, [addNotification, getRectFromPoints, isTitleBlockMode, resetTitleBlockSelection, titleBlockStart]);

  const handleTitleBlockMouseMove = useCallback((e: Konva.KonvaEventObject<MouseEvent>) => {
    if (!isTitleBlockMode || !titleBlockStart) return;

    const stage = e.target.getStage();
    if (!stage) return;
    const pos = stage.getRelativePointerPosition();
    if (!pos) return;

    setTitleBlockCurrent({ x: pos.x, y: pos.y });
  }, [isTitleBlockMode, titleBlockStart]);

  const fetchPage = useCallback(async () => {
    const response = await apiClient.get<Page>(`/pages/${activeSheetId}`);
    return response.data;
  }, [activeSheetId]);

  const handleSaveTitleBlockRegion = useCallback(async () => {
    if (!pendingTitleBlock || !activeSheet || !activeSheet.width || !activeSheet.height) return;

    const clamp = (value: number, min: number, max: number) =>
      Math.max(min, Math.min(value, max));

    const normalized = {
      x: clamp(pendingTitleBlock.x / activeSheet.width, 0, 1),
      y: clamp(pendingTitleBlock.y / activeSheet.height, 0, 1),
      width: clamp(pendingTitleBlock.width / activeSheet.width, 0, 1),
      height: clamp(pendingTitleBlock.height / activeSheet.height, 0, 1),
      source_page_id: activeSheetId!,
    };
    normalized.width = Math.min(normalized.width, 1 - normalized.x);
    normalized.height = Math.min(normalized.height, 1 - normalized.y);
    if (normalized.width <= 0 || normalized.height <= 0) {
      addNotification('warning', 'Invalid selection', 'Title block region must stay within the page bounds.');
      return;
    }

    const previousSheetNumber = pageData?.sheet_number ?? null;
    const previousTitle = pageData?.title ?? null;

    setIsSavingTitleBlock(true);
    try {
      const result = await updateTitleBlockRegion(activeSheet.document_id, normalized);
      addNotification('success', 'Title block region saved', `OCR queued for ${result.pages_queued} pages.`);

      await pollUntil<Page>({
        fetcher: fetchPage,
        shouldStop: (updatedPage) => {
          const hasRegion = !!updatedPage.document?.title_block_region;
          const sheetNumberChanged = updatedPage.sheet_number !== previousSheetNumber;
          const titleChanged = updatedPage.title !== previousTitle;
          const hasSheetOrTitle = !!updatedPage.sheet_number || !!updatedPage.title;
          return hasRegion && (sheetNumberChanged || titleChanged || hasSheetOrTitle);
        },
        onTick: (updatedPage) => queryClient.setQueryData(['page', activeSheetId], updatedPage),
        intervalMs: 2000,
        maxAttempts: 15,
        initialDelayMs: 2000,
      });

      queryClient.invalidateQueries({ queryKey: ['page', activeSheetId] });
      queryClient.invalidateQueries({ queryKey: ['project-sheets', projectId] });
      setShowTitleBlockRegion(true);
      setIsTitleBlockMode(false);
      resetTitleBlockSelection();
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to save title block region.';
      addNotification('error', 'Save failed', message);
    } finally {
      setIsSavingTitleBlock(false);
    }
  }, [addNotification, activeSheet, activeSheetId, fetchPage, pageData, pendingTitleBlock, projectId, queryClient, resetTitleBlockSelection]);

  // Compute title block display rects
  const existingTitleBlockRect = useMemo(() => {
    const region = pageData?.document?.title_block_region;
    if (!region || !activeSheet?.width || !activeSheet?.height) return null;
    return {
      x: region.x * activeSheet.width,
      y: region.y * activeSheet.height,
      width: region.width * activeSheet.width,
      height: region.height * activeSheet.height,
    };
  }, [pageData, activeSheet]);

  const titleBlockDraftRect = useMemo(() => {
    if (pendingTitleBlock) return pendingTitleBlock;
    if (titleBlockStart && titleBlockCurrent) return getRectFromPoints(titleBlockStart, titleBlockCurrent);
    return null;
  }, [pendingTitleBlock, titleBlockStart, titleBlockCurrent, getRectFromPoints]);

  // Cancel title block and calibration on sheet switch
  useEffect(() => {
    setIsTitleBlockMode(false);
    resetTitleBlockSelection();
    scaleCalibration.cancelCalibration();
    setShowCalibrationDialog(false);
    setShowScaleLocation(false);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeSheetId]);

  // Review mode integration
  const reviewCurrentId = useWorkspaceStore((s) => s.reviewCurrentId);
  const { approve, reject, autoAccept, isAutoAccepting } = useReviewActions(
    activeSheetId ?? undefined,
    projectId,
  );

  const handleReviewApprove = useCallback(() => {
    if (!reviewCurrentId) return;
    approve({ measurementId: reviewCurrentId, reviewer: 'user' });
  }, [reviewCurrentId, approve]);

  const handleReviewReject = useCallback(() => {
    if (!reviewCurrentId) return;
    reject({ measurementId: reviewCurrentId, reviewer: 'user', reason: 'Rejected via keyboard shortcut' });
  }, [reviewCurrentId, reject]);

  const handleReviewEdit = useCallback(() => {}, []);

  const handleAutoAccept = useCallback((threshold: number) => {
    autoAccept({ threshold });
  }, [autoAccept]);

  useReviewKeyboardShortcuts({
    pageId: activeSheetId ?? undefined,
    onApprove: handleReviewApprove,
    onReject: handleReviewReject,
    onEdit: handleReviewEdit,
  });

  // Derive document ID from active sheet for revision panel
  const activeDocumentId = activeSheet?.document_id ?? null;

  const handleCompare = useCallback(
    (oldDocId: string, newDocId: string) => {
      const maxPages = Math.max(
        ...(sheetsData?.groups.flatMap((g) => g.sheets.map((s) => s.page_number)) ?? [1]),
      );
      setCompareState({ oldDocId, newDocId, maxPages });
    },
    [sheetsData],
  );

  // Batch AI Assist
  const { runBatchAi, isRunning: isBatchAiRunning } = useAiAssist(
    projectId ?? null,
    activeSheetId,
  );

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        if (isTitleBlockMode) {
          setIsTitleBlockMode(false);
          resetTitleBlockSelection();
          return;
        }
        if (scaleCalibration.state.isCalibrating) {
          scaleCalibration.cancelCalibration();
          return;
        }
        useWorkspaceStore.getState().escapeAll();
      }
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isTitleBlockMode, resetTitleBlockSelection, scaleCalibration]);

  // Feature flag gate
  if (!ENABLE_NEW_WORKSPACE) {
    return <Navigate to={`/projects/${projectId}`} replace />;
  }

  if (!projectId) {
    return (
      <div className="flex h-screen items-center justify-center bg-neutral-950 text-neutral-400">
        <p>Project ID missing</p>
      </div>
    );
  }

  if (projectError) {
    return (
      <div className="flex h-screen items-center justify-center bg-neutral-950 text-neutral-400" data-testid="project-not-found">
        <div className="text-center">
          <p className="text-lg font-medium">Project not found</p>
          <p className="mt-1 text-sm">The project you're looking for doesn't exist or has been removed.</p>
        </div>
      </div>
    );
  }

  if (isLoadingProject) {
    return (
      <div className="flex h-screen items-center justify-center bg-neutral-950 text-neutral-400">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <FocusProvider>
      <div className="flex h-screen flex-col bg-neutral-950" data-testid="takeoff-workspace">
        {/* Top Toolbar */}
        <TopToolbar
          projectId={projectId}
          onAutoAccept={handleAutoAccept}
          isAutoAccepting={isAutoAccepting}
          onRunBatchAi={runBatchAi}
          isBatchAiRunning={isBatchAiRunning}
          onUndo={handleUndo}
          onRedo={handleRedo}
          canUndo={undoRedo.canUndo}
          canRedo={undoRedo.canRedo}
          onSetScale={handleSetScale}
          onDetectScale={scaleDetection.detectScale}
          isDetectingScale={scaleDetection.isDetecting}
          onToggleScaleLocation={() => setShowScaleLocation((prev) => !prev)}
          showScaleLocation={showScaleLocation}
          hasScaleLocation={!!scaleLocationBbox}
          onToggleTitleBlockMode={handleToggleTitleBlockMode}
          isTitleBlockMode={isTitleBlockMode}
          onToggleTitleBlockRegion={() => setShowTitleBlockRegion((prev) => !prev)}
          showTitleBlockRegion={showTitleBlockRegion}
          hasTitleBlockRegion={!!existingTitleBlockRect}
        />

        {/* Main Content Area */}
        <div
          className="flex-1 overflow-hidden"
          style={{
            height: `calc(100vh - ${TOP_TOOLBAR_HEIGHT}px - ${BOTTOM_STATUS_BAR_HEIGHT}px)`,
          }}
        >
          <Group orientation="horizontal" id="workspace-panels">
            {/* Left Sidebar - Sheet Tree */}
            {!leftPanelCollapsed && (
              <>
                <Panel
                  id="left-sidebar"
                  defaultSize={20}
                  minSize={15}
                  maxSize={35}
                  data-testid="left-sidebar"
                >
                  <div className="h-full overflow-hidden border-r border-neutral-700 bg-neutral-900">
                    <SheetTree
                      projectId={projectId}
                      sheetsData={sheetsData ?? null}
                      isLoading={isLoadingSheets}
                    />
                  </div>
                </Panel>
                <Separator className="w-1 bg-neutral-800 hover:bg-blue-600 transition-colors" />
              </>
            )}

            {/* Center Canvas */}
            <Panel id="center-canvas" minSize={30}>
              <CenterCanvas
                projectId={projectId}
                pageId={activeSheetId ?? undefined}
                isLoadingSheet={isLoadingSheetImage}
                sheetImageUrl={activeSheet?.image_url}
                scaleValue={activeSheet?.scale_value}
                pixelsPerUnit={
                  activeSheet?.scale_calibrated && activeSheet?.scale_value
                    ? activeSheet.scale_value
                    : undefined
                }
                isScaleCalibrated={activeSheet?.scale_calibrated}
                activeSheetScaleUnit={pageData?.scale_unit}
                undoRedo={undoRedo}
                calibrationState={scaleCalibration.state}
                calibrationCurrentPoint={calibrationCurrentPoint}
                onCalibrationClick={handleCalibrationClick}
                onCalibrationMouseMove={handleCalibrationMouseMove}
                scaleDetectionResult={scaleDetection.detectionResult}
                scaleHighlightBox={scaleDetection.scaleHighlightBox}
                onDismissDetection={scaleDetection.dismissResult}
                showScaleLocation={showScaleLocation}
                scaleLocationBbox={scaleLocationBbox}
                isTitleBlockMode={isTitleBlockMode}
                showTitleBlockRegion={showTitleBlockRegion}
                titleBlockRegion={existingTitleBlockRect}
                onTitleBlockClick={handleTitleBlockClick}
                onTitleBlockMouseMove={handleTitleBlockMouseMove}
                titleBlockDraftRect={titleBlockDraftRect}
              />
            </Panel>

            {/* Right Panel - Conditions */}
            {!rightPanelCollapsed && (
              <>
                <Separator className="w-1 bg-neutral-800 hover:bg-blue-600 transition-colors" />
                <Panel
                  id="right-panel"
                  defaultSize={25}
                  minSize={18}
                  maxSize={40}
                  data-testid="right-panel-wrapper"
                >
                  <RightPanel
                  projectId={projectId}
                  pageId={activeSheetId ?? undefined}
                  documentId={activeDocumentId ?? undefined}
                  onCompare={handleCompare}
                />
                </Panel>
              </>
            )}
          </Group>
        </div>

        {/* Plan Overlay Comparison View */}
        {compareState && (
          <PlanOverlayView
            oldDocumentId={compareState.oldDocId}
            newDocumentId={compareState.newDocId}
            maxPageCount={compareState.maxPages}
            onClose={() => setCompareState(null)}
          />
        )}

        {/* Bottom Status Bar */}
        <BottomStatusBar projectId={projectId} />

        {/* Scale Calibration Dialog */}
        <ScaleCalibrationDialog
          open={showCalibrationDialog}
          onOpenChange={setShowCalibrationDialog}
          page={pageData}
          pageId={activeSheetId ?? undefined}
          onScaleUpdated={handleScaleUpdated}
          calibrationState={scaleCalibration.state}
          onStartCalibration={scaleCalibration.startCalibration}
          onCancelCalibration={scaleCalibration.cancelCalibration}
          onClearLine={scaleCalibration.clearLine}
          onSubmitCalibration={scaleCalibration.submitCalibration}
        />

        {/* Title block save banner */}
        {isTitleBlockMode && pendingTitleBlock && (
          <div className="fixed bottom-16 left-1/2 z-50 -translate-x-1/2 rounded-lg border border-sky-500/50 bg-sky-900/90 px-4 py-2 shadow-lg">
            <div className="flex items-center gap-3">
              <span className="text-sm text-sky-200">Title block region selected</span>
              <button
                onClick={handleSaveTitleBlockRegion}
                disabled={isSavingTitleBlock}
                className="rounded bg-sky-500 px-3 py-1 text-xs font-medium text-black hover:bg-sky-400 disabled:opacity-60"
              >
                {isSavingTitleBlock ? 'Saving...' : 'Save & Re-run OCR'}
              </button>
              <button
                onClick={resetTitleBlockSelection}
                className="rounded bg-neutral-700 px-3 py-1 text-xs text-neutral-200 hover:bg-neutral-600"
              >
                Reset
              </button>
            </div>
          </div>
        )}

        {/* Tool rejection toast */}
        {toastVisible && (
          <div
            className="fixed bottom-12 left-1/2 z-50 -translate-x-1/2 rounded-lg bg-amber-600 px-4 py-2 text-sm font-medium text-white shadow-lg"
            role="alert"
          >
            {toastText}
          </div>
        )}
      </div>
    </FocusProvider>
  );
}
