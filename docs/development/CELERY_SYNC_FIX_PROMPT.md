# Fix: Convert Celery Workers to Use Sync SQLAlchemy

## Problem
Celery workers are failing with `InterfaceError: cannot perform operation: another operation is in progress` because they're trying to use async SQLAlchemy (asyncpg) in a synchronous multiprocessing context. This is architecturally incompatible.

## Current State
- ✅ FastAPI API uses async SQLAlchemy (asyncpg) - **KEEP THIS**
- ❌ Celery workers use async SQLAlchemy (asyncpg) - **FIX THIS**
- ✅ Document upload works
- ❌ OCR processing fails with database errors

## Solution: Use Sync SQLAlchemy for Celery Workers

Convert Celery workers to use synchronous SQLAlchemy with psycopg2 driver. This is the industry-standard pattern.

## Files to Modify

### 1. `backend/app/workers/ocr_tasks.py`
**Current approach (BROKEN):**
```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

def run_async(coro):
    loop = asyncio.new_event_loop()
    return loop.run_until_complete(coro)

@celery_app.task
def process_page_ocr_task(self, page_id: str):
    result = run_async(_process_page_ocr(page_id))  # ❌ Fails
```

**New approach (WORKING):**
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Create sync engine for Celery workers
sync_engine = create_engine(
    str(settings.database_url).replace('+asyncpg', ''),  # Remove +asyncpg
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)
SyncSession = sessionmaker(bind=sync_engine)

@celery_app.task(bind=True, max_retries=3)
def process_page_ocr_task(self, page_id: str) -> dict:
    """Process OCR for a single page using SYNC database."""
    logger.info("Starting OCR processing", page_id=page_id)
    
    try:
        with SyncSession() as session:
            page_uuid = uuid.UUID(page_id)
            
            # Get page (sync query)
            page = session.query(Page).filter(Page.id == page_uuid).one_or_none()
            if not page:
                raise ValueError(f"Page not found: {page_id}")
            
            # Download image
            storage = get_storage_service()
            image_bytes = storage.download_file(page.image_key)
            
            # Run OCR
            ocr_service = get_ocr_service()
            ocr_result = ocr_service.extract_text(image_bytes)
            
            # Parse title block
            title_block_parser = get_title_block_parser()
            title_block_data = title_block_parser.parse_title_block(
                ocr_result.blocks,
                page.width,
                page.height,
            )
            
            # Update page with OCR data
            page.ocr_text = ocr_result.full_text
            page.ocr_blocks = {
                "blocks": [b.to_dict() for b in ocr_result.blocks],
                "detected_scales": ocr_result.detected_scale_texts,
                "detected_sheet_numbers": ocr_result.detected_sheet_numbers,
                "detected_titles": ocr_result.detected_titles,
                "title_block": title_block_data,
            }
            
            # Set sheet number and title
            if ocr_result.detected_sheet_numbers:
                page.sheet_number = ocr_result.detected_sheet_numbers[0]
            elif title_block_data.get("sheet_number"):
                page.sheet_number = title_block_data["sheet_number"]
            
            if ocr_result.detected_titles:
                page.title = ocr_result.detected_titles[0]
            elif title_block_data.get("sheet_title"):
                page.title = title_block_data["sheet_title"]
            
            if ocr_result.detected_scale_texts:
                page.scale_text = ocr_result.detected_scale_texts[0]
            elif title_block_data.get("scale"):
                page.scale_text = title_block_data["scale"]
            
            page.status = "completed"
            session.commit()
            
            logger.info(
                "OCR processing complete",
                page_id=page_id,
                text_length=len(ocr_result.full_text),
                blocks_count=len(ocr_result.blocks),
            )
            
            return {
                "status": "success",
                "page_id": page_id,
                "text_length": len(ocr_result.full_text),
                "sheet_number": page.sheet_number,
                "title": page.title,
                "scale_text": page.scale_text,
            }
            
    except Exception as e:
        logger.error("OCR processing failed", page_id=page_id, error=str(e))
        
        # Update page with error
        try:
            with SyncSession() as session:
                page = session.query(Page).filter(Page.id == uuid.UUID(page_id)).one_or_none()
                if page:
                    page.status = "error"
                    page.processing_error = str(e)
                    session.commit()
        except Exception as update_error:
            logger.error("Failed to update page error", error=str(update_error))
        
        raise self.retry(exc=e, countdown=30)


@celery_app.task(bind=True)
def process_document_ocr_task(self, document_id: str) -> dict:
    """Process OCR for all pages in a document using SYNC database."""
    logger.info("Starting document OCR", document_id=document_id)
    
    doc_uuid = uuid.UUID(document_id)
    
    with SyncSession() as session:
        # Get all pages for document (sync query)
        pages = session.query(Page.id).filter(Page.document_id == doc_uuid).all()
        page_ids = [str(page.id) for page in pages]
    
    # Queue OCR tasks for each page
    for page_id in page_ids:
        process_page_ocr_task.delay(page_id)
    
    return {
        "status": "queued",
        "document_id": document_id,
        "pages_queued": len(page_ids),
    }
```

### 2. `backend/app/workers/document_tasks.py`
**Convert to sync if it uses async database operations.**

Check if it has async database calls. If so, convert them to use `SyncSession` similar to above.

### 3. `backend/requirements.txt`
**Ensure psycopg2-binary is installed:**
```
psycopg2-binary>=2.9.9
```

## Implementation Steps

1. **Read current `backend/app/workers/ocr_tasks.py`** to understand the full structure
2. **Create sync engine and session** at module level
3. **Remove all async/await** from Celery task functions
4. **Replace `async with AsyncSession()` with `with SyncSession()`**
5. **Replace `await session.execute()` with `session.query()`**
6. **Replace `await session.commit()` with `session.commit()`**
7. **Remove the `run_async()` helper function** (no longer needed)
8. **Test the changes:**
   ```bash
   cd docker
   docker compose restart worker
   docker compose logs -f worker
   ```
9. **Upload a PDF** and verify OCR processing works

## Verification Checklist

After implementation:
- [ ] Worker starts without errors
- [ ] Upload a PDF successfully
- [ ] Worker logs show OCR processing starting
- [ ] No `InterfaceError` or `MissingGreenlet` errors
- [ ] Page records updated with OCR data
- [ ] Can query `/api/v1/pages/{page_id}/ocr` and get results

## Important Notes

- **DO NOT change FastAPI routes** - they should stay async
- **DO NOT change `backend/app/database.py`** - async engine is for API
- **ONLY change Celery worker files** to use sync database
- **Keep the API async** - this is the correct architecture

## Expected Outcome

✅ Celery workers will process OCR tasks reliably
✅ No database connection conflicts
✅ Industry-standard architecture (async API + sync workers)
✅ Scales horizontally by adding more worker containers
✅ Simpler, more maintainable code

## Current Project State

- Phase 1B (OCR) is implemented but broken due to async/sync mismatch
- Document upload works (API is async - correct)
- OCR processing fails (workers are async - incorrect)
- Google Cloud Vision is configured and working
- All other services (PostgreSQL, Redis, MinIO) are healthy

## Commands to Run After Fix

```bash
# Restart worker with new code
cd docker
docker compose restart worker

# Watch logs
docker compose logs -f worker

# Test upload (in browser)
# Go to http://localhost:5173
# Upload a PDF
# Should see successful OCR processing in worker logs
```
