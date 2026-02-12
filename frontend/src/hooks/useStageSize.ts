import { useState, useEffect, useCallback, useRef } from 'react';

export interface StageSize {
  width: number;
  height: number;
}

/**
 * CM-002: ResizeObserver-based stage sizing hook.
 * Tracks container dimensions and provides debounced size updates
 * for the Konva Stage.
 */
export function useStageSize(containerRef: React.RefObject<HTMLDivElement | null>): StageSize {
  const [size, setSize] = useState<StageSize>({ width: 0, height: 0 });
  const rafRef = useRef<number>(0);

  const updateSize = useCallback(() => {
    const el = containerRef.current;
    if (!el) return;
    const w = el.clientWidth;
    const h = el.clientHeight;
    setSize((prev) => {
      if (prev.width === w && prev.height === h) return prev;
      return { width: w, height: h };
    });
  }, [containerRef]);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    // Initial measurement
    updateSize();

    const handleResize = () => {
      // Debounce via rAF to avoid layout thrashing during panel resizes
      cancelAnimationFrame(rafRef.current);
      rafRef.current = requestAnimationFrame(updateSize);
    };

    const resizeObserver = new ResizeObserver(handleResize);
    resizeObserver.observe(el);
    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(rafRef.current);
      resizeObserver.disconnect();
      window.removeEventListener('resize', handleResize);
    };
  }, [containerRef, updateSize]);

  return size;
}
