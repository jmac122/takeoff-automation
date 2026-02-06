import { useEffect, useRef, useState } from 'react';
import { useWorkspaceStore } from '@/stores/workspaceStore';
import type { SheetInfo } from '@/api/sheets';
import { updatePageDisplay, batchUpdateScale } from '@/api/sheets';
import { useQueryClient } from '@tanstack/react-query';
import { Pencil, Ruler, Copy, Eye, EyeOff } from 'lucide-react';

interface SheetContextMenuProps {
  sheet: SheetInfo;
  x: number;
  y: number;
  onClose: () => void;
}

export function SheetContextMenu({
  sheet,
  x,
  y,
  onClose,
}: SheetContextMenuProps) {
  const menuRef = useRef<HTMLDivElement>(null);
  const queryClient = useQueryClient();
  const selectedSheetIds = useWorkspaceStore((s) => s.selectedSheetIds);
  const [isRenaming, setIsRenaming] = useState(false);
  const [renameValue, setRenameValue] = useState(
    sheet.display_name || sheet.title || sheet.sheet_number || '',
  );

  // Close on click outside or Escape
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        onClose();
      }
    }
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose();
    }
    document.addEventListener('mousedown', handleClick);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handleClick);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [onClose]);

  // Position adjustment
  const adjustedX = Math.min(x, window.innerWidth - 200);
  const adjustedY = Math.min(y, window.innerHeight - 250);

  const handleRename = async () => {
    if (isRenaming) {
      try {
        await updatePageDisplay(sheet.id, { display_name: renameValue });
        queryClient.invalidateQueries({ queryKey: ['project-sheets'] });
      } catch {
        // Toast error in real impl
      }
      setIsRenaming(false);
      onClose();
    } else {
      setIsRenaming(true);
    }
  };

  const handleCopyScale = async () => {
    if (!sheet.scale_value) return;
    const targets = selectedSheetIds.length > 0 ? selectedSheetIds : [];
    if (targets.length === 0) {
      // Copy to clipboard for manual paste
      try {
        await navigator.clipboard.writeText(
          JSON.stringify({
            scale_value: sheet.scale_value,
            scale_text: sheet.scale_text,
            scale_unit: 'foot',
          }),
        );
      } catch {
        // ignore
      }
    } else {
      try {
        await batchUpdateScale(
          targets,
          sheet.scale_value,
          sheet.scale_text ?? undefined,
        );
        queryClient.invalidateQueries({ queryKey: ['project-sheets'] });
      } catch {
        // Toast error
      }
    }
    onClose();
  };

  const handleSetScale = () => {
    // Open scale calibration dialog (placeholder — full impl in Phase C)
    onClose();
  };

  return (
    <div
      ref={menuRef}
      className="fixed z-50 min-w-[180px] rounded border border-neutral-700 bg-neutral-800 py-1 shadow-xl"
      style={{ left: adjustedX, top: adjustedY }}
      data-testid="sheet-context-menu"
    >
      {isRenaming ? (
        <div className="px-2 py-1">
          <input
            autoFocus
            value={renameValue}
            onChange={(e) => setRenameValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleRename();
              if (e.key === 'Escape') {
                setIsRenaming(false);
                onClose();
              }
            }}
            className="w-full rounded bg-neutral-700 px-2 py-1 text-xs text-neutral-200 outline-none ring-1 ring-blue-500"
          />
          <div className="mt-1 flex justify-end gap-1">
            <button
              onClick={() => { setIsRenaming(false); onClose(); }}
              className="rounded px-2 py-0.5 text-xs text-neutral-400 hover:text-white"
            >
              Cancel
            </button>
            <button
              onClick={handleRename}
              className="rounded bg-blue-600 px-2 py-0.5 text-xs text-white hover:bg-blue-500"
            >
              Save
            </button>
          </div>
        </div>
      ) : (
        <>
          <MenuItem
            icon={<Pencil size={13} />}
            label="Rename"
            onClick={handleRename}
          />
          <MenuItem
            icon={<Ruler size={13} />}
            label="Set Scale..."
            onClick={handleSetScale}
          />
          {sheet.scale_value && (
            <MenuItem
              icon={<Copy size={13} />}
              label={
                selectedSheetIds.length > 0
                  ? `Copy Scale to ${selectedSheetIds.length} sheets`
                  : 'Copy Scale'
              }
              onClick={handleCopyScale}
            />
          )}
          <div className="my-1 border-t border-neutral-700" />
          <MenuItem
            icon={sheet.is_relevant ? <EyeOff size={13} /> : <Eye size={13} />}
            label={sheet.is_relevant ? 'Mark as Irrelevant' : 'Mark as Relevant'}
            onClick={async () => {
              try {
                const { updatePageRelevance } = await import('@/api/sheets');
                await updatePageRelevance(sheet.id, {
                  is_relevant: !sheet.is_relevant,
                });
                queryClient.invalidateQueries({ queryKey: ['project-sheets'] });
              } catch {
                // Toast error
              }
              onClose();
            }}
          />
        </>
      )}
    </div>
  );
}

function MenuItem({
  icon,
  label,
  onClick,
  disabled,
}: {
  icon: React.ReactNode;
  label: string;
  onClick: () => void;
  disabled?: boolean;
}) {
  return (
    <button
      className="flex w-full items-center gap-2 px-3 py-1.5 text-xs text-neutral-300 hover:bg-neutral-700 hover:text-white disabled:opacity-50"
      onClick={onClick}
      disabled={disabled}
    >
      {icon}
      {label}
    </button>
  );
}
