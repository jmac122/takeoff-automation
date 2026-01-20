"""PDF and TIFF processing utilities."""

import io
from typing import Iterator

import fitz  # PyMuPDF
from PIL import Image


def get_pdf_page_count(pdf_bytes: bytes) -> int:
    """Get the number of pages in a PDF."""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        count = doc.page_count
        doc.close()
        return count
    except Exception:
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
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    try:
        for page_num in range(doc.page_count):
            page = doc[page_num]

            # Calculate zoom factor for desired DPI
            # PyMuPDF default is 72 DPI
            zoom = dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)

            # Render page to pixmap
            pix = page.get_pixmap(matrix=mat)

            # Convert to PIL Image
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            # Convert to bytes
            img_bytes_io = io.BytesIO()
            img.save(img_bytes_io, format=fmt)
            img_bytes = img_bytes_io.getvalue()

            yield (page_num + 1, img_bytes, pix.width, pix.height)
    finally:
        doc.close()


def get_tiff_page_count(tiff_bytes: bytes) -> int:
    """Get the number of pages in a TIFF file."""
    try:
        img = Image.open(io.BytesIO(tiff_bytes))
        page_count = 0
        try:
            while True:
                page_count += 1
                img.seek(page_count)
        except EOFError:
            pass
        return page_count
    except Exception:
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
    img = Image.open(io.BytesIO(tiff_bytes))
    page_num = 0

    try:
        while True:
            # Convert current page to RGB (in case it's CMYK or other format)
            if img.mode != "RGB":
                rgb_img = img.convert("RGB")
            else:
                rgb_img = img

            # Convert to bytes
            img_bytes_io = io.BytesIO()
            rgb_img.save(img_bytes_io, format=fmt)
            img_bytes = img_bytes_io.getvalue()

            width, height = rgb_img.size
            page_num += 1

            yield (page_num, img_bytes, width, height)

            # Move to next page
            img.seek(page_num)
    except EOFError:
        # No more pages
        pass


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

    # Convert to RGB if needed
    if img.mode != "RGB":
        img = img.convert("RGB")

    # Calculate thumbnail size maintaining aspect ratio
    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

    # Convert to bytes
    thumb_bytes_io = io.BytesIO()
    img.save(thumb_bytes_io, format=fmt)
    return thumb_bytes_io.getvalue()


def validate_pdf(pdf_bytes: bytes) -> tuple[bool, str | None]:
    """Validate that bytes represent a valid PDF.

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        if doc.page_count == 0:
            doc.close()
            return False, "PDF has no pages"
        doc.close()
        return True, None
    except Exception as e:
        return False, f"Invalid PDF: {str(e)}"


def validate_tiff(tiff_bytes: bytes) -> tuple[bool, str | None]:
    """Validate that bytes represent a valid TIFF.

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        img = Image.open(io.BytesIO(tiff_bytes))
        img.verify()
        return True, None
    except Exception as e:
        return False, f"Invalid TIFF: {str(e)}"
