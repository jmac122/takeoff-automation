import { useEffect, useState } from 'react';
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
import type { Condition } from '@/types';
import { useUpdateCondition } from '@/hooks/useConditions';

interface EditConditionModalProps {
  condition: Condition;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

type MeasurementType = 'linear' | 'area' | 'volume' | 'count';

const MEASUREMENT_TYPES = [
  { value: 'linear', label: 'Linear (LF)', unit: 'LF' },
  { value: 'area', label: 'Area (SF)', unit: 'SF' },
  { value: 'volume', label: 'Volume (CY)', unit: 'CY' },
  { value: 'count', label: 'Count (EA)', unit: 'EA' },
];

export function EditConditionModal({ condition, open, onOpenChange }: EditConditionModalProps) {
  const updateConditionMutation = useUpdateCondition(condition.project_id);

  const [name, setName] = useState(condition.name);
  const [measurementType, setMeasurementType] = useState<MeasurementType>(
    condition.measurement_type
  );
  const [depth, setDepth] = useState(condition.depth?.toString() || '');
  const [color, setColor] = useState(condition.color);

  useEffect(() => {
    setName(condition.name);
    setMeasurementType(condition.measurement_type);
    setDepth(condition.depth?.toString() || '');
    setColor(condition.color);
  }, [condition]);

  const handleSave = () => {
    const selected = MEASUREMENT_TYPES.find((t) => t.value === measurementType);
    updateConditionMutation.mutate(
      {
        conditionId: condition.id,
        data: {
          name,
          measurement_type: measurementType,
          unit: selected?.unit || condition.unit,
          depth: measurementType === 'area' || measurementType === 'volume'
            ? depth
              ? Number(depth)
              : null
            : null,
          color,
        },
      },
      {
        onSuccess: () => onOpenChange(false),
      }
    );
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="uppercase tracking-wide">Edit Condition</DialogTitle>
          <DialogDescription>
            <div className="flex items-center justify-between text-xs font-mono uppercase tracking-widest text-muted-foreground">
              <span>Status: {updateConditionMutation.isPending ? 'Updating' : 'Ready'}</span>
              <span>Time: {new Date().toLocaleTimeString('en-US', { hour12: false })}</span>
            </div>
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="edit-condition-name">Condition Name</Label>
            <Input
              id="edit-condition-name"
              value={name}
              onChange={(event) => setName(event.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="edit-measurement-type">Measurement Type</Label>
            <Select
              value={measurementType}
              onValueChange={(value: string) => setMeasurementType(value as MeasurementType)}
            >
              <SelectTrigger id="edit-measurement-type">
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
              <Label htmlFor="edit-depth">Depth/Thickness (inches)</Label>
              <Input
                id="edit-depth"
                type="number"
                value={depth}
                onChange={(event) => setDepth(event.target.value)}
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
            <Button onClick={handleSave} disabled={!name || updateConditionMutation.isPending}>
              {updateConditionMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                'Save Changes'
              )}
            </Button>
          </DialogFooter>
        </div>
      </DialogContent>
    </Dialog>
  );
}
