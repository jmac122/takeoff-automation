# Phase-Specific Context Files

Use these files to give the AI focused context for each phase. Copy the relevant section into your prompt or rules.

---

## PHASE_A_CONTEXT.md

```markdown
# Phase A: Sheet Manager & Navigation

## Current Task Scope
Building: SheetTree, workspace layout, sheet selection, scale indicators, batch ops, search

## Key Files to Create/Modify
- pages/TakeoffWorkspace.tsx
- stores/workspaceStore.ts (activeSheetId, selectedSheetIds, expandedGroups slices)
- components/workspace/SheetTree.tsx
- components/workspace/SheetTreeNode.tsx
- components/workspace/SheetSearch.tsx
- components/workspace/ThumbnailStrip.tsx
- hooks/useSheetTree.ts
- lib/FocusContext.tsx
- lib/constants.ts

## API Endpoints Used
GET /documents/{id}/pages?include=classification,scale
GET /projects/{id}/sheets
PUT /pages/{id}/display
PUT /pages/{id}/relevance
POST /pages/{id}/scale/copy-from/{sourceId}
POST /pages/{id}/scale/detect

## State Slices Active
```typescript
activeSheetId: string | null;
selectedSheetIds: Set<string>;
expandedGroups: Set<string>;
focusRegion: FocusRegion;
leftPanelWidth: number;
leftPanelCollapsed: boolean;
```

## Keyboard Shortcuts This Phase
↑/↓: Navigate tree
←/→: Collapse/expand
Enter: Load sheet
Space: Toggle expand
PageUp/Down: Prev/next sheet
Ctrl+G: Go to sheet

## Scale Status Indicators
🟢 Green: confidence >= 0.85
🟡 Yellow: confidence 0.50-0.85
🔴 Red: no scale
🔵 Blue: manually calibrated
```

---

## PHASE_B_CONTEXT.md

```markdown
# Phase B: Conditions Panel Overhaul

## Current Task Scope
Building: Quick-create bar, conditions list, properties inspector, visibility toggles, number key shortcuts

## Key Files to Create/Modify
- components/conditions/ConditionPanel.tsx (refactor to 3-section)
- components/conditions/QuickCreateBar.tsx
- components/conditions/ConditionList.tsx
- components/conditions/PropertiesInspector.tsx
- components/conditions/PerSheetBreakdown.tsx
- stores/workspaceStore.ts (activeConditionId, conditionVisibility slices)

## API Endpoints Used
GET /conditions/templates
POST /conditions
PATCH /conditions/{id}
DELETE /conditions/{id}
GET /conditions/{id}/measurements

## State Slices Active
```typescript
activeConditionId: string | null;
conditionVisibility: Map<string, boolean>;
```

## Critical Invariant
Cannot set activeTool !== null unless activeConditionId !== null (except 'M').
When no condition: toast "Select a condition first", pulse panel, block tool activation.

## Keyboard Shortcuts This Phase
1-9: Select condition by position
Ctrl+N: New condition
Ctrl+D: Duplicate
V: Toggle visibility
Ctrl+Shift+V: Toggle all visibility
Delete: Delete (with confirm)
```

---

## PHASE_C_CONTEXT.md

```markdown
# Phase C: Plan Viewer & Drawing Tools

## Current Task Scope
Building: Undo/redo, drawing tools, snap, measurement interaction, status bar, selection

## Key Files to Create/Modify
- lib/UndoManager.ts
- lib/commands/DrawMeasurementCommand.ts
- lib/commands/DeleteMeasurementCommand.ts
- lib/commands/MoveMeasurementCommand.ts
- lib/commands/EditMeasurementCommand.ts
- lib/commands/ChangeConditionCommand.ts
- lib/SnapEngine.ts
- hooks/useUndoRedo.ts
- hooks/useDrawingTool.ts
- hooks/useSnap.ts
- components/viewer/PlanViewer.tsx
- components/viewer/MeasurementLayer.tsx
- components/viewer/MeasurementShape.tsx
- components/viewer/DrawingPreview.tsx
- components/viewer/SelectionRectangle.tsx
- components/workspace/StatusBar.tsx

## API Endpoints Used
POST /conditions/{id}/measurements
PATCH /measurements/{id}
DELETE /measurements/{id}
GET /pages/{id}/measurements

## State Slices Active
```typescript
activeTool: DrawingTool | null;
isDrawing: boolean;
currentPoints: Point[];
selectedMeasurementIds: Set<string>;
editingMeasurementId: string | null;
zoom: number;
panOffset: { x: number; y: number };
cursorPosition: { x: number; y: number } | null;
clipboard: ClipboardEntry | null;
```

## Undo Command Pattern
All commands async. execute/undo/redo return Promise<void>.
Server fail during undo/redo: toast + remove from stack.

## Persistence Rules
- During draw: currentPoints only (no server)
- Draw complete: POST
- Edit/move: PATCH debounced 500ms
- Delete: immediate DELETE

## Z-Order
1. Areas 2. Lines 3. Points 4. Selected 5. Preview 6. AI ghosts

## Keyboard Shortcuts This Phase
L: Line, P: Polyline, A: Area/Polygon, R: Rectangle, C: Count, M: Measure
Escape: Cancel/deselect
Enter/double-click: Finish polyline/polygon
Backspace: Remove last point
Ctrl+Z/Ctrl+Shift+Z: Undo/redo
Delete: Delete selected
Ctrl+C/V: Copy/paste
Ctrl+A: Select all
Shift (hold): Constrain 45° angles
```

---

## PHASE_D_CONTEXT.md

```markdown
# Phase D: AI Assist Layer

## Current Task Scope
Building: AutoTab backend, ghost point UI, batch AI inline, QuickDraw prototype

## Key Files to Create/Modify
- backend/app/services/ai_predict.py
- backend/app/api/routes/ai_predict.py
- components/viewer/GhostPoint.tsx
- components/viewer/DraftMeasurementLayer.tsx
- hooks/useAutoTab.ts

## API Endpoints
POST /ai/predict-next-point
Request: { page_id, current_points[], condition_type, viewport, scale_pixels_per_foot }
Response: { predicted_point: {x,y}, confidence, reasoning }

## State Slices Active
```typescript
autoTabEnabled: boolean;
pendingPrediction: PredictedPoint | null;
```

## AutoTab Flow
1. User places 2+ points on polyline/polygon
2. Fire prediction request (debounce 200ms)
3. Show ghost point at predicted location
4. Tab: accept (add point, trigger next prediction)
5. Escape: dismiss ghost
6. Click elsewhere: override prediction

## Latency Budget
Image crop + encode: <50ms
API round-trip: <100ms
LLM inference: <500ms
Render: <50ms
Total: <800ms

## Visual Treatment
- Ghost point: semi-transparent circle, GHOST_POINT_OPACITY (0.5)
- Dashed line from last point to ghost
- Pulsing indicator while loading
- Draft measurements (batch AI): dashed stroke, ghost fill

## AI Failure Handling
Silent degradation. No ghost point shown. Never block drawing. Never toast on predict fail.
```

---

## PHASE_E_CONTEXT.md

```markdown
# Phase E: Export & Reporting

## Current Task Scope
Building: Export dropdown, options dialog, download handling

## Key Files to Create/Modify
- components/export/ExportDropdown.tsx
- components/export/ExportOptionsDialog.tsx
- hooks/useExport.ts

## API Endpoints
POST /projects/{id}/export/excel
POST /projects/{id}/export/ost
POST /projects/{id}/export/csv
POST /projects/{id}/export/pdf
Returns: { job_id }

GET /exports/{job_id}/status
Returns: { status: 'pending'|'processing'|'complete'|'failed', download_url? }

## Export Flow
1. User selects format from dropdown
2. Options dialog: select sheets, conditions, format prefs
3. POST export → get job_id
4. Poll status every 2000ms (EXPORT_POLL_INTERVAL_MS)
5. On complete: auto-download or show download button
6. On fail: toast with error + "Try Again"

## Options to Support
- Sheets: all / selected
- Conditions: all / selected
- Include summary sheet (Excel)
- Include thumbnails (PDF)
- Group by: condition / page / CSI code
```
