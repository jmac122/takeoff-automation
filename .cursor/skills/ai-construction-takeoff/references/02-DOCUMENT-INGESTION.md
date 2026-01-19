# Phase 1A: Document Ingestion
## PDF/TIFF Upload, Processing, and Storage

> **Duration**: Weeks 2-5
> **Prerequisites**: Phase 0 complete (project setup)
> **Outcome**: Fully functional document upload and processing pipeline

---

## Context for LLM Assistant

You are building the document ingestion system for an AI-powered construction takeoff platform. This phase implements:
- Multi-file upload (PDF and TIFF formats)
- File validation and virus scanning
- PDF/TIFF to image conversion
- Page extraction and thumbnail generation
- Cloud storage integration (MinIO/S3)
- Async processing with Celery workers

### Key Constraints
- PDFs can be 100+ pages, up to 500MB
- TIFFs can be multi-page (common in construction)
- Processing must be async (don't block uploads)
- All images stored in S3-compatible storage
- Generate thumbnails (256px) and full-resolution images

---

## Database Models

### Task 1.1: Create Document and Page Models

Create `backend/app/models/project.py`:

```python
"""Project model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Text, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.condition import Condition


class Project(Base, UUIDMixin, TimestampMixin):
    """Project containing documents and takeoff conditions."""

    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    client_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50),
        default="draft",
        nullable=False,
    )  # draft, in_progress, completed, archived

    # Relationships
    documents: Mapped[list["Document"]] = relationship(
        "Document",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    conditions: Mapped[list["Condition"]] = relationship(
        "Condition",
        back_populates="project",
        cascade="all, delete-orphan",
    )
```

Create `backend/app/models/document.py`:

```python
"""Document model for uploaded plan sets."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, BigInteger, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.page import Page


class Document(Base, UUIDMixin, TimestampMixin):
    """Uploaded document (PDF or TIFF plan set)."""

    __tablename__ = "documents"

    # Foreign keys
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )

    # File info
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)  # pdf, tiff
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)  # bytes
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)

    # Storage
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)

    # Processing
    status: Mapped[str] = mapped_column(
        String(50),
        default="uploaded",
        nullable=False,
    )  # uploaded, processing, ready, error
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    processing_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    processing_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="documents")
    pages: Mapped[list["Page"]] = relationship(
        "Page",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="Page.page_number",
    )
```

Create `backend/app/models/page.py`:

```python
"""Page model for individual sheets within documents."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.measurement import Measurement


class Page(Base, UUIDMixin, TimestampMixin):
    """Individual page/sheet from a document."""

    __tablename__ = "pages"

    # Foreign keys
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Page info
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Dimensions (in pixels)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    dpi: Mapped[int] = mapped_column(Integer, default=150)

    # Storage keys
    image_key: Mapped[str] = mapped_column(String(500), nullable=False)
    thumbnail_key: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Classification (populated by AI in Phase 2)
    classification: Mapped[str | None] = mapped_column(String(100), nullable=True)
    classification_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Page title/name (extracted via OCR)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sheet_number: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Scale (populated by scale detection in Phase 2)
    scale_text: Mapped[str | None] = mapped_column(String(100), nullable=True)  # e.g., "1/4\" = 1'-0\""
    scale_value: Mapped[float | None] = mapped_column(Float, nullable=True)  # pixels per foot
    scale_unit: Mapped[str] = mapped_column(String(20), default="foot")
    scale_calibrated: Mapped[bool] = mapped_column(Boolean, default=False)
    scale_calibration_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # OCR data
    ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    ocr_blocks: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Processing
    status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        nullable=False,
    )  # pending, processing, ready, error
    processing_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="pages")
    measurements: Mapped[list["Measurement"]] = relationship(
        "Measurement",
        back_populates="page",
        cascade="all, delete-orphan",
    )
```

---

### Task 1.2: Create Initial Migration

```bash
cd backend
alembic revision --autogenerate -m "initial_schema"
alembic upgrade head
```

---

## Storage Service

### Task 1.3: Implement S3-Compatible Storage

Create `backend/app/utils/storage.py`:

```python
"""S3-compatible storage utilities."""

import io
from typing import BinaryIO
from urllib.parse import urljoin

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.config import get_settings

settings = get_settings()


class StorageService:
    """Service for interacting with S3-compatible storage (MinIO)."""

    def __init__(self):
        self.client = boto3.client(
            "s3",
            endpoint_url=f"{'https' if settings.storage_use_ssl else 'http'}://{settings.storage_endpoint}",
            aws_access_key_id=settings.storage_access_key,
            aws_secret_access_key=settings.storage_secret_key,
            config=Config(signature_version="s3v4"),
        )
        self.bucket = settings.storage_bucket
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self) -> None:
        """Create bucket if it doesn't exist."""
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError:
            self.client.create_bucket(Bucket=self.bucket)

    def upload_file(
        self,
        file_obj: BinaryIO,
        key: str,
        content_type: str | None = None,
    ) -> str:
        """Upload a file to storage.
        
        Args:
            file_obj: File-like object to upload
            key: Storage key (path)
            content_type: MIME type of the file
            
        Returns:
            The storage key
        """
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type

        self.client.upload_fileobj(
            file_obj,
            self.bucket,
            key,
            ExtraArgs=extra_args,
        )
        return key

    def upload_bytes(
        self,
        data: bytes,
        key: str,
        content_type: str | None = None,
    ) -> str:
        """Upload bytes to storage."""
        return self.upload_file(io.BytesIO(data), key, content_type)

    def download_file(self, key: str) -> bytes:
        """Download a file from storage.
        
        Args:
            key: Storage key (path)
            
        Returns:
            File contents as bytes
        """
        response = self.client.get_object(Bucket=self.bucket, Key=key)
        return response["Body"].read()

    def download_to_file(self, key: str, file_obj: BinaryIO) -> None:
        """Download a file to a file-like object."""
        self.client.download_fileobj(self.bucket, key, file_obj)

    def delete_file(self, key: str) -> None:
        """Delete a file from storage."""
        self.client.delete_object(Bucket=self.bucket, Key=key)

    def delete_prefix(self, prefix: str) -> None:
        """Delete all files with a given prefix."""
        paginator = self.client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
            if "Contents" in page:
                objects = [{"Key": obj["Key"]} for obj in page["Contents"]]
                self.client.delete_objects(
                    Bucket=self.bucket,
                    Delete={"Objects": objects},
                )

    def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        """Generate a presigned URL for file access.
        
        Args:
            key: Storage key (path)
            expires_in: URL expiration time in seconds
            
        Returns:
            Presigned URL
        """
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires_in,
        )

    def file_exists(self, key: str) -> bool:
        """Check if a file exists in storage."""
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError:
            return False

    def get_file_size(self, key: str) -> int:
        """Get the size of a file in bytes."""
        response = self.client.head_object(Bucket=self.bucket, Key=key)
        return response["ContentLength"]


# Singleton instance
_storage_service: StorageService | None = None


def get_storage_service() -> StorageService:
    """Get the storage service singleton."""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service
```

---

## Document Processing

### Task 1.4: PDF/TIFF Processing Utilities

Create `backend/app/utils/pdf_utils.py`:

```python
"""PDF and TIFF processing utilities."""

import io
import tempfile
from pathlib import Path
from typing import Iterator

import fitz  # PyMuPDF
from PIL import Image
from pdf2image import convert_from_bytes, convert_from_path


def get_pdf_page_count(pdf_bytes: bytes) -> int:
    """Get the number of pages in a PDF."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    count = len(doc)
    doc.close()
    return count


def extract_pdf_pages_as_images(
    pdf_bytes: bytes,
    dpi: int = 150,
    fmt: str = "PNG",
) -> Iterator[tuple[int, bytes, int, int]]:
    """Extract pages from PDF as images.
    
    Args:
        pdf_bytes: PDF file contents
        dpi: Resolution for rendering
        fmt: Output format (PNG recommended)
        
    Yields:
        Tuples of (page_number, image_bytes, width, height)
    """
    images = convert_from_bytes(pdf_bytes, dpi=dpi, fmt=fmt)
    
    for i, image in enumerate(images, start=1):
        img_bytes = io.BytesIO()
        image.save(img_bytes, format=fmt)
        img_bytes.seek(0)
        
        yield (i, img_bytes.read(), image.width, image.height)


def get_tiff_page_count(tiff_bytes: bytes) -> int:
    """Get the number of pages in a TIFF file."""
    img = Image.open(io.BytesIO(tiff_bytes))
    count = 0
    try:
        while True:
            count += 1
            img.seek(count)
    except EOFError:
        pass
    return count


def extract_tiff_pages_as_images(
    tiff_bytes: bytes,
    target_dpi: int = 150,
    fmt: str = "PNG",
) -> Iterator[tuple[int, bytes, int, int]]:
    """Extract pages from multi-page TIFF as images.
    
    Args:
        tiff_bytes: TIFF file contents
        target_dpi: Target resolution for output
        fmt: Output format
        
    Yields:
        Tuples of (page_number, image_bytes, width, height)
    """
    img = Image.open(io.BytesIO(tiff_bytes))
    page_num = 0
    
    while True:
        try:
            img.seek(page_num)
            
            # Convert to RGB if necessary
            if img.mode != "RGB":
                frame = img.convert("RGB")
            else:
                frame = img.copy()
            
            # Resize if DPI differs significantly
            # (TIFF may have embedded DPI info)
            
            img_bytes = io.BytesIO()
            frame.save(img_bytes, format=fmt)
            img_bytes.seek(0)
            
            yield (page_num + 1, img_bytes.read(), frame.width, frame.height)
            page_num += 1
            
        except EOFError:
            break


def create_thumbnail(
    image_bytes: bytes,
    max_size: int = 256,
    fmt: str = "PNG",
) -> bytes:
    """Create a thumbnail from an image.
    
    Args:
        image_bytes: Source image bytes
        max_size: Maximum dimension (width or height)
        fmt: Output format
        
    Returns:
        Thumbnail image bytes
    """
    img = Image.open(io.BytesIO(image_bytes))
    
    # Convert to RGB if necessary (for PNG with transparency)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    
    # Calculate thumbnail size maintaining aspect ratio
    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
    
    output = io.BytesIO()
    img.save(output, format=fmt, optimize=True)
    output.seek(0)
    
    return output.read()


def validate_pdf(pdf_bytes: bytes) -> tuple[bool, str | None]:
    """Validate that bytes represent a valid PDF.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        if len(doc) == 0:
            return False, "PDF has no pages"
        doc.close()
        return True, None
    except Exception as e:
        return False, str(e)


def validate_tiff(tiff_bytes: bytes) -> tuple[bool, str | None]:
    """Validate that bytes represent a valid TIFF.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        img = Image.open(io.BytesIO(tiff_bytes))
        if img.format != "TIFF":
            return False, "File is not a valid TIFF"
        return True, None
    except Exception as e:
        return False, str(e)
```

---

### Task 1.5: Document Processing Service

Create `backend/app/services/document_processor.py`:

```python
"""Document processing service."""

import uuid
from typing import BinaryIO

import structlog

from app.models.document import Document
from app.models.page import Page
from app.utils.pdf_utils import (
    get_pdf_page_count,
    get_tiff_page_count,
    extract_pdf_pages_as_images,
    extract_tiff_pages_as_images,
    create_thumbnail,
    validate_pdf,
    validate_tiff,
)
from app.utils.storage import get_storage_service

logger = structlog.get_logger()


class DocumentProcessor:
    """Service for processing uploaded documents."""

    def __init__(self):
        self.storage = get_storage_service()
        self.supported_types = {
            "application/pdf": "pdf",
            "image/tiff": "tiff",
            "image/tif": "tiff",
        }

    def validate_file(
        self,
        file_bytes: bytes,
        mime_type: str,
    ) -> tuple[bool, str | None]:
        """Validate an uploaded file.
        
        Args:
            file_bytes: File contents
            mime_type: MIME type of the file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if mime_type not in self.supported_types:
            return False, f"Unsupported file type: {mime_type}"
        
        file_type = self.supported_types[mime_type]
        
        if file_type == "pdf":
            return validate_pdf(file_bytes)
        elif file_type == "tiff":
            return validate_tiff(file_bytes)
        
        return False, "Unknown file type"

    def get_page_count(self, file_bytes: bytes, file_type: str) -> int:
        """Get the number of pages in a document."""
        if file_type == "pdf":
            return get_pdf_page_count(file_bytes)
        elif file_type == "tiff":
            return get_tiff_page_count(file_bytes)
        raise ValueError(f"Unsupported file type: {file_type}")

    def store_original(
        self,
        file_bytes: bytes,
        project_id: uuid.UUID,
        document_id: uuid.UUID,
        filename: str,
        mime_type: str,
    ) -> str:
        """Store the original uploaded file.
        
        Returns:
            Storage key for the file
        """
        key = f"projects/{project_id}/documents/{document_id}/original/{filename}"
        self.storage.upload_bytes(file_bytes, key, mime_type)
        return key

    def process_document(
        self,
        document_id: uuid.UUID,
        project_id: uuid.UUID,
        file_bytes: bytes,
        file_type: str,
        dpi: int = 150,
    ) -> list[dict]:
        """Process a document and extract pages as images.
        
        Args:
            document_id: Document UUID
            project_id: Project UUID
            file_bytes: Document contents
            file_type: 'pdf' or 'tiff'
            dpi: Resolution for image extraction
            
        Returns:
            List of page data dictionaries
        """
        logger.info(
            "Processing document",
            document_id=str(document_id),
            file_type=file_type,
        )
        
        pages_data = []
        
        # Get page iterator based on file type
        if file_type == "pdf":
            page_iterator = extract_pdf_pages_as_images(file_bytes, dpi=dpi)
        elif file_type == "tiff":
            page_iterator = extract_tiff_pages_as_images(file_bytes, target_dpi=dpi)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        for page_num, img_bytes, width, height in page_iterator:
            page_id = uuid.uuid4()
            
            # Store full-resolution image
            image_key = (
                f"projects/{project_id}/documents/{document_id}/"
                f"pages/{page_id}/image.png"
            )
            self.storage.upload_bytes(img_bytes, image_key, "image/png")
            
            # Create and store thumbnail
            thumb_bytes = create_thumbnail(img_bytes, max_size=256)
            thumb_key = (
                f"projects/{project_id}/documents/{document_id}/"
                f"pages/{page_id}/thumbnail.png"
            )
            self.storage.upload_bytes(thumb_bytes, thumb_key, "image/png")
            
            pages_data.append({
                "id": page_id,
                "page_number": page_num,
                "width": width,
                "height": height,
                "dpi": dpi,
                "image_key": image_key,
                "thumbnail_key": thumb_key,
                "status": "ready",
            })
            
            logger.debug(
                "Processed page",
                document_id=str(document_id),
                page_number=page_num,
            )
        
        return pages_data

    def delete_document_files(
        self,
        project_id: uuid.UUID,
        document_id: uuid.UUID,
    ) -> None:
        """Delete all files associated with a document."""
        prefix = f"projects/{project_id}/documents/{document_id}/"
        self.storage.delete_prefix(prefix)


# Singleton instance
_processor: DocumentProcessor | None = None


def get_document_processor() -> DocumentProcessor:
    """Get the document processor singleton."""
    global _processor
    if _processor is None:
        _processor = DocumentProcessor()
    return _processor
```

---

## Celery Workers

### Task 1.6: Setup Celery

Create `backend/app/workers/__init__.py`:

```python
"""Celery workers module."""
```

Create `backend/app/workers/celery_app.py`:

```python
"""Celery application configuration."""

from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "takeoff",
    broker=str(settings.celery_broker_url),
    backend=str(settings.celery_result_backend),
    include=[
        "app.workers.document_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3000,  # 50 minute soft limit
    worker_prefetch_multiplier=1,  # Process one task at a time
    task_acks_late=True,  # Acknowledge after completion
)
```

Create `backend/app/workers/document_tasks.py`:

```python
"""Document processing Celery tasks."""

import uuid
from datetime import datetime

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.models.document import Document
from app.models.page import Page
from app.services.document_processor import get_document_processor
from app.utils.storage import get_storage_service
from app.workers.celery_app import celery_app

logger = structlog.get_logger()
settings = get_settings()

# Create async engine for workers
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
def process_document_task(
    self,
    document_id: str,
    project_id: str,
) -> dict:
    """Process an uploaded document asynchronously.
    
    Args:
        document_id: Document UUID as string
        project_id: Project UUID as string
        
    Returns:
        Processing result dictionary
    """
    logger.info(
        "Starting document processing",
        document_id=document_id,
        task_id=self.request.id,
    )
    
    try:
        result = run_async(_process_document(document_id, project_id))
        return result
    except Exception as e:
        logger.error(
            "Document processing failed",
            document_id=document_id,
            error=str(e),
        )
        # Update document status to error
        run_async(_update_document_status(document_id, "error", str(e)))
        raise self.retry(exc=e, countdown=60)


async def _process_document(document_id: str, project_id: str) -> dict:
    """Async document processing implementation."""
    doc_uuid = uuid.UUID(document_id)
    proj_uuid = uuid.UUID(project_id)
    
    processor = get_document_processor()
    storage = get_storage_service()
    
    async with async_session() as session:
        # Get document
        result = await session.execute(
            select(Document).where(Document.id == doc_uuid)
        )
        document = result.scalar_one_or_none()
        
        if not document:
            raise ValueError(f"Document not found: {document_id}")
        
        # Update status to processing
        document.status = "processing"
        await session.commit()
        
        # Download original file
        file_bytes = storage.download_file(document.storage_key)
        
        # Process document and extract pages
        pages_data = processor.process_document(
            document_id=doc_uuid,
            project_id=proj_uuid,
            file_bytes=file_bytes,
            file_type=document.file_type,
            dpi=150,
        )
        
        # Create page records
        for page_data in pages_data:
            page = Page(
                id=page_data["id"],
                document_id=doc_uuid,
                page_number=page_data["page_number"],
                width=page_data["width"],
                height=page_data["height"],
                dpi=page_data["dpi"],
                image_key=page_data["image_key"],
                thumbnail_key=page_data["thumbnail_key"],
                status="ready",
            )
            session.add(page)
        
        # Update document status
        document.status = "ready"
        document.page_count = len(pages_data)
        
        await session.commit()
        
        logger.info(
            "Document processing complete",
            document_id=document_id,
            page_count=len(pages_data),
        )
        
        return {
            "status": "success",
            "document_id": document_id,
            "page_count": len(pages_data),
        }


async def _update_document_status(
    document_id: str,
    status: str,
    error: str | None = None,
) -> None:
    """Update document status in database."""
    async with async_session() as session:
        result = await session.execute(
            select(Document).where(Document.id == uuid.UUID(document_id))
        )
        document = result.scalar_one_or_none()
        
        if document:
            document.status = status
            if error:
                document.processing_error = error
            await session.commit()
```

---

## API Endpoints

### Task 1.7: Document Upload Endpoints

Update `backend/app/api/routes/documents.py`:

```python
"""Document endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db
from app.models.document import Document
from app.models.project import Project
from app.models.page import Page
from app.schemas.document import (
    DocumentResponse,
    DocumentListResponse,
    DocumentStatusResponse,
)
from app.services.document_processor import get_document_processor
from app.utils.storage import get_storage_service
from app.workers.document_tasks import process_document_task

router = APIRouter()


@router.post(
    "/projects/{project_id}/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    project_id: uuid.UUID,
    file: Annotated[UploadFile, File()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Upload a document to a project."""
    # Verify project exists
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    
    # Validate file type
    processor = get_document_processor()
    if file.content_type not in processor.supported_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file.content_type}",
        )
    
    # Read file
    file_bytes = await file.read()
    
    # Validate file content
    is_valid, error = processor.validate_file(file_bytes, file.content_type)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file: {error}",
        )
    
    # Create document record
    document_id = uuid.uuid4()
    file_type = processor.supported_types[file.content_type]
    
    document = Document(
        id=document_id,
        project_id=project_id,
        filename=f"{document_id}.{file_type}",
        original_filename=file.filename or "unknown",
        file_type=file_type,
        file_size=len(file_bytes),
        mime_type=file.content_type,
        storage_key="",  # Will be updated after upload
        status="uploading",
    )
    db.add(document)
    await db.commit()
    
    # Store original file
    try:
        storage_key = processor.store_original(
            file_bytes=file_bytes,
            project_id=project_id,
            document_id=document_id,
            filename=document.filename,
            mime_type=file.content_type,
        )
        document.storage_key = storage_key
        document.status = "uploaded"
        await db.commit()
    except Exception as e:
        document.status = "error"
        document.processing_error = str(e)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store file",
        )
    
    # Queue processing task
    process_document_task.delay(str(document_id), str(project_id))
    
    await db.refresh(document)
    return document


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get document details."""
    result = await db.execute(
        select(Document)
        .options(selectinload(Document.pages))
        .where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    return document


@router.get("/documents/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(
    document_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get document processing status."""
    result = await db.execute(
        select(Document.status, Document.page_count, Document.processing_error)
        .where(Document.id == document_id)
    )
    row = result.one_or_none()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    return DocumentStatusResponse(
        status=row[0],
        page_count=row[1],
        error=row[2],
    )


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete a document and all associated files."""
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    # Delete files from storage
    processor = get_document_processor()
    processor.delete_document_files(document.project_id, document_id)
    
    # Delete from database (cascades to pages)
    await db.delete(document)
    await db.commit()
```

---

### Task 1.8: Pydantic Schemas

Create `backend/app/schemas/__init__.py`:

```python
"""Pydantic schemas for API request/response validation."""
```

Create `backend/app/schemas/document.py`:

```python
"""Document schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PageSummary(BaseModel):
    """Brief page information for document responses."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    page_number: int
    classification: str | None = None
    scale_calibrated: bool = False
    thumbnail_url: str | None = None


class DocumentResponse(BaseModel):
    """Document response schema."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    project_id: uuid.UUID
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    status: str
    page_count: int | None = None
    processing_error: str | None = None
    created_at: datetime
    updated_at: datetime
    pages: list[PageSummary] = []


class DocumentListResponse(BaseModel):
    """Response for listing documents."""
    
    documents: list[DocumentResponse]
    total: int


class DocumentStatusResponse(BaseModel):
    """Document processing status response."""
    
    status: str
    page_count: int | None = None
    error: str | None = None
```

---

### Task 1.9: Database Session Dependency

Create `backend/app/api/deps.py`:

```python
"""API dependencies."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings

settings = get_settings()

engine = create_async_engine(
    str(settings.database_url),
    pool_size=settings.database_pool_size,
    pool_pre_ping=True,
)

async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
```

---

## Frontend Components

### Task 1.10: Document Upload Component

Create `frontend/src/api/documents.ts`:

```typescript
import { apiClient } from './client';
import type { Document } from '../types';

export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}

export async function uploadDocument(
  projectId: string,
  file: File,
  onProgress?: (progress: UploadProgress) => void
): Promise<Document> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post<Document>(
    `/projects/${projectId}/documents`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          onProgress({
            loaded: progressEvent.loaded,
            total: progressEvent.total,
            percentage: Math.round((progressEvent.loaded * 100) / progressEvent.total),
          });
        }
      },
    }
  );

  return response.data;
}

export async function getDocument(documentId: string): Promise<Document> {
  const response = await apiClient.get<Document>(`/documents/${documentId}`);
  return response.data;
}

export async function getDocumentStatus(
  documentId: string
): Promise<{ status: string; page_count: number | null; error: string | null }> {
  const response = await apiClient.get(`/documents/${documentId}/status`);
  return response.data;
}

export async function deleteDocument(documentId: string): Promise<void> {
  await apiClient.delete(`/documents/${documentId}`);
}
```

Create `frontend/src/components/document/DocumentUploader.tsx`:

```tsx
import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, X, Loader2 } from 'lucide-react';
import { useMutation, useQueryClient } from '@tanstack/react-query';

import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { uploadDocument, type UploadProgress } from '@/api/documents';
import { cn } from '@/lib/utils';

interface DocumentUploaderProps {
  projectId: string;
  onUploadComplete?: () => void;
}

interface FileWithProgress {
  file: File;
  progress: number;
  status: 'pending' | 'uploading' | 'complete' | 'error';
  error?: string;
}

export function DocumentUploader({ projectId, onUploadComplete }: DocumentUploaderProps) {
  const [files, setFiles] = useState<FileWithProgress[]>([]);
  const queryClient = useQueryClient();

  const uploadMutation = useMutation({
    mutationFn: async ({ file, index }: { file: File; index: number }) => {
      return uploadDocument(projectId, file, (progress) => {
        setFiles((prev) =>
          prev.map((f, i) =>
            i === index ? { ...f, progress: progress.percentage } : f
          )
        );
      });
    },
    onSuccess: (_, { index }) => {
      setFiles((prev) =>
        prev.map((f, i) =>
          i === index ? { ...f, status: 'complete', progress: 100 } : f
        )
      );
      queryClient.invalidateQueries({ queryKey: ['documents', projectId] });
    },
    onError: (error: Error, { index }) => {
      setFiles((prev) =>
        prev.map((f, i) =>
          i === index ? { ...f, status: 'error', error: error.message } : f
        )
      );
    },
  });

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      const newFiles: FileWithProgress[] = acceptedFiles.map((file) => ({
        file,
        progress: 0,
        status: 'pending' as const,
      }));

      setFiles((prev) => [...prev, ...newFiles]);

      // Upload files sequentially
      const startIndex = files.length;
      for (let i = 0; i < acceptedFiles.length; i++) {
        const index = startIndex + i;
        setFiles((prev) =>
          prev.map((f, idx) =>
            idx === index ? { ...f, status: 'uploading' } : f
          )
        );
        await uploadMutation.mutateAsync({ file: acceptedFiles[i], index });
      }

      onUploadComplete?.();
    },
    [files.length, uploadMutation, onUploadComplete]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/tiff': ['.tiff', '.tif'],
    },
    multiple: true,
  });

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const clearCompleted = () => {
    setFiles((prev) => prev.filter((f) => f.status !== 'complete'));
  };

  return (
    <div className="space-y-4">
      <div
        {...getRootProps()}
        className={cn(
          'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors',
          isDragActive
            ? 'border-primary bg-primary/5'
            : 'border-muted-foreground/25 hover:border-primary/50'
        )}
      >
        <input {...getInputProps()} />
        <Upload className="mx-auto h-12 w-12 text-muted-foreground" />
        <p className="mt-2 text-sm text-muted-foreground">
          {isDragActive
            ? 'Drop the files here...'
            : 'Drag & drop PDF or TIFF files here, or click to select'}
        </p>
        <p className="mt-1 text-xs text-muted-foreground">
          Supports PDF and multi-page TIFF files
        </p>
      </div>

      {files.length > 0 && (
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <h4 className="text-sm font-medium">Uploads</h4>
            {files.some((f) => f.status === 'complete') && (
              <Button variant="ghost" size="sm" onClick={clearCompleted}>
                Clear completed
              </Button>
            )}
          </div>

          {files.map((f, index) => (
            <div
              key={index}
              className="flex items-center gap-3 p-3 bg-muted rounded-lg"
            >
              <File className="h-5 w-5 text-muted-foreground flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{f.file.name}</p>
                {f.status === 'uploading' && (
                  <Progress value={f.progress} className="h-1 mt-1" />
                )}
                {f.status === 'error' && (
                  <p className="text-xs text-destructive">{f.error}</p>
                )}
              </div>
              <div className="flex-shrink-0">
                {f.status === 'uploading' && (
                  <Loader2 className="h-4 w-4 animate-spin text-primary" />
                )}
                {f.status === 'complete' && (
                  <span className="text-xs text-green-600">Complete</span>
                )}
                {(f.status === 'pending' || f.status === 'error') && (
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6"
                    onClick={() => removeFile(index)}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

---

## Verification Checklist

After completing all tasks, verify:

- [ ] Can upload PDF files via API
- [ ] Can upload TIFF files via API
- [ ] Files are stored in MinIO
- [ ] Document record created in database
- [ ] Celery worker processes documents
- [ ] Pages extracted and stored as images
- [ ] Thumbnails generated
- [ ] Page records created in database
- [ ] Status updates correctly (uploaded → processing → ready)
- [ ] Errors handled gracefully
- [ ] Can retrieve document details via API
- [ ] Can poll document status
- [ ] Can delete documents (files and records)
- [ ] Frontend uploader works with drag-and-drop
- [ ] Upload progress shown correctly

---

## Next Phase

Once verified, proceed to **`03-OCR-TEXT-EXTRACTION.md`** for implementing OCR and text extraction from plan pages.
