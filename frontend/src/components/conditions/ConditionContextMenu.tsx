import { useEffect, useRef } from 'react';
import { Copy, Pencil, Trash2, ArrowUp, ArrowDown, Eye, EyeOff, Calculator } from 'lucide-react';
import type { Condition } from '@/types';

interface ConditionContextMenuProps {
  condition: Condition;
  position: { x: number; y: number };
  isFirst: boolean;
  isLast: boolean;
  onClose: () => void;
  onEdit: (condition: Condition) => void;
  onDuplicate: (condition: Condition) => void;
  onDelete: (condition: Condition) => void;
  onMoveUp: (condition: Condition) => void;
  onMoveDown: (condition: Condition) => void;
  onToggleVisibility: (condition: Condition) => void;
  onCreateAssembly?: (condition: Condition) => void;
}

interface MenuItem {
  label: string;
  icon: React.ReactNode;
  shortcut?: string;
  onClick: () => void;
  danger?: boolean;
  disabled?: boolean;
}

export function ConditionContextMenu({
  condition,
  position,
  isFirst,
  isLast,
  onClose,
  onEdit,
  onDuplicate,
  onDelete,
  onMoveUp,
  onMoveDown,
  onToggleVisibility,
  onCreateAssembly,
}: ConditionContextMenuProps) {
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        onClose();
      }
    };
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('mousedown', handleClick);
    document.addEventListener('keydown', handleEscape);
    return () => {
      document.removeEventListener('mousedown', handleClick);
      document.removeEventListener('keydown', handleEscape);
    };
  }, [onClose]);

  const items: MenuItem[] = [
    {
      label: 'Edit',
      icon: <Pencil className="h-3.5 w-3.5" />,
      onClick: () => { onEdit(condition); onClose(); },
    },
    {
      label: 'Duplicate',
      icon: <Copy className="h-3.5 w-3.5" />,
      shortcut: 'Ctrl+D',
      onClick: () => { onDuplicate(condition); onClose(); },
    },
    ...(onCreateAssembly
      ? [
          {
            label: 'Create Assembly',
            icon: <Calculator className="h-3.5 w-3.5" />,
            onClick: () => { onCreateAssembly(condition); onClose(); },
          },
        ]
      : []),
    {
      label: condition.is_visible ? 'Hide' : 'Show',
      icon: condition.is_visible ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />,
      shortcut: 'V',
      onClick: () => { onToggleVisibility(condition); onClose(); },
    },
    {
      label: 'Move Up',
      icon: <ArrowUp className="h-3.5 w-3.5" />,
      onClick: () => { onMoveUp(condition); onClose(); },
      disabled: isFirst,
    },
    {
      label: 'Move Down',
      icon: <ArrowDown className="h-3.5 w-3.5" />,
      onClick: () => { onMoveDown(condition); onClose(); },
      disabled: isLast,
    },
    {
      label: 'Delete',
      icon: <Trash2 className="h-3.5 w-3.5" />,
      shortcut: 'Del',
      onClick: () => { onDelete(condition); onClose(); },
      danger: true,
    },
  ];

  return (
    <div
      ref={menuRef}
      className="fixed z-50 min-w-[160px] rounded border border-neutral-600 bg-neutral-800 py-1 shadow-xl"
      style={{ left: position.x, top: position.y }}
      data-testid="condition-context-menu"
    >
      {items.map((item, i) => (
        <button
          key={item.label}
          onClick={item.onClick}
          disabled={item.disabled}
          className={`flex w-full items-center gap-2 px-3 py-1.5 text-xs transition-colors ${
            item.danger
              ? 'text-red-400 hover:bg-red-900/30'
              : 'text-neutral-300 hover:bg-neutral-700'
          } ${item.disabled ? 'cursor-not-allowed opacity-40' : ''} ${
            i === items.length - 1 ? 'border-t border-neutral-700 mt-1 pt-2' : ''
          }`}
        >
          {item.icon}
          <span className="flex-1 text-left">{item.label}</span>
          {item.shortcut && (
            <span className="text-[10px] text-neutral-600">{item.shortcut}</span>
          )}
        </button>
      ))}
    </div>
  );
}
