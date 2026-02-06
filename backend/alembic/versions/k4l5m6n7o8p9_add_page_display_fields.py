"""Add page display fields for UI overhaul Phase A.

Revision ID: k4l5m6n7o8p9
Revises: j3k4l5m6n7o8
Create Date: 2026-02-06 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'k4l5m6n7o8p9'
down_revision = 'j3k4l5m6n7o8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('pages', sa.Column('display_name', sa.String(255), nullable=True))
    op.add_column('pages', sa.Column('display_order', sa.Integer(), nullable=True))
    op.add_column('pages', sa.Column('group_name', sa.String(100), nullable=True))
    op.add_column('pages', sa.Column('is_relevant', sa.Boolean(), nullable=False, server_default=sa.text('true')))


def downgrade() -> None:
    op.drop_column('pages', 'is_relevant')
    op.drop_column('pages', 'group_name')
    op.drop_column('pages', 'display_order')
    op.drop_column('pages', 'display_name')
