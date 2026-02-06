import { useEffect, useMemo, useState } from 'react';
import { useParams, Navigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Panel, Group, Separator } from 'react-resizable-panels';
import { useWorkspaceStore, selectToolRejectionMessage } from '@/stores/workspaceStore';
import { FocusProvider } from '@/contexts/FocusContext';
import {
  ENABLE_NEW_WORKSPACE,
  TOP_TOOLBAR_HEIGHT,
  BOTTOM_STATUS_BAR_HEIGHT,
} from '@/lib/constants';
import { getProjectSheets, type SheetInfo } from '@/api/sheets';
import { projectsApi } from '@/api/projects';
import { TopToolbar } from './TopToolbar';
import { BottomStatusBar } from './BottomStatusBar';
import { CenterCanvas } from './CenterCanvas';
import { RightPanel } from './RightPanel';
import { SheetTree } from '@/components/sheets/SheetTree';
import { Loader2 } from 'lucide-react';

export function TakeoffWorkspace() {
  const { id: projectId } = useParams<{ id: string }>();
  const activeSheetId = useWorkspaceStore((s) => s.activeSheetId);
  const leftPanelCollapsed = useWorkspaceStore((s) => s.leftPanelCollapsed);
  const rightPanelCollapsed = useWorkspaceStore((s) => s.rightPanelCollapsed);
  const toolRejectionMessage = useWorkspaceStore(selectToolRejectionMessage);
  const clearToolRejection = useWorkspaceStore((s) => s.clearToolRejection);

  const [toastVisible, setToastVisible] = useState(false);
  const [toastText, setToastText] = useState('');

  useEffect(() => {
    if (toolRejectionMessage) {
      setToastText(toolRejectionMessage);
      setToastVisible(true);
      clearToolRejection();
      const timer = setTimeout(() => setToastVisible(false), 3000);
      return () => clearTimeout(timer);
    }
  }, [toolRejectionMessage, clearToolRejection]);

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

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        useWorkspaceStore.getState().escapeAll();
      }
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

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

  // 404 handling
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

  // Loading state
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
        <TopToolbar />

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
                isLoadingSheet={isLoadingSheetImage}
                sheetImageUrl={activeSheet?.image_url}
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
                  <RightPanel projectId={projectId} />
                </Panel>
              </>
            )}
          </Group>
        </div>

        {/* Bottom Status Bar */}
        <BottomStatusBar />

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
