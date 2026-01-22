import io

from PIL import Image

from app.services.ocr_service import TextBlock, TitleBlockParser
from app.utils.image_utils import crop_image_bytes, resolve_region_to_pixels


def test_resolve_region_to_pixels_clamps_bounds() -> None:
    region = {"x": 0.9, "y": 0.9, "width": 0.2, "height": 0.2}
    resolved = resolve_region_to_pixels(region, image_width=100, image_height=200)

    assert resolved["x"] == 90
    assert resolved["y"] == 180
    assert resolved["width"] == 10
    assert resolved["height"] == 20


def test_crop_image_bytes_returns_expected_size() -> None:
    img = Image.new("RGB", (100, 80), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_bytes = buf.getvalue()

    region = {"x": 10, "y": 5, "width": 30, "height": 20}
    cropped_bytes, width, height = crop_image_bytes(img_bytes, region, fmt="PNG")

    assert width == 30
    assert height == 20
    assert len(cropped_bytes) > 0


def test_title_block_parser_full_region_uses_all_blocks() -> None:
    blocks = [
        TextBlock(
            text="SHEET NO: A1.01",
            confidence=0.9,
            bounding_box={"x": 10, "y": 10, "width": 100, "height": 20},
        ),
        TextBlock(
            text="TITLE: FIRST FLOOR PLAN",
            confidence=0.9,
            bounding_box={"x": 10, "y": 40, "width": 200, "height": 20},
        ),
    ]

    parser = TitleBlockParser()

    result_default = parser.parse_title_block(
        blocks,
        page_width=1000,
        page_height=1000,
        use_full_region=False,
    )
    assert result_default["sheet_number"] is None
    assert result_default["sheet_title"] is None

    result_full = parser.parse_title_block(
        blocks,
        page_width=1000,
        page_height=1000,
        use_full_region=True,
    )
    assert result_full["sheet_number"] == "A1.01"
    assert result_full["sheet_title"] == "FIRST FLOOR PLAN"
