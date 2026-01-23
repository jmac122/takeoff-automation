import { getToolLabel, type DrawingTool } from '@/components/viewer/DrawingToolbar';
import { cn } from '@/lib/utils';

interface DrawingInstructionsProps {
    isVisible: boolean;
    tool: DrawingTool;
    conditionName?: string | null;
    isDrawing: boolean;
    isCloseToStart?: boolean;
}

const TOOL_INSTRUCTIONS: Record<DrawingTool, string> = {
    select: 'Click to select measurements',
    line: 'Click start point, then end point',
    polyline: 'Click to add points, double-click to finish',
    polygon: 'Click to add points, double-click to close',
    rectangle: 'Click and drag to draw rectangle',
    circle: 'Click center, drag to set radius',
    point: 'Click to place point',
};

export function DrawingInstructions({
    isVisible,
    tool,
    conditionName,
    isDrawing,
    isCloseToStart = false,
}: DrawingInstructionsProps) {
    if (!isVisible) return null;

    const toolLabel = getToolLabel(tool);
    const instruction = TOOL_INSTRUCTIONS[tool];
    const status = isDrawing ? 'Drawing' : 'Ready';

    return (
        <div
            className={cn(
                'absolute top-4 right-4 z-10 rounded-lg border border-neutral-700 bg-neutral-900/90 px-3 py-2 text-xs text-neutral-200 shadow-lg',
                'backdrop-blur'
            )}
        >
            <div className="flex items-center justify-between gap-3 text-[10px] uppercase tracking-widest text-neutral-400">
                <span>Drawing mode</span>
                <span>{status}</span>
            </div>
            <div className="mt-1 text-sm font-semibold text-white">
                {toolLabel}
                {conditionName ? ` - ${conditionName}` : ''}
            </div>
            <div className="mt-1 text-xs text-neutral-300">{instruction}</div>
            {isCloseToStart && tool === 'polygon' && (
                <div className="mt-1 text-xs text-amber-300">Click the first point to close.</div>
            )}
            <div className="mt-1 text-[10px] uppercase text-neutral-500">Esc cancels</div>
        </div>
    );
}
