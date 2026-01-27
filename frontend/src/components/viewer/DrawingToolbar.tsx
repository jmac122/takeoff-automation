import {
    Mouse,
    Minus,
    Pencil,
    Square,
    Circle as CircleIcon,
    MapPin,
    Pentagon,
    Undo,
    Redo,
    Trash2,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

export type DrawingTool =
    | 'select'
    | 'line'
    | 'polyline'
    | 'polygon'
    | 'rectangle'
    | 'circle'
    | 'point';

interface DrawingToolbarProps {
    activeTool: DrawingTool;
    onToolChange: (tool: DrawingTool) => void;
    canUndo: boolean;
    canRedo: boolean;
    onUndo: () => void;
    onRedo: () => void;
    onDelete: () => void;
    hasSelection: boolean;
    disabled?: boolean;
    orientation?: 'horizontal' | 'vertical';
}

const TOOLS = [
    { id: 'select' as const, icon: Mouse, label: 'Select', shortcut: 'V' },
    { id: 'line' as const, icon: Minus, label: 'Line', shortcut: 'L' },
    { id: 'polyline' as const, icon: Pencil, label: 'Polyline', shortcut: 'P' },
    { id: 'polygon' as const, icon: Pentagon, label: 'Polygon', shortcut: 'G' },
    { id: 'rectangle' as const, icon: Square, label: 'Rectangle', shortcut: 'R' },
    { id: 'circle' as const, icon: CircleIcon, label: 'Circle', shortcut: 'C' },
    { id: 'point' as const, icon: MapPin, label: 'Point', shortcut: 'M' },
];

export function DrawingToolbar({
    activeTool,
    onToolChange,
    canUndo,
    canRedo,
    onUndo,
    onRedo,
    onDelete,
    hasSelection,
    disabled = false,
    orientation = 'horizontal',
}: DrawingToolbarProps) {
    const isVertical = orientation === 'vertical';
    const modeLabel = activeTool === 'select' ? 'Selection mode' : 'Drawing mode';
    const toolLabel = getToolLabel(activeTool);
    const toolInstructions = getInstructions(activeTool);
    return (
        <div
            className={cn(
                'p-2 bg-neutral-900 border border-neutral-700 rounded-lg',
                isVertical ? 'flex flex-col items-center gap-2' : 'flex items-center gap-2'
            )}
        >
            {/* Drawing Tools */}
            <div className={cn('flex gap-1', isVertical ? 'flex-col' : 'flex-row')}>
                {TOOLS.map((tool) => {
                    const Icon = tool.icon;
                    const isActive = activeTool === tool.id;

                    return (
                        <Button
                            key={tool.id}
                            variant={isActive ? 'default' : 'ghost'}
                            size="sm"
                            onClick={() => onToolChange(tool.id)}
                            disabled={disabled}
                            title={`${tool.label} (${tool.shortcut})`}
                            className={cn(
                                'w-10 h-10 p-0',
                                isActive
                                    ? 'bg-amber-500 hover:bg-amber-400 text-black'
                                    : 'text-white hover:bg-neutral-800'
                            )}
                        >
                            <Icon className="w-4 h-4" />
                        </Button>
                    );
                })}
            </div>

            <div className={cn('bg-neutral-700', isVertical ? 'h-px w-full' : 'w-px h-8')} />

            {/* Action Buttons */}
            <div className={cn('flex gap-1', isVertical ? 'flex-col' : 'flex-row')}>
                <Button
                    variant="ghost"
                    size="sm"
                    onClick={onUndo}
                    disabled={!canUndo || disabled}
                    title="Undo (Ctrl+Z)"
                    className="w-10 h-10 p-0 text-white hover:bg-neutral-800"
                >
                    <Undo className="w-4 h-4" />
                </Button>
                <Button
                    variant="ghost"
                    size="sm"
                    onClick={onRedo}
                    disabled={!canRedo || disabled}
                    title="Redo (Ctrl+Y)"
                    className="w-10 h-10 p-0 text-white hover:bg-neutral-800"
                >
                    <Redo className="w-4 h-4" />
                </Button>
                <Button
                    variant="ghost"
                    size="sm"
                    onClick={onDelete}
                    disabled={!hasSelection || disabled}
                    title="Delete (Delete)"
                    className="w-10 h-10 p-0 text-red-400 hover:text-red-300 hover:bg-red-900/20"
                >
                    <Trash2 className="w-4 h-4" />
                </Button>
            </div>

            {/* Instructions */}
            <div
                className={cn(
                    'text-xs text-neutral-400 font-mono',
                    isVertical ? 'text-center whitespace-normal' : 'ml-auto'
                )}
            >
                <div className="uppercase text-[10px] text-neutral-500">{modeLabel}</div>
                <div>
                    {toolLabel}: {toolInstructions}
                </div>
            </div>
        </div>
    );
}

export function getToolLabel(tool: DrawingTool): string {
    const match = TOOLS.find((item) => item.id === tool);
    return match?.label ?? 'Tool';
}

function getInstructions(tool: DrawingTool): string {
    switch (tool) {
        case 'select':
            return 'Click to select measurements';
        case 'line':
            return 'Click start point, then end point';
        case 'polyline':
            return 'Click to add points, double-click to finish';
        case 'polygon':
            return 'Click to add points, double-click or close to finish';
        case 'rectangle':
            return 'Click and drag to draw rectangle';
        case 'circle':
            return 'Click center, drag to set radius';
        case 'point':
            return 'Click to place point';
        default:
            return '';
    }
}
