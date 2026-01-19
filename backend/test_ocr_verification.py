"""Verification script for Phase 1B - OCR and Text Extraction."""

import asyncio
import sys
from pathlib import Path

import structlog

# Setup logging
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ]
)

logger = structlog.get_logger()


async def verify_phase_1b():
    """Verify Phase 1B implementation."""

    logger.info("=" * 60)
    logger.info("Phase 1B Verification: OCR and Text Extraction")
    logger.info("=" * 60)

    checks_passed = 0
    checks_failed = 0

    # Check 1: Verify google-cloud-vision is installed
    logger.info("\n[1/10] Checking google-cloud-vision installation...")
    try:
        from google.cloud import vision

        logger.info("[PASS] google-cloud-vision is installed")
        checks_passed += 1
    except ImportError as e:
        logger.error(f"[FAIL] google-cloud-vision not installed: {e}")
        checks_failed += 1

    # Check 2: Verify OCR service exists
    logger.info("\n[2/10] Checking OCR service implementation...")
    try:
        from app.services.ocr_service import (
            OCRService,
            get_ocr_service,
            TextBlock,
            OCRResult,
        )

        logger.info("[PASS] OCR service module exists")
        checks_passed += 1
    except ImportError as e:
        logger.error(f"[FAIL] OCR service not found: {e}")
        checks_failed += 1

    # Check 3: Verify TitleBlockParser exists
    logger.info("\n[3/10] Checking TitleBlockParser implementation...")
    try:
        from app.services.ocr_service import TitleBlockParser, get_title_block_parser

        logger.info("[PASS] TitleBlockParser exists")
        checks_passed += 1
    except ImportError as e:
        logger.error(f"[FAIL] TitleBlockParser not found: {e}")
        checks_failed += 1

    # Check 4: Verify OCR tasks exist
    logger.info("\n[4/10] Checking OCR Celery tasks...")
    try:
        # Check if the file exists and contains the expected functions
        import inspect
        from pathlib import Path

        ocr_tasks_file = Path("app/workers/ocr_tasks.py")
        if ocr_tasks_file.exists():
            source = ocr_tasks_file.read_text()
            if (
                "process_page_ocr_task" in source
                and "process_document_ocr_task" in source
            ):
                logger.info("[PASS] OCR Celery tasks exist")
                checks_passed += 1
            else:
                logger.error("[FAIL] OCR tasks missing expected functions")
                checks_failed += 1
        else:
            logger.error("[FAIL] OCR tasks file not found")
            checks_failed += 1
    except Exception as e:
        logger.error(f"[FAIL] Error checking OCR tasks: {e}")
        checks_failed += 1

    # Check 5: Verify celery_app includes ocr_tasks
    logger.info("\n[5/10] Checking Celery app configuration...")
    try:
        from app.workers.celery_app import celery_app

        if "app.workers.ocr_tasks" in celery_app.conf.include:
            logger.info("[PASS] Celery app includes ocr_tasks")
            checks_passed += 1
        else:
            logger.error("[FAIL] Celery app does not include ocr_tasks")
            checks_failed += 1
    except Exception as e:
        logger.error(f"[FAIL] Error checking Celery config: {e}")
        checks_failed += 1

    # Check 6: Verify Page schemas exist
    logger.info("\n[6/10] Checking Page schemas...")
    try:
        from app.schemas.page import (
            PageResponse,
            PageSummaryResponse,
            PageListResponse,
            PageOCRResponse,
            ScaleUpdateRequest,
        )

        logger.info("[PASS] Page schemas exist")
        checks_passed += 1
    except ImportError as e:
        logger.error(f"[FAIL] Page schemas not found: {e}")
        checks_failed += 1

    # Check 7: Verify Page API endpoints exist
    logger.info("\n[7/10] Checking Page API endpoints...")
    try:
        from pathlib import Path

        pages_file = Path("app/api/routes/pages.py")
        if pages_file.exists():
            source = pages_file.read_text()
            endpoints = [
                "list_document_pages",
                "get_page",
                "get_page_image",
                "get_page_ocr",
                "reprocess_page_ocr",
                "search_pages",
            ]
            missing = [e for e in endpoints if f"def {e}" not in source]
            if not missing:
                logger.info("[PASS] Page API endpoints exist")
                checks_passed += 1
            else:
                logger.error(f"[FAIL] Missing endpoints: {missing}")
                checks_failed += 1
        else:
            logger.error("[FAIL] Pages routes file not found")
            checks_failed += 1
    except Exception as e:
        logger.error(f"[FAIL] Error checking Page API endpoints: {e}")
        checks_failed += 1

    # Check 8: Verify OCR patterns are defined
    logger.info("\n[8/10] Checking OCR pattern definitions...")
    try:
        from app.services.ocr_service import OCRService

        service = OCRService.__new__(OCRService)  # Don't initialize client
        assert len(service.SCALE_PATTERNS) > 0, "No scale patterns defined"
        assert len(service.SHEET_NUMBER_PATTERNS) > 0, (
            "No sheet number patterns defined"
        )
        assert len(service.TITLE_PATTERNS) > 0, "No title patterns defined"
        logger.info(
            f"[PASS] OCR patterns defined: {len(service.SCALE_PATTERNS)} scale, "
            f"{len(service.SHEET_NUMBER_PATTERNS)} sheet number, "
            f"{len(service.TITLE_PATTERNS)} title patterns"
        )
        checks_passed += 1
    except Exception as e:
        logger.error(f"[FAIL] Error checking OCR patterns: {e}")
        checks_failed += 1

    # Check 9: Verify migration file exists
    logger.info("\n[9/10] Checking full-text search migration...")
    try:
        migrations_dir = Path("alembic/versions")
        migration_files = list(migrations_dir.glob("*_add_fulltext_search.py"))
        if migration_files:
            logger.info(
                f"[PASS] Full-text search migration exists: {migration_files[0].name}"
            )
            checks_passed += 1
        else:
            logger.error("[FAIL] Full-text search migration not found")
            checks_failed += 1
    except Exception as e:
        logger.error(f"[FAIL] Error checking migration: {e}")
        checks_failed += 1

    # Check 10: Verify document processing triggers OCR
    logger.info("\n[10/10] Checking document processing OCR integration...")
    try:
        from pathlib import Path

        doc_tasks_file = Path("app/workers/document_tasks.py")
        if doc_tasks_file.exists():
            source = doc_tasks_file.read_text()
            if (
                "process_document_ocr_task" in source
                and "from app.workers.ocr_tasks" in source
            ):
                logger.info("[PASS] Document processing triggers OCR")
                checks_passed += 1
            else:
                logger.error("[FAIL] Document processing does not trigger OCR")
                checks_failed += 1
        else:
            logger.error("[FAIL] Document tasks file not found")
            checks_failed += 1
    except Exception as e:
        logger.error(f"[FAIL] Error checking document processing: {e}")
        checks_failed += 1

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Verification Summary")
    logger.info("=" * 60)
    logger.info(f"Checks passed: {checks_passed}/10")
    logger.info(f"Checks failed: {checks_failed}/10")

    if checks_failed == 0:
        logger.info("\n[SUCCESS] All checks passed! Phase 1B is ready.")
        logger.info("\nNext steps:")
        logger.info("1. Set up Google Cloud Vision credentials")
        logger.info("2. Run database migration: alembic upgrade head")
        logger.info("3. Test with actual PDF documents")
        return 0
    else:
        logger.error(
            f"\n[FAILED] {checks_failed} check(s) failed. Please fix the issues above."
        )
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(verify_phase_1b())
    sys.exit(exit_code)
