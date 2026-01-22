import { ChevronLeft, ChevronRight } from 'lucide-react';
import { DrawingToolbar, type DrawingTool } from './DrawingToolbar';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

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
    isCollapsed: boolean;
    onToggleCollapse: () => void;
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
    isCollapsed,
    onToggleCollapse,
}: MeasurementToolbarSidebarProps) {
    return (
        <div
            className={cn(
                'flex-shrink-0 bg-neutral-950 border-r border-neutral-700 flex flex-col items-center py-3 px-2 transition-all duration-200',
                isCollapsed ? 'w-12' : 'w-24'
            )}
        >
            <Button
                variant="ghost"
                size="sm"
                onClick={onToggleCollapse}
                title={isCollapsed ? 'Expand tools' : 'Collapse tools'}
                aria-label={isCollapsed ? 'Expand measurement tools' : 'Collapse measurement tools'}
                className="w-9 h-9 p-0 text-neutral-400 hover:text-white hover:bg-neutral-800"
            >
                {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
            </Button>

            {!isCollapsed && (
                <div className="mt-3 w-full">
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
            )}
        </div>
    );
}
