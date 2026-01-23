import { MEASUREMENT_COLORS } from '@/lib/colors';
import { cn } from '@/lib/utils';

interface ColorPickerProps {
  value: string;
  onChange: (color: string) => void;
}

const RESERVED_COLORS = new Set<string>([
  MEASUREMENT_COLORS.selected,
  MEASUREMENT_COLORS.hover,
  MEASUREMENT_COLORS.approved,
  MEASUREMENT_COLORS.rejected,
  MEASUREMENT_COLORS.pending,
]);

export function ColorPicker({ value, onChange }: ColorPickerProps) {
  const colors = Object.values(MEASUREMENT_COLORS).filter((color) => !RESERVED_COLORS.has(color));

  return (
    <div className="flex flex-wrap gap-2">
      {colors.map((color) => (
        <button
          key={color}
          type="button"
          className={cn(
            'h-8 w-8 rounded-md border-2 transition-transform hover:scale-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
            value === color ? 'border-primary ring-2 ring-primary/30' : 'border-transparent'
          )}
          style={{ backgroundColor: color }}
          onClick={() => onChange(color)}
          aria-label={`Select ${color}`}
        />
      ))}
    </div>
  );
}
