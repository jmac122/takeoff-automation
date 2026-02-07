import { ChevronDown, ChevronRight, Pencil, Trash2 } from 'lucide-react';
import { useState } from 'react';
import type { Condition } from '@/types';

interface PropertiesInspectorProps {
  condition: Condition | null;
  onEdit?: (condition: Condition) => void;
  onDelete?: (condition: Condition) => void;
}

const TYPE_LABELS: Record<string, string> = {
  linear: 'Linear',
  area: 'Area',
  volume: 'Volume',
  count: 'Count',
};

const UNIT_LABELS: Record<string, string> = {
  LF: 'Linear Feet',
  SF: 'Square Feet',
  CY: 'Cubic Yards',
  EA: 'Each',
};

export function PropertiesInspector({ condition, onEdit, onDelete }: PropertiesInspectorProps) {
  const [breakdownOpen, setBreakdownOpen] = useState(false);

  if (!condition) {
    return (
      <div className="border-t border-neutral-700 px-3 py-4" data-testid="properties-empty">
        <p className="text-[10px] text-neutral-600 text-center">
          Select a condition to view properties.
        </p>
      </div>
    );
  }

  return (
    <div className="border-t border-neutral-700" data-testid="properties-inspector">
      <div className="px-3 py-2">
        {/* Condition name header */}
        <div className="flex items-center gap-2 mb-2">
          <span
            className="h-3 w-3 rounded-full flex-shrink-0"
            style={{ backgroundColor: condition.color }}
          />
          <span className="text-xs font-medium text-neutral-200 truncate flex-1">
            {condition.name}
          </span>
          <button
            onClick={() => onEdit?.(condition)}
            className="rounded p-1 text-neutral-500 hover:bg-neutral-700 hover:text-neutral-300"
            title="Edit condition"
            data-testid="edit-condition-btn"
          >
            <Pencil className="h-3 w-3" />
          </button>
          <button
            onClick={() => onDelete?.(condition)}
            className="rounded p-1 text-neutral-500 hover:bg-red-900/50 hover:text-red-400"
            title="Delete condition"
            data-testid="delete-condition-btn"
          >
            <Trash2 className="h-3 w-3" />
          </button>
        </div>

        {/* Properties grid */}
        <div className="space-y-1.5">
          <PropertyRow label="Type" value={TYPE_LABELS[condition.measurement_type] ?? condition.measurement_type} />
          <PropertyRow label="Unit" value={UNIT_LABELS[condition.unit] ?? condition.unit} />

          {(condition.depth != null && condition.depth > 0) && (
            <PropertyRow label="Depth" value={`${condition.depth}"`} />
          )}
          {(condition.thickness != null && condition.thickness > 0) && (
            <PropertyRow label="Thickness" value={`${condition.thickness}"`} />
          )}

          <PropertyRow
            label="Total"
            value={`${condition.total_quantity.toFixed(1)} ${condition.unit}`}
            highlight
          />
          <PropertyRow label="Measurements" value={String(condition.measurement_count)} />

          <PropertyRow label="Line Width" value={`${condition.line_width}px`} />
          <PropertyRow label="Fill Opacity" value={`${Math.round(condition.fill_opacity * 100)}%`} />
        </div>

        {/* Per-sheet breakdown (placeholder - wired when measurements have page data) */}
        {condition.measurement_count > 0 && (
          <button
            onClick={() => setBreakdownOpen(!breakdownOpen)}
            className="mt-2 flex w-full items-center gap-1 text-[10px] text-neutral-500 hover:text-neutral-400"
            data-testid="breakdown-toggle"
          >
            {breakdownOpen ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
            Per-sheet breakdown
          </button>
        )}
        {breakdownOpen && (
          <div className="mt-1 rounded bg-neutral-800/50 p-2 text-[10px] text-neutral-500" data-testid="per-sheet-breakdown">
            <p>Detailed per-sheet breakdown available when measurements are linked to specific sheets.</p>
          </div>
        )}
      </div>
    </div>
  );
}

function PropertyRow({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className="flex items-center justify-between text-[11px]">
      <span className="text-neutral-500">{label}</span>
      <span className={highlight ? 'font-medium text-blue-400' : 'text-neutral-300'}>{value}</span>
    </div>
  );
}
