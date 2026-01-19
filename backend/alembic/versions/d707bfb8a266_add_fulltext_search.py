"""add_fulltext_search

Revision ID: d707bfb8a266
Revises: b01e3b57e974
Create Date: 2026-01-19 17:14:05.883003

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d707bfb8a266"
down_revision: Union[str, Sequence[str], None] = "b01e3b57e974"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add GIN index for full-text search on OCR text
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_pages_ocr_text_search 
        ON pages 
        USING gin(to_tsvector('english', COALESCE(ocr_text, '')));
    """)

    # Add trigram index for fuzzy matching
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_pages_ocr_text_trgm 
        ON pages 
        USING gin(ocr_text gin_trgm_ops);
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX IF EXISTS idx_pages_ocr_text_search;")
    op.execute("DROP INDEX IF EXISTS idx_pages_ocr_text_trgm;")
