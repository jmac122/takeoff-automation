import { useState, useCallback, useRef } from 'react';

export type NotificationType = 'error' | 'warning' | 'info' | 'success';

export interface Notification {
    id: string;
    type: NotificationType;
    title: string;
    message: string;
    timestamp: Date;
    read: boolean;
}

interface UseNotificationsReturn {
    notifications: Notification[];
    unreadCount: number;
    addNotification: (type: NotificationType, title: string, message: string) => void;
    markAsRead: (id: string) => void;
    markAllAsRead: () => void;
    removeNotification: (id: string) => void;
    clearAll: () => void;
}

export function useNotifications(): UseNotificationsReturn {
    const [notifications, setNotifications] = useState<Notification[]>([]);
    const idCounter = useRef(0);

    const addNotification = useCallback((type: NotificationType, title: string, message: string) => {
        const id = `notification-${Date.now()}-${idCounter.current++}`;
        const notification: Notification = {
            id,
            type,
            title,
            message,
            timestamp: new Date(),
            read: false,
        };

        setNotifications(prev => [notification, ...prev]);
    }, []);

    const markAsRead = useCallback((id: string) => {
        setNotifications(prev =>
            prev.map(n => (n.id === id ? { ...n, read: true } : n))
        );
    }, []);

    const markAllAsRead = useCallback(() => {
        setNotifications(prev => prev.map(n => ({ ...n, read: true })));
    }, []);

    const removeNotification = useCallback((id: string) => {
        setNotifications(prev => prev.filter(n => n.id !== id));
    }, []);

    const clearAll = useCallback(() => {
        setNotifications([]);
    }, []);

    const unreadCount = notifications.filter(n => !n.read).length;

    return {
        notifications,
        unreadCount,
        addNotification,
        markAsRead,
        markAllAsRead,
        removeNotification,
        clearAll,
    };
}
