# UX Improvements - Classification & Display

## Changes Made

### 1. **Sheet Number Display** ✅

**Problem**: Sheet numbers (S1.01, S0.02, etc.) were buried in small text at the bottom of cards.

**Solution**: Moved sheet number to **TOP of card overlay** in large, bold text:

```
┌─────────────────┐
│ S1.01 - FOUND   │  ← BOLD, prominent
│ Structural:Plan │  ← Classification below
│ ██████░░ 95%    │  ← Confidence bar
└─────────────────┘
```

**Display Priority**:
1. **Sheet Number** (from OCR) - Large, bold, white text
2. **Classification** (Discipline:Type) - Smaller, gray text below
3. **Confidence** - Progress bar at bottom

### 2. **Individual Page Re-classification** ✅

**Problem**: All-or-nothing classification - had to re-run entire document if one page was wrong.

**Solution**: Added **per-page re-classify button** that appears on hover:

- **Hover over any page card** → "Re-classify" button appears
- Click to re-classify just that one page
- Button shows spinner while processing
- Results update automatically

**Implementation**:
- `POST /api/v1/pages/{page_id}/classify` with `use_vision: false`
- Fast OCR-based re-classification (same as auto-classification)
- No need to re-run entire document

### 3. **Better Button Messaging** ✅

**Problem**: Users didn't know classification was automatic or when to use the button.

**Solution**: Clear messaging and visual hierarchy:

**Before**:
```
[Classify All Pages]  ← Unclear if needed
```

**After**:
```
✓ Auto-classified from OCR data  ← Green success message

Not happy with results?
Re-classify all pages or hover over individual pages

[Re-Classify All Pages]  ← Amber/outline style (secondary action)
```

**Key Changes**:
- Green "✓ Auto-classified" alert at top
- Explains classification already happened
- Button is now **secondary action** (outline style, amber color)
- Text changed from "Classify" to "**Re-Classify**"
- Explains individual page option

### 4. **Automatic Classification** ✅

**Flow**:
```
Upload PDF
    ↓
OCR Extraction (5-10 sec/page)
    ↓ extracts: sheet number, title, text
    ↓
✨ AUTO-CLASSIFICATION ✨ (<100ms, $0)
    ↓
Pages display with:
    • Sheet number (S1.01)
    • Classification (Structural:Plan)
    • Confidence (95%)
    • Concrete relevance badge
```

**No button click needed!**

## Visual Hierarchy

### Page Card Layout

```
┌─────────────────────────┐
│ ┌─────────────────────┐ │
│ │ S1.01 - FOUNDATION  │ │ ← Sheet # (bold, large)
│ │ Structural:Plan     │ │ ← Classification
│ │ ██████████░ 95%     │ │ ← Confidence
│ │                     │ │
│ │   [Page Image]      │ │
│ │                     │ │
│ │            [HIGH]   │ │ ← Concrete badge
│ └─────────────────────┘ │
│                         │
│ Page 6                  │ ← Small page number
│                         │
│ [Open Takeoff]          │ ← Primary action
│ [Re-classify] (hover)   │ ← Secondary (on hover)
└─────────────────────────┘
```

### Document Header

```
┌────────────────────────────────────┐
│ Structural IFCs.pdf                │
│ 25 pages • ready • Uploaded 1h ago │
├────────────────────────────────────┤
│ ✓ Auto-classified from OCR data    │ ← Green success
│                                    │
│ Not happy with results?            │
│ Re-classify all pages or hover     │
│ over individual pages              │
│                                    │
│ [Re-Classify All Pages]            │ ← Amber outline
└────────────────────────────────────┘
```

## User Flows

### Happy Path (95% of cases)
1. Upload PDF
2. Wait 10-20 seconds
3. See all pages with sheet numbers & classifications
4. Click "Open Takeoff" on any page
5. **Done!** (no manual classification needed)

### Correction Path (5% of cases)
**Option A - Single Page**:
1. Hover over incorrect page
2. Click "Re-classify"
3. Wait 2 seconds
4. See updated classification

**Option B - All Pages**:
1. Click "Re-Classify All Pages"
2. Wait 10-20 seconds
3. See all updated classifications

## Technical Details

### API Endpoints

**Single Page**:
```http
POST /api/v1/pages/{page_id}/classify
{
  "use_vision": false  // Fast OCR-based (default)
}
```

**All Pages**:
```http
POST /api/v1/documents/{document_id}/classify
{
  "use_vision": false  // Fast OCR-based (default)
}
```

### Frontend Components

**Modified Files**:
1. `frontend/src/components/document/PageCard.tsx`
   - Added re-classify button (hover state)
   - Moved sheet number to top overlay
   - Improved visual hierarchy

2. `frontend/src/pages/DocumentDetail.tsx`
   - Added auto-classification indicator
   - Changed button to "Re-Classify"
   - Added explanatory text
   - Improved polling logic

### Backend Changes

**Modified Files**:
1. `backend/app/workers/ocr_tasks.py`
   - Auto-trigger classification after OCR
   
2. `backend/app/api/routes/pages.py`
   - Added `use_vision` parameter to single page endpoint

## Cost & Performance

| Action | Time | Cost | When to Use |
|--------|------|------|-------------|
| **Auto-classify (OCR)** | <100ms | $0 | Automatic after upload |
| **Re-classify single page** | <100ms | $0 | Fix one wrong page |
| **Re-classify all pages** | 2-3 sec | $0 | Fix multiple pages |
| **Vision LLM (optional)** | 3-5 sec | $0.003-0.015 | Complex/non-standard sheets |

## Testing

1. Upload a new PDF
2. Wait for OCR to complete
3. Verify pages show:
   - Sheet numbers at top (bold)
   - Classification below
   - Confidence bars
4. Hover over a page → verify "Re-classify" button appears
5. Click "Re-classify" → verify it updates
6. Check "Re-Classify All Pages" button works

## Future Enhancements

- [ ] Bulk select multiple pages for re-classification
- [ ] "Use Vision LLM" toggle for detailed analysis
- [ ] Classification history/comparison view
- [ ] Confidence threshold warnings
