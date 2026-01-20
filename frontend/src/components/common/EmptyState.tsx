/**
 * EmptyState component for displaying empty states with icon, title, description, and optional action.
 */

import { LucideIcon } from 'lucide-react';

interface EmptyStateProps {
    icon: LucideIcon;
    title: string;
    description: string;
    action?: React.ReactNode;
}

export function EmptyState({ icon: Icon, title, description, action }: EmptyStateProps) {
    return (
        <div className="flex flex-col items-center justify-center py-12 text-center">
            <Icon className="w-16 h-16 text-gray-400 mb-4" />
            <h3 className="text-lg font-semibold mb-2">{title}</h3>
            <p className="text-gray-600 mb-4 max-w-md">{description}</p>
            {action}
        </div>
    );
}
