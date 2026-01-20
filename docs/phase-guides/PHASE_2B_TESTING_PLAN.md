# Phase 2B - Scale Detection and Calibration Testing Plan

**Date**: January 20, 2026  
**Status**: Ready for Verification Testing  
**Estimated Time**: 20-30 minutes

---

## ✅ Already Completed (Unit Tests)

These were verified with `backend/test_scale_detection.py`:

- ✅ Scale parser correctly parses "1/4" = 1'-0"" → Result: 48.0 ✅
- ✅ Scale parser correctly parses "1" = 20'" → Result: 240.0 ✅
- ✅ Scale parser correctly parses "1:100" → Result: 100.0 ✅
- ✅ Scale parser handles "NOT TO SCALE" → Result: 0.0 ✅
- ✅ Manual calibration calculates correct pixels/foot → All tests passed ✅

**How to re-run**:
```bash
docker compose exec api python test_scale_detection.py
```

---

## 🧪 Integration Tests (Need to Verify in Docker)

These require the full application stack running with a real database.

### Prerequisites

1. **Start Docker services**:
```bash
docker compose up -d
```

2. **Verify services are running**:
```bash
docker compose ps
```

Expected output:
- ✅ forgex-api (backend)
- ✅ forgex-frontend
- ✅ forgex-db (PostgreSQL)
- ✅ forgex-redis
- ✅ forgex-celery-worker
- ✅ forgex-minio

3. **Check backend logs**:
```bash
docker logs forgex-api -f
```

---

## Test Suite

### Test 1: API Endpoint - Automatic Scale Detection

**Objective**: Verify `/pages/{page_id}/detect-scale` endpoint works

**Prerequisites**:
- Upload a document with pages
- Get a valid `page_id` from the database

**Steps**:

**Option A - Using Frontend** (Recommended):
1. Open http://localhost:5173
2. Upload a PDF document
3. Wait for OCR to complete
4. Click on a page to view it
5. Look for "Detect Scale" button or automatic detection indicator

**Option B - Using curl**:
```bash
# Replace {page_id} with actual UUID from database
curl -X POST http://localhost:8000/api/v1/pages/{page_id}/detect-scale \
  -H "Content-Type: application/json"
```

**Expected Response**:
```json
{
  "status": "queued",
  "page_id": "uuid-here"
}
```

**Verification**:
- [ ] Endpoint returns 202 Accepted
- [ ] Celery task is triggered
- [ ] Check Celery logs: `docker logs forgex-celery-worker -f`
- [ ] Page is updated with detected scale after task completes

---

### Test 2: API Endpoint - Manual Scale Update

**Objective**: Verify `PUT /pages/{page_id}/scale` endpoint works

**Steps**:
```bash
curl -X PUT http://localhost:8000/api/v1/pages/{page_id}/scale \
  -H "Content-Type: application/json" \
  -d '{
    "scale_text": "1/4\" = 1'\''-0\"",
    "scale_value": 48.0,
    "scale_unit": "foot"
  }'
```

**Expected Response**:
```json
{
  "id": "uuid",
  "scale_text": "1/4\" = 1'-0\"",
  "scale_value": 48.0,
  "scale_unit": "foot",
  "scale_calibrated": false
}
```

**Verification**:
- [ ] Endpoint returns 200 OK
- [ ] Scale fields are updated in database
- [ ] Get page shows updated scale: `curl http://localhost:8000/api/v1/pages/{page_id}`

---

### Test 3: API Endpoint - Manual Calibration

**Objective**: Verify `POST /pages/{page_id}/calibrate` endpoint calculates correct pixels/foot

**Test Cases**:

**Case 1**: 100 pixels = 10 feet (should give 10 px/ft)
```bash
curl -X POST http://localhost:8000/api/v1/pages/{page_id}/calibrate \
  -H "Content-Type: application/json" \
  -d '{
    "pixel_distance": 100,
    "real_distance": 10,
    "real_unit": "foot"
  }'
```

**Expected**: `scale_value: 10.0`

**Case 2**: 240 pixels = 20 feet (should give 12 px/ft)
```bash
curl -X POST http://localhost:8000/api/v1/pages/{page_id}/calibrate \
  -H "Content-Type: application/json" \
  -d '{
    "pixel_distance": 240,
    "real_distance": 20,
    "real_unit": "foot"
  }'
```

**Expected**: `scale_value: 12.0`

**Case 3**: Inches to feet conversion (120 pixels = 10 inches → 144 px/ft)
```bash
curl -X POST http://localhost:8000/api/v1/pages/{page_id}/calibrate \
  -H "Content-Type: application/json" \
  -d '{
    "pixel_distance": 120,
    "real_distance": 10,
    "real_unit": "inch"
  }'
```

**Expected**: `scale_value: 144.0`

**Verification**:
- [ ] Case 1: scale_value = 10.0 ✅
- [ ] Case 2: scale_value = 12.0 ✅
- [ ] Case 3: scale_value = 144.0 ✅
- [ ] scale_calibrated = true for all cases
- [ ] scale_calibration_data contains calibration metadata

---

### Test 4: API Endpoint - Copy Scale Between Pages

**Objective**: Verify `POST /pages/{page_id}/copy-scale-from/{source_page_id}` works

**Prerequisites**:
- Have two pages in the same document
- Calibrate the first page (source)

**Steps**:
```bash
# Calibrate source page first
curl -X POST http://localhost:8000/api/v1/pages/{source_page_id}/calibrate \
  -H "Content-Type: application/json" \
  -d '{"pixel_distance": 100, "real_distance": 10, "real_unit": "foot"}'

# Copy scale to target page
curl -X POST http://localhost:8000/api/v1/pages/{target_page_id}/copy-scale-from/{source_page_id}
```

**Expected Response**:
```json
{
  "id": "target_page_id",
  "scale_value": 10.0,
  "scale_calibrated": true,
  "copied_from": "source_page_id"
}
```

**Verification**:
- [ ] Target page has same scale_value as source
- [ ] scale_calibrated = true on target
- [ ] scale_calibration_data contains source_page_id reference

---

### Test 5: Database Persistence

**Objective**: Verify scale data persists correctly in PostgreSQL

**Steps**:
1. Connect to database:
```bash
docker compose exec db psql -U postgres -d takeoff_db
```

2. Query page with scale:
```sql
SELECT 
  id,
  document_id,
  page_number,
  scale_text,
  scale_value,
  scale_unit,
  scale_calibrated,
  scale_calibration_data
FROM pages
WHERE scale_value IS NOT NULL
LIMIT 5;
```

**Verification**:
- [ ] scale_text contains detected scale notation
- [ ] scale_value is numeric (pixels per foot)
- [ ] scale_unit is "foot", "inch", or "meter"
- [ ] scale_calibrated is true for manually calibrated pages
- [ ] scale_calibration_data is valid JSONB with expected structure

**Expected scale_calibration_data structure**:
```json
{
  "parsed_scales": [...],
  "scale_bars": [...],
  "best_scale": {...},
  "needs_calibration": false,
  "calibration": {
    "pixels_per_foot": 10.5,
    "method": "manual_calibration"
  }
}
```

---

### Test 6: Frontend Component - ScaleCalibration.tsx

**Objective**: Verify the scale calibration UI works in the browser

**Steps**:

1. **Navigate to page viewer**:
   - Open http://localhost:5173
   - Upload a document (if not already done)
   - Click on a page thumbnail to view it

2. **Locate Scale Calibration Component**:
   - Look for scale indicator showing "Not Calibrated" or scale value
   - Should see a "Calibrate" button or ruler icon

3. **Test Manual Calibration Flow**:
   - Click "Calibrate" button
   - Component should enter calibration mode
   - Draw a line on the plan image (click start point, move, click end point)
   - Click "Done" or similar button
   - Dialog should appear asking for real-world distance
   - Enter a distance (e.g., "10")
   - Select unit (feet/inches/meters)
   - Click "Save" or "Confirm"

4. **Verify Scale Display**:
   - Scale indicator should update
   - Should show calibrated status
   - Should display pixels/foot value
   - Scale text should be visible

5. **Test Copy Scale Feature** (if multiple pages):
   - Navigate to a different page
   - Look for "Copy Scale" button
   - Click it and select source page
   - Verify scale is copied

**Verification**:
- [ ] Scale indicator shows current status
- [ ] Calibration mode can be activated
- [ ] Line drawing works (start/end points visible)
- [ ] Distance input dialog appears
- [ ] Unit selection works (dropdown with feet/inches/meters)
- [ ] Calibration saves successfully
- [ ] Scale updates in real-time
- [ ] Copy scale button works (if multiple pages available)
- [ ] UI uses shadcn/ui components (Button, Dialog, Input, Label, Select)
- [ ] Lucide icons are visible (Ruler, Check, Copy)

---

### Test 7: Celery Task Execution

**Objective**: Verify scale detection tasks run successfully in Celery worker

**Steps**:

1. **Monitor Celery logs**:
```bash
docker logs forgex-celery-worker -f
```

2. **Trigger scale detection**:
```bash
curl -X POST http://localhost:8000/api/v1/pages/{page_id}/detect-scale
```

3. **Watch logs for**:
```
[detect_page_scale_task] Starting scale detection for page_id=...
[detect_page_scale_task] Detected scale: 1/4" = 1'-0" (confidence: 0.9)
[detect_page_scale_task] Scale detection complete
Task detect_page_scale_task succeeded
```

**Verification**:
- [ ] Task appears in Celery logs
- [ ] Task completes without errors
- [ ] Scale detection logic executes
- [ ] Database is updated with results
- [ ] Task shows success status

---

### Test 8: High Confidence Auto-Calibration

**Objective**: Verify pages with 85%+ confidence are marked as calibrated

**Test Case**: Upload a page with clear scale text like "SCALE: 1/4" = 1'-0""

**Steps**:
1. Upload a document with clear scale notation
2. Wait for OCR and auto-detection to complete
3. Check page in database or via API

**Expected**:
```json
{
  "scale_text": "1/4\" = 1'-0\"",
  "scale_value": 48.0,
  "scale_calibrated": true,
  "scale_calibration_data": {
    "best_scale": {
      "confidence": 0.9  // >= 0.85
    }
  }
}
```

**Verification**:
- [ ] scale_calibrated = true when confidence >= 0.85
- [ ] scale_calibrated = false when confidence < 0.85
- [ ] Manual calibration always sets scale_calibrated = true

---

## 📋 Quick Verification Checklist

Run through this checklist to confirm Phase 2B is complete:

### Backend
- [ ] `docker compose up -d` starts all services
- [ ] Backend API is accessible at http://localhost:8000
- [ ] Scale detection endpoint responds (202 Accepted)
- [ ] Manual calibration endpoint works (200 OK)
- [ ] Scale update endpoint works (200 OK)
- [ ] Copy scale endpoint works (200 OK)
- [ ] Celery worker processes scale detection tasks
- [ ] Database stores scale data correctly

### Frontend
- [ ] Frontend loads at http://localhost:5173
- [ ] ScaleCalibration component renders
- [ ] Calibration mode can be activated
- [ ] Line drawing works on plan viewer
- [ ] Distance input dialog appears
- [ ] Scale saves and displays correctly
- [ ] Copy scale feature works (if multiple pages)

### Integration
- [ ] Upload document → OCR → Scale detection → Database update
- [ ] Manual calibration → API call → Database update → UI refresh
- [ ] Copy scale → API call → Target page updated
- [ ] High confidence (>=85%) → auto-calibrated
- [ ] Low confidence (<85%) → needs manual calibration

---

## 🐛 Troubleshooting

### Issue: Scale detection not running

**Check**:
1. Celery worker is running: `docker compose ps | grep celery`
2. Redis is accessible: `docker compose exec api redis-cli -h redis ping`
3. OCR has completed: Check `pages.ocr_data` is not null
4. Logs: `docker logs forgex-celery-worker -f`

### Issue: Frontend component not showing

**Check**:
1. Frontend is built: `docker logs forgex-frontend`
2. Component is imported in viewer
3. Browser console for errors (F12)
4. shadcn/ui components are installed: `docker compose exec frontend npm list lucide-react`

### Issue: Calibration calculation wrong

**Check**:
1. Unit conversion: feet vs inches vs meters
2. Pixel distance is correct
3. Real distance is correct
4. Formula: `pixels_per_foot = pixel_distance / real_distance_in_feet`

### Issue: Database not updating

**Check**:
1. Database is running: `docker compose ps | grep db`
2. Migrations applied: Check `alembic_version` table
3. API has database access: Check backend logs
4. Transaction committed: No rollbacks in logs

---

## 🎯 Success Criteria

Phase 2B is **VERIFIED COMPLETE** when:

✅ All unit tests pass (test_scale_detection.py)  
✅ All 4 API endpoints work correctly  
✅ Manual calibration calculates accurate pixels/foot  
✅ Scale copying works between pages  
✅ Frontend calibration UI is functional  
✅ High-confidence scales auto-calibrate (>=85%)  
✅ Low-confidence scales require manual calibration  
✅ Database persists all scale data correctly  
✅ Celery tasks execute without errors  

---

## 📝 Testing Assignment

### I (AI) will test:
1. ✅ Unit tests (already done - test_scale_detection.py)
2. Backend API endpoints via curl (if you provide page IDs)
3. Database queries to verify persistence
4. Celery task logs to verify execution

### You (User) should test:
1. Frontend component in browser (visual/interactive elements)
2. Upload document workflow (end-to-end)
3. Manual calibration drawing tool (requires human interaction)
4. UI/UX verification (buttons, dialogs, responsiveness)
5. Cross-browser compatibility (optional)

### We can test together:
1. Integration flow: Upload → OCR → Scale Detection → UI Display
2. Debugging any issues that arise
3. Performance and edge cases

---

## 🚀 Let's Start!

**Recommended Testing Order**:

1. **Me first**: Run unit tests again to confirm baseline
2. **You**: Upload a document via frontend
3. **Me**: Check database for page IDs
4. **Me**: Test API endpoints with curl
5. **You**: Test frontend calibration UI
6. **Both**: Verify end-to-end flow works

**Ready to begin? Let me know and I'll start with step 1!**
