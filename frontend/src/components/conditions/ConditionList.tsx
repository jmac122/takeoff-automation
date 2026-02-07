import { Eye, EyeOff } from 'lucide-react';
import { useWorkspaceStore } from '@/stores/workspaceStore';
import { useUpdateCondition } from '@/hooks/useConditions';
import type { Condition } from '@/types';

interface ConditionListProps {
  conditions: Condition[];
  projectId: string;
  onContextMenu?: (e: React.MouseEvent, condition: Condition) => void;
}

const UNIT_LABELS: Record<string, string> = {
  LF: 'LF',
  SF: 'SF',
  CY: 'CY',
  EA: 'EA',
};

function formatQuantity(qty: number): string {
  if (qty === 0) return '0';
  if (qty >= 1000) return `${(qty / 1000).toFixed(1)}k`;
  if (qty >= 100) return qty.toFixed(0);
  return qty.toFixed(1);
}

export function ConditionList({ conditions, projectId, onContextMenu }: ConditionListProps) {
  const activeConditionId = useWorkspaceStore((s) => s.activeConditionId);
  const setActiveCondition = useWorkspaceStore((s) => s.setActiveCondition);
  const updateCondition = useUpdateCondition(projectId);

  const handleToggleVisibility = (e: React.MouseEvent, condition: Condition) => {
    e.stopPropagation();
    updateCondition.mutate({
      conditionId: condition.id,
      data: { is_visible: !condition.is_visible },
    });
  };

  if (conditions.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center px-3 py-8 text-center" data-testid="condition-list-empty">
        <p className="text-xs text-neutral-500">No conditions yet.</p>
        <p className="mt-1 text-[10px] text-neutral-600">
          Use the button above to create your first condition.
        </p>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto" data-testid="condition-list">
      {conditions.map((condition, index) => {
        const isActive = condition.id === activeConditionId;
        return (
          <div
            key={condition.id}
            role="button"
            tabIndex={0}
            onClick={() => setActiveCondition(isActive ? null : condition.id)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                setActiveCondition(isActive ? null : condition.id);
              }
            }}
            onContextMenu={(e) => onContextMenu?.(e, condition)}
            className={`flex w-full cursor-pointer items-center gap-2 border-b border-neutral-800 px-3 py-2 text-left transition-colors ${
              isActive
                ? 'bg-blue-900/30 border-l-2 border-l-blue-500'
                : 'hover:bg-neutral-800/50 border-l-2 border-l-transparent'
            } ${!condition.is_visible ? 'opacity-50' : ''}`}
            data-testid={`condition-row-${index}`}
          >
            {/* Color dot */}
            <span
              className="h-3 w-3 flex-shrink-0 rounded-full"
              style={{ backgroundColor: condition.color }}
            />

            {/* Name and quantity */}
            <div className="min-w-0 flex-1">
              <div className="truncate text-xs font-medium text-neutral-200">
                {condition.name}
              </div>
              {condition.measurement_count > 0 && (
                <div className="text-[10px] text-neutral-500">
                  {condition.measurement_count} measurement{condition.measurement_count !== 1 ? 's' : ''}
                </div>
              )}
            </div>

            {/* Total */}
            <div className="flex-shrink-0 text-right">
              <span className="text-xs font-medium text-neutral-300">
                {formatQuantity(condition.total_quantity)}
              </span>
              <span className="ml-0.5 text-[10px] text-neutral-500">
                {UNIT_LABELS[condition.unit] ?? condition.unit}
              </span>
            </div>

            {/* Visibility toggle */}
            <button
              onClick={(e) => handleToggleVisibility(e, condition)}
              className="ml-1 flex-shrink-0 rounded p-0.5 text-neutral-500 hover:bg-neutral-700 hover:text-neutral-300"
              title={condition.is_visible ? 'Hide measurements' : 'Show measurements'}
              data-testid={`visibility-toggle-${index}`}
            >
              {condition.is_visible ? (
                <Eye className="h-3.5 w-3.5" />
              ) : (
                <EyeOff className="h-3.5 w-3.5" />
              )}
            </button>

            {/* Shortcut indicator */}
            {index < 9 && (
              <span className="flex-shrink-0 rounded bg-neutral-800 px-1 py-0.5 text-[9px] text-neutral-600">
                {index + 1}
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
}
