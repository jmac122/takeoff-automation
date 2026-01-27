# Troubleshooting Guide - AI Construction Takeoff Platform

## Overview

This guide documents common issues, their root causes, and solutions discovered during development and testing. Each entry includes the problem, diagnosis steps, solution, and preventive measures.

**Last Updated:** January 26, 2026

---

## Table of Contents

1. [Frontend Issues](#frontend-issues)
2. [Backend API Issues](#backend-api-issues)
3. [Scale Detection Issues](#scale-detection-issues)
4. [OCR Processing Issues](#ocr-processing-issues)
5. [Database Issues](#database-issues)
6. [Classification Issues](#classification-issues)

---

## Frontend Issues

### Issue 1: AI Evaluation Modal Image Not Loading

**Symptoms:**
- Classification timeline modal shows "Loading image..." indefinitely
- No image displayed despite valid `image_url` in page data

**Root Cause:**
Incorrect use of `useState` for side effects. The code was trying to use `useState` to set `imageUrl` based on `pageData`, but this doesn't trigger on prop changes.

**Solution:**
```typescript
// ❌ WRONG
const [imageUrl, setImageUrl] = useState<string | null>(null);
useState(() => {
    if (pageData?.image_url) {
        setImageUrl(pageData.image_url);
    }
});

// ✅ CORRECT
const imageUrl = pageData?.image_url || null;
```

**Files Modified:**
- `frontend/src/pages/AIEvaluation.tsx`

---

### Issue 2: Canvas Goes Black When Opening Dialogs

**Symptoms:**
- Clicking "Set Scale" or other buttons causes the canvas/image area to go completely black
- Console shows "Failed to load image" errors from react-konva
- Image reappears after page navigation or refresh

**Root Cause:**
Presigned MinIO URLs include timestamps that change on every API call. When React Query refetches page data, a new URL is generated. The original `usePageImage` hook had a cleanup function that set `img.src = ''` when the URL changed, aborting the current image load.

**Solution:**
```typescript
// usePageImage.ts - Compare base URLs (without query params)
const baseUrl = useMemo(() => {
    if (!imageUrl) return null;
    const url = new URL(imageUrl);
    return url.origin + url.pathname; // Strip query params
}, [imageUrl]);

// Only reload if base URL changes, not presigned params
if (image && currentUrlRef.current === baseUrl) {
    return; // Keep existing image
}

// Remove cleanup that clears img.src
// The browser handles garbage collection
```

**Files Modified:**
- `frontend/src/hooks/usePageImage.ts`

---

### Issue 3: Konva CalibrationOverlay Crashes on Zero-Length Lines

**Symptoms:**
- Black screen or crash when starting calibration
- Error: "Text components are not supported... Your text is: '0'"

**Root Cause:**
Konva Text component fails when rendering very short or zero-length lines (distance = 0).

**Solution:**
```typescript
// Only show label when line is long enough
const showLabel = displayDistance > 20;
{showLabel && <Text ... />}

// Also add safety checks for scale
const safeScale = scale > 0 && Number.isFinite(scale) ? scale : 1;
```

**Files Modified:**
- `frontend/src/components/viewer/CalibrationOverlay.tsx`

**Prevention:**
- Derive state from props directly when possible
- Use `useEffect` for side effects, not `useState`
- Test modal components with real data

---

### Issue 4: TakeoffViewer Page Loads Black After Drawing Measurements

**Symptoms:**
- Specific pages render a black canvas after saving shapes
- Other pages in the same document load normally
- DevTools shows `InvalidStateError: drawImage ... canvas element with width or height of 0`

**Root Cause:**
Invalid measurement geometry (zero-length line, empty/degenerate polyline/polygon, invalid dimensions) causes Konva to draw a 0x0 cached canvas and crash the stage.

**Solution:**
```tsx
// MeasurementShape.tsx - Skip invalid geometry
if (!isValidGeometry) {
  return null;
}
```

**Files Modified:**
- `frontend/src/components/viewer/MeasurementShape.tsx`
- `frontend/src/pages/TakeoffViewer.tsx`
- `frontend/src/hooks/usePageImage.ts`
- `frontend/src/hooks/useCanvasControls.ts`

**Prevention:**
- Validate geometry before saving measurements
- Guard rendering against invalid shapes

---

### Issue 5: TakeoffViewer Vertical Scrollbar

**Symptoms:**
- Unwanted vertical scrollbar in TakeoffViewer
- Layout not filling available space
- Canvas area too small

**Root Cause:**
Improper flexbox layout with nested containers using height-based sizing instead of flex-based sizing.

**Solution:**
```tsx
// Use flexbox with flex-1 and min-h-0 to prevent overflow
<div className="flex flex-col h-screen">
  <Header className="flex-shrink-0" />
  <div className="flex flex-1 min-h-0">
    <Sidebar className="flex-shrink-0" />
    <div className="flex-1 overflow-auto">
      {/* Canvas here */}
    </div>
  </div>
</div>
```

**Files Modified:**
- `frontend/src/pages/TakeoffViewer.tsx`

**Prevention:**
- Use `flex-1` and `min-h-0` for flex children that should fill space
- Avoid mixing height percentages with flexbox
- Test layout at different viewport sizes

---

### Issue 3: Classification Sidebar Missing Data

**Symptoms:**
- Sidebar shows classification but missing "Elements Detected" and "Description"
- AI Evaluation modal shows all data for same page
- `hasClassification` check failing

**Root Cause:**
1. Sidebar was using `page` data directly, which may have null values for detailed fields
2. `hasClassification` check was too strict, only checking `discipline` and `page_type`
3. Detailed classification data is in the history API, not always in the page object

**Solution:**
```typescript
// Fetch classification history
const { data: historyData } = useQuery({
  queryKey: ['page-classification-history', page.id],
  queryFn: () => classificationApi.getPageHistory(page.id),
});

// Use latest classification from history
const latestClassification = historyData?.history?.[0];
const displayData = latestClassification || page;

// Broaden hasClassification check
const hasClassification = displayData.discipline || displayData.page_type || displayData.classification;
```

**Files Modified:**
- `frontend/src/components/viewer/ClassificationSidebar.tsx`

**Prevention:**
- Always use the most complete data source (history API over page object)
- Make conditional checks inclusive, not exclusive
- Test with pages that have been classified via different methods

---

### Issue 4: Multi-Step Re-Classification Not Working

**Symptoms:**
- Hover-based re-classify button not appearing
- No way to select multiple pages for re-classification
- User experience not intuitive

**Root Cause:**
Original design used hover-based UI which was not implemented and not user-friendly for deliberate actions.

**Solution:**
Implemented multi-step selection process:
1. Click "Re-Classify Pages" → enters selection mode
2. Checkboxes appear on all page cards
3. User selects pages (or "Select All")
4. Click "Classify Selected (N)" to trigger

```typescript
const [isSelectionMode, setIsSelectionMode] = useState(false);
const [selectedPages, setSelectedPages] = useState<Set<string>>(new Set());

// Selection mode UI
{isSelectionMode ? (
  <div className="flex gap-2">
    <Button onClick={handleSelectAll}>Select All</Button>
    <Button onClick={() => setIsSelectionMode(false)}>Cancel</Button>
    <Button onClick={handleClassifySelected}>
      Classify Selected ({selectedPages.size})
    </Button>
  </div>
) : (
  <Button onClick={() => setIsSelectionMode(true)}>
    Re-Classify Pages
  </Button>
)}
```

**Files Modified:**
- `frontend/src/pages/DocumentDetail.tsx`
- `frontend/src/components/document/PageCard.tsx`
- `frontend/src/components/ui/checkbox.tsx` (new)

**Prevention:**
- Use deliberate multi-step processes for batch operations
- Provide clear visual feedback for selection state
- Follow established UI patterns (checkboxes for multi-select)

---

## Backend API Issues

### Issue 5: Missing Classification Fields in API Response

**Symptoms:**
- Frontend requests `/api/v1/pages/{page_id}` but doesn't receive all classification fields
- `discipline`, `page_type`, `concrete_elements`, `description` are null or missing
- `AttributeError: 'Page' object has no attribute 'discipline'`

**Root Cause:**
1. Backend `PageResponse` schema didn't include new classification fields
2. Database `Page` model was missing the columns
3. API endpoint wasn't returning the fields

**Solution:**

1. **Add fields to SQLAlchemy model:**
```python
# backend/app/models/page.py
class Page(Base, UUIDMixin, TimestampMixin):
    # ... existing fields ...
    discipline = Column(String, nullable=True)
    discipline_confidence = Column(Float, nullable=True)
    page_type = Column(String, nullable=True)
    page_type_confidence = Column(Float, nullable=True)
    concrete_elements = Column(JSONB, nullable=True)
    description = Column(Text, nullable=True)
    llm_provider = Column(String, nullable=True)
    llm_latency_ms = Column(Float, nullable=True)
```

2. **Add fields to Pydantic schema:**
```python
# backend/app/schemas/page.py
class PageResponse(BaseModel):
    # ... existing fields ...
    discipline: str | None = None
    discipline_confidence: float | None = None
    page_type: str | None = None
    page_type_confidence: float | None = None
    concrete_elements: list[str] | None = None
    description: str | None = None
    llm_provider: str | None = None
    llm_latency_ms: float | None = None
```

3. **Return fields in API endpoint:**
```python
# backend/app/api/routes/pages.py
return PageResponse(
    # ... existing fields ...
    discipline=page.discipline,
    discipline_confidence=page.discipline_confidence,
    page_type=page.page_type,
    page_type_confidence=page.page_type_confidence,
    concrete_elements=page.concrete_elements,
    description=page.description,
    llm_provider=page.llm_provider,
    llm_latency_ms=page.llm_latency_ms,
)
```

4. **Create and apply migration:**
```bash
cd backend
alembic revision --autogenerate -m "add_detailed_classification_fields_to_pages"
alembic upgrade head
```

**Files Modified:**
- `backend/app/models/page.py`
- `backend/app/schemas/page.py`
- `backend/app/api/routes/pages.py`
- `backend/alembic/versions/0f19e78be270_add_detailed_classification_fields_to_.py` (new)

**Prevention:**
- Always update model, schema, AND endpoint when adding fields
- Run migrations immediately after model changes
- Test API responses with real data

---

## Scale Detection Issues

### Issue 6: Scale Detection Results Auto-Clearing

**Symptoms:**
- "Auto Detect Scale" button runs successfully
- Results disappear after 5 seconds
- "Set Scale" field not auto-populated
- No visual feedback for detected scale location

**Root Cause:**
Frontend hook had a 5-second timeout that cleared `detectionResult` and `scaleHighlightBox` state.

**Solution:**
```typescript
// ❌ REMOVE THIS
if (status.detection?.best_scale) {
    setTimeout(() => {
        setDetectionResult(null);
        setScaleHighlightBox(null);
    }, 5000);
}

// ✅ ADD SUCCESS NOTIFICATION INSTEAD
addNotification(
    'success',
    'Scale Detected',
    `Scale Detected: ${status.detection.best_scale.text}. Click 'SET SCALE' to review or adjust.`
);
```

**Files Modified:**
- `frontend/src/hooks/useScaleDetection.ts`

**Prevention:**
- Don't auto-clear important results
- Use notifications for feedback instead of temporary state
- Let users explicitly dismiss or refresh

---

### Issue 7: Scale Detection Bounding Box Inaccurate

**Symptoms:**
- "Show Scale Location" button shows bbox in wrong location
- Bbox coordinates don't match visual scale location on page
- Off by a significant margin (50%+)

**Root Cause:**
LLM analyzes a compressed version of the image (for cost/speed), but returns bbox coordinates based on the compressed dimensions. Frontend displays the full-resolution image, causing coordinate mismatch.

**Solution:**

1. **Track compression scale factor:**
```python
# backend/app/services/llm_client.py
def _compress_image_if_needed(self, image_bytes: bytes) -> tuple[bytes, float, tuple[int, int]]:
    img = Image.open(io.BytesIO(image_bytes))
    original_dimensions = (img.width, img.height)
    
    if img.width > self.max_image_size or img.height > self.max_image_size:
        ratio = self.max_image_size / max(img.width, img.height)
        new_size = (int(img.width * ratio), int(img.height * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
        scale_factor = ratio
    else:
        scale_factor = 1.0
    
    return (compressed_bytes, scale_factor, original_dimensions)
```

2. **Use OCR bounding boxes for pixel-perfect accuracy:**
```python
# backend/app/services/scale_detector.py
# Search OCR blocks for the detected scale text
for block in ocr_blocks["blocks"]:
    if normalized_scale in block.get("text", "").lower():
        # Use OCR's accurate bounding box
        if "bounding_box" in block:
            ocr_bbox = block["bounding_box"]
            final_bbox = {
                "x": int(ocr_bbox["x"]),
                "y": int(ocr_bbox["y"]),
                "width": int(ocr_bbox["width"]),
                "height": int(ocr_bbox["height"]),
            }
            logger.info("Using OCR bbox for better accuracy")
            break
```

3. **Scale LLM bbox if OCR not available:**
```python
if llm_bbox and not final_bbox:
    final_bbox = {
        "x": int(llm_bbox["x"] / scale_factor),
        "y": int(llm_bbox["y"] / scale_factor),
        "width": int(llm_bbox["width"] / scale_factor),
        "height": int(llm_bbox["height"] / scale_factor),
    }
```

**Files Modified:**
- `backend/app/services/llm_client.py`
- `backend/app/services/scale_detector.py`
- `backend/app/workers/scale_tasks.py`

**Prevention:**
- Always track image transformations (compression, scaling, rotation)
- Prefer OCR bounding boxes over LLM bounding boxes when available
- Test with images of various sizes

---

### Issue 8: LLM Response Truncated (MAX_TOKENS)

**Symptoms:**
- Worker logs show `finish_reason=<FinishReason.MAX_TOKENS: 2>`
- Scale detection returns incomplete JSON
- `bbox` field is null or missing

**Root Cause:**
Default `max_tokens` was set to 1024, which is insufficient for detailed scale detection responses with bounding boxes.

**Solution:**
```python
# backend/app/services/llm_client.py
async def analyze_image_json(
    self,
    image_bytes: bytes,
    prompt: str,
    model: str | None = None,
    max_tokens: int = 8192,  # Increased from 1024
) -> LLMResponse:
```

**Impact:**
- Minimal cost increase (actual tokens used determines billing)
- Prevents JSON truncation
- Ensures complete responses

**Files Modified:**
- `backend/app/services/llm_client.py`

**Prevention:**
- Set `max_tokens` generously for JSON responses
- Monitor `finish_reason` in logs
- Validate JSON completeness before parsing

---

### Issue 9: Markdown Code Fences in LLM Response

**Symptoms:**
- JSON parsing fails with `JSONDecodeError`
- LLM response includes ` ```json` and ` ``` ` wrappers
- Scale detection fails despite valid JSON content

**Root Cause:**
Some LLM providers (especially Gemini) wrap JSON responses in markdown code fences for better readability.

**Solution:**
```python
# backend/app/services/scale_detector.py
# Clean response - remove markdown code fences if present
content = response.content.strip()
if content.startswith("```json"):
    content = content[7:]  # Remove ```json
if content.startswith("```"):
    content = content[3:]  # Remove ```
if content.endswith("```"):
    content = content[:-3]  # Remove trailing ```
content = content.strip()

# Now parse JSON
result = json.loads(content)
```

**Files Modified:**
- `backend/app/services/scale_detector.py`

**Prevention:**
- Always strip markdown formatting before JSON parsing
- Test with multiple LLM providers
- Add robust error handling for parsing

---

### Issue 10: Scale Detection Overwrites Good Bbox on Failed Re-run

**Symptoms:**
- First auto-detect finds scale with bbox successfully
- Re-running auto-detect fails to find bbox
- "Show Scale Location" button disappears
- Historical bbox data is lost

**Root Cause:**
Scale detection task was unconditionally updating `scale_calibration_data`, overwriting good historical data with failed detection results.

**Solution:**
```python
# backend/app/workers/scale_tasks.py
# Only update scale_calibration_data if new detection has a best_scale with bbox
if detection.get("best_scale") and detection["best_scale"].get("bbox"):
    page.scale_calibration_data = detection
else:
    # Preserve existing if it has a bbox
    if page.scale_calibration_data and page.scale_calibration_data.get("best_scale") and page.scale_calibration_data["best_scale"].get("bbox"):
        logger.info("Preserving existing scale_calibration_data with bbox")
    else:
        page.scale_calibration_data = detection
```

**Files Modified:**
- `backend/app/workers/scale_tasks.py`

**Prevention:**
- Preserve historical data when new attempts fail
- Only overwrite with better or equal quality data
- Log preservation decisions for debugging

---

### Issue 11: OCR Blocks Not Passed to Scale Detector

**Symptoms:**
- Worker logs show `error=name 'ocr_blocks' is not defined`
- Scale detection fails with NameError
- OCR bounding boxes not being used

**Root Cause:**
`detect_scale()` function signature was updated to accept `ocr_blocks` parameter, but the Celery task wasn't passing it.

**Solution:**
```python
# backend/app/workers/scale_tasks.py
detection = detector.detect_scale(
    image_bytes,
    ocr_text=page.ocr_text,
    ocr_blocks=page.ocr_blocks,  # Added this line
    detected_scale_texts=detected_scales,
)
```

**Files Modified:**
- `backend/app/workers/scale_tasks.py`

**Prevention:**
- Update all call sites when changing function signatures
- Use type hints to catch missing parameters
- Test end-to-end workflows after API changes

---

## OCR Processing Issues

### Issue 12: OCR Extracting Too Much Text for Title/Sheet Number

**Symptoms:**
- `title` field contains entire page text instead of just the title
- `sheet_number` field contains multiple numbers from throughout the page
- Classification accuracy degraded due to noisy data

**Root Cause:**
`_extract_sheet_numbers()` and `_extract_titles()` methods were searching the entire page text instead of just the title block region (bottom-right corner).

**Solution:**
Modify extraction methods to only search OCR blocks in the bottom-right 30% x 30% region:

```python
# backend/app/services/ocr_service.py
def _extract_sheet_numbers(self, text: str, blocks: list[TextBlock], page_width: int, page_height: int) -> list[str]:
    """Extract sheet numbers from title block region only."""
    # Define title block region (bottom-right 30% x 30%)
    title_block_x = page_width * 0.7
    title_block_y = page_height * 0.7
    
    # Filter blocks to title block region
    title_block_text = " ".join([
        block.text for block in blocks
        if (block.bounding_box["x"] + block.bounding_box["width"]/2 > title_block_x
            and block.bounding_box["y"] + block.bounding_box["height"]/2 > title_block_y)
    ])
    
    # Search only title block text
    for pattern in self.SHEET_NUMBER_PATTERNS:
        matches = re.findall(pattern, title_block_text, re.IGNORECASE)
        # ... rest of logic
```

**Files Modified:**
- `backend/app/services/ocr_service.py`

**Prevention:**
- Always consider spatial context when extracting data from construction drawings
- Use bounding boxes to filter OCR results by region
- Test with diverse drawing types and layouts

---

### Issue 13: Database Column Too Short for OCR Text

**Symptoms:**
- `StringDataRightTruncation: value too long for type character varying(500)`
- OCR processing fails when saving results
- Some pages have very long titles or sheet numbers

**Root Cause:**
Database columns for `title` and `sheet_number` were defined as `VARCHAR(500)`, which is insufficient for some OCR extractions.

**Solution:**
Create migration to change columns to `Text` type:

```python
# backend/alembic/versions/d5b881957963_increase_ocr_field_lengths.py
def upgrade():
    op.alter_column('pages', 'title',
        existing_type=sa.VARCHAR(length=500),
        type_=sa.Text(),
        existing_nullable=True
    )
    op.alter_column('pages', 'sheet_number',
        existing_type=sa.VARCHAR(length=500),
        type_=sa.Text(),
        existing_nullable=True
    )

def downgrade():
    op.alter_column('pages', 'sheet_number',
        existing_type=sa.Text(),
        type_=sa.VARCHAR(length=500),
        existing_nullable=True
    )
    op.alter_column('pages', 'title',
        existing_type=sa.Text(),
        type_=sa.VARCHAR(length=500),
        existing_nullable=True
    )
```

**Files Modified:**
- `backend/alembic/versions/d5b881957963_increase_ocr_field_lengths.py` (new)

**Prevention:**
- Use `Text` type for variable-length text fields
- Only use `VARCHAR(N)` when you have a business reason for the limit
- Test with edge cases (very long text)

---

## Database Issues

### Issue 14: Missing Database Columns After Model Update

**Symptoms:**
- `AttributeError: 'Page' object has no attribute 'discipline'`
- API returns 500 errors when accessing new fields
- Frontend receives incomplete data

**Root Cause:**
SQLAlchemy model was updated with new columns, but database migration wasn't created or applied.

**Solution:**

1. **Generate migration:**
```bash
cd backend
alembic revision --autogenerate -m "add_detailed_classification_fields_to_pages"
```

2. **Review migration file:**
```python
# Verify the migration looks correct
cat alembic/versions/0f19e78be270_add_detailed_classification_fields_to_.py
```

3. **Apply migration:**
```bash
alembic upgrade head
```

4. **Verify in database:**
```sql
\d pages  -- PostgreSQL
-- Check that new columns exist
```

**Files Modified:**
- `backend/alembic/versions/0f19e78be270_add_detailed_classification_fields_to_.py` (new)

**Prevention:**
- Always create and apply migrations after model changes
- Test migrations in development before production
- Use `alembic current` to verify migration state

---

## Classification Issues

### Issue 15: Classification Data Not Persisting

**Symptoms:**
- Classification runs successfully
- Frontend shows results briefly
- Refreshing page shows no classification data
- Database has null values for classification fields

**Root Cause:**
Classification worker was not saving all fields to the database, only updating `classification` and `classification_confidence`.

**Solution:**
Update classification worker to save all fields:

```python
# backend/app/workers/classification_tasks.py
page.classification = result.classification
page.classification_confidence = result.confidence
page.discipline = result.discipline
page.discipline_confidence = result.discipline_confidence
page.page_type = result.page_type
page.page_type_confidence = result.page_type_confidence
page.concrete_relevance = result.concrete_relevance
page.concrete_elements = result.concrete_elements
page.description = result.description
page.llm_provider = result.provider
page.llm_latency_ms = result.latency_ms

await db.commit()
```

**Files Modified:**
- `backend/app/workers/classification_tasks.py`

**Prevention:**
- Ensure all model fields are populated in worker tasks
- Test data persistence after async operations
- Verify database state after task completion

---

## General Debugging Tips

### Enable Debug Logging

```python
# backend/app/main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Docker Logs

```bash
cd docker
docker compose logs api --tail 50 --follow
docker compose logs worker --tail 50 --follow
docker compose logs frontend --tail 50 --follow
```

### Verify Database State

```bash
docker compose exec db psql -U postgres -d takeoff
```

```sql
-- Check page data
SELECT id, page_number, classification, discipline, page_type, scale_calibrated 
FROM pages 
WHERE document_id = 'YOUR_DOCUMENT_ID' 
ORDER BY page_number;

-- Check classification history
SELECT page_id, classification, discipline, page_type, created_at 
FROM classification_history 
ORDER BY created_at DESC 
LIMIT 10;
```

### Test API Endpoints

```bash
# Get page details
curl http://localhost:8000/api/v1/pages/{page_id}

# Get classification history
curl http://localhost:8000/api/v1/pages/{page_id}/classification/history

# Trigger scale detection
curl -X POST http://localhost:8000/api/v1/pages/{page_id}/detect-scale
```

### Frontend DevTools

1. Open React DevTools
2. Check component props and state
3. Verify API responses in Network tab
4. Check console for errors

---

## Contact and Support

For issues not covered in this guide:

1. Check the relevant service documentation in `docs/services/`
2. Review the API reference in `docs/api/`
3. Search the codebase for similar patterns
4. Add new issues to this document as they're discovered

---

**Document Maintenance:**
This guide should be updated whenever new issues are discovered and resolved. Include:
- Clear symptom description
- Root cause analysis
- Complete solution with code examples
- Prevention tips
- Files modified
