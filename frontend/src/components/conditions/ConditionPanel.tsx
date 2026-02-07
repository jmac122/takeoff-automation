import { useCallback, useEffect, useState } from 'react';
import { useWorkspaceStore } from '@/stores/workspaceStore';
import {
  useConditions,
  useDeleteCondition,
  useDuplicateCondition,
  useUpdateCondition,
  useReorderConditions,
} from '@/hooks/useConditions';
import type { Condition } from '@/types';
import { QuickCreateBar } from './QuickCreateBar';
import { ConditionList } from './ConditionList';
import { PropertiesInspector } from './PropertiesInspector';
import { ConditionContextMenu } from './ConditionContextMenu';

interface ConditionPanelProps {
  projectId: string;
}

export function ConditionPanel({ projectId }: ConditionPanelProps) {
  const { data } = useConditions(projectId);
  const conditions = data?.conditions ?? [];

  const activeConditionId = useWorkspaceStore((s) => s.activeConditionId);
  const setActiveCondition = useWorkspaceStore((s) => s.setActiveCondition);
  const setActiveTool = useWorkspaceStore((s) => s.setActiveTool);
  const focusRegion = useWorkspaceStore((s) => s.focusRegion);
  const setFocusRegion = useWorkspaceStore((s) => s.setFocusRegion);

  const deleteCondition = useDeleteCondition(projectId);
  const duplicateCondition = useDuplicateCondition(projectId);
  const updateCondition = useUpdateCondition(projectId);
  const reorderConditions = useReorderConditions(projectId);

  const [contextMenu, setContextMenu] = useState<{
    condition: Condition;
    position: { x: number; y: number };
  } | null>(null);

  const [deleteConfirm, setDeleteConfirm] = useState<Condition | null>(null);

  const activeCondition = conditions.find((c) => c.id === activeConditionId) ?? null;

  // Clear active condition if it was deleted
  useEffect(() => {
    if (activeConditionId && conditions.length > 0 && !conditions.find((c) => c.id === activeConditionId)) {
      setActiveCondition(null);
      setActiveTool('select');
    }
  }, [activeConditionId, conditions, setActiveCondition, setActiveTool]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Only fire when canvas or conditions panel is focused
      if (focusRegion === 'dialog' || focusRegion === 'search') return;

      // Number keys 1-9: select condition by position
      if (e.key >= '1' && e.key <= '9' && !e.ctrlKey && !e.metaKey && !e.altKey) {
        const index = parseInt(e.key) - 1;
        if (index < conditions.length) {
          setActiveCondition(conditions[index].id);
          e.preventDefault();
        }
        return;
      }

      // V: toggle visibility of active condition
      if (e.key === 'v' && !e.ctrlKey && !e.metaKey && activeConditionId) {
        const cond = conditions.find((c) => c.id === activeConditionId);
        if (cond) {
          updateCondition.mutate({
            conditionId: cond.id,
            data: { is_visible: !cond.is_visible },
          });
          e.preventDefault();
        }
        return;
      }

      // Ctrl+D: duplicate active condition
      if ((e.ctrlKey || e.metaKey) && e.key === 'd' && activeConditionId) {
        duplicateCondition.mutate(activeConditionId);
        e.preventDefault();
        return;
      }

      // Delete: delete active condition (with confirmation)
      if (e.key === 'Delete' && activeConditionId && !e.ctrlKey) {
        const cond = conditions.find((c) => c.id === activeConditionId);
        if (cond) setDeleteConfirm(cond);
        e.preventDefault();
        return;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [
    focusRegion, conditions, activeConditionId,
    setActiveCondition, updateCondition, duplicateCondition,
  ]);

  const handleContextMenu = useCallback((e: React.MouseEvent, condition: Condition) => {
    e.preventDefault();
    setContextMenu({ condition, position: { x: e.clientX, y: e.clientY } });
  }, []);

  const handleDelete = useCallback((condition: Condition) => {
    setDeleteConfirm(condition);
    setFocusRegion('dialog');
  }, [setFocusRegion]);

  const dismissDeleteConfirm = useCallback(() => {
    setDeleteConfirm(null);
    setFocusRegion('conditions');
  }, [setFocusRegion]);

  const confirmDelete = useCallback(() => {
    if (deleteConfirm) {
      if (activeConditionId === deleteConfirm.id) {
        setActiveCondition(null);
        setActiveTool('select');
      }
      deleteCondition.mutate(deleteConfirm.id);
      dismissDeleteConfirm();
    }
  }, [deleteConfirm, activeConditionId, setActiveCondition, setActiveTool, deleteCondition, dismissDeleteConfirm]);

  const handleMoveUp = useCallback((condition: Condition) => {
    const idx = conditions.findIndex((c) => c.id === condition.id);
    if (idx <= 0) return;
    const ids = conditions.map((c) => c.id);
    [ids[idx - 1], ids[idx]] = [ids[idx], ids[idx - 1]];
    reorderConditions.mutate(ids);
  }, [conditions, reorderConditions]);

  const handleMoveDown = useCallback((condition: Condition) => {
    const idx = conditions.findIndex((c) => c.id === condition.id);
    if (idx < 0 || idx >= conditions.length - 1) return;
    const ids = conditions.map((c) => c.id);
    [ids[idx], ids[idx + 1]] = [ids[idx + 1], ids[idx]];
    reorderConditions.mutate(ids);
  }, [conditions, reorderConditions]);

  const handleToggleVisibility = useCallback((condition: Condition) => {
    updateCondition.mutate({
      conditionId: condition.id,
      data: { is_visible: !condition.is_visible },
    });
  }, [updateCondition]);

  const handleCreated = useCallback((conditionId: string) => {
    setActiveCondition(conditionId);
  }, [setActiveCondition]);

  return (
    <div className="flex flex-1 min-h-0 flex-col" data-testid="condition-panel">
      {/* Quick Create */}
      <QuickCreateBar projectId={projectId} onCreated={handleCreated} />

      {/* Condition List */}
      <ConditionList
        conditions={conditions}
        projectId={projectId}
        onContextMenu={handleContextMenu}
      />

      {/* Properties Inspector */}
      <PropertiesInspector
        condition={activeCondition}
        onEdit={() => {/* TODO: open edit modal */}}
        onDelete={activeCondition ? () => handleDelete(activeCondition) : undefined}
      />

      {/* Context Menu */}
      {contextMenu && (
        <ConditionContextMenu
          condition={contextMenu.condition}
          position={contextMenu.position}
          isFirst={conditions[0]?.id === contextMenu.condition.id}
          isLast={conditions[conditions.length - 1]?.id === contextMenu.condition.id}
          onClose={() => setContextMenu(null)}
          onEdit={() => {/* TODO: open edit modal */}}
          onDuplicate={(c) => duplicateCondition.mutate(c.id)}
          onDelete={handleDelete}
          onMoveUp={handleMoveUp}
          onMoveDown={handleMoveDown}
          onToggleVisibility={handleToggleVisibility}
        />
      )}

      {/* Delete confirmation dialog */}
      {deleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="rounded-lg border border-neutral-600 bg-neutral-800 p-4 shadow-xl" data-testid="delete-confirm-dialog">
            <p className="text-sm text-neutral-200">
              Delete &ldquo;{deleteConfirm.name}&rdquo;?
            </p>
            <p className="mt-1 text-xs text-neutral-500">
              This will also delete {deleteConfirm.measurement_count} measurement{deleteConfirm.measurement_count !== 1 ? 's' : ''}.
            </p>
            <div className="mt-3 flex justify-end gap-2">
              <button
                onClick={dismissDeleteConfirm}
                className="rounded px-3 py-1.5 text-xs text-neutral-400 hover:bg-neutral-700"
              >
                Cancel
              </button>
              <button
                onClick={confirmDelete}
                className="rounded bg-red-600 px-3 py-1.5 text-xs text-white hover:bg-red-500"
                data-testid="confirm-delete-btn"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
