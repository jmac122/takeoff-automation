import { useState } from 'react';
import {
  ChevronDown,
  ChevronRight,
  Copy,
  Edit,
  GripVertical,
  Layers,
  MoreHorizontal,
  Plus,
  Trash2,
} from 'lucide-react';
import {
  DndContext,
  KeyboardSensor,
  PointerSensor,
  type DragEndEvent,
  closestCenter,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import {
  SortableContext,
  arrayMove,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';

import { Button } from '@/components/ui/button';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { EmptyState } from '@/components/ui/empty-state';
import { cn } from '@/lib/utils';
import type { Condition } from '@/types';
import {
  useConditions,
  useDeleteCondition,
  useDuplicateCondition,
  useReorderConditions,
} from '@/hooks/useConditions';

import { CreateConditionModal } from './CreateConditionModal';
import { EditConditionModal } from './EditConditionModal';

interface ConditionsPanelProps {
  projectId: string;
  selectedConditionId: string | null;
  onConditionSelect: (id: string | null) => void;
}

export function ConditionsPanel({
  projectId,
  selectedConditionId,
  onConditionSelect,
}: ConditionsPanelProps) {
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [editingCondition, setEditingCondition] = useState<Condition | null>(null);
  const [deleteCandidate, setDeleteCandidate] = useState<Condition | null>(null);
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(
    new Set(['foundations', 'slabs', 'paving', 'vertical', 'miscellaneous'])
  );

  const { data, isLoading } = useConditions(projectId);
  const deleteMutation = useDeleteCondition(projectId);
  const duplicateMutation = useDuplicateCondition(projectId);
  const reorderMutation = useReorderConditions(projectId);

  const conditions = data?.conditions ?? [];

  const groupedConditions = conditions.reduce((acc, condition) => {
    const category = condition.category || 'other';
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(condition);
    return acc;
  }, {} as Record<string, Condition[]>);

  const toggleCategory = (category: string) => {
    setExpandedCategories((prev) => {
      const next = new Set(prev);
      if (next.has(category)) {
        next.delete(category);
      } else {
        next.add(category);
      }
      return next;
    });
  };

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragEnd = (event: DragEndEvent) => {
    if (!event.over) return;

    const activeId = String(event.active.id);
    const overId = String(event.over.id);
    if (activeId === overId) return;

    const oldIndex = conditions.findIndex((c) => c.id === activeId);
    const newIndex = conditions.findIndex((c) => c.id === overId);
    if (oldIndex === -1 || newIndex === -1) return;

    const newOrder = arrayMove(conditions, oldIndex, newIndex);
    reorderMutation.mutate(newOrder.map((c) => c.id));
  };

  const totalQuantityByUnit = conditions.reduce((acc, condition) => {
    acc[condition.unit] = (acc[condition.unit] || 0) + condition.total_quantity;
    return acc;
  }, {} as Record<string, number>);

  return (
    <div className="absolute bottom-4 left-4 bg-card/95 backdrop-blur border border-border rounded-md shadow-xl max-w-sm max-h-[32rem] overflow-hidden z-10 flex flex-col">
      <div className="flex items-center justify-between px-3 py-2 border-b border-border text-xs font-mono uppercase tracking-widest text-muted-foreground">
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
            Status: Active
          </span>
          <span className="text-muted-foreground/60">|</span>
          <span>Module: Conditions</span>
        </div>
        <span>UTC {new Date().toLocaleTimeString('en-US', { hour12: false })}</span>
      </div>
      <div className="flex items-center justify-between p-3 border-b border-border">
        <h3 className="text-sm font-semibold text-foreground font-mono uppercase tracking-wider">
          Conditions
        </h3>
        <Button size="sm" onClick={() => setIsCreateOpen(true)}>
          <Plus className="h-4 w-4 mr-1" />
          Add Condition
        </Button>
      </div>

      <div className="flex-1 overflow-auto">
        {isLoading ? (
          <div className="p-4 text-center text-muted-foreground text-sm">Loading...</div>
        ) : conditions.length === 0 ? (
          <EmptyState
            icon={Layers}
            title="No conditions yet"
            description="Create your first condition to start measuring."
            action={
              <Button size="sm" onClick={() => setIsCreateOpen(true)}>
                <Plus className="h-4 w-4 mr-1" />
                Create Condition
              </Button>
            }
          />
        ) : (
          <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragEnd={handleDragEnd}
          >
            <SortableContext
              items={conditions.map((c) => c.id)}
              strategy={verticalListSortingStrategy}
            >
              {Object.entries(groupedConditions).map(([category, items]) => (
                <Collapsible
                  key={category}
                  open={expandedCategories.has(category)}
                  onOpenChange={() => toggleCategory(category)}
                >
                  <CollapsibleTrigger className="flex items-center w-full p-2 text-xs font-mono uppercase tracking-widest text-foreground hover:bg-muted">
                    {expandedCategories.has(category) ? (
                      <ChevronDown className="h-4 w-4 mr-1" />
                    ) : (
                      <ChevronRight className="h-4 w-4 mr-1" />
                    )}
                    {category}
                    <span className="ml-auto text-muted-foreground">{items.length}</span>
                  </CollapsibleTrigger>
                  <CollapsibleContent>
                    {items.map((condition) => (
                      <SortableConditionItem
                        key={condition.id}
                        condition={condition}
                        isSelected={condition.id === selectedConditionId}
                        onSelect={() => onConditionSelect(condition.id)}
                        onEdit={() => setEditingCondition(condition)}
                        onDuplicate={() => duplicateMutation.mutate(condition.id)}
                        onDelete={() => setDeleteCandidate(condition)}
                      />
                    ))}
                  </CollapsibleContent>
                </Collapsible>
              ))}
            </SortableContext>
          </DndContext>
        )}
      </div>

      {conditions.length > 0 && (
        <div className="border-t border-border p-3 space-y-1">
          <h4 className="text-xs font-mono uppercase tracking-widest text-muted-foreground">
            Totals
          </h4>
          {Object.entries(totalQuantityByUnit).map(([unit, total]) => (
            <div key={unit} className="flex justify-between text-xs text-foreground font-mono">
              <span className="text-muted-foreground">{unit}</span>
              <span>{total.toFixed(1)}</span>
            </div>
          ))}
        </div>
      )}

      <CreateConditionModal
        projectId={projectId}
        open={isCreateOpen}
        onOpenChange={setIsCreateOpen}
      />

      {editingCondition && (
        <EditConditionModal
          condition={editingCondition}
          open={!!editingCondition}
          onOpenChange={(open) => !open && setEditingCondition(null)}
        />
      )}

      <Dialog open={!!deleteCandidate} onOpenChange={(open) => !open && setDeleteCandidate(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="uppercase tracking-wide">Confirm Delete</DialogTitle>
            <DialogDescription>
              Delete "{deleteCandidate?.name}" and all linked measurements? This action cannot be
              undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2 sm:gap-0">
            <Button variant="outline" onClick={() => setDeleteCandidate(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => {
                if (!deleteCandidate) return;
                deleteMutation.mutate(deleteCandidate.id, {
                  onSuccess: () => {
                    if (selectedConditionId === deleteCandidate.id) {
                      onConditionSelect(null);
                    }
                    setDeleteCandidate(null);
                  },
                });
              }}
            >
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function SortableConditionItem({
  condition,
  isSelected,
  onSelect,
  onEdit,
  onDuplicate,
  onDelete,
}: {
  condition: Condition;
  isSelected: boolean;
  onSelect: () => void;
  onEdit: () => void;
  onDuplicate: () => void;
  onDelete: () => void;
}) {
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({
    id: condition.id,
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={cn(
        'flex items-center gap-2 px-2 py-1.5 ml-4 mr-2 rounded border border-transparent',
        isSelected ? 'bg-primary/10 border-primary/40' : 'hover:bg-muted'
      )}
    >
      <button
        type="button"
        className="cursor-grab hover:bg-muted rounded p-0.5 text-muted-foreground"
        {...attributes}
        {...listeners}
        aria-label="Drag to reorder"
      >
        <GripVertical className="h-3 w-3" />
      </button>

      <button
        type="button"
        className="flex-1 min-w-0 text-left"
        onClick={onSelect}
      >
        <div className="flex items-center gap-2">
          <div
            className="w-3 h-3 rounded flex-shrink-0 border border-border"
            style={{ backgroundColor: condition.color }}
          />
          <div className="flex-1 min-w-0">
            <div className="text-sm truncate text-foreground">{condition.name}</div>
            <div className="text-xs text-muted-foreground font-mono">
              {condition.total_quantity.toFixed(1)} {condition.unit}
              {condition.measurement_count > 0 && (
                <span className="ml-1">({condition.measurement_count})</span>
              )}
            </div>
          </div>
        </div>
      </button>

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="icon" className="h-6 w-6">
            <MoreHorizontal className="h-3 w-3" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem onClick={onEdit}>
            <Edit className="h-4 w-4 mr-2" />
            Edit
          </DropdownMenuItem>
          <DropdownMenuItem onClick={onDuplicate}>
            <Copy className="h-4 w-4 mr-2" />
            Duplicate
          </DropdownMenuItem>
          <DropdownMenuItem onClick={onDelete} className="text-destructive">
            <Trash2 className="h-4 w-4 mr-2" />
            Delete
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}
