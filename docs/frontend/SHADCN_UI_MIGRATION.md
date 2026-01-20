# Frontend Migration to shadcn/ui Design System

**Date:** January 20, 2026  
**Status:** ✅ Complete  
**Phase:** Phase 2B Frontend Update  
**Completed:** January 20, 2026

---

## Overview

Migrating the entire frontend from custom Tailwind components to shadcn/ui to ensure consistency with the design system, improve accessibility, and streamline development.

## Initial State

- ❌ No shadcn/ui components installed
- ❌ Custom Tailwind components without design tokens
- ❌ No `lib/utils.ts` with `cn()` helper
- ❌ Inconsistent component patterns
- ❌ Missing Lucide React icons
- ❌ No Radix UI primitives

## Completed State

- ✅ shadcn/ui fully configured
- ✅ All components use design system tokens (HSL variables)
- ✅ Consistent `cn()` usage for conditional classes
- ✅ Lucide React icons throughout (replaced all custom SVGs)
- ✅ Accessible Radix UI primitives
- ✅ Components follow design system patterns
- ✅ Path aliases configured (`@/` for `src/`)
- ✅ Dashboard refactored into focused components (SOLID principles)

---

## Implementation Plan

### Step 1: Install Dependencies

```bash
cd frontend
npm install class-variance-authority clsx tailwind-merge lucide-react
npm install @radix-ui/react-dialog @radix-ui/react-select @radix-ui/react-label @radix-ui/react-slot
```

### Step 2: Configure Tailwind

Update `tailwind.config.js` with shadcn/ui design tokens.

### Step 3: Create Utils

Create `src/lib/utils.ts` with `cn()` helper function.

### Step 4: Install shadcn/ui Components

Components needed:
- Button
- Card (Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle)
- Dialog (Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger)
- Input
- Label
- Select (Select, SelectContent, SelectItem, SelectTrigger, SelectValue)
- Badge
- Skeleton
- Alert (Alert, AlertDescription, AlertTitle)
- Progress

### Step 5: Refactor Components

**Priority Order:**
1. `DocumentUploader.tsx` - Upload component
2. `PageBrowser.tsx` - Page grid with filters
3. `LLMProviderSelector.tsx` - Provider selector
4. `Dashboard.tsx` - Main dashboard
5. `ScaleCalibration.tsx` - Already done (Phase 2B)

---

## Dependencies to Add

```json
{
  "dependencies": {
    "@radix-ui/react-dialog": "^1.0.5",
    "@radix-ui/react-label": "^2.0.2",
    "@radix-ui/react-select": "^2.0.0",
    "@radix-ui/react-slot": "^1.0.2",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.0",
    "lucide-react": "^0.312.0",
    "tailwind-merge": "^2.2.0"
  }
}
```

---

## Files to Create

1. `src/lib/utils.ts` - cn() helper
2. `src/components/ui/button.tsx` - Button component
3. `src/components/ui/card.tsx` - Card components
4. `src/components/ui/dialog.tsx` - Dialog components
5. `src/components/ui/input.tsx` - Input component
6. `src/components/ui/label.tsx` - Label component
7. `src/components/ui/select.tsx` - Select components
8. `src/components/ui/badge.tsx` - Badge component
9. `src/components/ui/skeleton.tsx` - Skeleton component
10. `src/components/ui/alert.tsx` - Alert components
11. `src/components/ui/progress.tsx` - Progress component

---

## Files to Update

1. `tailwind.config.js` - Add design tokens
2. `src/components/document/DocumentUploader.tsx` - Use Button, Progress, Badge
3. `src/components/document/PageBrowser.tsx` - Use Select, Label, Badge, Skeleton
4. `src/components/LLMProviderSelector.tsx` - Use Select, Label
5. `src/pages/Dashboard.tsx` - Use Card, Button, Badge, Alert
6. `src/App.tsx` - Update header to use design system
7. `package.json` - Add new dependencies

---

## Design System Compliance

### Color Tokens

Using HSL color system from design system:

```css
--background: 0 0% 100%;
--foreground: 222.2 84% 4.9%;
--card: 0 0% 100%;
--card-foreground: 222.2 84% 4.9%;
--popover: 0 0% 100%;
--popover-foreground: 222.2 84% 4.9%;
--primary: 221.2 83.2% 53.3%;
--primary-foreground: 210 40% 98%;
--secondary: 210 40% 96.1%;
--secondary-foreground: 222.2 47.4% 11.2%;
--muted: 210 40% 96.1%;
--muted-foreground: 215.4 16.3% 46.9%;
--accent: 210 40% 96.1%;
--accent-foreground: 222.2 47.4% 11.2%;
--destructive: 0 84.2% 60.2%;
--destructive-foreground: 210 40% 98%;
--border: 214.3 31.8% 91.4%;
--input: 214.3 31.8% 91.4%;
--ring: 221.2 83.2% 53.3%;
```

### Typography

- Font: Inter (system fallback)
- Scales: xs, sm, base, lg, xl, 2xl, 3xl
- Usage: Consistent with design system guidelines

### Spacing

- Using Tailwind's spacing scale (1-12)
- Consistent padding: p-4 for cards, p-6 for sections
- Gap: gap-2 for buttons, gap-4 for sections

---

## Migration Checklist

### Configuration
- ✅ Install shadcn/ui dependencies
- ✅ Update `tailwind.config.js` (HSL design tokens, borderRadius, fontFamily)
- ✅ Update `index.css` (CSS variables for colors)
- ✅ Create `src/lib/utils.ts` (cn() helper)
- ✅ Update `vite.config.ts` (path alias @/)
- ✅ Update `tsconfig.json` (paths configuration)
- ✅ Create `src/components/ui/` directory

### UI Components
- ✅ Button (with variants: default, destructive, outline, secondary, ghost, link)
- ✅ Card (Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent)
- ✅ Dialog (Dialog, DialogTrigger, DialogContent, DialogHeader, DialogFooter, DialogTitle, DialogDescription)
- ✅ Input
- ✅ Label
- ✅ Select (Select, SelectGroup, SelectValue, SelectTrigger, SelectContent, SelectLabel, SelectItem, SelectSeparator)
- ✅ Badge (with variants: default, secondary, destructive, outline)
- ✅ Skeleton
- ✅ Alert (Alert, AlertTitle, AlertDescription)
- ✅ Progress

### Component Refactoring
- ✅ DocumentUploader (Button, Badge, Progress, Lucide icons)
- ✅ PageBrowser (Select, Label, Badge, Skeleton)
- ✅ LLMProviderSelector (Select, Label)
- ✅ Dashboard (Complete refactor - see DASHBOARD_REFACTOR.md)
- ✅ App.tsx header (design system colors)

### Testing
- ✅ Upload document flow
- ✅ Page browsing and filtering
- ✅ LLM provider selection
- ✅ Classification workflow
- ✅ All interactive elements keyboard accessible
- ✅ Focus states visible
- ✅ Loading states work correctly
- ✅ API health check working

---

## Breaking Changes

None - this is a visual/structural update that maintains all existing functionality.

---

## Benefits

✅ **Accessibility:** Radix UI primitives include ARIA attributes  
✅ **Consistency:** All components follow same design patterns  
✅ **Maintainability:** Standard component library  
✅ **Developer Experience:** Auto-complete with proper types  
✅ **Future-proof:** Easy to add new components  
✅ **Performance:** Tree-shakeable, optimized bundle

---

## Next Steps

After migration:
1. Test all user flows in Docker
2. Update screenshot in documentation
3. Add Storybook (optional, future enhancement)
4. Document custom component patterns

---

## Implementation Summary

### What Was Done

1. **Dependencies Added:**
   - `class-variance-authority`, `clsx`, `tailwind-merge` (utility functions)
   - `lucide-react` (icon library)
   - `@radix-ui/react-*` packages (accessible primitives)
   - `@radix-ui/react-progress` (progress bars)

2. **Configuration Updates:**
   - `tailwind.config.js`: Added HSL color tokens, custom border radius, Inter font
   - `index.css`: Added CSS variables for light/dark mode support
   - `vite.config.ts`: Added `@/` path alias
   - `tsconfig.json`: Added paths configuration for TypeScript

3. **New Files Created:**
   - `src/lib/utils.ts` - cn() helper function
   - `src/components/ui/button.tsx` - Button component with variants
   - `src/components/ui/card.tsx` - Card and sub-components
   - `src/components/ui/input.tsx` - Input component
   - `src/components/ui/label.tsx` - Label component
   - `src/components/ui/select.tsx` - Select and sub-components
   - `src/components/ui/badge.tsx` - Badge component with variants
   - `src/components/ui/skeleton.tsx` - Loading skeleton
   - `src/components/ui/alert.tsx` - Alert component
   - `src/components/ui/progress.tsx` - Progress bar
   - `src/components/ui/dialog.tsx` - Dialog/modal component
   - `src/components/dashboard/HealthStatusBadge.tsx` - Extracted component
   - `src/components/dashboard/PageInfoCard.tsx` - Extracted component

4. **Refactored Components:**
   - `DocumentUploader.tsx` - Now uses Button, Badge, Progress, Lucide icons
   - `PageBrowser.tsx` - Now uses Select, Label, Badge, Skeleton
   - `LLMProviderSelector.tsx` - Now uses Select, Label
   - `Dashboard.tsx` - Complete refactor (see DASHBOARD_REFACTOR.md)
   - `App.tsx` - Updated to use design system colors

5. **Backend Update:**
   - Added `opencv-python-headless==4.9.0.80` to `requirements.txt` (Phase 2B scale detection dependency)
   - Updated `docker/Dockerfile.api` to use base requirements (not full ML stack)

### Technical Improvements

- **Better Type Safety:** All components have explicit TypeScript types
- **Accessibility:** Radix UI primitives include proper ARIA attributes
- **Consistency:** All components use same design tokens and patterns
- **Maintainability:** Smaller, focused components following SOLID principles
- **Performance:** Tree-shakeable imports, no unnecessary dependencies

### Breaking Changes

None - all existing functionality maintained.

---

**Status:** ✅ Complete  
**Actual Time:** ~3 hours  
**Risk Level:** Low (purely UI, no logic changes)  
**Outcome:** Successful - all tests passing, dashboard loading correctly
