# Component Library Reference

**Last Updated:** January 20, 2026  
**Status:** Production Ready  
**Location:** `frontend/src/components/ui/`

---

## Overview

Complete shadcn/ui component library for ForgeX Takeoffs platform. All components follow the design system defined in `DESIGN-SYSTEM.md` and use HSL color tokens from Tailwind config.

### Core Principles

- ✅ **Accessible:** Built on Radix UI primitives with ARIA attributes
- ✅ **Composable:** Small, focused components that work together
- ✅ **Type-safe:** Full TypeScript support with explicit types
- ✅ **Themeable:** Uses CSS variables for easy customization
- ✅ **Consistent:** Follows design system tokens and patterns

---

## Component Index

| Component | Purpose | Variants | File |
|-----------|---------|----------|------|
| [Button](#button) | Interactive actions | 6 variants | `button.tsx` |
| [Card](#card) | Content containers | 1 + 5 sub-components | `card.tsx` |
| [Input](#input) | Text input fields | 1 | `input.tsx` |
| [Label](#label) | Form labels | 1 | `label.tsx` |
| [Select](#select) | Dropdown selection | 1 + 6 sub-components | `select.tsx` |
| [Badge](#badge) | Status indicators | 4 variants | `badge.tsx` |
| [Skeleton](#skeleton) | Loading states | 1 | `skeleton.tsx` |
| [Alert](#alert) | Notifications | 1 + 2 sub-components | `alert.tsx` |
| [Progress](#progress) | Progress bars | 1 | `progress.tsx` |
| [Dialog](#dialog) | Modal overlays | 1 + 6 sub-components | `dialog.tsx` |

---

## Components

### Button

**Purpose:** Primary interactive element for user actions.

**File:** `frontend/src/components/ui/button.tsx`

**Variants:**
- `default` - Primary action (blue background)
- `destructive` - Dangerous actions (red background)
- `outline` - Secondary action (bordered)
- `secondary` - Tertiary action (gray background)
- `ghost` - Minimal action (transparent)
- `link` - Text link style

**Sizes:**
- `default` - Standard size (h-10 px-4 py-2)
- `sm` - Small size (h-9 px-3)
- `lg` - Large size (h-11 px-8)
- `icon` - Icon-only button (h-10 w-10)

**Props:**
```typescript
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "destructive" | "outline" | "secondary" | "ghost" | "link"
  size?: "default" | "sm" | "lg" | "icon"
  asChild?: boolean
}
```

**Usage:**
```tsx
import { Button } from "@/components/ui/button"
import { Upload } from "lucide-react"

// Primary action
<Button>Submit</Button>

// Destructive action
<Button variant="destructive">Delete</Button>

// With icon
<Button>
  <Upload className="mr-2 h-4 w-4" />
  Upload File
</Button>

// Icon only
<Button variant="ghost" size="icon">
  <Upload className="h-4 w-4" />
</Button>

// Disabled
<Button disabled>Processing...</Button>
```

**When to Use:**
- Primary actions: Use `default` variant
- Dangerous actions: Use `destructive` variant (delete, remove, etc.)
- Secondary actions: Use `outline` or `secondary` variant
- Toolbar actions: Use `ghost` variant
- Navigation: Use `link` variant

---

### Card

**Purpose:** Container for grouping related content with consistent styling.

**File:** `frontend/src/components/ui/card.tsx`

**Components:**
- `Card` - Main container
- `CardHeader` - Top section (optional)
- `CardTitle` - Header title
- `CardDescription` - Header description
- `CardContent` - Main content area
- `CardFooter` - Bottom section (optional, for actions)

**Props:**
```typescript
// All components extend their respective HTML element props
Card extends HTMLDivElement
CardHeader extends HTMLDivElement
CardFooter extends HTMLDivElement
CardTitle extends HTMLHeadingElement
CardDescription extends HTMLParagraphElement
CardContent extends HTMLDivElement
```

**Usage:**
```tsx
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"

<Card>
  <CardHeader>
    <CardTitle>Card Title</CardTitle>
    <CardDescription>Card description goes here</CardDescription>
  </CardHeader>
  <CardContent>
    <p>Main content of the card</p>
  </CardContent>
  <CardFooter className="flex justify-between">
    <Button variant="outline">Cancel</Button>
    <Button>Save</Button>
  </CardFooter>
</Card>

// Simple card
<Card>
  <CardContent className="pt-6">
    <p>Simple content without header</p>
  </CardContent>
</Card>
```

**When to Use:**
- Grouping related information (project details, document info)
- Dashboard widgets
- Settings sections
- List items with multiple fields

---

### Input

**Purpose:** Single-line text input field.

**File:** `frontend/src/components/ui/input.tsx`

**Props:**
```typescript
interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  // Inherits all standard input props (type, placeholder, value, onChange, etc.)
}
```

**Usage:**
```tsx
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

// Basic input
<Input type="text" placeholder="Enter text..." />

// With label
<div className="space-y-2">
  <Label htmlFor="email">Email</Label>
  <Input id="email" type="email" placeholder="you@example.com" />
</div>

// Disabled
<Input disabled value="Read only" />

// With error state (add custom className)
<Input className="border-destructive" placeholder="Error state" />
```

**When to Use:**
- Single-line text entry
- Email, password, search fields
- Number inputs
- Date/time inputs

**Not For:**
- Multi-line text (use `<textarea>`)
- Selections (use `Select`)

---

### Label

**Purpose:** Accessible label for form fields.

**File:** `frontend/src/components/ui/label.tsx`

**Props:**
```typescript
interface LabelProps extends React.LabelHTMLAttributes<HTMLLabelElement> {
  // Inherits all standard label props (htmlFor, etc.)
}
```

**Usage:**
```tsx
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"

<div className="space-y-2">
  <Label htmlFor="name">Project Name</Label>
  <Input id="name" placeholder="Enter project name" />
</div>

// Required field indicator
<Label htmlFor="required">
  Email <span className="text-destructive">*</span>
</Label>
```

**When to Use:**
- Always pair with form inputs for accessibility
- Use `htmlFor` attribute matching input's `id`

---

### Select

**Purpose:** Dropdown selection menu (native select alternative).

**File:** `frontend/src/components/ui/select.tsx`

**Components:**
- `Select` - Root component
- `SelectTrigger` - Button that opens dropdown
- `SelectValue` - Displays selected value
- `SelectContent` - Dropdown container
- `SelectItem` - Individual option
- `SelectGroup` - Groups related options
- `SelectLabel` - Label for a group
- `SelectSeparator` - Visual divider

**Props:**
```typescript
// Built on Radix UI Select primitive
Select: { value, onValueChange, disabled, defaultValue }
SelectItem: { value, disabled, textValue }
```

**Usage:**
```tsx
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

// Basic select
<Select value={value} onValueChange={setValue}>
  <SelectTrigger className="w-[180px]">
    <SelectValue placeholder="Select option" />
  </SelectTrigger>
  <SelectContent>
    <SelectItem value="option1">Option 1</SelectItem>
    <SelectItem value="option2">Option 2</SelectItem>
    <SelectItem value="option3">Option 3</SelectItem>
  </SelectContent>
</Select>

// With groups
<Select value={provider} onValueChange={setProvider}>
  <SelectTrigger>
    <SelectValue placeholder="Select provider" />
  </SelectTrigger>
  <SelectContent>
    <SelectGroup>
      <SelectLabel>Anthropic</SelectLabel>
      <SelectItem value="claude-3.5-sonnet">Claude 3.5 Sonnet</SelectItem>
      <SelectItem value="claude-3-opus">Claude 3 Opus</SelectItem>
    </SelectGroup>
    <SelectSeparator />
    <SelectGroup>
      <SelectLabel>OpenAI</SelectLabel>
      <SelectItem value="gpt-4o">GPT-4o</SelectItem>
      <SelectItem value="gpt-4-turbo">GPT-4 Turbo</SelectItem>
    </SelectGroup>
  </SelectContent>
</Select>

// With label
<div className="space-y-2">
  <Label htmlFor="model">LLM Model</Label>
  <Select value={model} onValueChange={setModel}>
    <SelectTrigger id="model">
      <SelectValue placeholder="Select model" />
    </SelectTrigger>
    <SelectContent>
      <SelectItem value="model1">Model 1</SelectItem>
    </SelectContent>
  </Select>
</div>
```

**When to Use:**
- Choosing from a list of options (3+ options)
- LLM provider selection
- Filter dropdowns
- Settings with predefined values

**Not For:**
- 2 options (use radio buttons or toggle)
- Large lists (>50 items, consider search/autocomplete)

---

### Badge

**Purpose:** Small status indicators and labels.

**File:** `frontend/src/components/ui/badge.tsx`

**Variants:**
- `default` - Primary badge (blue background)
- `secondary` - Subtle badge (gray background)
- `destructive` - Error/danger badge (red background)
- `outline` - Bordered badge (transparent)

**Props:**
```typescript
interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "secondary" | "destructive" | "outline"
}
```

**Usage:**
```tsx
import { Badge } from "@/components/ui/badge"

// Status indicators
<Badge>Active</Badge>
<Badge variant="secondary">Pending</Badge>
<Badge variant="destructive">Error</Badge>
<Badge variant="outline">Draft</Badge>

// With icons
<Badge>
  <CheckCircle className="mr-1 h-3 w-3" />
  Completed
</Badge>

// In context
<div className="flex items-center gap-2">
  <h3>Project Name</h3>
  <Badge variant="secondary">In Progress</Badge>
</div>
```

**When to Use:**
- Status indicators (processing, completed, error)
- Tags and categories
- Counts and metrics
- API health status

**Color Mapping:**
- `default` (blue): Active, healthy, primary status
- `secondary` (gray): Pending, inactive, neutral status
- `destructive` (red): Error, failed, critical status
- `outline`: Draft, optional, secondary info

---

### Skeleton

**Purpose:** Loading placeholder that mimics content shape.

**File:** `frontend/src/components/ui/skeleton.tsx`

**Props:**
```typescript
interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  // Inherits className for custom sizing
}
```

**Usage:**
```tsx
import { Skeleton } from "@/components/ui/skeleton"

// Basic skeleton
<Skeleton className="h-4 w-[250px]" />

// Card skeleton
<Card>
  <CardHeader>
    <Skeleton className="h-8 w-3/4" />
    <Skeleton className="h-4 w-1/2 mt-2" />
  </CardHeader>
  <CardContent>
    <div className="space-y-2">
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-5/6" />
      <Skeleton className="h-4 w-4/6" />
    </div>
  </CardContent>
</Card>

// Grid of skeletons
<div className="grid grid-cols-3 gap-4">
  {Array.from({ length: 6 }).map((_, i) => (
    <Skeleton key={i} className="h-32 w-full" />
  ))}
</div>

// Circle skeleton (avatar)
<Skeleton className="h-12 w-12 rounded-full" />
```

**When to Use:**
- Initial page load
- Lazy-loaded content
- API data fetching
- Pagination loading

**Best Practices:**
- Match the shape of actual content
- Use multiple skeletons for complex layouts
- Combine with suspense boundaries

---

### Alert

**Purpose:** Prominent messages for user feedback.

**File:** `frontend/src/components/ui/alert.tsx`

**Components:**
- `Alert` - Main container
- `AlertTitle` - Bold title (optional)
- `AlertDescription` - Message content

**Variants:**
- `default` - Informational (blue)
- `destructive` - Error/warning (red)

**Props:**
```typescript
interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "destructive"
}
```

**Usage:**
```tsx
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { AlertCircle, CheckCircle } from "lucide-react"

// Informational alert
<Alert>
  <AlertTitle>Info</AlertTitle>
  <AlertDescription>
    Your document has been uploaded successfully.
  </AlertDescription>
</Alert>

// Error alert
<Alert variant="destructive">
  <AlertCircle className="h-4 w-4" />
  <AlertTitle>Error</AlertTitle>
  <AlertDescription>
    Failed to process document. Please try again.
  </AlertDescription>
</Alert>

// Success alert (custom styling)
<Alert className="border-green-500 text-green-900 bg-green-50">
  <CheckCircle className="h-4 w-4" />
  <AlertTitle>Success</AlertTitle>
  <AlertDescription>
    Classification completed for all pages.
  </AlertDescription>
</Alert>

// Simple alert (no title)
<Alert>
  <AlertDescription>
    This is a simple informational message.
  </AlertDescription>
</Alert>
```

**When to Use:**
- Form validation errors
- Operation success/failure messages
- System notifications
- Contextual information

**Not For:**
- Toasts (transient notifications)
- Persistent page-level errors (use error boundary)

---

### Progress

**Purpose:** Visual indicator for progress/completion.

**File:** `frontend/src/components/ui/progress.tsx`

**Props:**
```typescript
interface ProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  value?: number // 0-100
}
```

**Usage:**
```tsx
import { Progress } from "@/components/ui/progress"

// Basic progress
<Progress value={33} />
<Progress value={66} />
<Progress value={100} />

// With label
<div className="space-y-2">
  <div className="flex justify-between text-sm">
    <span>Upload Progress</span>
    <span>{progress}%</span>
  </div>
  <Progress value={progress} />
</div>

// Indeterminate (no value)
<Progress />

// In context (file upload)
<div className="space-y-2">
  <p className="text-sm font-medium">Uploading document.pdf</p>
  <Progress value={uploadProgress} />
  <p className="text-xs text-muted-foreground">
    {uploadProgress}% complete
  </p>
</div>
```

**When to Use:**
- File uploads
- Multi-step forms
- Long-running operations
- Loading indicators with known duration

**Not For:**
- Unknown duration (use Spinner or Skeleton)
- Binary states (use Badge or Alert)

---

### Dialog

**Purpose:** Modal overlay for focused interactions.

**File:** `frontend/src/components/ui/dialog.tsx`

**Components:**
- `Dialog` - Root component (manages open state)
- `DialogTrigger` - Button that opens dialog
- `DialogContent` - Modal container
- `DialogHeader` - Header section
- `DialogTitle` - Modal title
- `DialogDescription` - Modal description
- `DialogFooter` - Footer section (for actions)
- `DialogClose` - Close button

**Props:**
```typescript
Dialog: { open, onOpenChange, defaultOpen }
DialogContent: { className }
// Other components extend their respective HTML elements
```

**Usage:**
```tsx
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"

// Basic dialog
<Dialog>
  <DialogTrigger asChild>
    <Button>Open Dialog</Button>
  </DialogTrigger>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Dialog Title</DialogTitle>
      <DialogDescription>
        This is the dialog description text.
      </DialogDescription>
    </DialogHeader>
    <div className="py-4">
      Dialog content goes here
    </div>
    <DialogFooter>
      <Button variant="outline">Cancel</Button>
      <Button>Confirm</Button>
    </DialogFooter>
  </DialogContent>
</Dialog>

// Controlled dialog
const [open, setOpen] = useState(false)

<Dialog open={open} onOpenChange={setOpen}>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Confirm Delete</DialogTitle>
      <DialogDescription>
        Are you sure you want to delete this document?
      </DialogDescription>
    </DialogHeader>
    <DialogFooter>
      <Button variant="outline" onClick={() => setOpen(false)}>
        Cancel
      </Button>
      <Button variant="destructive" onClick={handleDelete}>
        Delete
      </Button>
    </DialogFooter>
  </DialogContent>
</Dialog>

// Form in dialog
<Dialog>
  <DialogTrigger asChild>
    <Button>Create Project</Button>
  </DialogTrigger>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Create New Project</DialogTitle>
      <DialogDescription>
        Enter project details below.
      </DialogDescription>
    </DialogHeader>
    <form onSubmit={handleSubmit}>
      <div className="space-y-4 py-4">
        <div className="space-y-2">
          <Label htmlFor="name">Name</Label>
          <Input id="name" placeholder="Project name" />
        </div>
        <div className="space-y-2">
          <Label htmlFor="description">Description</Label>
          <Input id="description" placeholder="Description" />
        </div>
      </div>
      <DialogFooter>
        <Button type="submit">Create</Button>
      </DialogFooter>
    </form>
  </DialogContent>
</Dialog>
```

**When to Use:**
- Confirmations (delete, discard changes)
- Forms (create, edit)
- Additional information
- Multi-step workflows

**Not For:**
- Complex wizards (use separate page)
- Non-critical information (use Alert)
- Navigation (use routing)

---

## Utility Functions

### cn() - Class Name Utility

**File:** `frontend/src/lib/utils.ts`

**Purpose:** Merge Tailwind classes intelligently, handling conflicts.

```typescript
import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

**Usage:**
```tsx
import { cn } from "@/lib/utils"

// Basic usage
<div className={cn("base-class", "additional-class")} />

// Conditional classes
<div className={cn(
  "base-class",
  isActive && "active-class",
  isDisabled && "disabled-class"
)} />

// Override classes (later classes override earlier ones)
<Button className={cn("bg-primary", error && "bg-destructive")} />

// Array of classes
const classes = ["class1", "class2"]
<div className={cn(classes)} />

// In components
const buttonVariants = cva("base-classes", {
  variants: {
    variant: {
      default: "variant-classes",
      destructive: "destructive-classes"
    }
  }
})

<button className={cn(buttonVariants({ variant }), className)} />
```

---

## Common Patterns

### Form with Validation

```tsx
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Alert, AlertDescription } from "@/components/ui/alert"

function ProjectForm() {
  const [error, setError] = useState<string | null>(null)
  const [name, setName] = useState("")

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    
    if (!name.trim()) {
      setError("Project name is required")
      return
    }
    
    // Submit logic...
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      
      <div className="space-y-2">
        <Label htmlFor="name">Project Name</Label>
        <Input
          id="name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className={cn(error && "border-destructive")}
        />
      </div>
      
      <Button type="submit">Create Project</Button>
    </form>
  )
}
```

### Loading States

```tsx
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"

function DataCard({ data, isLoading }: { data?: Data, isLoading: boolean }) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-20 w-full" />
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{data.title}</CardTitle>
      </CardHeader>
      <CardContent>
        {data.content}
      </CardContent>
    </Card>
  )
}
```

### Status Badges

```tsx
import { Badge } from "@/components/ui/badge"

function getStatusBadge(status: string) {
  const statusConfig = {
    completed: { variant: "default" as const, label: "Completed" },
    processing: { variant: "secondary" as const, label: "Processing" },
    error: { variant: "destructive" as const, label: "Error" },
    pending: { variant: "outline" as const, label: "Pending" }
  }

  const config = statusConfig[status] || statusConfig.pending

  return <Badge variant={config.variant}>{config.label}</Badge>
}

// Usage
<div className="flex items-center gap-2">
  <h3>Document Name</h3>
  {getStatusBadge(document.status)}
</div>
```

### Confirmation Dialog

```tsx
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"

function DeleteConfirmDialog({ 
  open, 
  onOpenChange, 
  onConfirm,
  itemName 
}: DeleteConfirmDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Confirm Deletion</DialogTitle>
          <DialogDescription>
            Are you sure you want to delete "{itemName}"? This action cannot be undone.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button 
            variant="destructive" 
            onClick={() => {
              onConfirm()
              onOpenChange(false)
            }}
          >
            Delete
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
```

---

## Accessibility Guidelines

### Keyboard Navigation

All components support keyboard navigation:

- **Button:** Space/Enter to activate
- **Select:** Arrow keys to navigate, Enter to select
- **Dialog:** Escape to close, Tab to focus trap
- **Form fields:** Tab to navigate, Enter to submit

### Screen Readers

- Use `Label` with `htmlFor` for all form fields
- Dialog includes proper ARIA roles
- Select announces options
- Alert uses `role="alert"`

### Focus Management

- All interactive elements have visible focus states
- Dialog traps focus while open
- Focus returns to trigger after dialog closes

---

## Design Tokens Reference

### Colors (HSL)

```css
--background: 0 0% 100%;
--foreground: 222.2 84% 4.9%;
--primary: 221.2 83.2% 53.3%;
--primary-foreground: 210 40% 98%;
--secondary: 210 40% 96.1%;
--secondary-foreground: 222.2 47.4% 11.2%;
--destructive: 0 84.2% 60.2%;
--destructive-foreground: 210 40% 98%;
--muted: 210 40% 96.1%;
--muted-foreground: 215.4 16.3% 46.9%;
--accent: 210 40% 96.1%;
--accent-foreground: 222.2 47.4% 11.2%;
--border: 214.3 31.8% 91.4%;
--input: 214.3 31.8% 91.4%;
--ring: 221.2 83.2% 53.3%;
```

### Border Radius

```javascript
borderRadius: {
  lg: "var(--radius)",      // 0.5rem
  md: "calc(var(--radius) - 2px)",  // 0.375rem
  sm: "calc(var(--radius) - 4px)",  // 0.25rem
}
```

### Typography

```javascript
fontFamily: {
  sans: ['Inter', 'system-ui', 'sans-serif']
}
```

---

## Adding New Components

To add a new shadcn/ui component:

1. **Copy from shadcn/ui documentation:**
   ```bash
   # If using shadcn CLI (optional)
   npx shadcn-ui@latest add [component-name]
   ```

2. **Or manually create:**
   - Create file in `frontend/src/components/ui/`
   - Follow existing patterns (use `cn()`, variants with `cva`)
   - Import Radix UI primitive if needed
   - Add TypeScript types

3. **Test accessibility:**
   - Keyboard navigation works
   - Screen reader announces correctly
   - Focus states visible

4. **Document:**
   - Add to this file
   - Update DESIGN-SYSTEM.md if needed

---

## Migration Notes

### From Custom Components

When replacing custom components:

1. **Find all usages:**
   ```bash
   grep -r "CustomButton" frontend/src/
   ```

2. **Replace imports:**
   ```tsx
   // Before
   import { CustomButton } from "./CustomButton"
   
   // After
   import { Button } from "@/components/ui/button"
   ```

3. **Update props:**
   - Match variant names
   - Adjust size props
   - Update class names to use design tokens

4. **Test functionality:**
   - Click handlers work
   - Form submissions work
   - Keyboard navigation works

---

## Troubleshooting

### Component Not Found

```
Error: Cannot find module '@/components/ui/button'
```

**Solution:** Ensure path alias is configured in `tsconfig.json` and `vite.config.ts`:

```json
// tsconfig.json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

### Styles Not Applied

**Solution:** Ensure `index.css` includes CSS variables and Tailwind is configured.

### TypeScript Errors

**Solution:** 
- Check component props match interface
- Import types correctly
- Use `React.ComponentPropsWithoutRef` for extending HTML elements

---

## Resources

- **Design System:** `docs/design/DESIGN-SYSTEM.md`
- **Migration Guide:** `docs/frontend/SHADCN_UI_MIGRATION.md`
- **shadcn/ui Docs:** https://ui.shadcn.com
- **Radix UI Docs:** https://www.radix-ui.com
- **Lucide Icons:** https://lucide.dev

---

**Last Updated:** January 20, 2026  
**Maintained By:** Development Team  
**Questions?** See DESIGN-SYSTEM.md or ask in team chat
