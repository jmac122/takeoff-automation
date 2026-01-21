# Verification Checklist - Recent Changes

## Overview
This document provides a comprehensive checklist to verify all recent changes are working correctly after the Docker rebuild.

---

## Backend API Changes

### ✅ Classification Data in Page Endpoint

**Endpoint:** `GET /api/v1/pages/{page_id}`

**What Changed:**
- Added classification fields to `PageResponse` schema
- Updated endpoint to return all classification data

**Fields to Verify:**
```json
{
  "id": "...",
  "classification": "Structural:Detail",
  "classification_confidence": 0.95,
  "discipline": "Structural",           // ← NEW
  "page_type": "Detail",                // ← NEW
  "concrete_relevance": "high",         // ← NEW
  "concrete_elements": ["foundation", "slab"], // ← NEW
  "description": "AI description...",   // ← NEW
  "llm_provider": "ANTHROPIC",          // ← NEW
  "llm_latency_ms": 5240,               // ← NEW
  "sheet_number": "S3.01",
  "title": "STRUCTURAL NOTES",
  "scale_text": "...",
  "image_url": "...",
  ...
}
```

**Test:**
1. Open any page in TakeoffViewer
2. Open browser DevTools → Network tab
3. Look for `/api/v1/pages/{id}` request
4. Verify response includes all new fields above

---

## Frontend Changes

### ✅ 1. TakeoffViewer Classification Sidebar

**File:** `frontend/src/components/viewer/ClassificationSidebar.tsx`

**What to Test:**
1. Open any page in TakeoffViewer (click "Open Takeoff" on a page card)
2. Look for classification sidebar on the right side
3. Verify it shows:
   - ✅ Classification: "Structural:Detail" (or similar)
   - ✅ Confidence bar with percentage
   - ✅ Discipline with confidence
   - ✅ Page Type with confidence
   - ✅ Concrete Relevance badge (color-coded)
   - ✅ Elements Detected list
   - ✅ Description text
   - ✅ Technical details (Provider, Latency)
   - ✅ "View full history →" link
4. Click the collapse arrow (→) - sidebar should collapse to 40px
5. Click expand arrow (←) - sidebar should expand to 320px
6. Click fullscreen button - sidebar should hide completely

**Expected Behavior:**
- If data shows: ✅ API connection working
- If shows "No classification data available": ❌ Check API response

---

### ✅ 2. Multi-Step Re-Classify with Checkboxes

**File:** `frontend/src/pages/DocumentDetail.tsx`

**What to Test:**

**Step 1: Enter Selection Mode**
1. Go to document detail page (list of pages)
2. Click "Re-Classify Pages" button (amber outline)
3. Verify:
   - ✅ All page cards show checkboxes in top-left corner
   - ✅ "Select All" and "Cancel" buttons appear
   - ✅ "Classify Selected (0)" button appears (disabled)

**Step 2: Select Pages**
1. Click on a page card or its checkbox
2. Verify:
   - ✅ Checkbox shows checkmark
   - ✅ Page card has amber ring highlight
   - ✅ Counter updates: "Classify Selected (1)"
3. Click "Select All" button
4. Verify:
   - ✅ All checkboxes checked
   - ✅ All cards have amber ring
   - ✅ Counter shows total: "Classify Selected (25)"
5. Click "Select All" again (should deselect all)
6. Verify all checkboxes unchecked

**Step 3: Execute Classification**
1. Select 2-3 pages
2. Click "Classify Selected (3)" button
3. Verify:
   - ✅ Button shows "Classifying..."
   - ✅ Returns to normal view (checkboxes disappear)
   - ✅ Blue alert shows "Re-classification in progress..."
   - ✅ Pages update after ~2-5 seconds

**Cancel:**
1. Enter selection mode
2. Select some pages
3. Click "Cancel" button
4. Verify:
   - ✅ Returns to normal view
   - ✅ No classification triggered

---

### ✅ 3. Sheet Title Display

**File:** `frontend/src/components/document/PageCard.tsx`

**What to Test:**
1. Go to document detail page
2. Look at page cards
3. Verify top overlay shows:
   - ✅ **Bold sheet number:** "S0.01" or "S3.22"
   - ✅ **Gray title after dash:** "S0.01 - STRUCTURAL NOTES"
   - ✅ Classification below: "Structural:Plan"
   - ✅ Confidence bar at bottom

**Expected Format:**
```
┌─────────────────────────┐
│ S3.01 - FOUNDATION      │ ← Sheet # + Title
│ Structural:Detail       │ ← Classification
│ ████████████░ 95%       │ ← Confidence
└─────────────────────────┘
```

---

### ✅ 4. AI Evaluation Modal Image Loading

**File:** `frontend/src/pages/AIEvaluation.tsx`

**What to Test:**
1. Go to "AI EVALUATION" page (top navigation)
2. Scroll down to "Classification Timeline"
3. Click on any timeline entry
4. Verify modal opens with:
   - ✅ **Left side:** Page image loads (not stuck on "Loading image...")
   - ✅ **Right side:** Classification details display
   - ✅ **Header:** Not excessively tall (should be ~50px)
   - ✅ **Layout:** Image and details side-by-side
5. Try scrolling both sides independently
6. Click X or press Escape to close

**If Image Doesn't Load:**
- Check browser console for errors
- Verify `image_url` in API response is valid

---

### ✅ 5. Consolidated TakeoffViewer Top Bar

**File:** `frontend/src/components/viewer/ViewerHeader.tsx`

**What to Test:**
1. Open any page in TakeoffViewer
2. Look at top bar (should be ~70px tall)
3. Verify layout from left to right:
   - ✅ **[← Back]** button
   - ✅ **Separator line**
   - ✅ **Sheet info:** "S0.01" (bold) + scale text below
   - ✅ **Separator line**
   - ✅ **Drawing tools:** Select, Pan, Draw, Circle, Rectangle, Pin, Undo, Redo, Delete
   - ✅ **Helper text:** "Click to select measurements"
   - ✅ **Separator line**
   - ✅ **Scale buttons:** "AUTO DETECT" and "SET SCALE"
   - ✅ **Separator line**
   - ✅ **Zoom controls:** [-] [20%] [+] [Fit] [Fullscreen]
4. Verify NO vertical scrollbar on page
5. Click each tool to verify it works

---

## API Route Verification

### Quick API Tests

Open browser console and run these:

```javascript
// Test 1: Get page with classification data
fetch('/api/v1/pages/YOUR_PAGE_ID_HERE')
  .then(r => r.json())
  .then(data => {
    console.log('Classification:', data.classification);
    console.log('Discipline:', data.discipline);
    console.log('Page Type:', data.page_type);
    console.log('Relevance:', data.concrete_relevance);
    console.log('Elements:', data.concrete_elements);
    console.log('Description:', data.description);
    console.log('Provider:', data.llm_provider);
    console.log('Latency:', data.llm_latency_ms);
  });

// Test 2: Classify single page
fetch('/api/v1/pages/YOUR_PAGE_ID_HERE/classify', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ use_vision: false })
})
  .then(r => r.json())
  .then(data => console.log('Classification started:', data));

// Test 3: Classify document (all pages)
fetch('/api/v1/documents/YOUR_DOC_ID_HERE/classify', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ use_vision: false })
})
  .then(r => r.json())
  .then(data => console.log('Batch classification started:', data));
```

---

## Common Issues & Solutions

### Issue: "No classification data available" in sidebar

**Cause:** API not returning classification fields

**Fix:**
1. Check backend logs: `docker logs forgex-api`
2. Verify `/api/v1/pages/{id}` returns new fields
3. Restart API container: `docker restart forgex-api`

---

### Issue: Checkbox not showing or errors

**Cause:** Missing `@radix-ui/react-checkbox` package

**Fix:**
1. Check package installed: `docker exec forgex-frontend npm list @radix-ui/react-checkbox`
2. Should show: `@radix-ui/react-checkbox@1.3.3`
3. If missing, rebuild: `docker compose up --build frontend`

---

### Issue: Image not loading in AI Evaluation modal

**Cause:** Image URL not being derived from query data

**Fix:**
1. Check browser console for errors
2. Verify `pageData?.image_url` exists in network response
3. Check MinIO is running: `docker ps | grep minio`

---

### Issue: Vertical scrollbar appears in TakeoffViewer

**Cause:** Layout not using `h-screen` properly

**Fix:**
1. Check TakeoffViewer container has `h-screen` class
2. Verify top bar is ~70px (not taller)
3. Check no extra padding/margins

---

## Docker Container Status

### Check All Containers Running

```bash
docker ps
```

**Expected output:**
- ✅ forgex-db (PostgreSQL)
- ✅ forgex-redis (Redis)
- ✅ forgex-minio (MinIO)
- ✅ forgex-api (FastAPI backend)
- ✅ forgex-worker (Celery worker)
- ✅ forgex-frontend (React/Vite)

### Check Logs

```bash
# API logs
docker logs forgex-api --tail 50

# Worker logs
docker logs forgex-worker --tail 50

# Frontend logs
docker logs forgex-frontend --tail 50
```

---

## Access URLs

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **MinIO Console:** http://localhost:9001

---

## Final Checklist

Before going home, verify:

- [ ] Docker containers all running (6 containers)
- [ ] Frontend loads at http://localhost:3000
- [ ] Can upload a document
- [ ] Pages show sheet numbers + titles
- [ ] Can open TakeoffViewer for a page
- [ ] Classification sidebar shows data (not "No data")
- [ ] Sidebar collapses/expands
- [ ] Can enter selection mode with checkboxes
- [ ] Can select pages and classify selected
- [ ] AI Evaluation modal shows images
- [ ] No vertical scrollbar in TakeoffViewer
- [ ] All drawing tools accessible in top bar

---

## Quick Test Workflow

1. **Upload Document** → Wait for processing
2. **View Pages** → Verify sheet numbers + titles show
3. **Click "Re-Classify Pages"** → Verify checkboxes appear
4. **Select 2-3 pages** → Click "Classify Selected"
5. **Open Takeoff on any page** → Verify sidebar shows classification data
6. **Toggle sidebar** → Verify collapse/expand works
7. **Go to AI Evaluation** → Click timeline entry → Verify modal shows image
8. **Check top bar** → Verify all tools in one horizontal row

If all above work: ✅ **Everything is connected and working!**

---

**Last Updated:** January 20, 2026, 11:30 PM
**Docker Rebuild:** In progress...
