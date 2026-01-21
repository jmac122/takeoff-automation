# OCR Service Documentation

## Overview

The OCR (Optical Character Recognition) service extracts text from construction plan images using Google Cloud Vision API. It provides pattern-based detection for scales, sheet numbers, and titles, along with title block parsing for structured metadata extraction.

**Location:** `backend/app/services/ocr_service.py`

---

## Architecture

### Components

```
┌─────────────────────────────────────────────────────┐
│                  OCR Service                        │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────┐      ┌──────────────────┐       │
│  │  OCRService  │      │ TitleBlockParser │       │
│  └──────┬───────┘      └────────┬─────────┘       │
│         │                       │                  │
│         ▼                       ▼                  │
│  ┌──────────────────────────────────────┐         │
│  │     Google Cloud Vision API          │         │
│  └──────────────────────────────────────┘         │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Data Flow

```
Image Bytes
    ↓
Google Cloud Vision API
    ↓
Document Text Detection
    ↓
Extract Full Text + Blocks
    ↓
Pattern Detection (Scales, Sheet Numbers, Titles)
    ↓
Title Block Parsing
    ↓
OCRResult (structured data)
```

---

## Classes

### TextBlock

Represents a detected text block with position and confidence.

```python
@dataclass
class TextBlock:
    text: str                      # Extracted text
    confidence: float              # Detection confidence (0-1)
    bounding_box: dict[str, int]  # {x, y, width, height}
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
```

**Example:**
```python
block = TextBlock(
    text="FOUNDATION PLAN",
    confidence=0.98,
    bounding_box={"x": 100, "y": 50, "width": 400, "height": 60}
)
```

---

### OCRResult

Complete OCR result for a page.

```python
@dataclass
class OCRResult:
    full_text: str                    # Complete extracted text
    blocks: list[TextBlock]           # Individual text blocks
    detected_scale_texts: list[str]   # Found scale notations
    detected_sheet_numbers: list[str] # Found sheet numbers
    detected_titles: list[str]        # Found titles
```

**Example:**
```python
result = OCRResult(
    full_text="FOUNDATION PLAN\nSCALE: 1/4\" = 1'-0\"\n...",
    blocks=[block1, block2, ...],
    detected_scale_texts=["1/4\" = 1'-0\""],
    detected_sheet_numbers=["A1.01"],
    detected_titles=["FOUNDATION PLAN"]
)
```

---

### OCRService

Main service class for text extraction.

#### Initialization

```python
service = OCRService()
# Creates Google Cloud Vision ImageAnnotatorClient
```

**Requirements:**
- `GOOGLE_APPLICATION_CREDENTIALS` environment variable set
- Google Cloud Vision API enabled
- Service account with Vision API permissions

#### Methods

##### extract_text()

Extract text from an image.

```python
def extract_text(self, image_bytes: bytes) -> OCRResult:
    """
    Extract text from an image using Google Cloud Vision.
    
    Args:
        image_bytes: Image file contents (PNG, JPEG, TIFF)
        
    Returns:
        OCRResult with full text and structured blocks
        
    Raises:
        RuntimeError: If Vision API returns an error
    """
```

**Example:**
```python
from app.services.ocr_service import get_ocr_service

service = get_ocr_service()

with open("plan.png", "rb") as f:
    image_bytes = f.read()

result = service.extract_text(image_bytes)

print(f"Extracted {len(result.full_text)} characters")
print(f"Found {len(result.blocks)} text blocks")
print(f"Detected scales: {result.detected_scale_texts}")
```

---

### Pattern Detection

#### Scale Patterns

Detects architectural, engineering, and metric scales.

```python
SCALE_PATTERNS = [
    r'(?:SCALE[:\s]*)?(\d+(?:/\d+)?["\']?\s*=\s*\d+[\'"]\s*-?\s*\d*[\'""]?)',
    r'(\d+/\d+"\s*=\s*1\'-0")',  # 1/4" = 1'-0"
    r'(\d+"\s*=\s*\d+\')',        # 1" = 10'
    r'SCALE[:\s]*1[:\s]*(\d+)',   # SCALE: 1:100
    r'(\d+:\d+)\s*SCALE',
    r'NTS|NOT\s*TO\s*SCALE',      # Not to scale
]
```

**Detected Formats:**
- Architectural: `1/4" = 1'-0"`, `1/8" = 1'-0"`
- Engineering: `1" = 10'`, `1" = 20'`
- Metric: `SCALE: 1:100`, `1:50`
- Special: `NTS`, `NOT TO SCALE`

#### Sheet Number Patterns

Detects standard sheet numbering formats.

```python
SHEET_NUMBER_PATTERNS = [
    r'\b([A-Z]{1,2}[-.]?\d{1,3}(?:\.\d{1,2})?)\b',  # A1.01, S-101
    r'SHEET\s*(?:NO\.?|NUMBER|#)?\s*:?\s*([A-Z0-9.-]+)',
    r'DWG\.?\s*(?:NO\.?)?:?\s*([A-Z0-9.-]+)',
]
```

**Detected Formats:**
- Standard: `A1.01`, `S-101`, `M101`
- With labels: `SHEET NO: A1.01`, `DWG. NO: S-101`

#### Title Patterns

Detects common drawing titles.

```python
TITLE_PATTERNS = [
    r'^([A-Z][A-Z\s]{3,40}(?:PLAN|ELEVATION|SECTION|DETAIL|SCHEDULE))$',
    r'TITLE[:\s]*([A-Z][A-Z\s]+)',
]
```

**Detected Formats:**
- Direct: `FOUNDATION PLAN`, `SITE ELEVATION`
- With label: `TITLE: FOUNDATION PLAN`

---

### TitleBlockParser

Extracts structured data from title blocks.

#### Methods

##### parse_title_block()

Parse title block from OCR blocks.

```python
def parse_title_block(
    self,
    blocks: list[TextBlock],
    page_width: int,
    page_height: int,
) -> dict[str, Any]:
    """
    Parse title block from OCR blocks.
    
    Title blocks are typically in the bottom-right corner.
    
    Args:
        blocks: List of detected text blocks
        page_width: Page width in pixels
        page_height: Page height in pixels
        
    Returns:
        Dictionary with extracted title block fields
    """
```

**Extracted Fields:**
- `sheet_number` - Drawing identifier (e.g., "A1.01")
- `sheet_title` - Drawing name (e.g., "FOUNDATION PLAN")
- `project_name` - Project identifier
- `project_number` - Job number
- `date` - Drawing date
- `revision` - Revision number/letter
- `scale` - Drawing scale
- `drawn_by` - Drafter initials
- `checked_by` - Checker initials

**Example:**
```python
from app.services.ocr_service import get_title_block_parser

parser = get_title_block_parser()

title_block = parser.parse_title_block(
    blocks=ocr_result.blocks,
    page_width=2550,
    page_height=3300
)

print(f"Sheet: {title_block['sheet_number']}")
print(f"Title: {title_block['sheet_title']}")
print(f"Scale: {title_block['scale']}")
```

**Title Block Region:**
- Bottom-right 30% x 30% of page
- Standard location for most construction drawings
- Parsed using regex patterns

---

## Usage Examples

### Basic OCR

```python
from app.services.ocr_service import get_ocr_service

# Get singleton instance
service = get_ocr_service()

# Read image
with open("plan.png", "rb") as f:
    image_bytes = f.read()

# Extract text
result = service.extract_text(image_bytes)

# Access results
print(f"Full text:\n{result.full_text}")
print(f"\nDetected scales: {result.detected_scale_texts}")
print(f"Sheet numbers: {result.detected_sheet_numbers}")
print(f"Titles: {result.detected_titles}")

# Access individual blocks
for block in result.blocks:
    print(f"Text: {block.text}")
    print(f"Confidence: {block.confidence}")
    print(f"Position: {block.bounding_box}")
```

### With Title Block Parsing

```python
from app.services.ocr_service import get_ocr_service, get_title_block_parser

# Extract text
service = get_ocr_service()
result = service.extract_text(image_bytes)

# Parse title block
parser = get_title_block_parser()
title_block = parser.parse_title_block(
    blocks=result.blocks,
    page_width=2550,
    page_height=3300
)

# Use extracted metadata
sheet_number = title_block['sheet_number'] or result.detected_sheet_numbers[0]
title = title_block['sheet_title'] or result.detected_titles[0]
scale = title_block['scale'] or result.detected_scale_texts[0]

print(f"Sheet: {sheet_number}")
print(f"Title: {title}")
print(f"Scale: {scale}")
```

### In Celery Task

```python
from app.services.ocr_service import get_ocr_service, get_title_block_parser
from app.utils.storage import get_storage_service

async def process_page_ocr(page_id: str):
    # Get services
    ocr_service = get_ocr_service()
    title_block_parser = get_title_block_parser()
    storage = get_storage_service()
    
    # Get page from database
    page = await get_page(page_id)
    
    # Download image
    image_bytes = storage.download_file(page.image_key)
    
    # Run OCR
    ocr_result = ocr_service.extract_text(image_bytes)
    
    # Parse title block
    title_block_data = title_block_parser.parse_title_block(
        ocr_result.blocks,
        page.width,
        page.height
    )
    
    # Update page with results
    page.ocr_text = ocr_result.full_text
    page.ocr_blocks = {
        "blocks": [b.to_dict() for b in ocr_result.blocks],
        "detected_scales": ocr_result.detected_scale_texts,
        "detected_sheet_numbers": ocr_result.detected_sheet_numbers,
        "detected_titles": ocr_result.detected_titles,
        "title_block": title_block_data,
    }
    
    # Set primary values
    page.sheet_number = (
        ocr_result.detected_sheet_numbers[0] 
        if ocr_result.detected_sheet_numbers 
        else title_block_data['sheet_number']
    )
    page.title = (
        ocr_result.detected_titles[0] 
        if ocr_result.detected_titles 
        else title_block_data['sheet_title']
    )
    page.scale_text = (
        ocr_result.detected_scale_texts[0] 
        if ocr_result.detected_scale_texts 
        else title_block_data['scale']
    )
    
    await save_page(page)
```

---

## Configuration

### Environment Variables

```bash
# Required: Path to Google Cloud service account JSON key
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

### Google Cloud Setup

1. **Create Project:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create new project or select existing

2. **Enable API:**
   - Navigate to "APIs & Services"
   - Enable "Cloud Vision API"

3. **Create Service Account:**
   - Go to "IAM & Admin" → "Service Accounts"
   - Create service account
   - Grant "Cloud Vision API User" role

4. **Download Key:**
   - Click on service account
   - Go to "Keys" tab
   - Add key → Create new key → JSON
   - Download and save securely

5. **Set Environment Variable:**
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
   ```

---

## Performance

### Processing Time

- **Single Page:** 1-3 seconds
- **Batch Processing:** Parallel via Celery
- **Network Latency:** ~500ms to Google Cloud

### Optimization Tips

1. **Image Size:** Resize large images to 2000-3000px width
2. **Format:** Use PNG or JPEG (avoid TIFF if possible)
3. **Quality:** Higher DPI = better OCR but slower
4. **Caching:** Store OCR results, don't reprocess

### Cost Considerations

**Google Cloud Vision Pricing:**
- First 1,000 images/month: **Free**
- 1,001 - 5,000,000: **$1.50 per 1,000 images**
- 5,000,001+: **$0.60 per 1,000 images**

**Example Costs:**
- 100-page document: $0.15
- 1,000-page project: $1.50
- 10,000 pages/month: $15.00

---

## Error Handling

### Common Errors

#### 1. Missing Credentials

```python
google.auth.exceptions.DefaultCredentialsError: 
Could not automatically determine credentials.
```

**Solution:**
```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
```

#### 2. API Not Enabled

```python
google.api_core.exceptions.PermissionDenied: 
Cloud Vision API has not been used in project...
```

**Solution:**
- Enable Cloud Vision API in Google Cloud Console

#### 3. Quota Exceeded

```python
google.api_core.exceptions.ResourceExhausted: 
Quota exceeded for quota metric...
```

**Solution:**
- Wait for quota reset
- Request quota increase
- Implement rate limiting

#### 4. Invalid Image Format

```python
RuntimeError: Vision API error: Invalid image content
```

**Solution:**
- Verify image format (PNG, JPEG, TIFF)
- Check image is not corrupted
- Ensure image size < 20MB

### Retry Logic

OCR tasks automatically retry on failure:

```python
@celery_app.task(bind=True, max_retries=3)
def process_page_ocr_task(self, page_id: str):
    try:
        # Process OCR
        ...
    except Exception as e:
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=30)
```

---

## Testing

### Unit Tests

```python
def test_scale_detection():
    """Test scale pattern detection."""
    service = OCRService()
    text = 'SCALE: 1/4" = 1\'-0"'
    scales = service._extract_scales(text)
    assert '1/4" = 1\'-0"' in scales

def test_sheet_number_detection():
    """Test sheet number detection."""
    service = OCRService()
    text = "SHEET NO: A1.01"
    blocks = []
    numbers = service._extract_sheet_numbers(text, blocks)
    assert "A1.01" in numbers

def test_title_block_parsing():
    """Test title block parsing."""
    parser = TitleBlockParser()
    blocks = [
        TextBlock("A1.01", 0.98, {"x": 2000, "y": 2800, "width": 100, "height": 30}),
        TextBlock("FOUNDATION PLAN", 0.95, {"x": 1800, "y": 2700, "width": 300, "height": 40})
    ]
    result = parser.parse_title_block(blocks, 2550, 3300)
    assert result['sheet_number'] == "A1.01"
```

### Integration Tests

```python
async def test_full_ocr_workflow():
    """Test complete OCR workflow."""
    # Upload document
    document = await upload_test_document()
    
    # Wait for OCR processing
    await wait_for_ocr(document.id)
    
    # Verify OCR results
    pages = await get_document_pages(document.id)
    assert all(page.ocr_text for page in pages)
    assert all(page.sheet_number for page in pages)
```

---

## Troubleshooting

### Debug OCR Results

```python
# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check what Vision API returns
result = service.extract_text(image_bytes)
print(f"Blocks detected: {len(result.blocks)}")
for block in result.blocks[:5]:  # First 5 blocks
    print(f"  {block.text} (confidence: {block.confidence})")
```

### Verify Patterns

```python
# Test pattern matching
import re

text = "SCALE: 1/4\" = 1'-0\""
for pattern in OCRService.SCALE_PATTERNS:
    matches = re.findall(pattern, text, re.IGNORECASE)
    if matches:
        print(f"Pattern matched: {pattern}")
        print(f"Matches: {matches}")
```

### Check Title Block Region

```python
# Visualize title block region
def show_title_block_region(blocks, page_width, page_height):
    title_block_x = page_width * 0.7
    title_block_y = page_height * 0.7
    
    title_blocks = [
        b for b in blocks
        if (b.bounding_box["x"] + b.bounding_box["width"]/2 > title_block_x
            and b.bounding_box["y"] + b.bounding_box["height"]/2 > title_block_y)
    ]
    
    print(f"Title block region: x>{title_block_x}, y>{title_block_y}")
    print(f"Blocks in title block: {len(title_blocks)}")
    for block in title_blocks:
        print(f"  {block.text}")
```

---

## Automatic Classification Integration

After OCR processing completes, the system automatically triggers **OCR-based classification** for each page. This provides instant, free classification using the extracted OCR data (sheet numbers, titles, text) without requiring expensive LLM vision calls.

**Classification Flow:**
```
OCR Extraction → Sheet Number/Title Detected → Auto-Classification
```

**Classification Method:**
- Uses `OCRPageClassifier` service (`backend/app/services/ocr_classifier.py`)
- Derives discipline from sheet prefix (S=Structural, A=Architectural, etc.)
- Derives page type from title keywords (PLAN, ELEVATION, SECTION, etc.)
- Assesses concrete relevance from text content
- **Result**: Instant classification (<100ms), $0 cost, 95%+ accuracy

**Manual Re-classification:**
- Users can trigger LLM vision classification via "Re-Classify" button
- Provides more detailed analysis for complex/non-standard sheets
- See [Classification Optimization](../CLASSIFICATION_OPTIMIZATION.md) for details

## Recent Updates (January 21, 2026)

### OCR Extraction Refinement

**Issue:** OCR service was extracting too much text for `title` and `sheet_number` fields, pulling data from the entire page instead of just the bottom-right corner where title blocks are typically located.

**Solution:** Modified `_extract_sheet_numbers` and `_extract_titles` methods in `backend/app/services/ocr_service.py` to restrict extraction to the bottom-right 30% x 30% region of the page, where title blocks are standardly located on construction drawings.

**Database Migration:** Created migration `d5b881957963_increase_ocr_field_lengths.py` to change `title` and `sheet_number` columns from `VARCHAR(500)` to `Text` type to accommodate longer extracted strings when needed.

**Impact:**
- More accurate sheet number and title extraction
- Reduced false positives from body text
- Maintains backward compatibility with existing data
- Improved data quality for classification and search

## Related Documentation

- [OCR API Reference](../api/OCR_API.md) - API endpoints
- [Database Schema](../database/DATABASE_SCHEMA.md) - OCR data storage
- [Phase 1B Complete](../phase-guides/PHASE_1B_COMPLETE.md) - Implementation guide
- [Classification Optimization](../CLASSIFICATION_OPTIMIZATION.md) - OCR-based classification details

---

**Last Updated:** January 21, 2026 - OCR extraction refinement and database column size fixes
