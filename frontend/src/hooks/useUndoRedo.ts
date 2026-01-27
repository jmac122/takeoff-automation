import { useCallback, useEffect, useRef, useState } from 'react';

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
    const stateRef = useRef(state);
    const isProcessingRef = useRef(false);

    useEffect(() => {
        stateRef.current = state;
    }, [state]);

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
        if (isProcessingRef.current) return;
        const { index, actions } = stateRef.current;
        if (index < 0) return;
        const action = actions[index];
        isProcessingRef.current = true;
        try {
            await action.undo();
            setState((prev) => ({
                ...prev,
                index: Math.max(prev.index - 1, -1),
            }));
        } finally {
            isProcessingRef.current = false;
        }
    }, []);

    const redo = useCallback(async () => {
        if (isProcessingRef.current) return;
        const { index, actions } = stateRef.current;
        if (index >= actions.length - 1) return;
        const action = actions[index + 1];
        isProcessingRef.current = true;
        try {
            await action.redo();
            setState((prev) => ({
                ...prev,
                index: Math.min(prev.index + 1, prev.actions.length - 1),
            }));
        } finally {
            isProcessingRef.current = false;
        }
    }, []);

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
