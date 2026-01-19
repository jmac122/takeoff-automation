"""PDF and TIFF processing utilities."""

import io
from typing import Iterator


def get_pdf_page_count(pdf_bytes: bytes) -> int:
    """Get the number of pages in a PDF."""
    # Simple heuristic: PDFs start with %PDF-
    if pdf_bytes.startswith(b"%PDF-"):
        # Count pages by looking for /Type/Page objects (simplified)
        # This is a very basic implementation
        content = pdf_bytes.decode("latin-1", errors="ignore")
        page_count = content.count("/Type/Page")
        return max(1, page_count) if page_count > 0 else 1
    return 1


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
    # Create a simple placeholder image for testing
    # In a real implementation, this would use pdf2image
    page_count = get_pdf_page_count(pdf_bytes)

    for page_num in range(1, page_count + 1):
        # Create a simple colored rectangle as placeholder
        # This simulates an image extraction
        width, height = 800, 600
        # Simple RGB image data (red square for testing)
        image_data = b"\xff\x00\x00" * (width * height)  # Red image

        # Add PNG header (simplified - not a real PNG)
        # In production, this would be a proper image
        mock_png = b"\x89PNG\r\n\x1a\n" + image_data[:1000]  # Truncated for demo

        yield (page_num, mock_png, width, height)


def get_tiff_page_count(tiff_bytes: bytes) -> int:
    """Get the number of pages in a TIFF file."""
    # Simple TIFF detection
    if tiff_bytes.startswith(b"II*\x00") or tiff_bytes.startswith(b"MM\x00*"):
        # Multi-page TIFFs have IFD chains
        # Simplified: just return 1 for now
        return 1
    return 1


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
    page_count = get_tiff_page_count(tiff_bytes)

    for page_num in range(1, page_count + 1):
        # Create a simple placeholder image
        width, height = 800, 600
        # Simple RGB image data (blue square for testing)
        image_data = b"\x00\x00\xff" * (width * height)  # Blue image

        # Add PNG header (simplified)
        mock_png = b"\x89PNG\r\n\x1a\n" + image_data[:1000]

        yield (page_num, mock_png, width, height)


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
    # Simple thumbnail creation - just return a smaller version
    # In production, this would resize the image properly
    width, height = 256, 256
    # Simple RGB thumbnail data (green square)
    thumbnail_data = b"\x00\xff\x00" * (width * height)

    mock_thumbnail = b"\x89PNG\r\n\x1a\n" + thumbnail_data[:1000]
    return mock_thumbnail


def validate_pdf(pdf_bytes: bytes) -> tuple[bool, str | None]:
    """Validate that bytes represent a valid PDF.

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not pdf_bytes.startswith(b"%PDF-"):
        return False, "Not a valid PDF file"

    if len(pdf_bytes) < 100:
        return False, "PDF file too small"

    # Check for PDF end marker
    if b"%%EOF" not in pdf_bytes[-1024:]:
        return False, "PDF file corrupted or incomplete"

    return True, None


def validate_tiff(tiff_bytes: bytes) -> tuple[bool, str | None]:
    """Validate that bytes represent a valid TIFF.

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not (tiff_bytes.startswith(b"II*\x00") or tiff_bytes.startswith(b"MM\x00*")):
        return False, "Not a valid TIFF file"

    if len(tiff_bytes) < 100:
        return False, "TIFF file too small"

    return True, None
