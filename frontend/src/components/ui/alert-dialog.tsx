import * as React from 'react';
import * as AlertDialogPrimitive from '@radix-ui/react-alert-dialog';

import { cn } from '@/lib/utils';
import { buttonVariants } from '@/components/ui/button';

// #region agent log
fetch('http://127.0.0.1:7244/ingest/c2908297-06df-40fb-a71a-4f158024ffa0',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sessionId:'debug-session',runId:'run1',hypothesisId:'H2',location:'alert-dialog.tsx:8',message:'alert-dialog module loaded',data:{hasButtonVariants:typeof buttonVariants === 'function'},timestamp:Date.now()})}).catch(()=>{});
// #endregion

const AlertDialog = AlertDialogPrimitive.Root;
const AlertDialogTrigger = AlertDialogPrimitive.Trigger;
const AlertDialogPortal = AlertDialogPrimitive.Portal;
const AlertDialogOverlay = React.forwardRef<
    React.ElementRef<typeof AlertDialogPrimitive.Overlay>,
    React.ComponentPropsWithoutRef<typeof AlertDialogPrimitive.Overlay>
>(({ className, ...props }, ref) => (
    <AlertDialogPrimitive.Overlay
        className={cn(
            'fixed inset-0 z-50 bg-black/80 backdrop-blur-sm data-[state=open]:animate-in data-[state=closed]:animate-out',
            className
        )}
        {...props}
        ref={ref}
    />
));
AlertDialogOverlay.displayName = AlertDialogPrimitive.Overlay.displayName;

const AlertDialogContent = React.forwardRef<
    React.ElementRef<typeof AlertDialogPrimitive.Content>,
    React.ComponentPropsWithoutRef<typeof AlertDialogPrimitive.Content>
>(({ className, ...props }, ref) => (
    <AlertDialogPortal>
        <AlertDialogOverlay />
        <AlertDialogPrimitive.Content
            ref={ref}
            className={cn(
                'fixed left-[50%] top-[50%] z-50 w-full max-w-lg translate-x-[-50%] translate-y-[-50%] rounded-lg border border-border bg-background p-6 shadow-lg',
                className
            )}
            {...props}
        />
    </AlertDialogPortal>
));
AlertDialogContent.displayName = AlertDialogPrimitive.Content.displayName;

const AlertDialogHeader = ({
    className,
    ...props
}: React.HTMLAttributes<HTMLDivElement>) => (
    <div
        className={cn('flex flex-col space-y-2 text-center sm:text-left', className)}
        {...props}
    />
);
AlertDialogHeader.displayName = 'AlertDialogHeader';

const AlertDialogFooter = ({
    className,
    ...props
}: React.HTMLAttributes<HTMLDivElement>) => (
    <div
        className={cn('flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2', className)}
        {...props}
    />
);
AlertDialogFooter.displayName = 'AlertDialogFooter';

const AlertDialogTitle = React.forwardRef<
    React.ElementRef<typeof AlertDialogPrimitive.Title>,
    React.ComponentPropsWithoutRef<typeof AlertDialogPrimitive.Title>
>(({ className, ...props }, ref) => (
    <AlertDialogPrimitive.Title
        ref={ref}
        className={cn('text-lg font-semibold', className)}
        {...props}
    />
));
AlertDialogTitle.displayName = AlertDialogPrimitive.Title.displayName;

const AlertDialogDescription = React.forwardRef<
    React.ElementRef<typeof AlertDialogPrimitive.Description>,
    React.ComponentPropsWithoutRef<typeof AlertDialogPrimitive.Description>
>(({ className, ...props }, ref) => (
    <AlertDialogPrimitive.Description
        ref={ref}
        className={cn('text-sm text-muted-foreground', className)}
        {...props}
    />
));
AlertDialogDescription.displayName = AlertDialogPrimitive.Description.displayName;

const AlertDialogAction = React.forwardRef<
    React.ElementRef<typeof AlertDialogPrimitive.Action>,
    React.ComponentPropsWithoutRef<typeof AlertDialogPrimitive.Action>
>(({ className, ...props }, ref) => (
    <AlertDialogPrimitive.Action
        ref={ref}
        className={cn(buttonVariants({ variant: 'default' }), className)}
        {...props}
    />
));
AlertDialogAction.displayName = AlertDialogPrimitive.Action.displayName;

const AlertDialogCancel = React.forwardRef<
    React.ElementRef<typeof AlertDialogPrimitive.Cancel>,
    React.ComponentPropsWithoutRef<typeof AlertDialogPrimitive.Cancel>
>(({ className, ...props }, ref) => (
    <AlertDialogPrimitive.Cancel
        ref={ref}
        className={cn(buttonVariants({ variant: 'outline' }), className)}
        {...props}
    />
));
AlertDialogCancel.displayName = AlertDialogPrimitive.Cancel.displayName;

export {
    AlertDialog,
    AlertDialogTrigger,
    AlertDialogPortal,
    AlertDialogOverlay,
    AlertDialogContent,
    AlertDialogHeader,
    AlertDialogFooter,
    AlertDialogTitle,
    AlertDialogDescription,
    AlertDialogAction,
    AlertDialogCancel,
};
