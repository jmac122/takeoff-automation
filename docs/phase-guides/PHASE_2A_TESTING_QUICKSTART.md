# Phase 2A Testing - Quick Start Guide

## TL;DR

1. **Add LLM API keys** to `.env` file
2. **Rebuild containers:** `docker compose -f docker/docker-compose.yml build api worker frontend`
3. **Run migration:** `docker compose -f docker/docker-compose.yml exec api alembic upgrade head`
4. **Restart services:** `docker compose -f docker/docker-compose.yml restart`
5. **Test:** Upload document → Classify pages → Check results

---

## What Needs to Be Rebuilt

### ✅ Must Rebuild:
- **`api` container** - New services (`llm_client.py`, `page_classifier.py`), updated routes/models
- **`worker` container** - New tasks (`classification_tasks.py`)

### ✅ Optional Rebuild:
- **`frontend` container** - New components (`LLMProviderSelector.tsx`, `PageBrowser.tsx`)

### ❌ No Rebuild Needed:
- `db` container - No changes
- `redis` container - No changes  
- `minio` container - No changes

---

## Quick Commands

```bash
# From project root directory

# 1. Add API keys to .env (create if doesn't exist)
echo "ANTHROPIC_API_KEY=sk-ant-..." >> .env
echo "DEFAULT_LLM_PROVIDER=anthropic" >> .env

# 2. Rebuild containers
cd docker
docker compose build api worker frontend

# 3. Run migration
docker compose exec api alembic upgrade head

# 4. Restart services
docker compose restart api worker frontend

# 5. Verify
curl http://localhost:8000/api/v1/settings/llm/providers
```

---

## Testing Workflow

### 1. Upload Document
```bash
curl -X POST \
  http://localhost:8000/api/v1/projects/{PROJECT_ID}/documents \
  -F "file=@test-plan.pdf"
```

### 2. Wait for OCR (check document status)
```bash
curl http://localhost:8000/api/v1/documents/{DOCUMENT_ID}
```

### 3. Classify Pages
```bash
# Single page
curl -X POST \
  http://localhost:8000/api/v1/pages/{PAGE_ID}/classify \
  -H "Content-Type: application/json" \
  -d '{"provider": "anthropic"}'

# All pages
curl -X POST \
  http://localhost:8000/api/v1/documents/{DOCUMENT_ID}/classify \
  -H "Content-Type: application/json" \
  -d '{}'
```

### 4. Check Results
```bash
curl http://localhost:8000/api/v1/pages/{PAGE_ID}/classification
```

### 5. Monitor Worker
```bash
docker compose logs -f worker
```

---

## Environment Variables Required

Add to `.env` file in project root:

```bash
# At least one LLM provider API key required
ANTHROPIC_API_KEY=sk-ant-...
# OR
OPENAI_API_KEY=sk-...
# OR  
GOOGLE_AI_API_KEY=...
# OR
XAI_API_KEY=...

# Optional configuration
DEFAULT_LLM_PROVIDER=anthropic
LLM_FALLBACK_PROVIDERS=openai,google
```

---

## Troubleshooting

**"ANTHROPIC_API_KEY not configured"**
→ Add API key to `.env` and restart: `docker compose restart api`

**"Provider not available"**
→ Check API key is valid and restart container

**"Migration error"**
→ Check current migration: `docker compose exec api alembic current`

**Classification not running**
→ Check worker logs: `docker compose logs worker`

---

## Full Documentation

- **Complete Testing Guide:** `docs/phase-guides/PHASE_2A_DOCKER_TESTING.md`
- **Implementation Details:** `docs/phase-guides/PHASE_2A_COMPLETE.md`
- **Verification Checklist:** `PHASE_2A_VERIFICATION.md`

---

## Expected Results

✅ API returns available providers  
✅ Classification tasks queue successfully  
✅ Pages get classified with discipline/page_type  
✅ Concrete relevance set (high/medium/low/none)  
✅ Classification metadata stored in database  
✅ Frontend filters work correctly  

---

**Ready to test!** 🚀
