import { useEffect, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
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
import { recalculateConditionMeasurements } from '@/api/measurements';

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
  const queryClient = useQueryClient();
  const updateConditionMutation = useUpdateCondition(condition.project_id);

  const [name, setName] = useState(condition.name);
  const [measurementType, setMeasurementType] = useState<MeasurementType>(
    condition.measurement_type
  );
  const [unit, setUnit] = useState(condition.unit);
  const [thickness, setThickness] = useState(
    condition.thickness?.toString() || condition.depth?.toString() || ''
  );
  const [color, setColor] = useState(condition.color);

  useEffect(() => {
    setName(condition.name);
    setMeasurementType(condition.measurement_type);
    setUnit(condition.unit);
    setThickness(condition.thickness?.toString() || condition.depth?.toString() || '');
    setColor(condition.color);
  }, [condition]);

  const handleMeasurementTypeChange = (value: string) => {
    const nextType = value as MeasurementType;
    setMeasurementType(nextType);
    const nextUnit = MEASUREMENT_TYPES.find((type) => type.value === nextType)?.unit;
    if (nextUnit) {
      setUnit(nextUnit);
    }
  };

  const handleUnitChange = (value: string) => {
    setUnit(value);
    const nextType =
      value === 'LF' ? 'linear' : value === 'SF' ? 'area' : value === 'CY' ? 'volume' : 'count';
    setMeasurementType(nextType);
  };

  const handleSave = () => {
    const thicknessValue = thickness ? Number(thickness) : null;
    const depthValue =
      measurementType === 'area' || measurementType === 'volume' ? thicknessValue : null;
    const previousDepthValue = condition.thickness ?? condition.depth ?? null;
    const shouldRecalculate =
      unit !== condition.unit ||
      measurementType !== condition.measurement_type ||
      depthValue !== previousDepthValue;

    updateConditionMutation.mutate(
      {
        conditionId: condition.id,
        data: {
          name,
          measurement_type: measurementType,
          unit,
          depth: depthValue,
          thickness: thicknessValue,
          color,
        },
      },
      {
        onSuccess: () => {
          if (shouldRecalculate) {
            void recalculateConditionMeasurements(condition.id).then(() => {
              queryClient.invalidateQueries({ queryKey: ['measurements'] });
              queryClient.invalidateQueries({ queryKey: ['conditions', condition.project_id] });
            });
          }
          onOpenChange(false);
        },
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
              onValueChange={handleMeasurementTypeChange}
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

          <div className="space-y-2">
            <Label htmlFor="edit-unit">Unit of Measure</Label>
            <Select value={unit} onValueChange={handleUnitChange}>
              <SelectTrigger id="edit-unit">
                <SelectValue placeholder="Select unit" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="LF">LF - Linear Feet</SelectItem>
                <SelectItem value="SF">SF - Square Feet</SelectItem>
                <SelectItem value="CY">CY - Cubic Yards</SelectItem>
                <SelectItem value="EA">EA - Each</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {(measurementType === 'area' || measurementType === 'volume') && (
            <div className="space-y-2">
              <Label htmlFor="edit-depth">Thickness/Depth (inches)</Label>
              <Input
                id="edit-depth"
                type="number"
                value={thickness}
                onChange={(event) => setThickness(event.target.value)}
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
