# Test Data for E2E Tests

Place test PDF files in this directory for end-to-end testing.

## Quick Start

1. Copy any construction plan PDF into this folder
2. Run the E2E tests:

```bash
# From project root
cd docker
docker compose exec -e PYTHONPATH=/app api pytest tests/e2e/ -v -s

# Or use make
make test-e2e
```

## Recommended Test Files

### Minimum: One Foundation/Slab Plan
Any PDF with:
- Clear scale notation (e.g., 1/4" = 1'-0")  
- Concrete areas (slabs, footings)
- Readable text for OCR testing

### Ideal Test Set

| File | Purpose | Notes |
|------|---------|-------|
| `foundation_plan.pdf` | Single page foundation | Tests basic flow |
| `slab_plan.pdf` | Floor plan with SOG | Tests area takeoff |
| `full_plan_set.pdf` | Multi-page set | Tests classification |

## What Gets Tested

With PDFs in this folder, the E2E tests will:

1. **Upload & Process** - Upload PDF, extract pages, run OCR
2. **Classify Pages** - AI classification of page types  
3. **Detect Scale** - Find scale notation on drawings
4. **Calibrate** - Manual scale calibration workflow
5. **Create Conditions** - Set up takeoff conditions
6. **Manual Takeoff** - Draw measurements manually
7. **AI Takeoff** - LLM-powered element detection
8. **Verify Accuracy** - Check measurement calculations

## Test Commands

```bash
# Quick health check (no PDFs needed)
make test-e2e-quick

# Full E2E suite (needs PDFs)
make test-e2e

# Just AI takeoff tests (needs PDFs + LLM keys)
make test-e2e-ai

# Measurement accuracy (no PDFs needed)
make test-e2e-accuracy
```

## Expected Output

With PDFs present, you should see:

```
tests/e2e/test_document_upload.py::TestDocumentUpload::test_upload_pdf
  Uploading: foundation_plan.pdf
  Document ID: abc-123-...
  ✓ Upload successful

tests/e2e/test_takeoff_workflow.py::TestAITakeoff::test_ai_takeoff_full_flow
  Step 1: Getting project documents...
  Step 2: Getting document pages...
  Step 3: Calibrating page scale...
  Step 4: Triggering AI takeoff...
  Step 5: Waiting for AI analysis... Done!
  Step 6: Verifying results...
    Provider: anthropic
    Model: claude-sonnet-4-20250514
    Elements detected: 5
    Measurements created: 5
  ✓ AI takeoff complete
```

## Validation Data (Optional)

For accuracy testing, create `validation.json`:

```json
{
  "foundation_plan.pdf": {
    "page_1": {
      "scale": "1/4\" = 1'-0\"",
      "expected_measurements": [
        {
          "condition": "Strip Footing",
          "quantity_min": 200,
          "quantity_max": 300,
          "unit": "LF"
        }
      ]
    }
  }
}
```

## Notes

- PDFs are gitignored - each developer adds their own test files
- Use plans you have rights to test with
- Smaller files (<10MB) process faster
- Multi-page sets test classification better
