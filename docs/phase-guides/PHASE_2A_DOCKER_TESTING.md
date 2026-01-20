# Phase 2A: Docker Testing Instructions

## Overview

This guide provides step-by-step instructions for testing Phase 2A (Page Classification) in the Docker container environment.

---

## Prerequisites

1. **Docker and Docker Compose** installed and running
2. **LLM Provider API Keys** - At least one required:
   - Anthropic API key (recommended)
   - OpenAI API key
   - Google AI API key
   - xAI API key

---

## Step 1: Update Environment Variables

Add LLM provider API keys to your `.env` file or `docker-env.example`:

```bash
# LLM Provider API Keys (at least one required)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_AI_API_KEY=...
XAI_API_KEY=...

# LLM Provider Configuration
DEFAULT_LLM_PROVIDER=anthropic
LLM_FALLBACK_PROVIDERS=openai,google

# Optional: Per-task provider overrides
LLM_PROVIDER_PAGE_CLASSIFICATION=
LLM_PROVIDER_SCALE_DETECTION=
LLM_PROVIDER_ELEMENT_DETECTION=
LLM_PROVIDER_MEASUREMENT=
```

**Important:** Copy your `.env` file or update `docker-env.example` before rebuilding.

---

## Step 2: Rebuild Docker Containers

Phase 2A adds new Python dependencies and code, so you need to rebuild:

### 2.1 Rebuild Backend API Container

```bash
# From project root
cd docker
docker compose build api
```

**Why rebuild?**
- New Python packages: `anthropic`, `openai`, `google-generativeai` (already in requirements.txt)
- New service files: `llm_client.py`, `page_classifier.py`
- Updated routes: `pages.py`, `settings.py`
- Updated models: `page.py`

### 2.2 Rebuild Celery Worker Container

```bash
docker compose build worker
```

**Why rebuild?**
- New worker tasks: `classification_tasks.py`
- Updated celery_app.py includes

### 2.3 Rebuild Frontend Container (Optional)

```bash
docker compose build frontend
```

**Why rebuild?**
- New components: `LLMProviderSelector.tsx`, `PageBrowser.tsx`

### 2.4 Rebuild All at Once

```bash
# Rebuild everything
docker compose build

# Or rebuild specific services
docker compose build api worker frontend
```

---

## Step 3: Run Database Migration

The new classification fields require a database migration:

```bash
# Run migration inside API container
docker compose exec api alembic upgrade head
```

**Expected output:**
```
INFO  [alembic.runtime.migration] Running upgrade d707bfb8a266 -> 576b3ce9ef71, add_classification_fields_to_pages
```

**Verify migration:**
```bash
# Check current migration version
docker compose exec api alembic current
```

---

## Step 4: Restart Services

Restart containers to pick up new code:

```bash
# Restart all services
docker compose restart

# Or restart specific services
docker compose restart api worker
```

**Or start fresh:**
```bash
docker compose down
docker compose up -d
```

---

## Step 5: Verify Services Are Running

### 5.1 Check API Health

```bash
curl http://localhost:8000/api/v1/health
```

Expected: `{"status":"healthy"}`

### 5.2 Check LLM Providers Endpoint

```bash
curl http://localhost:8000/api/v1/settings/llm/providers
```

Expected: JSON with provider details including availability status

### 5.3 Check Celery Worker Logs

```bash
docker compose logs worker | tail -20
```

Look for: `celery@... ready` and no import errors

---

## Step 6: Test Classification Endpoints

### 6.1 Upload a Test Document

```bash
# Upload a PDF (replace PROJECT_ID with actual UUID)
curl -X POST \
  http://localhost:8000/api/v1/projects/{PROJECT_ID}/documents \
  -F "file=@path/to/test-plan.pdf"
```

**Note:** Wait for document processing and OCR to complete before classifying.

### 6.2 Get Document Pages

```bash
# List pages for the document
curl http://localhost:8000/api/v1/documents/{DOCUMENT_ID}/pages
```

### 6.3 Classify a Single Page

```bash
# Classify a specific page (replace PAGE_ID)
curl -X POST \
  http://localhost:8000/api/v1/pages/{PAGE_ID}/classify \
  -H "Content-Type: application/json" \
  -d '{"provider": "anthropic"}'
```

**Response:**
```json
{
  "task_id": "abc123...",
  "message": "Classification started for page {page_id} using anthropic"
}
```

### 6.4 Classify All Pages in Document

```bash
# Classify all pages (replace DOCUMENT_ID)
curl -X POST \
  http://localhost:8000/api/v1/documents/{DOCUMENT_ID}/classify \
  -H "Content-Type: application/json" \
  -d '{"provider": "anthropic"}'
```

**Response:**
```json
{
  "document_id": "...",
  "pages_queued": 5,
  "task_ids": ["task1", "task2", ...]
}
```

### 6.5 Check Classification Results

```bash
# Get classification for a page (replace PAGE_ID)
curl http://localhost:8000/api/v1/pages/{PAGE_ID}/classification
```

**Expected Response:**
```json
{
  "page_id": "...",
  "classification": "Structural:Plan",
  "confidence": 0.95,
  "concrete_relevance": "high",
  "metadata": {
    "discipline": "Structural",
    "discipline_confidence": 0.95,
    "page_type": "Plan",
    "page_type_confidence": 0.90,
    "concrete_relevance": "high",
    "concrete_elements": ["slab", "foundation wall"],
    "description": "Foundation plan showing footings and grade beams",
    "llm_provider": "anthropic",
    "llm_model": "claude-3-5-sonnet-20241022",
    "llm_latency_ms": 5234.5
  }
}
```

---

## Step 7: Monitor Classification Tasks

### 7.1 Check Celery Worker Logs

```bash
# Watch worker logs in real-time
docker compose logs -f worker
```

**Look for:**
- `Starting page classification` - Task started
- `Page classification complete` - Task succeeded
- `Page classification failed` - Task failed (will retry)

### 7.2 Check Task Status (if using Celery monitoring)

```bash
# If Flower is running
# Visit http://localhost:5555 to see task status
```

---

## Step 8: Test Frontend Components

### 8.1 Access Frontend

```bash
# Frontend should be available at
http://localhost:5173
```

### 8.2 Test LLMProviderSelector

1. Navigate to a page that uses classification
2. Look for provider selector dropdown
3. Verify providers are listed
4. Hover over providers to see tooltips with details

### 8.3 Test PageBrowser

1. Navigate to document pages view
2. Verify filters are visible:
   - Discipline filter
   - Page Type filter
   - Concrete Relevance filter
3. Test filtering:
   - Select "Structural" discipline → only S-prefixed pages shown
   - Select "high" concrete → only high-concrete pages shown
4. Verify visual highlights:
   - High-concrete pages have red border
   - Confidence percentages displayed
   - Discipline badges (A, S, C, M, E, P, L, G) shown

---

## Troubleshooting

### Issue: "ANTHROPIC_API_KEY not configured"

**Solution:**
1. Check `.env` file has `ANTHROPIC_API_KEY=...`
2. Restart API container: `docker compose restart api`
3. Verify environment variable: `docker compose exec api env | grep ANTHROPIC`

### Issue: "Provider 'anthropic' not available"

**Solution:**
1. Check API key is valid
2. Verify provider is in `available_providers`:
   ```bash
   curl http://localhost:8000/api/v1/settings/llm/providers
   ```
3. Check API container logs for initialization errors

### Issue: Classification tasks not running

**Solution:**
1. Check Celery worker is running: `docker compose ps worker`
2. Check worker logs: `docker compose logs worker`
3. Verify Redis is running: `docker compose ps redis`
4. Check task is queued: Look for task ID in response

### Issue: "Migration already applied" or "No such revision"

**Solution:**
```bash
# Check current migration
docker compose exec api alembic current

# Check migration history
docker compose exec api alembic history

# If needed, downgrade and upgrade
docker compose exec api alembic downgrade -1
docker compose exec api alembic upgrade head
```

### Issue: Frontend components not showing

**Solution:**
1. Rebuild frontend: `docker compose build frontend`
2. Restart frontend: `docker compose restart frontend`
3. Check browser console for errors
4. Verify API is accessible from frontend

### Issue: "All LLM providers failed"

**Solution:**
1. Check at least one API key is configured
2. Verify API keys are valid (test with curl to provider API)
3. Check network connectivity from container
4. Review provider-specific error messages in logs

---

## Performance Testing

### Test Classification Speed

```bash
# Time a single page classification
time curl -X POST \
  http://localhost:8000/api/v1/pages/{PAGE_ID}/classify \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Expected:** 5-30 seconds per page depending on provider

### Test Batch Classification

```bash
# Classify a document with multiple pages
curl -X POST \
  http://localhost:8000/api/v1/documents/{DOCUMENT_ID}/classify \
  -H "Content-Type: application/json" \
  -d '{}'

# Monitor worker logs to see parallel processing
docker compose logs -f worker
```

---

## Verification Checklist

After completing all steps, verify:

- [ ] API container rebuilt and running
- [ ] Worker container rebuilt and running
- [ ] Frontend container rebuilt and running (if using)
- [ ] Database migration applied successfully
- [ ] LLM providers endpoint returns available providers
- [ ] Can classify a single page
- [ ] Can classify all pages in document
- [ ] Classification results stored in database
- [ ] Frontend filters work correctly
- [ ] High-concrete pages highlighted visually
- [ ] Provider fallback works (test by disabling primary provider)

---

## Quick Test Script

Save this as `test-phase-2a.sh`:

```bash
#!/bin/bash

echo "Testing Phase 2A Classification..."

# Check API health
echo "1. Checking API health..."
curl -s http://localhost:8000/api/v1/health | jq .

# Check providers
echo "2. Checking LLM providers..."
curl -s http://localhost:8000/api/v1/settings/llm/providers | jq .

# Check migration
echo "3. Checking database migration..."
docker compose exec -T api alembic current

echo "Done! Now test classification endpoints manually."
```

Run: `chmod +x test-phase-2a.sh && ./test-phase-2a.sh`

---

## Next Steps

After successful testing:

1. **Monitor Performance:** Track classification latency and costs
2. **Test Accuracy:** Verify classifications match expected results
3. **Test Fallback:** Disable primary provider to test fallback
4. **Scale Testing:** Test with large documents (50+ pages)
5. **Integration:** Integrate auto-classification after OCR completion

---

## Summary

**What to Rebuild:**
- ✅ `api` container (new services, routes, models)
- ✅ `worker` container (new tasks)
- ✅ `frontend` container (new components)

**What to Run:**
- ✅ Database migration: `alembic upgrade head`
- ✅ Restart services: `docker compose restart`

**What to Test:**
- ✅ LLM providers endpoint
- ✅ Single page classification
- ✅ Batch classification
- ✅ Frontend filters and UI

**Documentation:**
- See `docs/phase-guides/PHASE_2A_COMPLETE.md` for full implementation details
- See `PHASE_2A_VERIFICATION.md` for verification checklist
