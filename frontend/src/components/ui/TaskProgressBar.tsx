/**
 * TaskProgressBar — displays task status with progress bar, step name,
 * spinner/checkmark/error icon, and optional cancel button.
 */

import * as React from 'react';
import { Check, Loader2, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import type { TaskStatus } from '@/hooks/useTaskPolling';

interface TaskProgressBarProps {
  task: TaskStatus;
  onCancel?: () => void;
  showDetail?: boolean;
  className?: string;
}

function StatusIcon({ status }: { status: string }) {
  switch (status) {
    case 'SUCCESS':
      return <Check className="h-4 w-4 text-green-500 shrink-0" />;
    case 'FAILURE':
    case 'REVOKED':
      return <X className="h-4 w-4 text-red-500 shrink-0" />;
    default:
      // Spinner for PENDING / STARTED / PROGRESS
      return <Loader2 className="h-4 w-4 text-blue-500 animate-spin shrink-0" />;
  }
}

const isRunning = (status: string) =>
  ['PENDING', 'STARTED', 'PROGRESS'].includes(status);

export function TaskProgressBar({
  task,
  onCancel,
  showDetail = true,
  className,
}: TaskProgressBarProps) {
  return (
    <div className={cn('flex flex-col gap-1.5 w-full', className)}>
      {/* Header row: icon + name + cancel */}
      <div className="flex items-center gap-2">
        <StatusIcon status={task.status} />
        <span className="text-sm font-medium truncate flex-1">
          {task.task_name ?? task.task_type ?? 'Task'}
        </span>
        {isRunning(task.status) && onCancel && (
          <Button
            variant="ghost"
            size="sm"
            className="h-6 px-2 text-xs"
            onClick={onCancel}
          >
            Cancel
          </Button>
        )}
      </div>

      {/* Progress bar — only while running */}
      {isRunning(task.status) && (
        <Progress value={task.progress.percent} className="h-2" />
      )}

      {/* Step + percentage */}
      {showDetail && isRunning(task.status) && (
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span className="truncate">{task.progress.step ?? 'Waiting...'}</span>
          <span className="ml-2 tabular-nums">
            {Math.round(task.progress.percent)}%
          </span>
        </div>
      )}

      {/* Error message */}
      {task.status === 'FAILURE' && task.error && showDetail && (
        <p className="text-xs text-red-500 truncate">{task.error}</p>
      )}
    </div>
  );
}
