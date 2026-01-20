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
}: DrawingToolbarProps) {
    return (
        <div className="flex items-center gap-2 p-2 bg-white border rounded-lg shadow-sm">
            {/* Drawing Tools */}
            <div className="flex gap-1">
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
                                isActive && 'bg-blue-600 hover:bg-blue-700'
                            )}
                        >
                            <Icon className="w-4 h-4" />
                        </Button>
                    );
                })}
            </div>

            <div className="w-px h-8 bg-gray-300" />

            {/* Action Buttons */}
            <div className="flex gap-1">
                <Button
                    variant="ghost"
                    size="sm"
                    onClick={onUndo}
                    disabled={!canUndo || disabled}
                    title="Undo (Ctrl+Z)"
                    className="w-10 h-10 p-0"
                >
                    <Undo className="w-4 h-4" />
                </Button>
                <Button
                    variant="ghost"
                    size="sm"
                    onClick={onRedo}
                    disabled={!canRedo || disabled}
                    title="Redo (Ctrl+Y)"
                    className="w-10 h-10 p-0"
                >
                    <Redo className="w-4 h-4" />
                </Button>
                <Button
                    variant="ghost"
                    size="sm"
                    onClick={onDelete}
                    disabled={!hasSelection || disabled}
                    title="Delete (Delete)"
                    className="w-10 h-10 p-0 text-red-600 hover:text-red-700 hover:bg-red-50"
                >
                    <Trash2 className="w-4 h-4" />
                </Button>
            </div>

            {/* Instructions */}
            <div className="ml-auto text-sm text-gray-600">
                {getInstructions(activeTool)}
            </div>
        </div>
    );
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
