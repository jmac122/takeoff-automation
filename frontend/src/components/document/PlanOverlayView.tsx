/**
 * PlanOverlayView — Overlay comparison view for two document revisions.
 *
 * Renders old and new page images with adjustable opacity, supporting
 * overlay, side-by-side, and swipe comparison modes.
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { revisionsApi } from '@/api/revisions';
import { Button } from '@/components/ui/button';
import {
  X,
  Layers,
  Columns,
  SplitSquareHorizontal,
  ChevronLeft,
  ChevronRight,
  Loader2,
  AlertTriangle,
} from 'lucide-react';

type CompareMode = 'overlay' | 'side-by-side' | 'swipe';

interface PlanOverlayViewProps {
  oldDocumentId: string;
  newDocumentId: string;
  initialPageNumber?: number;
  maxPageCount: number;
  onClose: () => void;
}

export function PlanOverlayView({
  oldDocumentId,
  newDocumentId,
  initialPageNumber = 1,
  maxPageCount,
  onClose,
}: PlanOverlayViewProps) {
  const [pageNumber, setPageNumber] = useState(initialPageNumber);
  const [mode, setMode] = useState<CompareMode>('overlay');
  const [opacity, setOpacity] = useState(0.5);
  const [swipePosition, setSwipePosition] = useState(50);
  const [isDragging, setIsDragging] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const swipeRef = useRef<HTMLDivElement>(null);

  // Fetch comparison data for the current page
  const { data: comparison, isLoading, error } = useQuery({
    queryKey: ['page-comparison', oldDocumentId, newDocumentId, pageNumber],
    queryFn: () =>
      revisionsApi.comparePages({
        old_document_id: oldDocumentId,
        new_document_id: newDocumentId,
        page_number: pageNumber,
      }),
    enabled: !!oldDocumentId && !!newDocumentId,
  });

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      } else if (e.key === 'ArrowLeft' && pageNumber > 1) {
        setPageNumber((p) => p - 1);
      } else if (e.key === 'ArrowRight' && pageNumber < maxPageCount) {
        setPageNumber((p) => p + 1);
      } else if (e.key === '1') {
        setMode('overlay');
      } else if (e.key === '2') {
        setMode('side-by-side');
      } else if (e.key === '3') {
        setMode('swipe');
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose, pageNumber, maxPageCount]);

  // Swipe drag handling
  const handleSwipeMove = useCallback(
    (clientX: number) => {
      if (!isDragging || !swipeRef.current) return;
      const rect = swipeRef.current.getBoundingClientRect();
      const x = clientX - rect.left;
      const pct = Math.max(0, Math.min(100, (x / rect.width) * 100));
      setSwipePosition(pct);
    },
    [isDragging],
  );

  useEffect(() => {
    if (!isDragging) return;
    const handleMouseMove = (e: MouseEvent) => handleSwipeMove(e.clientX);
    const handleMouseUp = () => setIsDragging(false);
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, handleSwipeMove]);

  const renderOverlayMode = () => (
    <div className="relative flex-1 flex items-center justify-center overflow-hidden">
      {/* Old image (base) */}
      {comparison?.old_image_url && (
        <img
          src={comparison.old_image_url}
          alt="Old revision"
          className="absolute max-h-full max-w-full object-contain"
          draggable={false}
        />
      )}
      {/* New image (overlay with adjustable opacity) */}
      {comparison?.new_image_url && (
        <img
          src={comparison.new_image_url}
          alt="New revision"
          className="absolute max-h-full max-w-full object-contain"
          style={{ opacity }}
          draggable={false}
        />
      )}
      {/* Opacity not having both images */}
      {!comparison?.has_both && comparison && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/50">
          <div className="flex items-center gap-2 rounded bg-amber-900/80 px-4 py-2 text-sm text-amber-200">
            <AlertTriangle size={16} />
            <span>
              {!comparison.old_image_url
                ? 'Old revision page not available'
                : 'New revision page not available'}
            </span>
          </div>
        </div>
      )}
    </div>
  );

  const renderSideBySideMode = () => (
    <div className="flex flex-1 gap-1 overflow-hidden">
      {/* Old */}
      <div className="flex-1 flex flex-col items-center justify-center overflow-hidden bg-neutral-950 border-r border-neutral-700">
        <div className="text-xs text-neutral-500 py-1">Old Revision</div>
        <div className="flex-1 flex items-center justify-center overflow-hidden p-2">
          {comparison?.old_image_url ? (
            <img
              src={comparison.old_image_url}
              alt="Old revision"
              className="max-h-full max-w-full object-contain"
              draggable={false}
            />
          ) : (
            <span className="text-sm text-neutral-600">No image</span>
          )}
        </div>
      </div>
      {/* New */}
      <div className="flex-1 flex flex-col items-center justify-center overflow-hidden bg-neutral-950">
        <div className="text-xs text-neutral-500 py-1">New Revision</div>
        <div className="flex-1 flex items-center justify-center overflow-hidden p-2">
          {comparison?.new_image_url ? (
            <img
              src={comparison.new_image_url}
              alt="New revision"
              className="max-h-full max-w-full object-contain"
              draggable={false}
            />
          ) : (
            <span className="text-sm text-neutral-600">No image</span>
          )}
        </div>
      </div>
    </div>
  );

  const renderSwipeMode = () => (
    <div
      ref={swipeRef}
      className="relative flex-1 flex items-center justify-center overflow-hidden cursor-col-resize"
      onMouseDown={() => setIsDragging(true)}
    >
      {/* New image (full) */}
      {comparison?.new_image_url && (
        <img
          src={comparison.new_image_url}
          alt="New revision"
          className="absolute max-h-full max-w-full object-contain"
          draggable={false}
        />
      )}
      {/* Old image (clipped to swipe position) */}
      {comparison?.old_image_url && (
        <div
          className="absolute inset-0 overflow-hidden"
          style={{ width: `${swipePosition}%` }}
        >
          <img
            src={comparison.old_image_url}
            alt="Old revision"
            className="max-h-full max-w-full object-contain"
            style={{ position: 'absolute', left: 0, top: 0, width: '100%', height: '100%', objectFit: 'contain' }}
            draggable={false}
          />
        </div>
      )}
      {/* Swipe divider */}
      <div
        className="absolute top-0 bottom-0 w-0.5 bg-blue-500 z-10"
        style={{ left: `${swipePosition}%` }}
      >
        <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-6 h-10 bg-blue-500 rounded flex items-center justify-center">
          <span className="text-white text-xs font-bold">||</span>
        </div>
      </div>
      {/* Labels */}
      <div className="absolute top-2 left-2 text-xs text-neutral-400 bg-neutral-900/80 px-2 py-0.5 rounded z-10">
        Old
      </div>
      <div className="absolute top-2 right-2 text-xs text-neutral-400 bg-neutral-900/80 px-2 py-0.5 rounded z-10">
        New
      </div>
    </div>
  );

  return (
    <div
      ref={containerRef}
      className="absolute inset-0 z-40 flex flex-col bg-neutral-950"
      data-testid="plan-overlay-view"
    >
      {/* Top control bar */}
      <div className="flex items-center justify-between border-b border-neutral-700 bg-neutral-900 px-4 py-2">
        <div className="flex items-center gap-3">
          {/* Mode selector */}
          <div className="flex rounded border border-neutral-700 overflow-hidden">
            <button
              onClick={() => setMode('overlay')}
              className={`px-3 py-1 text-xs flex items-center gap-1 transition-colors ${
                mode === 'overlay'
                  ? 'bg-blue-600 text-white'
                  : 'bg-neutral-800 text-neutral-400 hover:text-neutral-200'
              }`}
              title="Overlay (1)"
            >
              <Layers size={12} />
              Overlay
            </button>
            <button
              onClick={() => setMode('side-by-side')}
              className={`px-3 py-1 text-xs flex items-center gap-1 transition-colors ${
                mode === 'side-by-side'
                  ? 'bg-blue-600 text-white'
                  : 'bg-neutral-800 text-neutral-400 hover:text-neutral-200'
              }`}
              title="Side by Side (2)"
            >
              <Columns size={12} />
              Side by Side
            </button>
            <button
              onClick={() => setMode('swipe')}
              className={`px-3 py-1 text-xs flex items-center gap-1 transition-colors ${
                mode === 'swipe'
                  ? 'bg-blue-600 text-white'
                  : 'bg-neutral-800 text-neutral-400 hover:text-neutral-200'
              }`}
              title="Swipe (3)"
            >
              <SplitSquareHorizontal size={12} />
              Swipe
            </button>
          </div>

          {/* Opacity slider (overlay mode only) */}
          {mode === 'overlay' && (
            <div className="flex items-center gap-2">
              <span className="text-xs text-neutral-400">Opacity:</span>
              <input
                type="range"
                min={0}
                max={100}
                value={Math.round(opacity * 100)}
                onChange={(e) => setOpacity(Number(e.target.value) / 100)}
                className="w-24 h-1 accent-blue-500"
              />
              <span className="text-xs text-neutral-500 w-8">
                {Math.round(opacity * 100)}%
              </span>
            </div>
          )}
        </div>

        {/* Page navigation */}
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            disabled={pageNumber <= 1}
            onClick={() => setPageNumber((p) => p - 1)}
            className="text-neutral-400 h-7 w-7 p-0"
          >
            <ChevronLeft size={14} />
          </Button>
          <span className="text-xs text-neutral-300 min-w-[4rem] text-center">
            Page {pageNumber} / {maxPageCount}
          </span>
          <Button
            variant="ghost"
            size="sm"
            disabled={pageNumber >= maxPageCount}
            onClick={() => setPageNumber((p) => p + 1)}
            className="text-neutral-400 h-7 w-7 p-0"
          >
            <ChevronRight size={14} />
          </Button>
        </div>

        {/* Close button */}
        <Button
          variant="ghost"
          size="sm"
          onClick={onClose}
          className="text-neutral-400 hover:text-white"
        >
          <X size={16} />
        </Button>
      </div>

      {/* Content area */}
      {isLoading ? (
        <div className="flex-1 flex items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-neutral-500" />
        </div>
      ) : error ? (
        <div className="flex-1 flex items-center justify-center text-red-400 text-sm">
          Failed to load comparison data
        </div>
      ) : (
        <>
          {mode === 'overlay' && renderOverlayMode()}
          {mode === 'side-by-side' && renderSideBySideMode()}
          {mode === 'swipe' && renderSwipeMode()}
        </>
      )}

      {/* Bottom hint bar */}
      <div className="border-t border-neutral-700 bg-neutral-900 px-4 py-1 text-[10px] text-neutral-500 flex items-center justify-center gap-4">
        <span>Esc: Close</span>
        <span>1/2/3: Switch mode</span>
        <span>Arrow keys: Navigate pages</span>
      </div>
    </div>
  );
}
