import { useState, useMemo } from 'react';
import { Search, Package } from 'lucide-react';
import { useAssemblyTemplates, useCreateAssembly } from '@/hooks/useAssemblies';
import type { AssemblyTemplate } from '@/types';

interface AssemblyTemplateSelectorProps {
  conditionId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function AssemblyTemplateSelector({
  conditionId,
  open,
  onOpenChange,
}: AssemblyTemplateSelectorProps) {
  const { data: templates, isLoading } = useAssemblyTemplates({ scope: 'concrete' });
  const createAssembly = useCreateAssembly(conditionId);
  const [search, setSearch] = useState('');

  const grouped = useMemo(() => {
    if (!templates) return {};
    const filtered = templates.filter(
      (t) =>
        t.name.toLowerCase().includes(search.toLowerCase()) ||
        (t.description || '').toLowerCase().includes(search.toLowerCase()) ||
        (t.category || '').toLowerCase().includes(search.toLowerCase())
    );
    return filtered.reduce<Record<string, AssemblyTemplate[]>>((acc, t) => {
      const cat = t.category || 'Other';
      if (!acc[cat]) acc[cat] = [];
      acc[cat].push(t);
      return acc;
    }, {});
  }, [templates, search]);

  const handleSelect = (template: AssemblyTemplate) => {
    createAssembly.mutate(
      { template_id: template.id },
      {
        onSuccess: () => onOpenChange(false),
      }
    );
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="mx-4 w-full max-w-md rounded-lg border border-neutral-700 bg-neutral-800 shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-neutral-700 px-4 py-3">
          <h3 className="text-sm font-medium text-neutral-200">
            Choose Assembly Template
          </h3>
          <button
            className="text-neutral-500 hover:text-neutral-300 text-lg"
            onClick={() => onOpenChange(false)}
          >
            &times;
          </button>
        </div>

        {/* Search */}
        <div className="border-b border-neutral-700 px-4 py-2">
          <div className="flex items-center gap-2 rounded border border-neutral-600 bg-neutral-900 px-2 py-1.5">
            <Search className="h-3.5 w-3.5 text-neutral-500" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search templates..."
              className="flex-1 bg-transparent text-xs text-neutral-200 outline-none placeholder:text-neutral-600"
              autoFocus
            />
          </div>
        </div>

        {/* Template list */}
        <div className="max-h-[400px] overflow-y-auto p-2">
          {isLoading && (
            <div className="py-8 text-center text-xs text-neutral-500">
              Loading templates...
            </div>
          )}
          {!isLoading && Object.keys(grouped).length === 0 && (
            <div className="py-8 text-center text-xs text-neutral-500">
              No templates found
            </div>
          )}
          {Object.entries(grouped).map(([category, items]) => (
            <div key={category} className="mb-2">
              <div className="px-2 py-1 text-[10px] font-medium uppercase tracking-wider text-neutral-500">
                {category}
              </div>
              {items.map((template) => (
                <button
                  key={template.id}
                  className="flex w-full items-start gap-2 rounded px-2 py-2 text-left hover:bg-neutral-700 transition-colors"
                  onClick={() => handleSelect(template)}
                  disabled={createAssembly.isPending}
                >
                  <Package className="mt-0.5 h-4 w-4 flex-shrink-0 text-amber-500" />
                  <div className="min-w-0 flex-1">
                    <div className="text-xs font-medium text-neutral-200">
                      {template.name}
                    </div>
                    {template.description && (
                      <div className="mt-0.5 text-[10px] text-neutral-500 line-clamp-2">
                        {template.description}
                      </div>
                    )}
                    <div className="mt-1 flex gap-2 text-[10px] text-neutral-600">
                      <span>{template.expected_unit}</span>
                      <span>
                        {template.component_definitions.length} components
                      </span>
                      {template.csi_code && <span>CSI {template.csi_code}</span>}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="border-t border-neutral-700 px-4 py-2 text-right">
          <button
            className="rounded px-3 py-1.5 text-xs text-neutral-400 hover:text-neutral-200 transition-colors"
            onClick={() => onOpenChange(false)}
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
