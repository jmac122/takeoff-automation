import { useState, useRef, useEffect } from 'react';
import { Bell, X, AlertCircle, AlertTriangle, Info, CheckCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useNotificationContext } from '@/contexts/NotificationContext';
import type { Notification } from '@/hooks/useNotifications';
import { cn } from '@/lib/utils';

export function NotificationBell() {
    const {
        notifications,
        unreadCount,
        markAllAsRead,
        removeNotification,
    } = useNotificationContext();

    const [isOpen, setIsOpen] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);

    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };

        if (isOpen) {
            document.addEventListener('mousedown', handleClickOutside);
            return () => document.removeEventListener('mousedown', handleClickOutside);
        }
    }, [isOpen]);

    const handleToggle = () => {
        setIsOpen(prev => {
            if (!prev) {
                // Opening - mark all as read
                markAllAsRead();
            }
            return !prev;
        });
    };

    const getIcon = (type: Notification['type']) => {
        switch (type) {
            case 'error':
                return <AlertCircle className="w-4 h-4 text-red-400" />;
            case 'warning':
                return <AlertTriangle className="w-4 h-4 text-amber-400" />;
            case 'info':
                return <Info className="w-4 h-4 text-blue-400" />;
            case 'success':
                return <CheckCircle className="w-4 h-4 text-green-400" />;
        }
    };

    const getTypeStyles = (type: Notification['type']) => {
        switch (type) {
            case 'error':
                return 'border-red-500/50 bg-red-900/20';
            case 'warning':
                return 'border-amber-500/50 bg-amber-900/20';
            case 'info':
                return 'border-blue-500/50 bg-blue-900/20';
            case 'success':
                return 'border-green-500/50 bg-green-900/20';
        }
    };

    return (
        <div className="relative" ref={dropdownRef}>
            <Button
                variant="outline"
                size="sm"
                onClick={handleToggle}
                className="relative border-neutral-700 text-white hover:bg-neutral-800"
                title="Notifications"
            >
                <Bell className="w-4 h-4" />
                {unreadCount > 0 && (
                    <span className="absolute -top-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-xs font-bold text-white">
                        {unreadCount > 99 ? '99+' : unreadCount}
                    </span>
                )}
            </Button>

            {isOpen && (
                <div className="absolute right-0 top-full mt-2 w-96 rounded-lg border border-neutral-700 bg-neutral-900 shadow-xl z-50">
                    <div className="flex items-center justify-between border-b border-neutral-700 p-3">
                        <h3 className="text-sm font-semibold text-white font-mono uppercase">
                            Notifications
                        </h3>
                        {notifications.length > 0 && (
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => {
                                    markAllAsRead();
                                }}
                                className="text-xs text-neutral-400 hover:text-white h-auto p-1"
                            >
                                Mark all read
                            </Button>
                        )}
                    </div>

                    <div className="max-h-96 overflow-y-auto">
                        {notifications.length === 0 ? (
                            <div className="p-6 text-center text-neutral-400 text-sm font-mono">
                                No notifications
                            </div>
                        ) : (
                            <div className="divide-y divide-neutral-800">
                                {notifications.map((notification) => (
                                    <div
                                        key={notification.id}
                                        className={cn(
                                            'p-3 transition-colors',
                                            !notification.read && 'bg-neutral-800/50',
                                            getTypeStyles(notification.type)
                                        )}
                                    >
                                        <div className="flex items-start gap-3">
                                            <div className="mt-0.5 flex-shrink-0">
                                                {getIcon(notification.type)}
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-start justify-between gap-2">
                                                    <div className="flex-1">
                                                        <p className="text-sm font-semibold text-white font-mono">
                                                            {notification.title}
                                                        </p>
                                                        <p className="text-xs text-neutral-400 font-mono mt-1">
                                                            {notification.message}
                                                        </p>
                                                        <p className="text-xs text-neutral-500 font-mono mt-1">
                                                            {notification.timestamp.toLocaleTimeString()}
                                                        </p>
                                                    </div>
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        onClick={() => removeNotification(notification.id)}
                                                        className="text-neutral-500 hover:text-white h-auto p-1 flex-shrink-0"
                                                    >
                                                        <X className="w-3 h-3" />
                                                    </Button>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
