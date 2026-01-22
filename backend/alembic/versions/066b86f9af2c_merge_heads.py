"""merge heads

Revision ID: 066b86f9af2c
Revises: 927c822fd041, h1i2j3k4l5m6
Create Date: 2026-01-22 17:35:22.406044

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '066b86f9af2c'
down_revision: Union[str, Sequence[str], None] = ('927c822fd041', 'h1i2j3k4l5m6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
