# Phase 3A+ Manual Drawing Tools - Implementation Prompt

> **RECOMMENDED MODEL**: Claude 3.5 Sonnet (2024-10-22 or later)  
> **ALTERNATIVE**: GPT-4 Turbo or GPT-4o  
> **CONTEXT WINDOW**: Use at least 200k tokens  

---

# Implementation Task: Phase 3A+ Manual Drawing Tools

## ⚠️ CRITICAL FIRST STEP - READ THE SPECIFICATION

**BEFORE YOU DO ANYTHING ELSE:**

1. **Open and read `@plans/06B-MANUAL-DRAWING-TOOLS.md` in its entirety** (1,099 lines)
2. This specification file contains:
   - Complete implementation code for all 4 components
   - Full 490-line `TakeoffViewer.tsx` component (lines 505-995)
   - Drawing tool behaviors and interaction patterns
   - Integration examples and verification checklist
3. **MANDATORY**: After reading the spec, create your task list with **Task #0** being:
   ```
   ✅ Task #0: Read and understood complete specification file (@plans/06B-MANUAL-DRAWING-TOOLS.md)
   ```
4. Reference the spec file for ALL implementation details - **DO NOT improvise or guess**

**The spec file is your source of truth. This prompt is just a roadmap.**

---

## Context

Phase 3A implemented the measurement engine backend (geometry calculations, database models, API endpoints), but lacks the **frontend drawing interface** for manual measurement creation. 

You will implement 4 components + 1 page to enable interactive drawing on PDF plan pages using Konva.js canvas.

## Prerequisites (Already Complete)

✅ **Backend measurement engine working**: API endpoints, database models, geometry utilities  
✅ **Scale calibration (Phase 2B) working**: `ScaleCalibration` component exists  
✅ **Measurement rendering working**: `MeasurementLayer` component exists  

## Tech Stack

- React 18 + TypeScript (strict mode)
- React Router for navigation
- TanStack Query (React Query) for data fetching
- **Konva.js** (react-konva) for canvas drawing
- shadcn/ui components (already installed)
- Tailwind CSS for styling
- Lucide React for icons

## Components to Build

Refer to **`@plans/06B-MANUAL-DRAWING-TOOLS.md`** for complete implementation code:

### 1. DrawingToolbar Component
**Location**: `frontend/src/components/viewer/DrawingToolbar.tsx`  
**Spec Reference**: Lines 80-180  
**Features**:
- 7 tool buttons (Select, Line, Polyline, Polygon, Rectangle, Circle, Point)
- Action buttons (Undo, Redo, Delete)
- Keyboard shortcuts (V, L, P, G, R, C, M)
- Visual instructions for active tool
- Disabled state when scale not calibrated

### 2. Drawing State Hook
**Location**: `frontend/src/hooks/useDrawingState.ts`  
**Spec Reference**: Lines 182-350  
**Features**:
- Active tool management
- Drawing lifecycle (start, add point, update preview, finish, cancel)
- Point tracking and preview shape generation
- Undo/redo history management
- Geometry data generation for each tool type

### 3. Drawing Preview Layer
**Location**: `frontend/src/components/viewer/DrawingPreviewLayer.tsx`  
**Spec Reference**: Lines 352-503  
**Features**:
- Real-time preview shapes (dashed lines)
- Control points rendered as circles
- Updates on mouse move
- Different rendering for each geometry type

### 4. Takeoff Viewer Page
**Location**: `frontend/src/pages/TakeoffViewer.tsx`  
**Spec Reference**: Lines 505-995 (**490 lines - DO NOT abbreviate this file**)  
**Features**:
- 3-panel layout (conditions sidebar, canvas, measurements sidebar)
- Konva.js Stage/Layer setup with zoom and pan
- Mouse event handlers (mouseDown, mouseMove, mouseUp, doubleClick)
- Integration with all components
- Scale calibration integration
- Keyboard event listeners

### 5. Route Setup
**Location**: `frontend/src/App.tsx`  
**Spec Reference**: Lines 997-1003  
**Add Route**: `/documents/:documentId/pages/:pageId`

---

## Implementation Sequence

Follow this order exactly:

**Task #0**: ✅ Read `@plans/06B-MANUAL-DRAWING-TOOLS.md` completely (MANDATORY)

**Task #1**: Create `DrawingToolbar.tsx` (copy from spec lines 80-180)

**Task #2**: Create `useDrawingState.ts` (copy from spec lines 182-350)

**Task #3**: Create `DrawingPreviewLayer.tsx` (copy from spec lines 352-503)

**Task #4**: Create `TakeoffViewer.tsx` (copy from spec lines 505-995)
   - ⚠️ **This is 490 lines - copy it completely, do NOT abbreviate**

**Task #5**: Add route to `App.tsx` (see spec lines 997-1003)

**Task #6**: Test with Cursor browser tools (see detailed workflow in spec lines 1007-1099)

---

## Testing with Cursor Browser Tools

**CRITICAL**: Use Cursor's built-in browser tools for testing. Do NOT create separate test files.

### Quick Testing Steps

1. **Start services**:
   ```bash
   cd docker && docker compose up -d
   cd ../frontend && npm run dev
   ```

2. **Test with browser tools**:
   - `browser_navigate("http://localhost:5173")`
   - `browser_snapshot()` to inspect UI
   - Upload test PDF from `tests/` folder
   - Navigate to page viewer
   - `browser_click()` to select tools and draw on canvas
   - `browser_press_key()` to test keyboard shortcuts

3. **Verify checklist** (see spec lines 1064-1078 for complete list):
   - [ ] All 6 drawing tools work correctly
   - [ ] Measurements save with accurate quantities
   - [ ] Keyboard shortcuts functional (V, L, P, G, R, C, M, Delete, Ctrl+Z, Ctrl+Y)
   - [ ] Preview shapes appear while drawing
   - [ ] Condition totals update after measurements created
   - [ ] Scale warning appears when not calibrated

**Full testing workflow**: See spec file lines 1007-1099

---

## Drawing Tool Behaviors

Reference the spec for detailed interaction patterns:

- **Line**: Click start → move (preview) → click end → auto-finish
- **Polyline**: Click points → preview → double-click to finish
- **Polygon**: Click points → preview → double-click or close to finish
- **Rectangle**: Click corner → drag (preview) → release to finish
- **Circle**: Click center → drag (preview) → release to finish
- **Point**: Click location → auto-finish immediately

---

## Success Criteria

- [ ] **Task #0 completed**: Spec file read and understood
- [ ] All 4 components created **exactly from spec** (NO improvisation)
- [ ] `TakeoffViewer.tsx` is complete 490 lines (NOT abbreviated)
- [ ] All 6 drawing tools work (Line, Polyline, Polygon, Rectangle, Circle, Point)
- [ ] Measurements save to backend with correct quantities
- [ ] All keyboard shortcuts work
- [ ] Preview shapes display correctly while drawing
- [ ] Condition totals update after creating measurements
- [ ] Scale warning appears when not calibrated
- [ ] No TypeScript compilation errors

---

## Critical Warnings

⚠️ **DO NOT improvise code** - Copy EXACTLY from the spec file  
⚠️ **DO NOT abbreviate TakeoffViewer** - It's 490 lines for a reason  
⚠️ **DO NOT create test files** - Use Cursor's browser tools  
⚠️ **DO reference the spec constantly** - When in doubt, check the spec  
⚠️ **DO include Task #0 in your task list** - Shows you read the spec  

---

## Common Pitfalls (see spec for details)

1. **Coordinate transformation**: Account for zoom and pan in Konva.js
2. **React Query invalidation**: Invalidate both measurements AND conditions
3. **Preview state cleanup**: Clear preview when switching tools
4. **Event listener cleanup**: Unmount handlers to avoid memory leaks
5. **TypeScript strict mode**: All props need explicit types

---

## Questions to Ask Before Starting

If anything is unclear about the existing codebase:
- API client configuration location
- Current routing setup
- Environment variables for API base URL
- Existing type definitions

---

## Expected Completion Time

- Component creation: 30-45 minutes
- Integration & testing: 15-30 minutes
- Bug fixes & refinement: 15-30 minutes
- **Total: 1-2 hours**

---

**Ready to start?** Read the spec file first, create your task list with Task #0, then implement each component sequentially. Reference the spec constantly - it has ALL the code you need.
