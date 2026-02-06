import React, { createContext, useContext, useCallback, useEffect } from 'react';
import { useWorkspaceStore, type FocusRegion } from '@/stores/workspaceStore';

interface FocusContextValue {
  focusRegion: FocusRegion;
  setFocusRegion: (region: FocusRegion) => void;
  /**
   * Returns true if a single-key shortcut (no Ctrl/Meta) should fire.
   * Single-key shortcuts only fire when focus is on 'canvas' or 'sheet-tree'.
   * Ctrl+Key works everywhere except 'dialog' and 'search'.
   */
  shouldFireShortcut: (e: KeyboardEvent) => boolean;
}

const FocusCtx = createContext<FocusContextValue | null>(null);

export function FocusProvider({ children }: { children: React.ReactNode }) {
  const focusRegion = useWorkspaceStore((s) => s.focusRegion);
  const setFocusRegion = useWorkspaceStore((s) => s.setFocusRegion);

  const shouldFireShortcut = useCallback(
    (e: KeyboardEvent) => {
      const hasModifier = e.ctrlKey || e.metaKey;

      if (hasModifier) {
        // Ctrl+Key works everywhere except in dialogs and search fields
        return focusRegion !== 'dialog' && focusRegion !== 'search';
      }

      // Single-key shortcuts only fire in canvas or sheet-tree
      return focusRegion === 'canvas' || focusRegion === 'sheet-tree';
    },
    [focusRegion],
  );

  // Auto-detect focus region from DOM focus events
  useEffect(() => {
    function handleFocusIn(e: FocusEvent) {
      const target = e.target as HTMLElement;
      if (!target) return;

      // If an input or textarea gains focus, set region to 'search' to suppress single-key shortcuts
      const tag = target.tagName.toLowerCase();
      if (tag === 'input' || tag === 'textarea' || target.isContentEditable) {
        setFocusRegion('search');
        return;
      }

      // Check for data-focus-region attribute on target or ancestors
      const regionEl = target.closest('[data-focus-region]');
      if (regionEl) {
        const region = regionEl.getAttribute('data-focus-region') as FocusRegion;
        if (region) {
          setFocusRegion(region);
        }
      }
    }

    document.addEventListener('focusin', handleFocusIn);
    return () => document.removeEventListener('focusin', handleFocusIn);
  }, [setFocusRegion]);

  return (
    <FocusCtx.Provider value={{ focusRegion, setFocusRegion, shouldFireShortcut }}>
      {children}
    </FocusCtx.Provider>
  );
}

export function useFocusContext(): FocusContextValue {
  const ctx = useContext(FocusCtx);
  if (!ctx) {
    throw new Error('useFocusContext must be used within FocusProvider');
  }
  return ctx;
}
