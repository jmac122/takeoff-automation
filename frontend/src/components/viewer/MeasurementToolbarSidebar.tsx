import { DrawingToolbar, type DrawingTool } from './DrawingToolbar';

interface MeasurementToolbarSidebarProps {
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

export function MeasurementToolbarSidebar({
    activeTool,
    onToolChange,
    canUndo,
    canRedo,
    onUndo,
    onRedo,
    onDelete,
    hasSelection,
    disabled = false,
}: MeasurementToolbarSidebarProps) {
    return (
        <div className="flex-shrink-0 w-24 bg-neutral-950 border-r border-neutral-700 flex flex-col items-center py-3 px-2">
            <DrawingToolbar
                activeTool={activeTool}
                onToolChange={onToolChange}
                canUndo={canUndo}
                canRedo={canRedo}
                onUndo={onUndo}
                onRedo={onRedo}
                onDelete={onDelete}
                hasSelection={hasSelection}
                disabled={disabled}
                orientation="vertical"
            />
        </div>
    );
}
