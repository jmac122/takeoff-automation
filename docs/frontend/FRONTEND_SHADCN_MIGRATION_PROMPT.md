# Frontend Migration to shadcn/ui Design System - Implementation Prompt

**Project:** ForgeX Takeoffs - AI Construction Takeoff Platform  
**Task:** Migrate entire React frontend to shadcn/ui design system  
**Environment:** Docker-based development (Docker Desktop running)  
**Status:** Phase 2B Complete, Ready for Frontend Update

---

## 🎯 Objective

Update the entire React/TypeScript frontend to use shadcn/ui components following our design system specification in `@docs/design/DESIGN-SYSTEM.md`. The frontend currently uses raw Tailwind CSS without shadcn/ui, and needs to be modernized for consistency, accessibility, and maintainability.

---

## 📋 Context

### Current Frontend Stack
- React 18 + TypeScript
- Vite build tool
- TailwindCSS 3.4
- React Query (TanStack)
- Axios for API calls
- React Router DOM
- **NO shadcn/ui installed yet**

### What We Need to Achieve
1. Install shadcn/ui and all required dependencies
2. Configure Tailwind with design system tokens
3. Create all necessary UI components following the design system
4. Refactor 5 existing components to use shadcn/ui
5. Ensure all changes work in Docker environment

---

## 📚 Key Reference Documents

**MUST READ FIRST:**
1. `@docs/design/DESIGN-SYSTEM.md` - Complete design system specification with:
   - Color system (HSL tokens)
   - Typography scales
   - Component patterns
   - Accessibility requirements
   - File organization

2. `@docs/frontend/SHADCN_UI_MIGRATION.md` - Migration plan I created

---

## 🔍 Current Frontend Structure

```
frontend/src/
├── components/
│   ├── document/
│   │   ├── DocumentUploader.tsx    ⚠️ Needs refactoring
│   │   └── PageBrowser.tsx         ⚠️ Needs refactoring
│   ├── viewer/
│   │   └── ScaleCalibration.tsx    ✅ Already uses shadcn/ui (Phase 2B)
│   └── LLMProviderSelector.tsx     ⚠️ Needs refactoring
├── pages/
│   └── Dashboard.tsx                ⚠️ Needs refactoring (1100+ lines)
├── App.tsx                          ⚠️ Needs minor updates
└── (no lib/ or components/ui/ yet) ❌ Must create
```

---

## ✅ Implementation Checklist

### Phase 1: Setup & Configuration

1. **Install Dependencies**
   ```bash
   cd frontend
   npm install class-variance-authority clsx tailwind-merge lucide-react
   npm install @radix-ui/react-dialog @radix-ui/react-label @radix-ui/react-select @radix-ui/react-slot
   npm install @radix-ui/react-alert-dialog @radix-ui/react-progress
   ```

2. **Update `tailwind.config.js`**
   - Add design system color tokens (HSL format from design doc)
   - Configure borderRadius, fontFamily
   - Add CSS variable support
   - Reference: Section "Color System" in DESIGN-SYSTEM.md

3. **Create `src/lib/utils.ts`**
   ```typescript
   import { type ClassValue, clsx } from "clsx"
   import { twMerge } from "tailwind-merge"
   
   export function cn(...inputs: ClassValue[]) {
     return twMerge(clsx(inputs))
   }
   ```

4. **Create `src/components/ui/` directory structure**

---

### Phase 2: Create shadcn/ui Components

Create these components following exact patterns from DESIGN-SYSTEM.md:

**Priority 1 (Required for all components):**
- [ ] `components/ui/button.tsx` - All variants (default, secondary, outline, ghost, destructive, link)
- [ ] `components/ui/card.tsx` - Card + CardHeader + CardTitle + CardDescription + CardContent + CardFooter
- [ ] `components/ui/input.tsx` - Text input with proper focus states
- [ ] `components/ui/label.tsx` - Form label component

**Priority 2 (Needed for Dashboard & PageBrowser):**
- [ ] `components/ui/select.tsx` - Select + SelectTrigger + SelectValue + SelectContent + SelectItem
- [ ] `components/ui/badge.tsx` - Badge component with variants
- [ ] `components/ui/skeleton.tsx` - Loading skeleton
- [ ] `components/ui/alert.tsx` - Alert + AlertTitle + AlertDescription
- [ ] `components/ui/progress.tsx` - Progress bar for uploads

**Priority 3 (Dialog already created in ScaleCalibration, can reuse):**
- [ ] `components/ui/dialog.tsx` - Dialog + DialogTrigger + DialogContent + DialogHeader + DialogTitle + DialogDescription + DialogFooter

**Important:** Use the EXACT component patterns shown in DESIGN-SYSTEM.md sections. Don't create from scratch - copy the patterns provided.

---

### Phase 3: Refactor Components (IN ORDER)

#### 1. DocumentUploader.tsx (Priority: HIGH)
**Current issues:**
- Custom SVG icons (should use Lucide React)
- Raw Tailwind for status badges (should use Badge component)
- Custom progress bar (should use Progress component)
- Inline button styling (should use Button component)

**Changes needed:**
- Import Lucide icons: `Upload`, `Check`, `X`, `Loader2`
- Replace all `<button>` with `<Button variant="...">`
- Replace custom badges with `<Badge variant="...">`
- Replace progress bar `<div>` with `<Progress value={...}>`
- Use design system color tokens (bg-muted, text-muted-foreground)

#### 2. PageBrowser.tsx (Priority: HIGH)
**Current issues:**
- Raw `<select>` elements (should use Select component)
- Raw `<label>` elements (should use Label component)
- Custom skeleton loading (should use Skeleton component)
- Inconsistent badge colors

**Changes needed:**
- Replace all `<select>` with `<Select>` + `<SelectTrigger>` + `<SelectContent>` + `<SelectItem>`
- Replace `<label>` with `<Label>`
- Replace loading skeleton `<div>` with `<Skeleton>`
- Use `<Badge variant="..."` for all status indicators
- Import Lucide icons: `Filter`

#### 3. LLMProviderSelector.tsx (Priority: MEDIUM)
**Current issues:**
- Raw `<select>` and `<label>`
- Tooltip functionality could use Dialog/Popover

**Changes needed:**
- Replace with Select components
- Use Label component
- Consider Dialog or Popover for provider details

#### 4. Dashboard.tsx (Priority: HIGH - 1100+ lines!)
**Current issues:**
- MASSIVE file with inline styling everywhere
- No component extraction
- Raw HTML elements
- Custom cards, alerts, badges

**Changes needed:**
- Extract collapsible sections into separate components
- Replace all custom cards with `<Card>` components
- Replace inline alerts with `<Alert>` component
- Use `<Button>` for all buttons
- Use `<Badge>` for all status indicators
- Import Lucide icons: `Settings`, `FolderOpen`, `ChevronDown`, `RefreshCw`, etc.

#### 5. App.tsx (Priority: LOW)
**Changes needed:**
- Update header to use design system tokens
- Minor styling adjustments for consistency

---

### Phase 4: Icon Migration

**Replace ALL custom SVG icons with Lucide React:**

Common replacements:
- Upload icon → `<Upload className="h-4 w-4" />`
- Check/Success → `<Check className="h-4 w-4" />`
- Error/X → `<X className="h-4 w-4" />`
- Loading spinner → `<Loader2 className="h-4 w-4 animate-spin" />`
- Chevron down → `<ChevronDown className="h-4 w-4" />`
- Settings gear → `<Settings className="h-4 w-4" />`
- Folder → `<FolderOpen className="h-4 w-4" />`
- File → `<FileText className="h-4 w-4" />`
- Refresh → `<RefreshCw className="h-4 w-4" />`

Reference: DESIGN-SYSTEM.md "Icons" section for full list

---

## 🐳 Docker Workflow

**IMPORTANT:** All development happens in Docker. Never install packages locally.

### Start Development Environment
```bash
cd D:\Repos\takeoff-automation\docker
docker compose up -d
```

### Install npm Packages in Docker
```bash
docker compose exec frontend npm install <package-name>
```

### Rebuild Frontend Container After package.json Changes
```bash
docker compose build frontend
docker compose up -d frontend
```

### View Frontend Logs
```bash
docker logs forgex-frontend -f
```

### Access Frontend
- URL: http://localhost:5173
- Hot reload should work automatically

---

## 🎨 Design System Rules (CRITICAL)

### Color Usage
❌ **NEVER use raw colors:**
```tsx
// BAD
<div className="bg-blue-600 text-white">
```

✅ **ALWAYS use design tokens:**
```tsx
// GOOD
<div className="bg-primary text-primary-foreground">
```

### Component Patterns
❌ **NEVER use raw HTML:**
```tsx
// BAD
<button className="px-4 py-2 bg-blue-600 rounded">Click</button>
```

✅ **ALWAYS use shadcn/ui components:**
```tsx
// GOOD
<Button variant="default">Click</Button>
```

### Class Name Composition
✅ **ALWAYS use cn() helper:**
```tsx
import { cn } from "@/lib/utils"

<div className={cn("base-classes", conditionalClass && "conditional-classes")}>
```

---

## ✅ Verification Checklist

After implementation, verify:

### Functional Testing
- [ ] Upload document flow works
- [ ] Page browser filters work
- [ ] LLM provider selection works
- [ ] Classification workflow works
- [ ] All buttons clickable
- [ ] All forms submittable
- [ ] Loading states display correctly
- [ ] Error states display correctly

### Accessibility Testing
- [ ] All interactive elements keyboard accessible (Tab navigation)
- [ ] Focus states visible (ring utilities)
- [ ] Form labels associated with inputs
- [ ] Buttons have proper aria attributes
- [ ] Loading states announced to screen readers

### Visual Testing
- [ ] Colors use design system tokens
- [ ] Typography consistent (text-sm, text-base, etc.)
- [ ] Spacing consistent (gap-2, p-4, etc.)
- [ ] No raw hex colors in code
- [ ] All Lucide icons properly sized
- [ ] Components match design system examples

### Code Quality
- [ ] No eslint errors
- [ ] No TypeScript errors
- [ ] All imports use `@/` alias (configured in vite/tsconfig)
- [ ] cn() used for all conditional classes
- [ ] No inline style objects

---

## 📦 Expected Package.json After Installation

```json
{
  "dependencies": {
    "@radix-ui/react-alert-dialog": "^1.0.5",
    "@radix-ui/react-dialog": "^1.0.5",
    "@radix-ui/react-label": "^2.0.2",
    "@radix-ui/react-progress": "^1.0.3",
    "@radix-ui/react-select": "^2.0.0",
    "@radix-ui/react-slot": "^1.0.2",
    "@tanstack/react-query": "^5.17.15",
    "axios": "^1.6.7",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.0",
    "konva": "^9.3.1",
    "lucide-react": "^0.312.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-dropzone": "^14.2.3",
    "react-konva": "^18.2.0",
    "react-router-dom": "^6.22.0",
    "tailwind-merge": "^2.2.0",
    "zustand": "^4.5.0"
  }
}
```

---

## 🚨 Common Pitfalls to Avoid

1. **Don't install packages locally** - Use Docker exec
2. **Don't use raw colors** - Use design tokens
3. **Don't create custom components** - Use shadcn/ui
4. **Don't skip accessibility** - Radix UI provides it
5. **Don't guess patterns** - Follow DESIGN-SYSTEM.md exactly
6. **Don't forget cn()** - Required for conditional classes
7. **Don't use custom SVGs** - Use Lucide React icons
8. **Don't rebuild entire components** - Refactor incrementally

---

## 📝 Success Criteria

✅ Frontend builds without errors  
✅ All pages load correctly  
✅ All interactions work as before  
✅ No raw Tailwind colors (only design tokens)  
✅ All components use shadcn/ui  
✅ All icons are Lucide React  
✅ Accessibility improved (keyboard nav, focus states)  
✅ Code is cleaner and more maintainable  

---

## 🎯 Final Deliverables

1. **Updated Files** (7 total):
   - `package.json` - New dependencies
   - `tailwind.config.js` - Design tokens
   - `src/lib/utils.ts` - NEW
   - `src/components/document/DocumentUploader.tsx` - REFACTORED
   - `src/components/document/PageBrowser.tsx` - REFACTORED
   - `src/components/LLMProviderSelector.tsx` - REFACTORED
   - `src/pages/Dashboard.tsx` - REFACTORED

2. **New Components** (9-10 UI components in `src/components/ui/`):
   - button.tsx
   - card.tsx
   - input.tsx
   - label.tsx
   - select.tsx
   - badge.tsx
   - skeleton.tsx
   - alert.tsx
   - progress.tsx
   - (dialog.tsx if not already created)

3. **Documentation**: Update `docs/frontend/FRONTEND_IMPLEMENTATION.md` with shadcn/ui patterns

---

## 🚀 Start Here

1. **Read the design system**: Open `@docs/design/DESIGN-SYSTEM.md` and understand the component patterns
2. **Check current state**: Review the 5 components that need refactoring
3. **Start with Phase 1**: Install dependencies in Docker
4. **Follow the phases**: Complete setup → create UI components → refactor in order
5. **Test thoroughly**: Verify everything works in Docker at http://localhost:5173

---

**Good luck! This is a significant improvement that will make the codebase much more maintainable.** 🎉

---

## 📞 Need Help?

If stuck, refer to:
- `docs/design/DESIGN-SYSTEM.md` - Component patterns
- `frontend/src/components/viewer/ScaleCalibration.tsx` - Already migrated example (Phase 2B)
- shadcn/ui documentation: https://ui.shadcn.com/docs/components
- Lucide React icons: https://lucide.dev/icons

---

**Status**: Ready to implement  
**Estimated Time**: 3-4 hours  
**Difficulty**: Medium (Systematic refactoring, no logic changes)
