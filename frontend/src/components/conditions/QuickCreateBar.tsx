import { useState } from 'react';
import { Plus, ChevronDown } from 'lucide-react';
import { useConditionTemplates, useCreateConditionFromTemplate } from '@/hooks/useConditions';
import type { ConditionTemplate } from '@/types';

interface QuickCreateBarProps {
  projectId: string;
  onCreated?: (conditionId: string) => void;
}

const CATEGORY_LABELS: Record<string, string> = {
  foundations: 'Foundations',
  slabs: 'Slabs',
  paving: 'Paving',
  vertical: 'Vertical',
  miscellaneous: 'Misc',
};

export function QuickCreateBar({ projectId, onCreated }: QuickCreateBarProps) {
  const [isOpen, setIsOpen] = useState(false);
  const { data: templates } = useConditionTemplates();
  const createFromTemplate = useCreateConditionFromTemplate(projectId);

  const grouped = (templates ?? []).reduce<Record<string, ConditionTemplate[]>>((acc, t) => {
    const cat = t.category ?? 'other';
    (acc[cat] ??= []).push(t);
    return acc;
  }, {});

  const handleSelect = (templateName: string) => {
    createFromTemplate.mutate(templateName, {
      onSuccess: (condition) => {
        onCreated?.(condition.id);
        setIsOpen(false);
      },
    });
  };

  return (
    <div className="border-b border-neutral-700 px-3 py-2">
      <div className="relative">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex w-full items-center gap-1.5 rounded bg-blue-600 px-2.5 py-1.5 text-xs font-medium text-white hover:bg-blue-500 transition-colors"
          data-testid="quick-create-btn"
        >
          <Plus className="h-3.5 w-3.5" />
          <span>Add Condition</span>
          <ChevronDown className={`ml-auto h-3 w-3 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </button>

        {isOpen && (
          <div className="absolute left-0 right-0 top-full z-20 mt-1 max-h-64 overflow-y-auto rounded border border-neutral-600 bg-neutral-800 shadow-lg" data-testid="template-dropdown">
            {Object.entries(grouped).map(([category, items]) => (
              <div key={category}>
                <div className="px-2 py-1 text-[10px] font-semibold uppercase tracking-wider text-neutral-500">
                  {CATEGORY_LABELS[category] ?? category}
                </div>
                {items.map((t) => (
                  <button
                    key={t.name}
                    onClick={() => handleSelect(t.name)}
                    className="flex w-full items-center gap-2 px-2 py-1.5 text-xs text-neutral-300 hover:bg-neutral-700"
                    disabled={createFromTemplate.isPending}
                  >
                    <span
                      className="inline-block h-2.5 w-2.5 rounded-full"
                      style={{ backgroundColor: t.color }}
                    />
                    <span>{t.name}</span>
                    <span className="ml-auto text-[10px] text-neutral-500">{t.unit}</span>
                  </button>
                ))}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
