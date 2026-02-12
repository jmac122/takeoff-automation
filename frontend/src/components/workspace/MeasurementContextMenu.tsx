import { useEffect, useRef } from 'react';
import type { Measurement } from '@/types';

interface MeasurementContextMenuProps {
  measurement: Measurement;
  position: { x: number; y: number };
  onClose: () => void;
  onDelete: (measurement: Measurement) => void;
  onDuplicate?: (measurement: Measurement) => void;
}

/**
 * CM-030: Right-click context menu for measurements.
 * Rendered as absolutely positioned HTML div over the canvas.
 */
export function MeasurementContextMenu({
  measurement,
  position,
  onClose,
  onDelete,
  onDuplicate,
}: MeasurementContextMenuProps) {
  const menuRef = useRef<HTMLDivElement>(null);

  // Close on click-away or Escape
  useEffect(() => {
    const handleClickAway = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        onClose();
      }
    };
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };

    document.addEventListener('mousedown', handleClickAway);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handleClickAway);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [onClose]);

  const items = [
    {
      label: 'Delete',
      shortcut: 'Del',
      onClick: () => { onDelete(measurement); onClose(); },
      danger: true,
    },
    ...(onDuplicate ? [{
      label: 'Duplicate',
      shortcut: 'Ctrl+D',
      onClick: () => { onDuplicate(measurement); onClose(); },
      danger: false,
    }] : []),
  ];

  return (
    <div
      ref={menuRef}
      className="fixed z-50 min-w-[160px] rounded-md border border-neutral-700 bg-neutral-900 py-1 shadow-xl"
      style={{ left: position.x, top: position.y }}
    >
      {items.map((item) => (
        <button
          key={item.label}
          className={`flex w-full items-center justify-between px-3 py-1.5 text-left text-xs transition-colors ${
            item.danger
              ? 'text-red-400 hover:bg-red-500/20'
              : 'text-neutral-300 hover:bg-neutral-800'
          }`}
          onClick={item.onClick}
        >
          <span>{item.label}</span>
          {item.shortcut && (
            <span className="ml-4 text-neutral-500">{item.shortcut}</span>
          )}
        </button>
      ))}
    </div>
  );
}
