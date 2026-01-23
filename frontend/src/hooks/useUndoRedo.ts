import { useCallback, useState } from 'react';

export interface UndoableAction {
    label?: string;
    undo: () => void | Promise<void>;
    redo: () => void | Promise<void>;
}

export function useUndoRedo() {
    const [state, setState] = useState<{
        actions: UndoableAction[];
        index: number;
    }>({
        actions: [],
        index: -1,
    });

    const canUndo = state.index >= 0;
    const canRedo = state.index < state.actions.length - 1;

    const push = useCallback((action: UndoableAction) => {
        setState((prev) => {
            const nextActions = [...prev.actions.slice(0, prev.index + 1), action];
            return {
                actions: nextActions,
                index: nextActions.length - 1,
            };
        });
    }, []);

    const undo = useCallback(async () => {
        if (state.index < 0) return;
        const action = state.actions[state.index];
        await action.undo();
        setState((prev) => ({
            ...prev,
            index: prev.index - 1,
        }));
    }, [state.actions, state.index]);

    const redo = useCallback(async () => {
        if (state.index >= state.actions.length - 1) return;
        const action = state.actions[state.index + 1];
        await action.redo();
        setState((prev) => ({
            ...prev,
            index: prev.index + 1,
        }));
    }, [state.actions, state.index]);

    const clear = useCallback(() => {
        setState({ actions: [], index: -1 });
    }, []);

    return {
        canUndo,
        canRedo,
        push,
        undo,
        redo,
        clear,
    };
}
