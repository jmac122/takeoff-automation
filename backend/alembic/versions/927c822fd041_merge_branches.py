"""merge_branches

Revision ID: 927c822fd041
Revises: d5b881957963, g4h5i6j7k8l9
Create Date: 2026-01-22 01:14:49.928525

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '927c822fd041'
down_revision: Union[str, Sequence[str], None] = ('d5b881957963', 'g4h5i6j7k8l9')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
