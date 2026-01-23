import { useEffect } from 'react';
import type { DrawingTool } from '@/components/viewer/DrawingToolbar';

interface UseKeyboardShortcutsOptions {
    drawing: {
        setTool: (tool: DrawingTool) => void;
        cancelDrawing: () => void;
    };
    selectedMeasurementId: string | null;
    onDeleteMeasurement: (id: string) => void;
    onToggleFullscreen: () => void;
    onClearSelection: () => void;
    onUndo: () => void;
    onRedo: () => void;
}

export function useKeyboardShortcuts({
    drawing,
    selectedMeasurementId,
    onDeleteMeasurement,
    onToggleFullscreen,
    onClearSelection,
    onUndo,
    onRedo,
}: UseKeyboardShortcutsOptions) {
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'F11') {
                e.preventDefault();
                onToggleFullscreen();
                return;
            }

            // Tool shortcuts
            if (e.key === 'v') drawing.setTool('select');
            if (e.key === 'l') drawing.setTool('line');
            if (e.key === 'p') drawing.setTool('polyline');
            if (e.key === 'g') drawing.setTool('polygon');
            if (e.key === 'r') drawing.setTool('rectangle');
            if (e.key === 'c') drawing.setTool('circle');
            if (e.key === 'm') drawing.setTool('point');

            // Undo/Redo
            if (e.ctrlKey && e.key === 'z') onUndo();
            if (e.ctrlKey && e.key === 'y') onRedo();

            // Delete
            if (e.key === 'Delete' && selectedMeasurementId) {
                onDeleteMeasurement(selectedMeasurementId);
            }

            // Escape - cancel drawing
            if (e.key === 'Escape') {
                drawing.cancelDrawing();
                onClearSelection();
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [
        drawing,
        selectedMeasurementId,
        onDeleteMeasurement,
        onToggleFullscreen,
        onClearSelection,
        onUndo,
        onRedo,
    ]);
}
