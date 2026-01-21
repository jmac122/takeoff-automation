"""increase_ocr_field_lengths

Revision ID: d5b881957963
Revises: 0f19e78be270
Create Date: 2026-01-21 00:41:38

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d5b881957963"
down_revision: Union[str, None] = "0f19e78be270"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Increase column lengths for OCR-extracted fields
    # title: 500 -> 2000 (can be long descriptive text)
    # sheet_number: 500 -> 1000 (can include full sheet titles)
    # scale_text: 500 -> 500 (already sufficient)

    op.alter_column(
        "pages",
        "title",
        existing_type=sa.String(500),
        type_=sa.String(2000),
        existing_nullable=True,
    )

    op.alter_column(
        "pages",
        "sheet_number",
        existing_type=sa.String(500),
        type_=sa.String(1000),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "pages",
        "sheet_number",
        existing_type=sa.String(1000),
        type_=sa.String(500),
        existing_nullable=True,
    )

    op.alter_column(
        "pages",
        "title",
        existing_type=sa.String(2000),
        type_=sa.String(500),
        existing_nullable=True,
    )
