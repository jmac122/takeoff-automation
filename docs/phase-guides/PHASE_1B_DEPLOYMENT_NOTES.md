# Phase 1B Deployment Notes

## ⚠️ IMPORTANT: Docker-First Development

**This project uses Docker for everything.** All commands should be run inside Docker containers, not on your local machine.

**CRITICAL:** 
1. All docker commands must be run from the `docker/` folder!
2. The `.env` file must be in `docker/.env` (NOT project root!)

```bash
cd docker                                        # Navigate to docker folder
docker compose exec api python script.py        # Now this works
```

✅ **Correct:** `cd docker && docker compose exec api python script.py`  
✅ **Correct:** Environment file at `docker/.env`  
❌ **Wrong:** `python script.py` (don't install Python locally)  
❌ **Wrong:** `docker compose up -d` (from project root - won't work!)  
❌ **Wrong:** `.env` in project root (Docker Compose won't find it!)

See [Docker Workflow Guide](../development/DOCKER_WORKFLOW.md) for complete instructions.

---

## ✅ Completed and Committed

**Date:** January 19, 2026  
**Commit:** `46a5335` - feat(phase-1b): Implement OCR and text extraction  
**Status:** Pushed to `main` branch

---

## 📦 What Was Delivered

### Core Implementation

1. **OCR Service** (`backend/app/services/ocr_service.py`)
   - Google Cloud Vision integration
   - Pattern detection (6 scale, 3 sheet number, 2 title patterns)
   - Title block parser
   - Text block extraction with bounding boxes

2. **Celery Tasks** (`backend/app/workers/ocr_tasks.py`)
   - `process_page_ocr_task` - Single page OCR
   - `process_document_ocr_task` - Batch OCR for documents
   - Automatic retry logic (3 attempts)

3. **API Endpoints** (6 new endpoints in `backend/app/api/routes/pages.py`)
   - List pages with OCR metadata
   - Get page details and OCR data
   - Reprocess OCR on demand
   - Full-text search across pages

4. **Database Migration** (`d707bfb8a266_add_fulltext_search.py`)
   - GIN index for full-text search
   - Trigram index for fuzzy matching
   - pg_trgm extension

5. **Comprehensive Documentation**
   - OCR API reference
   - OCR service implementation guide
   - Database schema updates
   - Phase 1B completion guide

### Files Changed

**Added (8 files):**
- `backend/app/services/ocr_service.py` (333 lines)
- `backend/app/workers/ocr_tasks.py` (178 lines)
- `backend/alembic/versions/d707bfb8a266_add_fulltext_search.py` (44 lines)
- `backend/test_ocr_verification.py` (243 lines)
- `docs/api/OCR_API.md` (comprehensive API docs)
- `docs/services/OCR_SERVICE.md` (implementation guide)
- `docs/phase-guides/PHASE_1B_COMPLETE.md` (365 lines)
- `docs/phase-guides/PHASE_1B_SUMMARY.md` (343 lines)

**Modified (10 files):**
- `backend/app/api/routes/pages.py` - Added 6 endpoints
- `backend/app/schemas/page.py` - Added OCR schemas
- `backend/app/workers/celery_app.py` - Added ocr_tasks
- `backend/app/workers/document_tasks.py` - Trigger OCR
- `docker-env.example` - Google Cloud Vision config
- `docs/README.md` - Updated index
- `docs/api/API_REFERENCE.md` - Added Phase 1B
- `docs/database/DATABASE_SCHEMA.md` - OCR schema
- `README.md` - Updated status
- `STATUS.md` - Phase 1B complete

**Total:** 3,045 insertions, 66 deletions

---

## 🚀 Deployment Steps

### 1. Set Up Google Cloud Vision (REQUIRED)

Before deploying, you must configure Google Cloud Vision:

```bash
# 1. Create Google Cloud project
# 2. Enable Cloud Vision API
# 3. Create service account with Vision API access
# 4. Download JSON key file
# 5. Set environment variable

export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

**Or in Docker:**
```bash
# Add to .env file
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

### 2. Run Database Migration

```bash
# Navigate to docker folder
cd docker

# Apply full-text search indexes (inside Docker)
docker compose exec api alembic upgrade head
```

**Expected output:**
```
INFO  [alembic.runtime.migration] Running upgrade b01e3b57e974 -> d707bfb8a266, add_fulltext_search
```

### 3. Rebuild and Restart Services

```bash
# Make sure you're in docker folder
cd docker

# Rebuild containers with new code
docker compose build api worker

# Restart services
docker compose up -d
```

**Note:** Dependencies are already in `requirements.txt` and installed during Docker build. No local installation needed.

### 4. Verify Deployment

```bash
# Navigate to docker folder
cd docker

# Run verification script (inside Docker)
docker compose exec api python test_ocr_verification.py
```

**Expected:** All 10 checks pass ✅

---

## 🧪 Testing the Implementation

### Test 1: Upload Document with OCR

```bash
# All these commands run on your local machine (curl talks to Docker containers)

# 1. Upload a PDF
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@test-plan.pdf" \
  -F "project_id=YOUR_PROJECT_ID"

# 2. Wait for processing (check status)
curl http://localhost:8000/api/v1/documents/DOCUMENT_ID

# 3. List pages with OCR data
curl http://localhost:8000/api/v1/documents/DOCUMENT_ID/pages

# 4. Get OCR details for a page
curl http://localhost:8000/api/v1/pages/PAGE_ID/ocr
```

### Test 2: Full-Text Search

```bash
# Search for "foundation" across all pages
curl "http://localhost:8000/api/v1/projects/PROJECT_ID/search?q=foundation"
```

### Test 3: Reprocess OCR

```bash
# Reprocess OCR for a specific page
curl -X POST http://localhost:8000/api/v1/pages/PAGE_ID/reprocess-ocr
```

---

## 📊 Verification Checklist

Run through this checklist after deployment:

- [ ] Google Cloud Vision credentials configured
- [ ] Database migration applied (`alembic current` shows `d707bfb8a266`)
- [ ] All services running (API, Celery, Redis, PostgreSQL)
- [ ] Verification script passes (10/10 checks)
- [ ] Upload test document successfully
- [ ] OCR data appears in pages
- [ ] Scale text detected correctly
- [ ] Sheet numbers extracted
- [ ] Full-text search returns results
- [ ] API documentation accessible at `/api/docs`

---

## 🔧 Configuration

### Environment Variables

**Required for Phase 1B:**
```bash
# Google Cloud Vision (REQUIRED)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# Existing variables (from Phase 1A)
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://...
CELERY_BROKER_URL=redis://...
STORAGE_ENDPOINT=minio:9000
STORAGE_ACCESS_KEY=minioadmin
STORAGE_SECRET_KEY=minioadmin
```

### Docker Compose

No changes needed to `docker-compose.yml` - just rebuild:

```bash
docker compose build api worker
docker compose up -d
```

---

## 📈 Performance Expectations

### OCR Processing Time
- **Single Page:** 1-3 seconds (Google Cloud Vision)
- **10-page document:** ~15-30 seconds (parallel processing)
- **100-page document:** ~2-5 minutes (parallel processing)

### Search Performance
- **Query Time:** <100ms for typical searches
- **Index Type:** GIN (Generalized Inverted Index)

### Cost (Google Cloud Vision)
- **Free Tier:** 1,000 images/month
- **Paid:** $1.50 per 1,000 images
- **Example:** 100-page document = $0.15

---

## 🐛 Troubleshooting

### Issue: OCR not running

**Check:**
```bash
# 1. Verify Celery worker is running
docker compose logs worker

# 2. Check Redis connection (inside Docker)
docker compose exec redis redis-cli ping

# 3. Verify Google Cloud credentials (inside Docker)
docker compose exec api env | grep GOOGLE_APPLICATION_CREDENTIALS
```

### Issue: Search not working

**Check:**
```bash
# 1. Verify migration applied (inside Docker)
docker compose exec api alembic current
# Should show: d707bfb8a266

# 2. Check PostgreSQL extensions (inside Docker)
docker compose exec db psql -U forgex -d forgex -c "SELECT * FROM pg_extension WHERE extname = 'pg_trgm';"
```

### Issue: Pattern not detected

**Check:**
- OCR text quality (view via `/pages/{id}/ocr`)
- Pattern format matches expected (see OCR_SERVICE.md)
- Consider adding custom patterns to `OCRService.SCALE_PATTERNS`

---

## 📚 Documentation Links

- **[Phase 1B Complete Guide](docs/phase-guides/PHASE_1B_COMPLETE.md)** - Full implementation details
- **[OCR API Reference](docs/api/OCR_API.md)** - API endpoint documentation
- **[OCR Service Guide](docs/services/OCR_SERVICE.md)** - Service implementation
- **[Database Schema](docs/database/DATABASE_SCHEMA.md)** - Schema updates

---

## 🎯 Next Steps

### Immediate Actions
1. ✅ Set up Google Cloud Vision credentials
2. ✅ Run database migration
3. ✅ Test with actual construction plans
4. ⏳ Monitor OCR accuracy and costs

### Phase 2A: Page Classification
Ready to proceed to Phase 2A for AI-powered page classification.

**Read:** `plans/04-PAGE-CLASSIFICATION.md`

---

## 📝 Notes

### Known Limitations
1. **Google Cloud Vision Required** - Cannot run without credentials
2. **Title Block Location** - Assumes bottom-right 30% of page
3. **Pattern Matching** - Regex-based, may miss non-standard formats
4. **English Only** - Currently configured for English text

### Future Improvements
- Add more scale patterns for international standards
- Support custom title block templates
- Add OCR confidence thresholds
- Implement OCR result caching

---

**Deployment Status:** Ready for Production ✅  
**Last Updated:** January 19, 2026  
**Commit:** `46a5335`
