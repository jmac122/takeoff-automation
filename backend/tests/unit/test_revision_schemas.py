"""Unit tests for revision-related schemas."""

import uuid
from datetime import date, datetime

import pytest

from app.schemas.document import (
    LinkRevisionRequest,
    RevisionChainItem,
    RevisionChainResponse,
    PageComparisonRequest,
    PageComparisonResponse,
)


class TestLinkRevisionRequest:

    def test_minimal_fields(self):
        """Only supersedes_document_id is required."""
        doc_id = uuid.uuid4()
        req = LinkRevisionRequest(supersedes_document_id=doc_id)
        assert req.supersedes_document_id == doc_id
        assert req.revision_number is None
        assert req.revision_date is None
        assert req.revision_label is None

    def test_all_fields(self):
        """All optional fields can be set."""
        doc_id = uuid.uuid4()
        req = LinkRevisionRequest(
            supersedes_document_id=doc_id,
            revision_number="B",
            revision_date=date(2025, 6, 15),
            revision_label="Issued for Permit",
        )
        assert req.revision_number == "B"
        assert req.revision_date == date(2025, 6, 15)
        assert req.revision_label == "Issued for Permit"


class TestRevisionChainItem:

    def test_fields(self):
        item_id = uuid.uuid4()
        item = RevisionChainItem(
            id=item_id,
            original_filename="drawing-v2.pdf",
            revision_number="2",
            revision_date=date(2025, 3, 1),
            revision_label="For Construction",
            is_latest_revision=True,
            page_count=10,
            created_at=datetime(2025, 3, 1, 10, 0, 0),
        )
        assert item.id == item_id
        assert item.original_filename == "drawing-v2.pdf"
        assert item.is_latest_revision is True
        assert item.page_count == 10


class TestRevisionChainResponse:

    def test_chain_with_items(self):
        doc_id = uuid.uuid4()
        item1 = RevisionChainItem(
            id=uuid.uuid4(),
            original_filename="v1.pdf",
            revision_number="A",
            revision_date=None,
            revision_label=None,
            is_latest_revision=False,
            page_count=5,
            created_at=datetime(2025, 1, 1),
        )
        item2 = RevisionChainItem(
            id=doc_id,
            original_filename="v2.pdf",
            revision_number="B",
            revision_date=None,
            revision_label=None,
            is_latest_revision=True,
            page_count=5,
            created_at=datetime(2025, 2, 1),
        )
        resp = RevisionChainResponse(
            chain=[item1, item2],
            current_document_id=doc_id,
        )
        assert len(resp.chain) == 2
        assert resp.current_document_id == doc_id

    def test_empty_chain(self):
        doc_id = uuid.uuid4()
        resp = RevisionChainResponse(chain=[], current_document_id=doc_id)
        assert len(resp.chain) == 0


class TestPageComparisonRequest:

    def test_fields(self):
        req = PageComparisonRequest(
            old_document_id=uuid.uuid4(),
            new_document_id=uuid.uuid4(),
            page_number=3,
        )
        assert req.page_number == 3


class TestPageComparisonResponse:

    def test_both_pages_present(self):
        resp = PageComparisonResponse(
            old_page_id=uuid.uuid4(),
            new_page_id=uuid.uuid4(),
            old_image_url="https://example.com/old.png",
            new_image_url="https://example.com/new.png",
            page_number=1,
            has_both=True,
        )
        assert resp.has_both is True
        assert resp.old_image_url is not None
        assert resp.new_image_url is not None

    def test_one_page_missing(self):
        resp = PageComparisonResponse(
            old_page_id=None,
            new_page_id=uuid.uuid4(),
            old_image_url=None,
            new_image_url="https://example.com/new.png",
            page_number=2,
            has_both=False,
        )
        assert resp.has_both is False
        assert resp.old_page_id is None
        assert resp.old_image_url is None

    def test_neither_page_present(self):
        resp = PageComparisonResponse(
            old_page_id=None,
            new_page_id=None,
            old_image_url=None,
            new_image_url=None,
            page_number=5,
            has_both=False,
        )
        assert resp.has_both is False
