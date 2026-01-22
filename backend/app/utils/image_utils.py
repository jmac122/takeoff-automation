"""Image utilities for OCR and region processing."""

from __future__ import annotations

import io
from typing import Any

from PIL import Image


def resolve_region_to_pixels(
    region: dict[str, Any],
    image_width: int,
    image_height: int,
) -> dict[str, int]:
    """Convert a normalized region into absolute pixel bounds.

    Args:
        region: Region dict with x/y/width/height, normalized 0-1.
        image_width: Full image width in pixels.
        image_height: Full image height in pixels.

    Returns:
        Dict with integer pixel x/y/width/height.
    """
    if not region:
        raise ValueError("Region is required")

    units = region.get("units", "normalized")
    if units not in ("normalized", "pixels"):
        raise ValueError(f"Unsupported region units: {units}")

    if units == "pixels":
        x = int(round(region["x"]))
        y = int(round(region["y"]))
        width = int(round(region["width"]))
        height = int(round(region["height"]))
    else:
        x = int(round(region["x"] * image_width))
        y = int(round(region["y"] * image_height))
        width = int(round(region["width"] * image_width))
        height = int(round(region["height"] * image_height))

    # Clamp to image bounds
    x = max(0, min(x, image_width - 1))
    y = max(0, min(y, image_height - 1))
    width = max(1, min(width, image_width - x))
    height = max(1, min(height, image_height - y))

    return {"x": x, "y": y, "width": width, "height": height}


def crop_image_bytes(
    image_bytes: bytes,
    region: dict[str, int],
    fmt: str = "PNG",
) -> tuple[bytes, int, int]:
    """Crop an image to a region and return bytes.

    Args:
        image_bytes: Source image bytes.
        region: Pixel region with x/y/width/height.
        fmt: Output format (default PNG).

    Returns:
        Tuple of (cropped_image_bytes, width, height).
    """
    img = Image.open(io.BytesIO(image_bytes))

    # Convert to RGB for consistent OCR input
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    left = region["x"]
    upper = region["y"]
    right = region["x"] + region["width"]
    lower = region["y"] + region["height"]

    cropped = img.crop((left, upper, right, lower))

    output = io.BytesIO()
    cropped.save(output, format=fmt)
    return output.getvalue(), cropped.width, cropped.height
