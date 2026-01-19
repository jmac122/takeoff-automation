#!/usr/bin/env python3
"""Verification script for Phase 1A: Document Ingestion"""

import os
import tempfile
from pathlib import Path

import structlog
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, Session

from app.models.base import Base
from app.models.document import Document
from app.models.page import Page
from app.models.project import Project
from app.models.condition import Condition
from app.models.measurement import Measurement
from app.utils.pdf_utils import (
    validate_pdf,
    validate_tiff,
    get_pdf_page_count,
    get_tiff_page_count,
)

# Configure logging
logger = structlog.get_logger()

# Setup database
DATABASE_URL = "sqlite:///test_verification.db"
engine = create_engine(DATABASE_URL)
session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def setup_database():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)
    print("Database tables created")


def create_test_project():
    """Create a test project"""
    with session_local() as session:
        project = Project(
            name="Test Project",
            description="Verification test project",
            client_name="Test Client",
        )
        session.add(project)
        session.commit()
        session.refresh(project)
        print(f"Test project created with ID: {project.id}")
        return project.id


def test_pdf_validation():
    """Test PDF validation"""
    # Create a minimal valid PDF
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(Hello World) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n0000000200 00000 n\ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n284\n%%EOF"

    is_valid, error = validate_pdf(pdf_content)
    if is_valid:
        print("PDF validation works")
        return pdf_content
    else:
        print(f"PDF validation failed: {error}")
        return None


def test_tiff_validation():
    """Test TIFF validation"""
    # Create a minimal TIFF header
    tiff_content = b"II*\x00\x08\x00\x00\x00\x10\x00\x00\x01\x03\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x01\x03\x00\x01\x00\x00\x00\x01\x00\x00\x00\x02\x01\x03\x00\x03\x00\x00\x00\x1a\x00\x00\x00\x03\x01\x03\x00\x01\x00\x00\x00\x08\x00\x00\x00\x06\x01\x03\x00\x01\x00\x00\x00\x01\x00\x00\x00\x11\x01\x04\x00\x01\x00\x00\x00\x08\x00\x00\x00\x15\x01\x03\x00\x01\x00\x00\x00\x03\x00\x00\x00\x16\x01\x03\x00\x01\x00\x00\x00\x01\x00\x00\x00\x17\x01\x04\x00\x01\x00\x00\x00\x02\x00\x00\x00\x1a\x01\x05\x00\x01\x00\x00\x00\x48\x00\x00\x00\x1b\x01\x05\x00\x01\x00\x00\x00\x50\x00\x00\x00\x00\x00\x00\x00"

    is_valid, error = validate_tiff(tiff_content)
    if is_valid:
        print("TIFF validation works")
        return tiff_content
    else:
        print(f"TIFF validation failed: {error}")
        return None


def test_document_processing(pdf_content, tiff_content, project_id):
    """Test document processing"""
    print("Document processing test skipped - requires storage service setup")


def test_storage_service():
    """Test storage service"""
    print("Storage service test skipped - requires MinIO setup")


def main():
    """Run all verification tests"""
    print("Starting Phase 1A Verification\n")

    # Setup
    setup_database()
    project_id = create_test_project()

    # Test PDF validation
    pdf_content = test_pdf_validation()

    # Test TIFF validation
    tiff_content = test_tiff_validation()

    # Test processing
    if pdf_content and tiff_content:
        test_document_processing(pdf_content, tiff_content, project_id)

    # Test storage
    test_storage_service()

    print("\nVerification complete!")


if __name__ == "__main__":
    main()
