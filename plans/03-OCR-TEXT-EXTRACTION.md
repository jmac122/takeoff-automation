# Phase 1B: OCR and Text Extraction
## Text Recognition, Title Block Parsing, and Metadata Extraction

> **Duration**: Weeks 4-6
> **Prerequisites**: Phase 1A complete (document ingestion working)
> **Outcome**: Automatic text extraction and title block parsing for all pages

---

## Context for LLM Assistant

You are implementing the OCR (Optical Character Recognition) system for a construction takeoff platform. This phase adds:
- Google Cloud Vision API integration for OCR
- Text extraction from plan pages
- Title block detection and parsing
- Sheet number extraction
- Scale text detection (for later calibration)
- Full-text search capability

### Why OCR Matters
Construction plans contain critical text information:
- Sheet numbers (A1.01, S-101, etc.)
- Sheet titles ("FOUNDATION PLAN", "SITE PLAN")
- Scale notations ("1/4\" = 1'-0\"", "SCALE: 1\" = 20'")
- Dimensions, notes, and specifications
- Project information in title blocks

---

## Task List

### Task 3.1: Google Cloud Vision Setup

Install and configure Google Cloud Vision:

```bash
# Already in requirements.txt, but ensure it's installed
pip install google-cloud-vision
```

Create service account credentials:
1. Go to Google Cloud Console
2. Create a new project or select existing
3. Enable Cloud Vision API
4. Create a service account with Vision API access
5. Download JSON key file
6. Set `GOOGLE_APPLICATION_CREDENTIALS` in `.env`

---

### Task 3.2: OCR Service Implementation

Create `backend/app/services/ocr_service.py`:

```python
"""OCR service using Google Cloud Vision."""

import io
import re
from dataclasses import dataclass
from typing import Any

from google.cloud import vision
import structlog

from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


@dataclass
class TextBlock:
    """Represents a detected text block with position."""
    text: str
    confidence: float
    bounding_box: dict[str, int]  # x, y, width, height
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "confidence": self.confidence,
            "bounding_box": self.bounding_box,
        }


@dataclass
class OCRResult:
    """Complete OCR result for a page."""
    full_text: str
    blocks: list[TextBlock]
    detected_scale_texts: list[str]
    detected_sheet_numbers: list[str]
    detected_titles: list[str]


class OCRService:
    """Service for extracting text from images using Google Cloud Vision."""
    
    # Patterns for construction plan elements
    SCALE_PATTERNS = [
        # Standard architectural scales
        r'(?:SCALE[:\s]*)?(\d+(?:/\d+)?["\']?\s*=\s*\d+[\'"]\s*-?\s*\d*[\'""]?)',
        r'(\d+/\d+"\s*=\s*1\'-0")',  # 1/4" = 1'-0"
        r'(\d+"\s*=\s*\d+\')',  # 1" = 10'
        r'SCALE[:\s]*1[:\s]*(\d+)',  # SCALE: 1:100
        r'(\d+:\d+)\s*SCALE',
        r'NTS|NOT\s*TO\s*SCALE',  # Not to scale
    ]
    
    SHEET_NUMBER_PATTERNS = [
        r'\b([A-Z]{1,2}[-.]?\d{1,3}(?:\.\d{1,2})?)\b',  # A1.01, S-101, M101
        r'SHEET\s*(?:NO\.?|NUMBER|#)?\s*:?\s*([A-Z0-9.-]+)',
        r'DWG\.?\s*(?:NO\.?)?:?\s*([A-Z0-9.-]+)',
    ]
    
    TITLE_PATTERNS = [
        r'^([A-Z][A-Z\s]{3,40}(?:PLAN|ELEVATION|SECTION|DETAIL|SCHEDULE))$',
        r'TITLE[:\s]*([A-Z][A-Z\s]+)',
    ]

    def __init__(self):
        self.client = vision.ImageAnnotatorClient()

    def extract_text(self, image_bytes: bytes) -> OCRResult:
        """Extract text from an image.
        
        Args:
            image_bytes: Image file contents
            
        Returns:
            OCRResult with full text and structured blocks
        """
        image = vision.Image(content=image_bytes)
        
        # Use document text detection for better layout understanding
        response = self.client.document_text_detection(image=image)
        
        if response.error.message:
            raise RuntimeError(f"Vision API error: {response.error.message}")
        
        # Extract full text
        full_text = ""
        if response.full_text_annotation:
            full_text = response.full_text_annotation.text
        
        # Extract individual blocks with positions
        blocks: list[TextBlock] = []
        
        if response.full_text_annotation:
            for page in response.full_text_annotation.pages:
                for block in page.blocks:
                    block_text = ""
                    confidence = block.confidence
                    
                    for paragraph in block.paragraphs:
                        for word in paragraph.words:
                            word_text = "".join(
                                symbol.text for symbol in word.symbols
                            )
                            block_text += word_text + " "
                    
                    block_text = block_text.strip()
                    
                    if block_text:
                        # Get bounding box
                        vertices = block.bounding_box.vertices
                        bbox = {
                            "x": min(v.x for v in vertices),
                            "y": min(v.y for v in vertices),
                            "width": max(v.x for v in vertices) - min(v.x for v in vertices),
                            "height": max(v.y for v in vertices) - min(v.y for v in vertices),
                        }
                        
                        blocks.append(TextBlock(
                            text=block_text,
                            confidence=confidence,
                            bounding_box=bbox,
                        ))
        
        # Extract specific elements
        detected_scales = self._extract_scales(full_text)
        detected_sheet_numbers = self._extract_sheet_numbers(full_text, blocks)
        detected_titles = self._extract_titles(full_text, blocks)
        
        return OCRResult(
            full_text=full_text,
            blocks=blocks,
            detected_scale_texts=detected_scales,
            detected_sheet_numbers=detected_sheet_numbers,
            detected_titles=detected_titles,
        )

    def _extract_scales(self, text: str) -> list[str]:
        """Extract scale notations from text."""
        scales = []
        
        for pattern in self.SCALE_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            scales.extend(matches)
        
        # Clean and deduplicate
        cleaned = []
        for scale in scales:
            if isinstance(scale, tuple):
                scale = scale[0] if scale else ""
            scale = scale.strip()
            if scale and scale not in cleaned:
                cleaned.append(scale)
        
        return cleaned

    def _extract_sheet_numbers(
        self,
        text: str,
        blocks: list[TextBlock],
    ) -> list[str]:
        """Extract sheet numbers from text."""
        sheet_numbers = []
        
        for pattern in self.SHEET_NUMBER_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            sheet_numbers.extend(matches)
        
        # Also check title block area (typically bottom-right corner)
        # Look for blocks in bottom 20% of page
        if blocks:
            max_y = max(b.bounding_box["y"] + b.bounding_box["height"] for b in blocks)
            title_block_threshold = max_y * 0.8
            
            for block in blocks:
                if block.bounding_box["y"] > title_block_threshold:
                    for pattern in self.SHEET_NUMBER_PATTERNS:
                        matches = re.findall(pattern, block.text, re.IGNORECASE)
                        sheet_numbers.extend(matches)
        
        # Clean and deduplicate
        cleaned = list(set(s.strip().upper() for s in sheet_numbers if s.strip()))
        return cleaned

    def _extract_titles(
        self,
        text: str,
        blocks: list[TextBlock],
    ) -> list[str]:
        """Extract sheet titles from text."""
        titles = []
        
        # Look for common title patterns
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            for pattern in self.TITLE_PATTERNS:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    title = match.group(1) if match.lastindex else match.group(0)
                    titles.append(title.strip())
        
        # Look for large text blocks (likely titles)
        if blocks:
            avg_height = sum(b.bounding_box["height"] for b in blocks) / len(blocks)
            
            for block in blocks:
                # Titles are usually larger text
                if block.bounding_box["height"] > avg_height * 1.5:
                    text_upper = block.text.upper()
                    # Check if it looks like a title
                    if any(keyword in text_upper for keyword in 
                           ["PLAN", "ELEVATION", "SECTION", "DETAIL", "SCHEDULE", "FOUNDATION"]):
                        titles.append(block.text.strip())
        
        # Clean and deduplicate
        cleaned = list(set(t for t in titles if len(t) > 3))
        return cleaned


class TitleBlockParser:
    """Parser for extracting structured data from title blocks."""
    
    def parse_title_block(
        self,
        blocks: list[TextBlock],
        page_width: int,
        page_height: int,
    ) -> dict[str, Any]:
        """Parse title block from OCR blocks.
        
        Title blocks are typically in the bottom-right corner.
        
        Returns:
            Dictionary with extracted title block fields
        """
        result = {
            "sheet_number": None,
            "sheet_title": None,
            "project_name": None,
            "project_number": None,
            "date": None,
            "revision": None,
            "drawn_by": None,
            "checked_by": None,
            "scale": None,
        }
        
        if not blocks:
            return result
        
        # Filter to title block region (bottom-right 30% x 30%)
        title_block_x = page_width * 0.7
        title_block_y = page_height * 0.7
        
        title_block_blocks = [
            b for b in blocks
            if (b.bounding_box["x"] + b.bounding_box["width"]/2 > title_block_x
                and b.bounding_box["y"] + b.bounding_box["height"]/2 > title_block_y)
        ]
        
        # Combine all title block text
        title_block_text = " ".join(b.text for b in title_block_blocks)
        
        # Extract fields using patterns
        patterns = {
            "sheet_number": [
                r'SHEET\s*(?:NO\.?)?[:\s]*([A-Z]?\d+(?:\.\d+)?)',
                r'DWG\.?\s*(?:NO\.?)?[:\s]*([A-Z0-9.-]+)',
                r'\b([A-Z]\d{1,2}\.\d{2})\b',
            ],
            "project_number": [
                r'PROJECT\s*(?:NO\.?|NUMBER)?[:\s]*(\d+[-\d]*)',
                r'JOB\s*(?:NO\.?)?[:\s]*(\d+[-\d]*)',
            ],
            "date": [
                r'DATE[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
                r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
            ],
            "revision": [
                r'REV(?:ISION)?\.?[:\s]*([A-Z0-9]+)',
            ],
            "scale": [
                r'SCALE[:\s]*([^,\n]+)',
            ],
        }
        
        for field, field_patterns in patterns.items():
            for pattern in field_patterns:
                match = re.search(pattern, title_block_text, re.IGNORECASE)
                if match:
                    result[field] = match.group(1).strip()
                    break
        
        return result


# Singleton instances
_ocr_service: OCRService | None = None
_title_block_parser: TitleBlockParser | None = None


def get_ocr_service() -> OCRService:
    """Get the OCR service singleton."""
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = OCRService()
    return _ocr_service


def get_title_block_parser() -> TitleBlockParser:
    """Get the title block parser singleton."""
    global _title_block_parser
    if _title_block_parser is None:
        _title_block_parser = TitleBlockParser()
    return _title_block_parser
```

---

### Task 3.3: OCR Celery Task

Create `backend/app/workers/ocr_tasks.py`:

```python
"""OCR processing Celery tasks."""

import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.models.page import Page
from app.services.ocr_service import get_ocr_service, get_title_block_parser
from app.utils.storage import get_storage_service
from app.workers.celery_app import celery_app

logger = structlog.get_logger()
settings = get_settings()

engine = create_async_engine(str(settings.database_url))
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def run_async(coro):
    """Run an async coroutine in sync context."""
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=3)
def process_page_ocr_task(self, page_id: str) -> dict:
    """Process OCR for a single page.
    
    Args:
        page_id: Page UUID as string
        
    Returns:
        OCR processing result
    """
    logger.info("Starting OCR processing", page_id=page_id)
    
    try:
        result = run_async(_process_page_ocr(page_id))
        return result
    except Exception as e:
        logger.error("OCR processing failed", page_id=page_id, error=str(e))
        run_async(_update_page_ocr_error(page_id, str(e)))
        raise self.retry(exc=e, countdown=30)


@celery_app.task(bind=True)
def process_document_ocr_task(self, document_id: str) -> dict:
    """Process OCR for all pages in a document.
    
    Args:
        document_id: Document UUID as string
        
    Returns:
        Summary of OCR processing
    """
    logger.info("Starting document OCR", document_id=document_id)
    
    result = run_async(_process_document_ocr(document_id))
    return result


async def _process_page_ocr(page_id: str) -> dict:
    """Process OCR for a single page."""
    page_uuid = uuid.UUID(page_id)
    
    ocr_service = get_ocr_service()
    title_block_parser = get_title_block_parser()
    storage = get_storage_service()
    
    async with async_session() as session:
        # Get page
        result = await session.execute(
            select(Page).where(Page.id == page_uuid)
        )
        page = result.scalar_one_or_none()
        
        if not page:
            raise ValueError(f"Page not found: {page_id}")
        
        # Download page image
        image_bytes = storage.download_file(page.image_key)
        
        # Run OCR
        ocr_result = ocr_service.extract_text(image_bytes)
        
        # Parse title block
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
        
        # Set sheet number and title from detected values
        if ocr_result.detected_sheet_numbers:
            page.sheet_number = ocr_result.detected_sheet_numbers[0]
        elif title_block_data["sheet_number"]:
            page.sheet_number = title_block_data["sheet_number"]
        
        if ocr_result.detected_titles:
            page.title = ocr_result.detected_titles[0]
        elif title_block_data["sheet_title"]:
            page.title = title_block_data["sheet_title"]
        
        # Store detected scale text (not yet calibrated)
        if ocr_result.detected_scale_texts:
            page.scale_text = ocr_result.detected_scale_texts[0]
        elif title_block_data["scale"]:
            page.scale_text = title_block_data["scale"]
        
        await session.commit()
        
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


async def _process_document_ocr(document_id: str) -> dict:
    """Process OCR for all pages in a document."""
    doc_uuid = uuid.UUID(document_id)
    
    async with async_session() as session:
        # Get all pages for document
        result = await session.execute(
            select(Page.id).where(Page.document_id == doc_uuid)
        )
        page_ids = [str(row[0]) for row in result.all()]
    
    # Queue OCR tasks for each page
    for page_id in page_ids:
        process_page_ocr_task.delay(page_id)
    
    return {
        "status": "queued",
        "document_id": document_id,
        "pages_queued": len(page_ids),
    }


async def _update_page_ocr_error(page_id: str, error: str) -> None:
    """Update page with OCR error."""
    async with async_session() as session:
        result = await session.execute(
            select(Page).where(Page.id == uuid.UUID(page_id))
        )
        page = result.scalar_one_or_none()
        
        if page:
            page.processing_error = f"OCR error: {error}"
            await session.commit()
```

---

### Task 3.4: Update Document Processing to Trigger OCR

Update `backend/app/workers/document_tasks.py` to trigger OCR after page extraction:

```python
# Add to the end of _process_document function, after pages are created:

# Queue OCR processing for the document
from app.workers.ocr_tasks import process_document_ocr_task
process_document_ocr_task.delay(document_id)
```

Update celery_app.py to include OCR tasks:

```python
celery_app = Celery(
    "takeoff",
    broker=str(settings.celery_broker_url),
    backend=str(settings.celery_result_backend),
    include=[
        "app.workers.document_tasks",
        "app.workers.ocr_tasks",  # Add this
    ],
)
```

---

### Task 3.5: OCR API Endpoints

Update `backend/app/api/routes/pages.py`:

```python
"""Page endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.page import Page
from app.schemas.page import PageResponse, PageListResponse, PageOCRResponse
from app.utils.storage import get_storage_service
from app.workers.ocr_tasks import process_page_ocr_task

router = APIRouter()


@router.get("/documents/{document_id}/pages", response_model=PageListResponse)
async def list_document_pages(
    document_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List all pages for a document."""
    result = await db.execute(
        select(Page)
        .where(Page.document_id == document_id)
        .order_by(Page.page_number)
    )
    pages = result.scalars().all()
    
    # Generate URLs for images
    storage = get_storage_service()
    pages_data = []
    for page in pages:
        page_dict = {
            "id": page.id,
            "document_id": page.document_id,
            "page_number": page.page_number,
            "width": page.width,
            "height": page.height,
            "classification": page.classification,
            "title": page.title,
            "sheet_number": page.sheet_number,
            "scale_text": page.scale_text,
            "scale_calibrated": page.scale_calibrated,
            "status": page.status,
            "thumbnail_url": storage.get_presigned_url(page.thumbnail_key, 3600)
                if page.thumbnail_key else None,
        }
        pages_data.append(page_dict)
    
    return PageListResponse(pages=pages_data, total=len(pages_data))


@router.get("/pages/{page_id}", response_model=PageResponse)
async def get_page(
    page_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get page details."""
    result = await db.execute(select(Page).where(Page.id == page_id))
    page = result.scalar_one_or_none()
    
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found",
        )
    
    storage = get_storage_service()
    
    return PageResponse(
        id=page.id,
        document_id=page.document_id,
        page_number=page.page_number,
        width=page.width,
        height=page.height,
        classification=page.classification,
        classification_confidence=page.classification_confidence,
        title=page.title,
        sheet_number=page.sheet_number,
        scale_text=page.scale_text,
        scale_value=page.scale_value,
        scale_unit=page.scale_unit,
        scale_calibrated=page.scale_calibrated,
        status=page.status,
        image_url=storage.get_presigned_url(page.image_key, 3600),
        thumbnail_url=storage.get_presigned_url(page.thumbnail_key, 3600)
            if page.thumbnail_key else None,
    )


@router.get("/pages/{page_id}/image")
async def get_page_image(
    page_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get redirect URL to page image."""
    from fastapi.responses import RedirectResponse
    
    result = await db.execute(
        select(Page.image_key).where(Page.id == page_id)
    )
    row = result.one_or_none()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found",
        )
    
    storage = get_storage_service()
    url = storage.get_presigned_url(row[0], 3600)
    
    return RedirectResponse(url=url)


@router.get("/pages/{page_id}/ocr", response_model=PageOCRResponse)
async def get_page_ocr(
    page_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get OCR data for a page."""
    result = await db.execute(
        select(Page.ocr_text, Page.ocr_blocks, Page.sheet_number, Page.title, Page.scale_text)
        .where(Page.id == page_id)
    )
    row = result.one_or_none()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found",
        )
    
    return PageOCRResponse(
        full_text=row[0],
        blocks=row[1].get("blocks", []) if row[1] else [],
        detected_scales=row[1].get("detected_scales", []) if row[1] else [],
        detected_sheet_numbers=row[1].get("detected_sheet_numbers", []) if row[1] else [],
        detected_titles=row[1].get("detected_titles", []) if row[1] else [],
        sheet_number=row[2],
        title=row[3],
        scale_text=row[4],
    )


@router.post("/pages/{page_id}/reprocess-ocr", status_code=status.HTTP_202_ACCEPTED)
async def reprocess_page_ocr(
    page_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Reprocess OCR for a page."""
    result = await db.execute(select(Page.id).where(Page.id == page_id))
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found",
        )
    
    process_page_ocr_task.delay(str(page_id))
    
    return {"status": "queued", "page_id": str(page_id)}
```

---

### Task 3.6: Page Schemas

Create `backend/app/schemas/page.py`:

```python
"""Page schemas."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class PageResponse(BaseModel):
    """Page response schema."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    document_id: uuid.UUID
    page_number: int
    width: int
    height: int
    classification: str | None = None
    classification_confidence: float | None = None
    title: str | None = None
    sheet_number: str | None = None
    scale_text: str | None = None
    scale_value: float | None = None
    scale_unit: str = "foot"
    scale_calibrated: bool = False
    status: str
    image_url: str | None = None
    thumbnail_url: str | None = None


class PageSummaryResponse(BaseModel):
    """Brief page response for listings."""
    
    id: uuid.UUID
    document_id: uuid.UUID
    page_number: int
    classification: str | None = None
    title: str | None = None
    sheet_number: str | None = None
    scale_text: str | None = None
    scale_calibrated: bool = False
    status: str
    thumbnail_url: str | None = None


class PageListResponse(BaseModel):
    """Response for listing pages."""
    
    pages: list[PageSummaryResponse]
    total: int


class PageOCRResponse(BaseModel):
    """OCR data response."""
    
    full_text: str | None = None
    blocks: list[dict[str, Any]] = []
    detected_scales: list[str] = []
    detected_sheet_numbers: list[str] = []
    detected_titles: list[str] = []
    sheet_number: str | None = None
    title: str | None = None
    scale_text: str | None = None


class ScaleUpdateRequest(BaseModel):
    """Request to update page scale."""
    
    scale_value: float  # pixels per foot
    scale_unit: str = "foot"
    scale_text: str | None = None
```

---

### Task 3.7: Search Index (Optional Full-Text Search)

For full-text search across all pages, add PostgreSQL full-text search:

Create migration `backend/alembic/versions/xxx_add_fulltext_search.py`:

```python
"""Add full-text search index.

Revision ID: xxx
"""

from alembic import op


def upgrade() -> None:
    # Add GIN index for full-text search on OCR text
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_pages_ocr_text_search 
        ON pages 
        USING gin(to_tsvector('english', COALESCE(ocr_text, '')));
    """)
    
    # Add trigram index for fuzzy matching
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_pages_ocr_text_trgm 
        ON pages 
        USING gin(ocr_text gin_trgm_ops);
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_pages_ocr_text_search;")
    op.execute("DROP INDEX IF EXISTS idx_pages_ocr_text_trgm;")
```

Add search endpoint to `backend/app/api/routes/pages.py`:

```python
@router.get("/projects/{project_id}/search")
async def search_pages(
    project_id: uuid.UUID,
    q: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Search pages by OCR text within a project."""
    from sqlalchemy import text
    
    query = text("""
        SELECT p.id, p.document_id, p.page_number, p.title, p.sheet_number,
               ts_rank(to_tsvector('english', COALESCE(p.ocr_text, '')), 
                       plainto_tsquery('english', :query)) as rank
        FROM pages p
        JOIN documents d ON p.document_id = d.id
        WHERE d.project_id = :project_id
          AND to_tsvector('english', COALESCE(p.ocr_text, '')) @@ plainto_tsquery('english', :query)
        ORDER BY rank DESC
        LIMIT 50
    """)
    
    result = await db.execute(query, {"project_id": project_id, "query": q})
    rows = result.all()
    
    return {
        "results": [
            {
                "page_id": str(row[0]),
                "document_id": str(row[1]),
                "page_number": row[2],
                "title": row[3],
                "sheet_number": row[4],
                "relevance": float(row[5]),
            }
            for row in rows
        ],
        "total": len(rows),
    }
```

---

## Verification Checklist

After completing all tasks, verify:

- [ ] Google Cloud Vision credentials configured
- [ ] OCR service extracts text from plan images
- [ ] Scale text patterns detected correctly
- [ ] Sheet numbers extracted (e.g., "A1.01", "S-101")
- [ ] Sheet titles extracted
- [ ] Title block parsing works for standard formats
- [ ] OCR runs automatically after document processing
- [ ] OCR data stored in page records
- [ ] API endpoints return OCR data
- [ ] Can reprocess OCR for individual pages
- [ ] Full-text search returns relevant results
- [ ] Errors handled gracefully

### Test Cases

1. Upload a PDF with clear title block → verify sheet number and title extracted
2. Upload a PDF with scale notation "1/4\" = 1'-0\"" → verify scale text detected
3. Upload a scanned TIFF (lower quality) → verify OCR still works
4. Search for text that appears on a page → verify search returns correct page
5. Upload multi-page document → verify all pages get OCR processed

---

## Next Phase

Once verified, proceed to **`04-PAGE-CLASSIFICATION.md`** for implementing AI-powered page classification to identify concrete vs. structural vs. site plans, etc.
