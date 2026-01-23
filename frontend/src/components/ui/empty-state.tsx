import type { ReactNode } from 'react';
import type { LucideIcon } from 'lucide-react';

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: ReactNode;
}

export function EmptyState({ icon: Icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-8 text-center">
      <Icon className="h-10 w-10 text-muted-foreground/60 mb-3" />
      <h3 className="text-lg font-medium text-foreground">{title}</h3>
      <p className="text-sm text-muted-foreground mt-1 mb-4 max-w-sm">{description}</p>
      {action}
    </div>
  );
}
