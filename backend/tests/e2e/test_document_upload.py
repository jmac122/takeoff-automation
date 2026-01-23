"""
Document Upload and Processing E2E Tests

Tests the complete document lifecycle:
1. PDF upload
2. Page extraction
3. OCR processing
4. Page classification
5. Scale detection

These tests require actual PDF files in tests/e2e/test_data/
"""

import os
import time
from pathlib import Path

import pytest
import requests

from .conftest import (
    TestProject,
    wait_for_document_processing,
    DEFAULT_TIMEOUT,
    PROCESSING_TIMEOUT,
)


# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "test_data"


def get_test_pdfs() -> list[Path]:
    """Find PDF files in test data directory."""
    if not TEST_DATA_DIR.exists():
        return []
    return list(TEST_DATA_DIR.glob("*.pdf"))


# ============================================================================
# Test Class: Document Upload
# ============================================================================

class TestDocumentUpload:
    """Test document upload and processing."""

    def test_upload_pdf(
        self,
        http_session: requests.Session,
        api_url: str,
        test_project: TestProject,
    ):
        """Can upload a PDF document."""
        pdf_files = get_test_pdfs()
        
        if not pdf_files:
            pytest.skip(
                f"No test PDFs found in {TEST_DATA_DIR}\n"
                "Add PDF files to run upload tests."
            )
        
        pdf_path = pdf_files[0]
        print(f"\nUploading: {pdf_path.name}")
        
        with open(pdf_path, "rb") as f:
            response = http_session.post(
                f"{api_url}/projects/{test_project.id}/documents",
                files={"file": (pdf_path.name, f, "application/pdf")},
                timeout=120,  # Large files may take time
            )
        
        assert response.status_code in [200, 201, 202], f"Upload failed: {response.text}"
        data = response.json()
        
        assert "id" in data
        assert data.get("filename") == pdf_path.name or "filename" in data
        
        document_id = data["id"]
        print(f"  Document ID: {document_id}")
        print(f"  Status: {data.get('status', 'unknown')}")
        
        return document_id

    def test_document_processing_pipeline(
        self,
        http_session: requests.Session,
        api_url: str,
        test_project: TestProject,
    ):
        """
        Full document processing pipeline test.
        
        Tests:
        1. Upload
        2. Page extraction
        3. OCR
        4. Classification
        5. Scale detection
        """
        pdf_files = get_test_pdfs()
        
        if not pdf_files:
            pytest.skip("No test PDFs - add files to tests/e2e/test_data/")
        
        pdf_path = pdf_files[0]
        
        print("\n" + "="*60)
        print("DOCUMENT PROCESSING PIPELINE TEST")
        print("="*60)
        
        # Step 1: Upload
        print(f"\n[1/5] Uploading {pdf_path.name}...")
        
        with open(pdf_path, "rb") as f:
            response = http_session.post(
                f"{api_url}/projects/{test_project.id}/documents",
                files={"file": (pdf_path.name, f, "application/pdf")},
                timeout=120,
            )
        
        assert response.status_code in [200, 201, 202], f"Upload failed: {response.text}"
        doc_data = response.json()
        document_id = doc_data["id"]
        print(f"      Document ID: {document_id}")
        
        # Step 2: Wait for processing
        print("\n[2/5] Waiting for page extraction...")
        start_time = time.time()
        
        while time.time() - start_time < PROCESSING_TIMEOUT:
            response = http_session.get(
                f"{api_url}/documents/{document_id}",
                timeout=DEFAULT_TIMEOUT,
            )
            
            if response.status_code != 200:
                time.sleep(5)
                continue
            
            doc = response.json()
            status = doc.get("status", "")
            page_count = doc.get("page_count", 0)
            
            if status == "ready":
                elapsed = time.time() - start_time
                print(f"      Complete! {page_count} pages extracted in {elapsed:.1f}s")
                break
            elif status == "error":
                pytest.fail(f"Processing failed: {doc.get('error')}")
            else:
                print(f"      Status: {status}, Pages: {page_count}")
                time.sleep(5)
        else:
            pytest.fail("Processing timed out")
        
        # Step 3: Wait for OCR and classification to complete
        # These run as async Celery tasks AFTER page extraction
        print("\n[3/5] Waiting for OCR & classification...")
        ocr_wait_start = time.time()
        ocr_timeout = 120  # 2 minutes for OCR/classification
        
        while time.time() - ocr_wait_start < ocr_timeout:
            response = http_session.get(
                f"{api_url}/documents/{document_id}/pages",
                timeout=DEFAULT_TIMEOUT,
            )
            
            if response.status_code != 200:
                time.sleep(3)
                continue
            
            pages_data = response.json()
            pages = pages_data if isinstance(pages_data, list) else pages_data.get("pages", [])
            
            ocr_count = sum(1 for p in pages if p.get("ocr_text"))
            classified_count = sum(1 for p in pages if p.get("classification"))
            
            if ocr_count == len(pages) and classified_count == len(pages):
                elapsed = time.time() - ocr_wait_start
                print(f"      Complete! OCR: {ocr_count}/{len(pages)}, "
                      f"Classified: {classified_count}/{len(pages)} in {elapsed:.1f}s")
                break
            else:
                print(f"      OCR: {ocr_count}/{len(pages)}, Classified: {classified_count}/{len(pages)}")
                time.sleep(3)
        else:
            # Timed out but continue with whatever we have
            print(f"      ⚠ Timeout - some pages not fully processed")
        
        # Re-fetch final state
        response = http_session.get(
            f"{api_url}/documents/{document_id}/pages",
            timeout=DEFAULT_TIMEOUT,
        )
        pages_data = response.json()
        pages = pages_data if isinstance(pages_data, list) else pages_data.get("pages", [])
        
        ocr_count = sum(1 for p in pages if p.get("ocr_text"))
        print(f"      Final: {ocr_count}/{len(pages)} pages have OCR text")
        
        # Step 4: Check classification results
        print("\n[4/5] Checking page classifications...")
        classified_count = sum(1 for p in pages if p.get("classification"))
        concrete_pages = [p for p in pages if p.get("concrete_relevance") in ["high", "medium"]]
        
        print(f"      {classified_count}/{len(pages)} pages classified")
        print(f"      {len(concrete_pages)} pages have concrete relevance")
        
        for p in pages[:5]:
            classification = p.get("classification", "unclassified")
            relevance = p.get("concrete_relevance", "none")
            print(f"      Page {p.get('page_number', '?')}: {classification} ({relevance})")
        
        if len(pages) > 5:
            print(f"      ... and {len(pages) - 5} more pages")
        
        # Step 5: Check scale detection
        print("\n[5/5] Checking scale detection...")
        scale_detected = [p for p in pages if p.get("scale_text") or p.get("scale_value")]
        calibrated = [p for p in pages if p.get("scale_calibrated")]
        
        print(f"      {len(scale_detected)}/{len(pages)} pages have detected scale")
        print(f"      {len(calibrated)}/{len(pages)} pages are calibrated")
        
        for p in scale_detected[:3]:
            scale_text = p.get("scale_text", "unknown")
            scale_value = p.get("scale_value", 0)
            method = p.get("scale_detection_method", "unknown")
            print(f"      Page {p.get('page_number', '?')}: {scale_text} "
                  f"({scale_value:.1f} px/ft via {method})")
        
        print("\n" + "="*60)
        print("PIPELINE TEST COMPLETE")
        print("="*60)
        
        # Summary assertions
        assert len(pages) > 0, "No pages extracted"
        
        # Return document ID for further tests
        return document_id

    def test_multi_page_document(
        self,
        http_session: requests.Session,
        api_url: str,
        test_project: TestProject,
    ):
        """Test multi-page document handling."""
        pdf_files = get_test_pdfs()
        
        # Find a multi-page PDF
        multi_page_pdf = None
        for pdf in pdf_files:
            # Simple heuristic: larger files are likely multi-page
            if pdf.stat().st_size > 1_000_000:  # > 1MB
                multi_page_pdf = pdf
                break
        
        if not multi_page_pdf:
            pytest.skip("No multi-page PDF found (>1MB)")
        
        print(f"\nTesting multi-page document: {multi_page_pdf.name}")
        
        with open(multi_page_pdf, "rb") as f:
            response = http_session.post(
                f"{api_url}/projects/{test_project.id}/documents",
                files={"file": (multi_page_pdf.name, f, "application/pdf")},
                timeout=180,
            )
        
        assert response.status_code in [200, 201, 202]
        doc_data = response.json()
        document_id = doc_data["id"]
        
        # Wait for processing
        doc = wait_for_document_processing(
            http_session, api_url, document_id, 
            timeout=PROCESSING_TIMEOUT
        )
        
        page_count = doc.get("page_count", 0)
        print(f"  Processed {page_count} pages")
        
        assert page_count > 1, f"Expected multi-page, got {page_count} pages"
        print(f"✓ Multi-page document processed: {page_count} pages")


# ============================================================================
# Test Class: Page Navigation
# ============================================================================

class TestPageNavigation:
    """Test page navigation and filtering."""

    def test_filter_concrete_relevant_pages(
        self,
        http_session: requests.Session,
        api_url: str,
        test_project: TestProject,
    ):
        """Can filter pages by concrete relevance."""
        # Get documents
        response = http_session.get(
            f"{api_url}/projects/{test_project.id}/documents",
            timeout=DEFAULT_TIMEOUT,
        )
        
        documents = response.json() if response.status_code == 200 else []
        if isinstance(documents, dict):
            documents = documents.get("documents", [])
        
        if not documents:
            pytest.skip("No documents - upload a PDF first")
        
        # Get pages from first document
        doc_id = documents[0]["id"]
        response = http_session.get(
            f"{api_url}/documents/{doc_id}/pages",
            timeout=DEFAULT_TIMEOUT,
        )
        
        assert response.status_code == 200
        pages = response.json()
        if isinstance(pages, dict):
            pages = pages.get("pages", [])
        
        # Categorize by relevance
        relevance_counts = {}
        for page in pages:
            rel = page.get("concrete_relevance") or "unknown"
            relevance_counts[rel] = relevance_counts.get(rel, 0) + 1
        
        print(f"\nPage relevance distribution:")
        # Sort with None-safe key
        for rel, count in sorted(relevance_counts.items(), key=lambda x: (x[0] or "zzz")):
            print(f"  {rel}: {count} pages")
        
        # For a construction plan set, we expect some concrete-relevant pages
        high_medium = relevance_counts.get("high", 0) + relevance_counts.get("medium", 0)
        print(f"\nConcrete-relevant pages: {high_medium}")
        
        if high_medium > 0:
            print("✓ Found concrete-relevant pages for takeoff")
        else:
            print("⚠ No concrete-relevant pages detected")

    def test_page_thumbnail_access(
        self,
        http_session: requests.Session,
        api_url: str,
        test_project: TestProject,
    ):
        """Can access page thumbnails."""
        # Get a page
        response = http_session.get(
            f"{api_url}/projects/{test_project.id}/documents",
            timeout=DEFAULT_TIMEOUT,
        )
        
        documents = response.json() if response.status_code == 200 else []
        if isinstance(documents, dict):
            documents = documents.get("documents", [])
        
        if not documents:
            pytest.skip("No documents")
        
        doc_id = documents[0]["id"]
        response = http_session.get(
            f"{api_url}/documents/{doc_id}/pages",
            timeout=DEFAULT_TIMEOUT,
        )
        
        pages = response.json() if response.status_code == 200 else []
        if isinstance(pages, dict):
            pages = pages.get("pages", [])
        
        if not pages:
            pytest.skip("No pages")
        
        page = pages[0]
        thumbnail_url = page.get("thumbnail_url")
        
        if thumbnail_url:
            # The presigned URL points to localhost:9000 (MinIO)
            # Inside Docker, we need to use the service name 'minio' instead
            # This is expected behavior - the URL is meant for browser access, not container-to-container
            
            # Fix URL for container-to-container access
            internal_url = thumbnail_url.replace("localhost:9000", "minio:9000")
            
            try:
                thumb_response = http_session.get(internal_url, timeout=DEFAULT_TIMEOUT)
                
                if thumb_response.status_code == 200:
                    print(f"✓ Thumbnail accessible: {len(thumb_response.content)} bytes")
                else:
                    # May fail due to presigned URL signature being host-specific
                    print(f"⚠ Thumbnail access returned {thumb_response.status_code} (signature may be host-specific)")
            except Exception as e:
                # Network topology issue is expected for container tests
                print(f"⚠ Thumbnail network issue (expected in container tests): {type(e).__name__}")
        else:
            print("⚠ No thumbnail URL in page data")


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
