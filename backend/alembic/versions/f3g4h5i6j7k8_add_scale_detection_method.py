"""add scale detection method

Revision ID: f3g4h5i6j7k8
Revises: e1f2g3h4i5j6
Create Date: 2026-01-21 03:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f3g4h5i6j7k8"
down_revision: Union[str, None] = "e1f2g3h4i5j6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add scale_detection_method column to pages table."""
    op.add_column(
        "pages",
        sa.Column(
            "scale_detection_method",
            sa.String(50),
            nullable=True,
            comment="Method used to detect scale: vision_llm, ocr_predetected, ocr_pattern_match, manual_calibration, scale_bar",
        ),
    )

    # Set default for existing rows to 'ocr_predetected' if they have a scale
    op.execute("""
        UPDATE pages 
        SET scale_detection_method = 'ocr_predetected' 
        WHERE scale_value IS NOT NULL AND scale_text IS NOT NULL
    """)


def downgrade() -> None:
    """Remove scale_detection_method column from pages table."""
    op.drop_column("pages", "scale_detection_method")
