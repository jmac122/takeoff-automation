# Takeoff Platform - Design System & Component Library

> **Purpose**: Ensure visual and behavioral consistency across all frontend components
> **Stack**: React, TypeScript, Tailwind CSS, shadcn/ui

---

## Design Principles

1. **Clarity over decoration** - Construction professionals need to see data clearly, not wade through visual noise
2. **Information density** - Users work with complex plans; maximize useful info per screen
3. **Consistent feedback** - Every action should have clear visual confirmation
4. **Accessible by default** - Color is never the only indicator; support keyboard navigation

---

## Color System

### Semantic Colors

Use these semantic names, not raw hex values:

```typescript
// tailwind.config.js extends these from shadcn/ui
const colors = {
  // Base
  background: "hsl(var(--background))",      // Page background
  foreground: "hsl(var(--foreground))",      // Primary text
  
  // UI Elements
  card: "hsl(var(--card))",                  // Card backgrounds
  cardForeground: "hsl(var(--card-foreground))",
  popover: "hsl(var(--popover))",            // Dropdowns, tooltips
  popoverForeground: "hsl(var(--popover-foreground))",
  
  // Interactive
  primary: "hsl(var(--primary))",            // Primary buttons, links
  primaryForeground: "hsl(var(--primary-foreground))",
  secondary: "hsl(var(--secondary))",        // Secondary actions
  secondaryForeground: "hsl(var(--secondary-foreground))",
  
  // States
  muted: "hsl(var(--muted))",                // Disabled, placeholder
  mutedForeground: "hsl(var(--muted-foreground))",
  accent: "hsl(var(--accent))",              // Hover states
  accentForeground: "hsl(var(--accent-foreground))",
  
  // Feedback
  destructive: "hsl(var(--destructive))",    // Errors, delete actions
  destructiveForeground: "hsl(var(--destructive-foreground))",
  
  // Borders & inputs
  border: "hsl(var(--border))",
  input: "hsl(var(--input))",
  ring: "hsl(var(--ring))",                  // Focus rings
};
```

### Measurement/Condition Colors

These colors are used for drawing and highlighting measurements on plans:

```typescript
// frontend/src/lib/colors.ts
export const MEASUREMENT_COLORS = {
  // Concrete scopes - warm tones
  foundation: "#E57373",      // Red 300
  slab: "#FFB74D",            // Orange 300
  wall: "#FFF176",            // Yellow 300
  footing: "#A1887F",         // Brown 300
  
  // Linear elements - cool tones
  curb: "#4FC3F7",            // Light Blue 300
  beam: "#7986CB",            // Indigo 300
  column: "#BA68C8",          // Purple 300
  
  // Areas - greens
  flatwork: "#81C784",        // Green 300
  pavement: "#AED581",        // Light Green 300
  
  // Default/unclassified
  default: "#90A4AE",         // Blue Grey 300
  
  // Selection states
  selected: "#2196F3",        // Blue 500
  hover: "#64B5F6",           // Blue 300
  
  // Review states
  approved: "#4CAF50",        // Green 500
  rejected: "#F44336",        // Red 500
  pending: "#FF9800",         // Orange 500
} as const;

// Color with opacity for fills
export function withOpacity(hex: string, opacity: number): string {
  return `${hex}${Math.round(opacity * 255).toString(16).padStart(2, '0')}`;
}
```

### Usage Rules

1. **Never use raw hex codes in components** - Always reference the color system
2. **Measurement colors must have sufficient contrast** against plan backgrounds (usually white/light gray)
3. **Use opacity for fills** - Strokes at 100%, fills at 30-50% to see underlying plan
4. **Color alone cannot indicate state** - Always pair with icons or text

---

## Typography

### Font Stack

```css
/* Already configured in Tailwind via shadcn/ui */
--font-sans: "Inter", system-ui, -apple-system, sans-serif;
--font-mono: "JetBrains Mono", "Fira Code", monospace;
```

### Scale

| Name | Class | Size | Use Case |
|------|-------|------|----------|
| xs | `text-xs` | 12px | Captions, timestamps |
| sm | `text-sm` | 14px | Secondary text, labels |
| base | `text-base` | 16px | Body text (default) |
| lg | `text-lg` | 18px | Subheadings |
| xl | `text-xl` | 20px | Section titles |
| 2xl | `text-2xl` | 24px | Page titles |
| 3xl | `text-3xl` | 30px | Hero headings (rare) |

### Usage Rules

1. **Page titles**: `text-2xl font-semibold`
2. **Section headings**: `text-lg font-medium`
3. **Body text**: `text-base` (no modifier needed)
4. **Labels**: `text-sm font-medium text-muted-foreground`
5. **Data values**: `text-sm font-mono` for numbers/measurements
6. **Buttons**: `text-sm font-medium`

---

## Spacing

Use Tailwind's spacing scale consistently:

| Token | Value | Use Case |
|-------|-------|----------|
| 1 | 4px | Tight inline spacing |
| 2 | 8px | Icon-to-text gap |
| 3 | 12px | Compact padding |
| 4 | 16px | Standard padding |
| 6 | 24px | Section spacing |
| 8 | 32px | Card padding |
| 12 | 48px | Major section gaps |

### Standard Patterns

```tsx
// Card padding
<Card className="p-4 md:p-6">

// Form field spacing
<div className="space-y-4">

// Button group gap
<div className="flex gap-2">

// Page section margins
<section className="mb-8">
```

---

## Component Library

### Import Pattern

Always import shadcn/ui components from the local components/ui folder:

```tsx
// ✅ Correct
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

// ❌ Wrong - never import from shadcn directly
import { Button } from "shadcn/ui";
```

### Core Components

#### Button

```tsx
import { Button } from "@/components/ui/button";

// Variants
<Button variant="default">Primary Action</Button>
<Button variant="secondary">Secondary</Button>
<Button variant="outline">Tertiary</Button>
<Button variant="ghost">Minimal</Button>
<Button variant="destructive">Delete</Button>
<Button variant="link">Link Style</Button>

// Sizes
<Button size="sm">Small</Button>
<Button size="default">Default</Button>
<Button size="lg">Large</Button>
<Button size="icon"><IconName /></Button>

// With loading state
<Button disabled={isLoading}>
  {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
  Save
</Button>
```

**Usage rules:**
- One primary button per view/form
- Destructive actions require confirmation dialog
- Always show loading state during async operations

#### Card

```tsx
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";

<Card>
  <CardHeader>
    <CardTitle>Document Details</CardTitle>
    <CardDescription>Uploaded on Jan 15, 2025</CardDescription>
  </CardHeader>
  <CardContent>
    {/* Main content */}
  </CardContent>
  <CardFooter className="flex justify-end gap-2">
    <Button variant="outline">Cancel</Button>
    <Button>Save</Button>
  </CardFooter>
</Card>
```

#### Dialog / Modal

```tsx
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

<Dialog open={open} onOpenChange={setOpen}>
  <DialogTrigger asChild>
    <Button>Open Modal</Button>
  </DialogTrigger>
  <DialogContent className="sm:max-w-[425px]">
    <DialogHeader>
      <DialogTitle>Create Condition</DialogTitle>
      <DialogDescription>
        Define a new measurement condition for this project.
      </DialogDescription>
    </DialogHeader>
    {/* Form content */}
    <DialogFooter>
      <Button variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
      <Button onClick={handleSubmit}>Create</Button>
    </DialogFooter>
  </DialogContent>
</Dialog>
```

**Usage rules:**
- Always include DialogTitle for accessibility
- Escape key and backdrop click should close
- Destructive modals need explicit confirmation text

#### Form Components

```tsx
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";

// Text input with label
<div className="space-y-2">
  <Label htmlFor="name">Condition Name</Label>
  <Input 
    id="name" 
    placeholder="e.g., Foundation Walls"
    value={name}
    onChange={(e) => setName(e.target.value)}
  />
</div>

// Select dropdown
<div className="space-y-2">
  <Label>Measurement Type</Label>
  <Select value={type} onValueChange={setType}>
    <SelectTrigger>
      <SelectValue placeholder="Select type" />
    </SelectTrigger>
    <SelectContent>
      <SelectItem value="linear">Linear (LF)</SelectItem>
      <SelectItem value="area">Area (SF)</SelectItem>
      <SelectItem value="volume">Volume (CY)</SelectItem>
      <SelectItem value="count">Count (EA)</SelectItem>
    </SelectContent>
  </Select>
</div>

// Checkbox
<div className="flex items-center space-x-2">
  <Checkbox id="approved" checked={approved} onCheckedChange={setApproved} />
  <Label htmlFor="approved">Mark as approved</Label>
</div>
```

#### Table

```tsx
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

<Table>
  <TableHeader>
    <TableRow>
      <TableHead>Condition</TableHead>
      <TableHead>Type</TableHead>
      <TableHead className="text-right">Quantity</TableHead>
      <TableHead>Status</TableHead>
    </TableRow>
  </TableHeader>
  <TableBody>
    {conditions.map((condition) => (
      <TableRow key={condition.id}>
        <TableCell className="font-medium">{condition.name}</TableCell>
        <TableCell>{condition.type}</TableCell>
        <TableCell className="text-right font-mono">
          {condition.quantity.toFixed(2)}
        </TableCell>
        <TableCell>
          <StatusBadge status={condition.status} />
        </TableCell>
      </TableRow>
    ))}
  </TableBody>
</Table>
```

#### Toast / Notifications

```tsx
import { useToast } from "@/components/ui/use-toast";

function MyComponent() {
  const { toast } = useToast();
  
  const handleSave = async () => {
    try {
      await saveData();
      toast({
        title: "Saved",
        description: "Your changes have been saved.",
      });
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to save. Please try again.",
      });
    }
  };
}
```

**Usage rules:**
- Success toasts auto-dismiss after 5 seconds
- Error toasts persist until dismissed
- Never use toasts for critical errors that need action

---

## Custom Components

These are app-specific components built on top of shadcn/ui.

### StatusBadge

```tsx
// frontend/src/components/ui/status-badge.tsx
import { cn } from "@/lib/utils";

type Status = "pending" | "approved" | "rejected" | "processing" | "error";

const statusStyles: Record<Status, string> = {
  pending: "bg-yellow-100 text-yellow-800 border-yellow-200",
  approved: "bg-green-100 text-green-800 border-green-200",
  rejected: "bg-red-100 text-red-800 border-red-200",
  processing: "bg-blue-100 text-blue-800 border-blue-200",
  error: "bg-red-100 text-red-800 border-red-200",
};

interface StatusBadgeProps {
  status: Status;
  className?: string;
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium",
        statusStyles[status],
        className
      )}
    >
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
}
```

### MeasurementValue

```tsx
// frontend/src/components/ui/measurement-value.tsx
import { cn } from "@/lib/utils";

interface MeasurementValueProps {
  value: number;
  unit: string;
  precision?: number;
  className?: string;
}

export function MeasurementValue({ 
  value, 
  unit, 
  precision = 2,
  className 
}: MeasurementValueProps) {
  return (
    <span className={cn("font-mono", className)}>
      {value.toFixed(precision)}
      <span className="ml-1 text-muted-foreground text-xs">{unit}</span>
    </span>
  );
}
```

### ColorPicker

```tsx
// frontend/src/components/ui/color-picker.tsx
import { MEASUREMENT_COLORS } from "@/lib/colors";
import { cn } from "@/lib/utils";

interface ColorPickerProps {
  value: string;
  onChange: (color: string) => void;
}

export function ColorPicker({ value, onChange }: ColorPickerProps) {
  const colors = Object.values(MEASUREMENT_COLORS).filter(
    (c) => !["selected", "hover", "approved", "rejected", "pending"].includes(c)
  );
  
  return (
    <div className="flex flex-wrap gap-2">
      {colors.map((color) => (
        <button
          key={color}
          type="button"
          className={cn(
            "h-8 w-8 rounded-md border-2 transition-transform hover:scale-110",
            value === color ? "border-primary ring-2 ring-primary/20" : "border-transparent"
          )}
          style={{ backgroundColor: color }}
          onClick={() => onChange(color)}
        />
      ))}
    </div>
  );
}
```

### LoadingSpinner

```tsx
// frontend/src/components/ui/loading-spinner.tsx
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface LoadingSpinnerProps {
  size?: "sm" | "default" | "lg";
  className?: string;
}

const sizes = {
  sm: "h-4 w-4",
  default: "h-6 w-6",
  lg: "h-8 w-8",
};

export function LoadingSpinner({ size = "default", className }: LoadingSpinnerProps) {
  return (
    <Loader2 className={cn("animate-spin text-muted-foreground", sizes[size], className)} />
  );
}
```

### PageHeader

```tsx
// frontend/src/components/ui/page-header.tsx
interface PageHeaderProps {
  title: string;
  description?: string;
  actions?: React.ReactNode;
}

export function PageHeader({ title, description, actions }: PageHeaderProps) {
  return (
    <div className="flex items-start justify-between mb-6">
      <div>
        <h1 className="text-2xl font-semibold">{title}</h1>
        {description && (
          <p className="text-muted-foreground mt-1">{description}</p>
        )}
      </div>
      {actions && <div className="flex gap-2">{actions}</div>}
    </div>
  );
}
```

### EmptyState

```tsx
// frontend/src/components/ui/empty-state.tsx
import { LucideIcon } from "lucide-react";

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: React.ReactNode;
}

export function EmptyState({ icon: Icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <Icon className="h-12 w-12 text-muted-foreground/50 mb-4" />
      <h3 className="text-lg font-medium">{title}</h3>
      <p className="text-muted-foreground mt-1 mb-4 max-w-sm">{description}</p>
      {action}
    </div>
  );
}
```

---

## Icons

Use Lucide React icons exclusively:

```tsx
import { 
  Upload, 
  Download, 
  Trash2, 
  Edit, 
  Check, 
  X, 
  ChevronDown,
  FileText,
  Image,
  Ruler,
  Square,
  Circle,
  Layers,
  Settings,
  Search,
  Filter,
  MoreHorizontal,
  Loader2,
} from "lucide-react";

// Standard icon sizes
<Icon className="h-4 w-4" />  // In buttons, inline
<Icon className="h-5 w-5" />  // Standalone, navigation
<Icon className="h-6 w-6" />  // Large, emphasis
```

### Icon Conventions

| Action | Icon |
|--------|------|
| Upload | `Upload` |
| Download/Export | `Download` |
| Delete | `Trash2` |
| Edit | `Edit` or `Pencil` |
| Confirm/Approve | `Check` |
| Cancel/Reject | `X` |
| Expand/Collapse | `ChevronDown` / `ChevronUp` |
| Document | `FileText` |
| Image/Plan | `Image` |
| Linear measurement | `Ruler` |
| Area measurement | `Square` |
| Count measurement | `Circle` |
| Layers/Conditions | `Layers` |
| Settings | `Settings` |
| Search | `Search` |
| Filter | `Filter` |
| More actions | `MoreHorizontal` |
| Loading | `Loader2` (with `animate-spin`) |

---

## Layout Patterns

### Page Layout

```tsx
// Standard page structure
export default function ProjectPage() {
  return (
    <div className="container mx-auto py-6">
      <PageHeader 
        title="Project Name"
        description="12 pages • Uploaded Jan 15, 2025"
        actions={
          <>
            <Button variant="outline">Export</Button>
            <Button>Run AI Takeoff</Button>
          </>
        }
      />
      
      <div className="grid grid-cols-12 gap-6">
        {/* Main content */}
        <main className="col-span-12 lg:col-span-8">
          {/* ... */}
        </main>
        
        {/* Sidebar */}
        <aside className="col-span-12 lg:col-span-4">
          {/* ... */}
        </aside>
      </div>
    </div>
  );
}
```

### Split View (Plan + Panel)

```tsx
// For measurement/review views
export default function MeasurementView() {
  return (
    <div className="flex h-[calc(100vh-4rem)]">
      {/* Plan viewer - takes remaining space */}
      <div className="flex-1 relative">
        <PlanViewer />
      </div>
      
      {/* Side panel - fixed width */}
      <div className="w-80 border-l bg-card overflow-y-auto">
        <ConditionPanel />
      </div>
    </div>
  );
}
```

### List/Grid Toggle

```tsx
const [view, setView] = useState<"list" | "grid">("grid");

<div className="flex justify-end mb-4">
  <ToggleGroup type="single" value={view} onValueChange={(v) => v && setView(v)}>
    <ToggleGroupItem value="grid"><Grid className="h-4 w-4" /></ToggleGroupItem>
    <ToggleGroupItem value="list"><List className="h-4 w-4" /></ToggleGroupItem>
  </ToggleGroup>
</div>

{view === "grid" ? (
  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
    {/* Grid items */}
  </div>
) : (
  <Table>
    {/* Table rows */}
  </Table>
)}
```

---

## State Patterns

### Loading States

```tsx
// Full page loading
if (isLoading) {
  return (
    <div className="flex items-center justify-center h-64">
      <LoadingSpinner size="lg" />
    </div>
  );
}

// Inline loading
<Button disabled={isSaving}>
  {isSaving ? (
    <>
      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
      Saving...
    </>
  ) : (
    "Save"
  )}
</Button>

// Skeleton loading
<div className="space-y-4">
  <Skeleton className="h-8 w-48" />
  <Skeleton className="h-32 w-full" />
  <Skeleton className="h-32 w-full" />
</div>
```

### Error States

```tsx
// Full page error
if (error) {
  return (
    <EmptyState
      icon={AlertCircle}
      title="Failed to load project"
      description={error.message}
      action={
        <Button variant="outline" onClick={refetch}>
          Try Again
        </Button>
      }
    />
  );
}

// Inline error
{error && (
  <Alert variant="destructive">
    <AlertCircle className="h-4 w-4" />
    <AlertTitle>Error</AlertTitle>
    <AlertDescription>{error.message}</AlertDescription>
  </Alert>
)}
```

### Empty States

```tsx
if (conditions.length === 0) {
  return (
    <EmptyState
      icon={Layers}
      title="No conditions yet"
      description="Create your first condition to start measuring."
      action={
        <Button onClick={() => setShowCreateModal(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Create Condition
        </Button>
      }
    />
  );
}
```

---

## Accessibility Checklist

- [ ] All interactive elements are keyboard accessible
- [ ] Focus states are visible (using `ring` utilities)
- [ ] Images have alt text
- [ ] Form inputs have associated labels
- [ ] Color is not the only indicator of state
- [ ] Modals trap focus and close on Escape
- [ ] Loading states are announced to screen readers
- [ ] Error messages are associated with form fields

---

## File Organization

```
frontend/src/
├── components/
│   ├── ui/                    # shadcn/ui + custom base components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── status-badge.tsx   # Custom
│   │   ├── measurement-value.tsx
│   │   └── ...
│   ├── layout/                # Layout components
│   │   ├── page-header.tsx
│   │   ├── sidebar.tsx
│   │   └── ...
│   ├── documents/             # Document-related components
│   ├── measurement/           # Measurement tools
│   ├── conditions/            # Condition management
│   └── review/                # Review interface
├── lib/
│   ├── utils.ts               # cn() and other utilities
│   ├── colors.ts              # Color definitions
│   └── api.ts                 # API client
├── hooks/                     # Custom React hooks
├── pages/                     # Page components
└── types/                     # TypeScript types
```

---

## Adding New Components

When creating a new component:

1. **Check if shadcn/ui has it** - `npx shadcn@latest add [component]`
2. **Follow the naming pattern** - PascalCase, descriptive
3. **Add TypeScript props interface** - Document all props
4. **Use `cn()` for conditional classes** - Import from `@/lib/utils`
5. **Add to this design system doc** - Keep documentation current

```tsx
// Template for new components
import { cn } from "@/lib/utils";

interface MyComponentProps {
  /** Description of prop */
  propName: string;
  /** Optional className override */
  className?: string;
}

export function MyComponent({ propName, className }: MyComponentProps) {
  return (
    <div className={cn("base-classes", className)}>
      {/* Implementation */}
    </div>
  );
}
```
