import { useEffect } from 'react';
import { cn } from '@/lib/utils';

interface ShapeContextMenuProps {
    position: { x: number; y: number };
    isHidden: boolean;
    onEdit: () => void;
    onDuplicate: () => void;
    onDelete: () => void;
    onBringToFront: () => void;
    onSendToBack: () => void;
    onToggleHidden: () => void;
    onClose: () => void;
}

export function ShapeContextMenu({
    position,
    isHidden,
    onEdit,
    onDuplicate,
    onDelete,
    onBringToFront,
    onSendToBack,
    onToggleHidden,
    onClose,
}: ShapeContextMenuProps) {
    useEffect(() => {
        const handleClick = () => onClose();
        const handleKey = (event: KeyboardEvent) => {
            if (event.key === 'Escape') onClose();
        };
        window.addEventListener('click', handleClick);
        window.addEventListener('contextmenu', handleClick);
        window.addEventListener('keydown', handleKey);
        return () => {
            window.removeEventListener('click', handleClick);
            window.removeEventListener('contextmenu', handleClick);
            window.removeEventListener('keydown', handleKey);
        };
    }, [onClose]);

    const items = [
        { label: 'Edit Properties', onClick: onEdit },
        { label: 'Duplicate', onClick: onDuplicate },
        { label: 'Delete', onClick: onDelete, tone: 'danger' as const },
        { divider: true },
        { label: 'Bring to Front', onClick: onBringToFront },
        { label: 'Send to Back', onClick: onSendToBack },
        { divider: true },
        { label: isHidden ? 'Show' : 'Hide', onClick: onToggleHidden },
    ];

    return (
        <div
            className="fixed z-[100] rounded-md border border-neutral-700 bg-neutral-950/95 shadow-xl backdrop-blur"
            style={{ top: position.y, left: position.x }}
            role="menu"
            onContextMenu={(event) => event.preventDefault()}
        >
            <div className="min-w-[200px] py-1 text-xs text-neutral-200">
                {items.map((item, index) =>
                    item.divider ? (
                        <div
                            key={`divider-${index}`}
                            className="my-1 border-t border-neutral-800"
                        />
                    ) : (
                        <button
                            key={item.label}
                            type="button"
                            onClick={() => {
                                item.onClick?.();
                                onClose();
                            }}
                            className={cn(
                                'w-full px-3 py-2 text-left transition-colors hover:bg-neutral-800',
                                item.tone === 'danger' && 'text-red-400 hover:text-red-300'
                            )}
                        >
                            {item.label}
                        </button>
                    )
                )}
            </div>
        </div>
    );
}
