 # Page Load Black Screen (Takeoff Viewer)

> **Historical Context (January 2026):** This document describes an issue in the legacy `TakeoffViewer` route (`/documents/:id/pages/:id`), which is now deprecated. The fix (geometry validation in `MeasurementShape.tsx`) is still active and also protects the new `TakeoffWorkspace` canvas.

 ## Summary
 Some pages in the Takeoff Viewer can render as a black screen after drawing and saving measurements. The page image loads, but Konva throws a draw error due to invalid measurement geometry.
 
 ## Symptoms
 - Page loads with a black canvas area; UI chrome renders.
 - Page 7 loads normally, Page 8 fails after drawing shapes.
 - DevTools console shows:
   - `InvalidStateError: Failed to execute 'drawImage' ... canvas element with width or height of 0`
   - React-Konva `StageWrap` error boundary warnings.
 
 ## Root Cause
 At least one saved measurement has invalid geometry (zero-length line, empty/degenerate polyline/polygon, or invalid dimensions). Konva attempts to cache/draw that shape and creates an internal 0x0 canvas, which throws and crashes rendering.
 
 ## Diagnosis Steps
 1. Open the problematic page in Takeoff Viewer.
 2. Inspect DevTools console for `drawImage` InvalidStateError.
 3. Check debug logs for `invalid measurement geometry` entries (logged once per measurement id).
 
 ## Fix
 1. **Frontend guard**: Skip rendering invalid measurement geometry in `MeasurementShape`.
 2. **Image safety**: Only render Konva image when the plan image has valid dimensions.
 3. **Canvas safety**: Prevent zoom/fit calculations when image dimensions are zero.
 
 ## Verification
 - Reload the affected page.
 - The canvas renders and UI remains responsive.
 - Debug log includes invalid measurement entries (if any).
 - No `drawImage` InvalidStateError in DevTools.
 
 ## Related Files
 - `frontend/src/components/viewer/MeasurementShape.tsx`
 - `frontend/src/pages/TakeoffViewer.tsx`
 - `frontend/src/hooks/usePageImage.ts`
 - `frontend/src/hooks/useCanvasControls.ts`
