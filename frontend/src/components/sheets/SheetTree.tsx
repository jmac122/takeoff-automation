import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useWorkspaceStore } from '@/stores/workspaceStore';
import {
  LS_SHEET_TREE_STATE,
} from '@/lib/constants';
import type { SheetsResponse, SheetInfo, SheetGroup } from '@/api/sheets';
import {
  ChevronDown,
  ChevronRight,
  FileText,
  Search,
  Grid3x3,
  List,
  Loader2,
  MoreHorizontal,
} from 'lucide-react';
import { ScaleBadge } from './ScaleBadge';
import { SheetContextMenu } from './SheetContextMenu';
import { ThumbnailStrip } from './ThumbnailStrip';

// ============================================================================
// Props
// ============================================================================

interface SheetTreeProps {
  projectId: string;
  sheetsData: SheetsResponse | null;
  isLoading: boolean;
}

// ============================================================================
// Component
// ============================================================================

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function SheetTree({ projectId, sheetsData, isLoading }: SheetTreeProps) {
  const activeSheetId = useWorkspaceStore((s) => s.activeSheetId);
  const setActiveSheet = useWorkspaceStore((s) => s.setActiveSheet);
  const highlightedSheetId = useWorkspaceStore((s) => s.highlightedSheetId);
  const setHighlightedSheet = useWorkspaceStore((s) => s.setHighlightedSheet);
  const expandedGroups = useWorkspaceStore((s) => s.expandedGroups);
  const toggleGroupExpanded = useWorkspaceStore((s) => s.toggleGroupExpanded);
  const setExpandedGroups = useWorkspaceStore((s) => s.setExpandedGroups);
  const sheetSearchQuery = useWorkspaceStore((s) => s.sheetSearchQuery);
  const setSheetSearchQuery = useWorkspaceStore((s) => s.setSheetSearchQuery);
  const sheetViewMode = useWorkspaceStore((s) => s.sheetViewMode);
  const setSheetViewMode = useWorkspaceStore((s) => s.setSheetViewMode);
  const setFocusRegion = useWorkspaceStore((s) => s.setFocusRegion);

  // Context menu state
  const [contextMenu, setContextMenu] = useState<{
    x: number;
    y: number;
    sheet: SheetInfo;
  } | null>(null);

  const treeRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  const hasInitializedRef = useRef(false);

  // ---- Load persisted tree state OR initialize from sheetsData ----
  // Combined into a single effect to avoid race conditions between
  // load, persist, and initialize effects sharing stale closures.
  useEffect(() => {
    if (hasInitializedRef.current) return;

    // Try to load from localStorage first
    try {
      const saved = localStorage.getItem(LS_SHEET_TREE_STATE);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed.expandedGroups && Object.keys(parsed.expandedGroups).length > 0) {
          setExpandedGroups(parsed.expandedGroups);
          hasInitializedRef.current = true;
          return;
        }
      }
    } catch {
      // ignore invalid JSON
    }

    // If no persisted state, initialize from sheetsData
    if (sheetsData && sheetsData.groups.length > 0) {
      const initial: Record<string, boolean> = {};
      for (const group of sheetsData.groups) {
        initial[group.group_name] = true;
      }
      setExpandedGroups(initial);
      hasInitializedRef.current = true;
    }
  }, [sheetsData, setExpandedGroups]);

  // ---- Persist tree state on change ----
  // Skips writing until state has been initialized, preventing the
  // initial empty {} from overwriting saved preferences in localStorage.
  useEffect(() => {
    if (!hasInitializedRef.current) return;
    if (Object.keys(expandedGroups).length === 0) return;
    try {
      localStorage.setItem(
        LS_SHEET_TREE_STATE,
        JSON.stringify({ expandedGroups }),
      );
    } catch {
      // ignore quota errors
    }
  }, [expandedGroups]);

  // ---- Filter sheets by search ----
  const filteredGroups: SheetGroup[] = useMemo(() => {
    if (!sheetsData) return [];
    if (!sheetSearchQuery.trim()) return sheetsData.groups;

    const query = sheetSearchQuery.toLowerCase().trim();
    return sheetsData.groups
      .map((group) => ({
        ...group,
        sheets: group.sheets.filter((sheet) => {
          const name =
            sheet.display_name ||
            sheet.title ||
            sheet.sheet_number ||
            `Page ${sheet.page_number}`;
          return name.toLowerCase().includes(query);
        }),
      }))
      .filter((group) => group.sheets.length > 0);
  }, [sheetsData, sheetSearchQuery]);

  // ---- Flat list of visible sheets for keyboard navigation ----
  const flatVisibleSheets: SheetInfo[] = useMemo(() => {
    const sheets: SheetInfo[] = [];
    for (const group of filteredGroups) {
      if (expandedGroups[group.group_name] !== false) {
        sheets.push(...group.sheets);
      }
    }
    return sheets;
  }, [filteredGroups, expandedGroups]);

  // ---- Keyboard navigation ----
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (flatVisibleSheets.length === 0) return;

      const currentId = highlightedSheetId || activeSheetId;
      const currentIndex = currentId
        ? flatVisibleSheets.findIndex((s) => s.id === currentId)
        : -1;

      switch (e.key) {
        case 'ArrowDown': {
          e.preventDefault();
          const nextIdx = Math.min(currentIndex + 1, flatVisibleSheets.length - 1);
          setHighlightedSheet(flatVisibleSheets[nextIdx].id);
          scrollSheetIntoView(flatVisibleSheets[nextIdx].id);
          break;
        }
        case 'ArrowUp': {
          e.preventDefault();
          const prevIdx = Math.max(currentIndex - 1, 0);
          setHighlightedSheet(flatVisibleSheets[prevIdx].id);
          scrollSheetIntoView(flatVisibleSheets[prevIdx].id);
          break;
        }
        case 'Enter': {
          e.preventDefault();
          if (highlightedSheetId) {
            setActiveSheet(highlightedSheetId);
          }
          break;
        }
        case 'PageDown': {
          e.preventDefault();
          const jumpDown = Math.min(currentIndex + 10, flatVisibleSheets.length - 1);
          setHighlightedSheet(flatVisibleSheets[jumpDown].id);
          scrollSheetIntoView(flatVisibleSheets[jumpDown].id);
          break;
        }
        case 'PageUp': {
          e.preventDefault();
          const jumpUp = Math.max(currentIndex - 10, 0);
          setHighlightedSheet(flatVisibleSheets[jumpUp].id);
          scrollSheetIntoView(flatVisibleSheets[jumpUp].id);
          break;
        }
        case 'Home': {
          e.preventDefault();
          if (flatVisibleSheets.length > 0) {
            setHighlightedSheet(flatVisibleSheets[0].id);
            scrollSheetIntoView(flatVisibleSheets[0].id);
          }
          break;
        }
        case 'End': {
          e.preventDefault();
          if (flatVisibleSheets.length > 0) {
            const last = flatVisibleSheets[flatVisibleSheets.length - 1];
            setHighlightedSheet(last.id);
            scrollSheetIntoView(last.id);
          }
          break;
        }
      }
    },
    [flatVisibleSheets, highlightedSheetId, activeSheetId, setHighlightedSheet, setActiveSheet],
  );

  function scrollSheetIntoView(sheetId: string) {
    const el = treeRef.current?.querySelector(`[data-sheet-id="${sheetId}"]`);
    if (el) {
      el.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    }
  }

  // ---- Context menu handlers ----
  const handleContextMenu = useCallback(
    (e: React.MouseEvent, sheet: SheetInfo) => {
      e.preventDefault();
      setContextMenu({ x: e.clientX, y: e.clientY, sheet });
    },
    [],
  );

  const closeContextMenu = useCallback(() => {
    setContextMenu(null);
  }, []);

  // ---- Sheet display name ----
  function getSheetDisplayName(sheet: SheetInfo): string {
    return (
      sheet.display_name ||
      sheet.title ||
      (sheet.sheet_number ? `Sheet ${sheet.sheet_number}` : `Page ${sheet.page_number}`)
    );
  }

  // ---- Render ----
  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center" data-testid="sheet-tree-loading">
        <Loader2 className="h-5 w-5 animate-spin text-neutral-400" />
      </div>
    );
  }

  if (!sheetsData || sheetsData.total === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center p-4 text-center" data-testid="sheet-tree-empty">
        <FileText className="mb-2 h-8 w-8 text-neutral-600" />
        <p className="text-sm text-neutral-400">No sheets found</p>
        <p className="mt-1 text-xs text-neutral-500">
          Upload documents to this project to see sheets here.
        </p>
      </div>
    );
  }

  return (
    <div
      className="flex h-full flex-col"
      data-focus-region="sheet-tree"
      data-testid="sheet-tree"
    >
      {/* Header with search and view toggle */}
      <div className="border-b border-neutral-700 p-2">
        <div className="flex items-center gap-1">
          <div className="relative flex-1">
            <Search className="absolute left-2 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-neutral-500" />
            <input
              ref={searchInputRef}
              type="text"
              placeholder="Search sheets..."
              value={sheetSearchQuery}
              onChange={(e) => setSheetSearchQuery(e.target.value)}
              className="w-full rounded bg-neutral-800 py-1.5 pl-7 pr-2 text-xs text-neutral-200 placeholder-neutral-500 outline-none ring-1 ring-neutral-700 focus:ring-blue-500"
              data-testid="sheet-search"
            />
          </div>
          <button
            className={`rounded p-1.5 ${
              sheetViewMode === 'tree'
                ? 'bg-neutral-700 text-white'
                : 'text-neutral-400 hover:text-white'
            }`}
            onClick={() => setSheetViewMode('tree')}
            title="Tree view"
            data-testid="view-mode-tree"
          >
            <List size={14} />
          </button>
          <button
            className={`rounded p-1.5 ${
              sheetViewMode === 'thumbnails'
                ? 'bg-neutral-700 text-white'
                : 'text-neutral-400 hover:text-white'
            }`}
            onClick={() => setSheetViewMode('thumbnails')}
            title="Thumbnail view"
            data-testid="view-mode-thumbnails"
          >
            <Grid3x3 size={14} />
          </button>
        </div>
      </div>

      {/* Sheet list */}
      <div
        ref={treeRef}
        className="flex-1 overflow-y-auto"
        tabIndex={0}
        onKeyDown={handleKeyDown}
        onFocus={() => setFocusRegion('sheet-tree')}
        data-testid="sheet-tree-list"
        role="tree"
      >
        {sheetViewMode === 'thumbnails' ? (
          <ThumbnailStrip
            groups={filteredGroups}
            activeSheetId={activeSheetId}
            onSelectSheet={setActiveSheet}
          />
        ) : (
          filteredGroups.map((group) => (
            <div key={group.group_name} role="treeitem">
              {/* Group header */}
              <button
                className="flex w-full items-center gap-1 px-2 py-1.5 text-xs font-medium text-neutral-300 hover:bg-neutral-800"
                onClick={() => toggleGroupExpanded(group.group_name)}
                data-testid={`group-header-${group.group_name}`}
                role="treeitem"
                aria-expanded={expandedGroups[group.group_name] !== false}
              >
                {expandedGroups[group.group_name] !== false ? (
                  <ChevronDown size={14} />
                ) : (
                  <ChevronRight size={14} />
                )}
                <span className="flex-1 text-left">{group.group_name}</span>
                <span className="text-neutral-500">{group.sheets.length}</span>
              </button>

              {/* Sheets in group */}
              {expandedGroups[group.group_name] !== false && (
                <div role="group">
                  {group.sheets.map((sheet) => {
                    const isActive = activeSheetId === sheet.id;
                    const isHighlighted = highlightedSheetId === sheet.id;

                    return (
                      <div
                        key={sheet.id}
                        data-sheet-id={sheet.id}
                        className={`flex items-center gap-2 cursor-pointer px-3 py-1.5 pl-6 text-xs transition-colors ${
                          isActive
                            ? 'bg-blue-600/20 text-blue-300'
                            : isHighlighted
                              ? 'bg-neutral-800 text-neutral-200'
                              : 'text-neutral-400 hover:bg-neutral-800 hover:text-neutral-200'
                        }`}
                        onClick={() => setActiveSheet(sheet.id)}
                        onContextMenu={(e) => handleContextMenu(e, sheet)}
                        role="treeitem"
                        aria-selected={isActive}
                        data-testid={`sheet-item-${sheet.id}`}
                      >
                        <FileText size={13} className="flex-shrink-0" />
                        <span className="flex-1 truncate">
                          {getSheetDisplayName(sheet)}
                        </span>
                        <ScaleBadge sheet={sheet} />
                        {sheet.measurement_count > 0 && (
                          <span className="rounded bg-neutral-700 px-1 py-0.5 text-[10px] text-neutral-400">
                            {sheet.measurement_count}
                          </span>
                        )}
                        <button
                          className="invisible rounded p-0.5 text-neutral-500 hover:text-neutral-300 group-hover:visible"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleContextMenu(e as unknown as React.MouseEvent, sheet);
                          }}
                        >
                          <MoreHorizontal size={12} />
                        </button>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          ))
        )}

        {filteredGroups.length === 0 && sheetSearchQuery && (
          <div className="p-4 text-center text-xs text-neutral-500" data-testid="no-search-results">
            No sheets match "{sheetSearchQuery}"
          </div>
        )}
      </div>

      {/* Context menu */}
      {contextMenu && (
        <SheetContextMenu
          sheet={contextMenu.sheet}
          x={contextMenu.x}
          y={contextMenu.y}
          onClose={closeContextMenu}
        />
      )}
    </div>
  );
}
