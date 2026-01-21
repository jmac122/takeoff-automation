"""PDF and TIFF processing utilities."""

import io
from typing import Iterator

import fitz  # PyMuPDF
from PIL import Image

# Default max dimension for LLM-ready images (fits all LLM provider limits)
DEFAULT_LLM_MAX_DIMENSION = 1568


def _save_image(img: Image.Image, output: io.BytesIO, fmt: str) -> None:
    """Save image to BytesIO with format-specific options.

    Uses LZW compression for TIFF format.
    """
    if fmt.upper() == "TIFF":
        img.save(output, format="TIFF", compression="tiff_lzw")
    else:
        img.save(output, format=fmt)


def resize_image_for_llm(
    image_bytes: bytes,
    max_dimension: int = DEFAULT_LLM_MAX_DIMENSION,
    fmt: str = "TIFF",
) -> tuple[bytes, int, int]:
    """Resize an image so the longest edge is at most max_dimension pixels.

    Maintains aspect ratio. Only resizes if either dimension exceeds max_dimension.
    Uses LANCZOS resampling for high quality.

    Args:
        image_bytes: Source image bytes
        max_dimension: Maximum size for longest edge (default 1568)
        fmt: Output format (TIFF recommended for consistency)

    Returns:
        Tuple of (resized_image_bytes, new_width, new_height)
    """
    img = Image.open(io.BytesIO(image_bytes))

    # Convert to RGB if needed (for consistency)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    width, height = img.size

    # Only resize if needed
    if width <= max_dimension and height <= max_dimension:
        # Return original dimensions but ensure RGB format
        if img.mode != "RGB":
            img = img.convert("RGB")
        output = io.BytesIO()
        _save_image(img, output, fmt)
        return output.getvalue(), width, height

    # Calculate new dimensions maintaining aspect ratio
    if width > height:
        new_width = max_dimension
        new_height = int(height * (max_dimension / width))
    else:
        new_height = max_dimension
        new_width = int(width * (max_dimension / height))

    # Resize with high-quality resampling
    resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Convert to bytes
    output = io.BytesIO()
    _save_image(resized, output, fmt)
    return output.getvalue(), new_width, new_height


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
    fmt: str = "TIFF",
    max_dimension: int | None = None,
) -> Iterator[tuple[int, bytes, int, int, float, float]]:
    """Extract pages from PDF as images.

    Args:
        pdf_bytes: PDF file contents
        dpi: Resolution for rendering
        fmt: Output format (TIFF recommended for consistency)
        max_dimension: If provided, resize images so longest edge <= this value

    Yields:
        Tuples of (page_number, image_bytes, width, height, page_width_inches, page_height_inches)
        page_width_inches and page_height_inches are the physical PDF page dimensions
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    try:
        for page_num in range(doc.page_count):
            page = doc[page_num]

            # Get physical page dimensions (in points, 72 points = 1 inch)
            page_rect = page.rect
            page_width_inches = page_rect.width / 72.0
            page_height_inches = page_rect.height / 72.0

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
            _save_image(img, img_bytes_io, fmt)
            img_bytes = img_bytes_io.getvalue()

            # Resize if max_dimension specified
            if max_dimension:
                img_bytes, width, height = resize_image_for_llm(
                    img_bytes, max_dimension=max_dimension, fmt=fmt
                )
            else:
                width, height = pix.width, pix.height

            yield (page_num + 1, img_bytes, width, height, page_width_inches, page_height_inches)
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
    fmt: str = "TIFF",
    max_dimension: int | None = None,
) -> Iterator[tuple[int, bytes, int, int]]:
    """Extract pages from multi-page TIFF as normalized images.

    Re-saves each page as a clean raster image for consistent OCR/LLM processing.

    Args:
        tiff_bytes: TIFF file contents
        target_dpi: Target resolution for output
        fmt: Output format (TIFF recommended for consistency)
        max_dimension: If provided, resize images so longest edge <= this value

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

            # Convert to bytes (re-save as normalized TIFF)
            img_bytes_io = io.BytesIO()
            _save_image(rgb_img, img_bytes_io, fmt)
            img_bytes = img_bytes_io.getvalue()

            page_num += 1

            # Resize if max_dimension specified
            if max_dimension:
                img_bytes, width, height = resize_image_for_llm(
                    img_bytes, max_dimension=max_dimension, fmt=fmt
                )
            else:
                width, height = rgb_img.size

            yield (page_num, img_bytes, width, height)

            # Move to next page
            img.seek(page_num)
    except EOFError:
        # No more pages
        pass


def convert_to_png(image_bytes: bytes) -> bytes:
    """Convert image bytes to PNG format.

    Args:
        image_bytes: Source image bytes (any format PIL supports)

    Returns:
        PNG image bytes
    """
    img = Image.open(io.BytesIO(image_bytes))

    # Convert to RGB if needed
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    output = io.BytesIO()
    img.save(output, format="PNG")
    return output.getvalue()


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
