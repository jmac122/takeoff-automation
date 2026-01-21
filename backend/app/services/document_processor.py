"""Document processing service."""

import uuid
from typing import BinaryIO

import structlog

from app.config import get_settings
from app.models.document import Document
from app.models.page import Page
from app.utils.pdf_utils import (
    get_pdf_page_count,
    get_tiff_page_count,
    extract_pdf_pages_as_images,
    extract_tiff_pages_as_images,
    create_thumbnail,
    convert_to_png,
    validate_pdf,
    validate_tiff,
)
from app.utils.storage import get_storage_service

logger = structlog.get_logger()
settings = get_settings()


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
            dpi=dpi,
        )

        pages_data = []

        # Extract at full resolution - no max_dimension constraint
        # LLM resizing happens on-the-fly when sending to LLMs
        if file_type == "pdf":
            page_iterator = extract_pdf_pages_as_images(
                file_bytes, dpi=dpi, max_dimension=None
            )
        elif file_type == "tiff":
            page_iterator = extract_tiff_pages_as_images(
                file_bytes, target_dpi=dpi, max_dimension=None
            )
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

        for page_data in page_iterator:
            # PDF pages include physical dimensions, TIFF pages don't
            if file_type == "pdf":
                page_num, img_bytes, width, height, page_width_inches, page_height_inches = page_data
            else:
                page_num, img_bytes, width, height = page_data
                page_width_inches = None
                page_height_inches = None
            page_id = uuid.uuid4()
            base_path = f"projects/{project_id}/documents/{document_id}/pages/{page_id}"

            # Store TIFF for OCR/LLM processing (flattened, consistent)
            image_key = f"{base_path}/image.tiff"
            self.storage.upload_bytes(img_bytes, image_key, "image/tiff")

            # Store PNG for frontend viewer (browser-compatible)
            viewer_key = f"{base_path}/image.png"
            png_bytes = convert_to_png(img_bytes)
            self.storage.upload_bytes(png_bytes, viewer_key, "image/png")

            # Create and store thumbnail
            thumb_bytes = create_thumbnail(img_bytes, max_size=256)
            thumb_key = f"{base_path}/thumbnail.png"
            self.storage.upload_bytes(thumb_bytes, thumb_key, "image/png")

            pages_data.append(
                {
                    "id": page_id,
                    "page_number": page_num,
                    "width": width,
                    "height": height,
                    "dpi": dpi,
                    "page_width_inches": page_width_inches,
                    "page_height_inches": page_height_inches,
                    "image_key": image_key,
                    "thumbnail_key": thumb_key,
                    "status": "ready",
                }
            )

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
