import { useState } from 'react';
import {
  Calculator,
  Lock,
  Unlock,
  Plus,
  Package,
  HardHat,
  Truck,
  Wrench,
  DollarSign,
  ChevronDown,
  ChevronRight,
  Trash2,
} from 'lucide-react';
import {
  useConditionAssembly,
  useCreateAssembly,
  useCalculateAssembly,
  useDeleteAssembly,
  useLockAssembly,
  useUnlockAssembly,
  useDeleteComponent,
} from '@/hooks/useAssemblies';
import { AssemblyTemplateSelector } from './AssemblyTemplateSelector';
import type { AssemblyComponent } from '@/types';

interface AssemblyPanelProps {
  conditionId: string;
  projectId: string;
}

const COMPONENT_TYPE_CONFIG: Record<
  string,
  { label: string; icon: typeof Package; color: string }
> = {
  material: { label: 'Materials', icon: Package, color: 'text-blue-400' },
  labor: { label: 'Labor', icon: HardHat, color: 'text-green-400' },
  equipment: { label: 'Equipment', icon: Truck, color: 'text-orange-400' },
  subcontract: { label: 'Subcontract', icon: Wrench, color: 'text-purple-400' },
  other: { label: 'Other', icon: DollarSign, color: 'text-neutral-400' },
};

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

function formatNumber(value: number, decimals = 2): string {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 0,
    maximumFractionDigits: decimals,
  }).format(value);
}

export function AssemblyPanel({ conditionId, projectId }: AssemblyPanelProps) {
  const { data: assembly, isLoading } = useConditionAssembly(conditionId);
  const createAssembly = useCreateAssembly(conditionId);
  const calculateAssembly = useCalculateAssembly(conditionId, projectId);
  const deleteAssembly = useDeleteAssembly(conditionId);
  const lockAssemblyMutation = useLockAssembly(conditionId);
  const unlockAssemblyMutation = useUnlockAssembly(conditionId);
  const deleteComponentMutation = useDeleteComponent(conditionId);

  const [templateSelectorOpen, setTemplateSelectorOpen] = useState(false);
  const [collapsedGroups, setCollapsedGroups] = useState<Set<string>>(new Set());

  const toggleGroup = (group: string) => {
    setCollapsedGroups((prev) => {
      const next = new Set(prev);
      if (next.has(group)) {
        next.delete(group);
      } else {
        next.add(group);
      }
      return next;
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8 text-neutral-500 text-sm">
        Loading assembly...
      </div>
    );
  }

  // No assembly yet — show create options
  if (!assembly) {
    return (
      <div className="flex flex-col items-center gap-3 p-6 text-center">
        <DollarSign className="h-8 w-8 text-neutral-600" />
        <p className="text-sm text-neutral-400">No cost assembly</p>
        <p className="text-xs text-neutral-600">
          Create an assembly to estimate costs for this condition.
        </p>
        <div className="mt-2 flex gap-2">
          <button
            className="rounded bg-amber-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-amber-500 transition-colors"
            onClick={() => createAssembly.mutate({})}
            disabled={createAssembly.isPending}
          >
            {createAssembly.isPending ? 'Creating...' : 'Create Empty'}
          </button>
          <button
            className="rounded border border-amber-600 px-3 py-1.5 text-xs font-medium text-amber-400 hover:bg-amber-900/30 transition-colors"
            onClick={() => setTemplateSelectorOpen(true)}
          >
            From Template
          </button>
        </div>
        <AssemblyTemplateSelector
          conditionId={conditionId}
          open={templateSelectorOpen}
          onOpenChange={setTemplateSelectorOpen}
        />
      </div>
    );
  }

  // Group components by type
  const componentsByType = (assembly.components || []).reduce<
    Record<string, AssemblyComponent[]>
  >((acc, comp) => {
    const type = comp.component_type || 'other';
    if (!acc[type]) acc[type] = [];
    acc[type].push(comp);
    return acc;
  }, {});

  const isLocked = assembly.is_locked;

  return (
    <div className="flex h-full flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-neutral-700 px-3 py-2">
        <div className="flex items-center gap-2 min-w-0">
          <h4 className="text-xs font-medium text-neutral-200 truncate">
            {assembly.name}
          </h4>
          {isLocked && (
            <Lock className="h-3 w-3 flex-shrink-0 text-amber-500" />
          )}
        </div>
        <div className="flex items-center gap-1">
          <button
            className="rounded p-1 text-neutral-400 hover:text-amber-400 hover:bg-neutral-700 transition-colors"
            title="Calculate"
            onClick={() => calculateAssembly.mutate(assembly.id)}
            disabled={calculateAssembly.isPending}
          >
            <Calculator className="h-3.5 w-3.5" />
          </button>
          {isLocked ? (
            <button
              className="rounded p-1 text-amber-500 hover:text-amber-300 hover:bg-neutral-700 transition-colors"
              title="Unlock"
              onClick={() => unlockAssemblyMutation.mutate(assembly.id)}
            >
              <Unlock className="h-3.5 w-3.5" />
            </button>
          ) : (
            <button
              className="rounded p-1 text-neutral-400 hover:text-amber-400 hover:bg-neutral-700 transition-colors"
              title="Lock"
              onClick={() =>
                lockAssemblyMutation.mutate({
                  assemblyId: assembly.id,
                  lockedBy: 'user',
                })
              }
            >
              <Lock className="h-3.5 w-3.5" />
            </button>
          )}
          <button
            className="rounded p-1 text-neutral-400 hover:text-red-400 hover:bg-neutral-700 transition-colors"
            title="Delete assembly"
            onClick={() => {
              if (window.confirm('Delete this assembly and all its components?')) {
                deleteAssembly.mutate(assembly.id);
              }
            }}
            disabled={isLocked}
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto">
        {/* Cost summary grid */}
        <div className="border-b border-neutral-700 px-3 py-2">
          <div className="space-y-1">
            <CostRow
              label="Material"
              value={assembly.material_cost}
              color="text-blue-400"
            />
            <CostRow
              label="Labor"
              value={assembly.labor_cost}
              color="text-green-400"
            />
            <CostRow
              label="Equipment"
              value={assembly.equipment_cost}
              color="text-orange-400"
            />
            <CostRow
              label="Subcontract"
              value={assembly.subcontract_cost}
              color="text-purple-400"
            />
            {assembly.other_cost > 0 && (
              <CostRow
                label="Other"
                value={assembly.other_cost}
                color="text-neutral-400"
              />
            )}
            <div className="my-1.5 border-t border-neutral-700" />
            <CostRow
              label="Total Cost"
              value={assembly.total_cost}
              color="text-neutral-200"
              bold
            />
            <CostRow
              label="Unit Cost"
              value={assembly.unit_cost}
              color="text-neutral-400"
              prefix="$"
              suffix="/unit"
              isUnitCost
            />
            {(assembly.overhead_percent > 0 || assembly.profit_percent > 0) && (
              <>
                <div className="text-[10px] text-neutral-600">
                  O&P: {assembly.overhead_percent}% OH + {assembly.profit_percent}% P
                </div>
                <CostRow
                  label="Total w/ Markup"
                  value={assembly.total_with_markup}
                  color="text-amber-400"
                  bold
                />
              </>
            )}
          </div>
        </div>

        {/* Component groups */}
        <div className="px-1">
          {['material', 'labor', 'equipment', 'subcontract', 'other'].map(
            (type) => {
              const components = componentsByType[type];
              if (!components || components.length === 0) return null;

              const config = COMPONENT_TYPE_CONFIG[type];
              const Icon = config.icon;
              const isCollapsed = collapsedGroups.has(type);
              const subtotal = components.reduce(
                (sum, c) => sum + Number(c.extended_cost),
                0
              );

              return (
                <div key={type} className="border-b border-neutral-800">
                  {/* Group header */}
                  <button
                    className="flex w-full items-center gap-2 px-2 py-1.5 text-xs hover:bg-neutral-800 transition-colors"
                    onClick={() => toggleGroup(type)}
                  >
                    {isCollapsed ? (
                      <ChevronRight className="h-3 w-3 text-neutral-500" />
                    ) : (
                      <ChevronDown className="h-3 w-3 text-neutral-500" />
                    )}
                    <Icon className={`h-3.5 w-3.5 ${config.color}`} />
                    <span className={`font-medium ${config.color}`}>
                      {config.label}
                    </span>
                    <span className="text-neutral-600">({components.length})</span>
                    <span className="ml-auto text-neutral-400">
                      {formatCurrency(subtotal)}
                    </span>
                  </button>

                  {/* Component rows */}
                  {!isCollapsed &&
                    components.map((comp) => (
                      <div
                        key={comp.id}
                        className="group flex items-start gap-2 px-4 py-1 text-[11px] hover:bg-neutral-800/50"
                      >
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-1">
                            <span className="text-neutral-300 truncate">
                              {comp.name}
                            </span>
                            {!comp.is_included && (
                              <span className="text-[9px] text-neutral-600 bg-neutral-800 px-1 rounded">
                                excluded
                              </span>
                            )}
                          </div>
                          <div className="text-neutral-600">
                            {formatNumber(comp.calculated_quantity)} {comp.unit} @{' '}
                            {formatCurrency(comp.unit_cost)}
                            {comp.waste_percent > 0 && (
                              <span className="ml-1">
                                (+{comp.waste_percent}% waste)
                              </span>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center gap-1">
                          <span className="text-neutral-300 whitespace-nowrap">
                            {formatCurrency(Number(comp.extended_cost))}
                          </span>
                          {!isLocked && (
                            <button
                              className="hidden group-hover:block rounded p-0.5 text-neutral-600 hover:text-red-400 transition-colors"
                              onClick={() => deleteComponentMutation.mutate(comp.id)}
                              title="Remove component"
                            >
                              <Trash2 className="h-3 w-3" />
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                </div>
              );
            }
          )}
        </div>
      </div>

      {/* Footer */}
      {!isLocked && (
        <div className="border-t border-neutral-700 px-3 py-2">
          <button
            className="flex w-full items-center justify-center gap-1.5 rounded border border-neutral-600 px-2 py-1.5 text-xs text-neutral-400 hover:text-neutral-200 hover:border-neutral-500 transition-colors"
            disabled={isLocked}
          >
            <Plus className="h-3 w-3" />
            Add Component
          </button>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Helper component
// ---------------------------------------------------------------------------

function CostRow({
  label,
  value,
  color,
  bold,
  prefix,
  suffix,
  isUnitCost,
}: {
  label: string;
  value: number;
  color: string;
  bold?: boolean;
  prefix?: string;
  suffix?: string;
  isUnitCost?: boolean;
}) {
  return (
    <div className="flex items-center justify-between text-[11px]">
      <span className="text-neutral-500">{label}</span>
      <span className={`${color} ${bold ? 'font-medium' : ''}`}>
        {isUnitCost
          ? `${prefix || ''}${formatNumber(value, 4)}${suffix || ''}`
          : formatCurrency(value)}
      </span>
    </div>
  );
}
