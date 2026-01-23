import { useState } from 'react';
import { Loader2 } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { ColorPicker } from '@/components/ui/color-picker';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import { MEASUREMENT_COLORS } from '@/lib/colors';
import type { ConditionTemplate } from '@/types';
import {
  useConditionTemplates,
  useCreateCondition,
  useCreateConditionFromTemplate,
} from '@/hooks/useConditions';

interface CreateConditionModalProps {
  projectId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  defaultCategory?: string | null;
}

const DEFAULT_COLOR = MEASUREMENT_COLORS.default;

type MeasurementType = 'linear' | 'area' | 'volume' | 'count';

const MEASUREMENT_TYPES = [
  { value: 'linear', label: 'Linear (LF)', unit: 'LF' },
  { value: 'area', label: 'Area (SF)', unit: 'SF' },
  { value: 'volume', label: 'Volume (CY)', unit: 'CY' },
  { value: 'count', label: 'Count (EA)', unit: 'EA' },
];

export function CreateConditionModal({
  projectId,
  open,
  onOpenChange,
  defaultCategory,
}: CreateConditionModalProps) {
  const [tab, setTab] = useState<'template' | 'custom'>('template');
  const [name, setName] = useState('');
  const [measurementType, setMeasurementType] = useState<MeasurementType>('area');
  const [depth, setDepth] = useState('');
  const [color, setColor] = useState<string>(DEFAULT_COLOR);
  const resolvedCategory = defaultCategory || 'other';

  const { data: templates } = useConditionTemplates();
  const createFromTemplateMutation = useCreateConditionFromTemplate(projectId);
  const createCustomMutation = useCreateCondition(projectId);

  const groupedTemplates = (templates || []).reduce((acc, template) => {
    const category = template.category || 'other';
    if (!acc[category]) acc[category] = [];
    acc[category].push(template);
    return acc;
  }, {} as Record<string, ConditionTemplate[]>);

  const resetForm = () => {
    setName('');
    setMeasurementType('area');
    setDepth('');
    setColor(DEFAULT_COLOR);
  };

  const handleCreateCustom = () => {
    const selected = MEASUREMENT_TYPES.find((t) => t.value === measurementType);
    createCustomMutation.mutate(
      {
        name,
        measurement_type: measurementType,
        unit: selected?.unit || 'SF',
        depth: depth ? Number(depth) : null,
        color,
        scope: 'concrete',
        category: resolvedCategory,
        line_width: 2,
        fill_opacity: 0.3,
      },
      {
        onSuccess: () => {
          onOpenChange(false);
          resetForm();
        },
      }
    );
  };

  const handleCreateFromTemplate = (templateName: string) => {
    createFromTemplateMutation.mutate(templateName, {
      onSuccess: () => onOpenChange(false),
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="uppercase tracking-wide">New Condition</DialogTitle>
          <DialogDescription>
            <div className="flex items-center justify-between text-xs font-mono uppercase tracking-widest text-muted-foreground">
              <span>Status: {createCustomMutation.isPending ? 'Processing' : 'Ready'}</span>
              <span>Time: {new Date().toLocaleTimeString('en-US', { hour12: false })}</span>
            </div>
          </DialogDescription>
        </DialogHeader>

        <Tabs
          value={tab}
          onValueChange={(value: string) => setTab(value as 'template' | 'custom')}
        >
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="template">From Template</TabsTrigger>
            <TabsTrigger value="custom">Custom</TabsTrigger>
          </TabsList>

          <TabsContent value="template" className="space-y-4 mt-4">
            <div className="max-h-80 overflow-auto space-y-4">
              {Object.entries(groupedTemplates).map(([category, items]) => (
                <div key={category}>
                  <h4 className="text-xs font-mono uppercase tracking-widest text-muted-foreground mb-2">
                    {category}
                  </h4>
                  <div className="space-y-1">
                    {items.map((template) => (
                      <button
                        type="button"
                        key={template.name}
                        onClick={() => handleCreateFromTemplate(template.name)}
                        disabled={createFromTemplateMutation.isPending}
                        className="w-full flex items-center gap-3 p-2 rounded hover:bg-muted text-left"
                      >
                        <div
                          className="w-4 h-4 rounded"
                          style={{ backgroundColor: template.color }}
                        />
                        <div className="flex-1">
                          <div className="text-sm font-medium text-foreground">
                            {template.name}
                          </div>
                          <div className="text-xs font-mono uppercase tracking-widest text-muted-foreground">
                            {template.measurement_type} • {template.unit}
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="custom" className="space-y-4 mt-4">
            <div className="space-y-2">
              <Label htmlFor="condition-name">Condition Name</Label>
              <Input
                id="condition-name"
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder='e.g., 4" Concrete Slab'
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="measurement-type">Measurement Type</Label>
              <Select
                value={measurementType}
                onValueChange={(value: string) => setMeasurementType(value as MeasurementType)}
              >
                <SelectTrigger id="measurement-type">
                  <SelectValue placeholder="Select type" />
                </SelectTrigger>
                <SelectContent>
                  {MEASUREMENT_TYPES.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      {type.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {(measurementType === 'area' || measurementType === 'volume') && (
              <div className="space-y-2">
                <Label htmlFor="depth">Depth/Thickness (inches)</Label>
                <Input
                  id="depth"
                  type="number"
                  value={depth}
                  onChange={(event) => setDepth(event.target.value)}
                  placeholder="e.g., 4"
                />
              </div>
            )}

            <div className="space-y-2">
              <Label>Color</Label>
              <ColorPicker value={color} onChange={setColor} />
            </div>

            <DialogFooter className="gap-2 sm:gap-0">
              <Button variant="outline" onClick={() => onOpenChange(false)}>
                Cancel
              </Button>
              <Button onClick={handleCreateCustom} disabled={!name || createCustomMutation.isPending}>
                {createCustomMutation.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Creating...
                  </>
                ) : (
                  'Create Condition'
                )}
              </Button>
            </DialogFooter>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
