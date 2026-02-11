"""add review fields and measurement_history table

Revision ID: o3p4q5r6s7t8
Revises: n2o3p4q5r6s7
Create Date: 2026-02-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'o3p4q5r6s7t8'
down_revision: Union[str, Sequence[str], None] = 'n2o3p4q5r6s7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create measurement_history table
    op.create_table(
        'measurement_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('measurement_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('actor', sa.String(255), nullable=False),
        sa.Column('actor_type', sa.String(50), nullable=False, server_default='user'),
        sa.Column('previous_status', sa.String(50), nullable=True),
        sa.Column('new_status', sa.String(50), nullable=True),
        sa.Column('previous_geometry', postgresql.JSONB(), nullable=True),
        sa.Column('new_geometry', postgresql.JSONB(), nullable=True),
        sa.Column('previous_quantity', sa.Float(), nullable=True),
        sa.Column('new_quantity', sa.Float(), nullable=True),
        sa.Column('change_description', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['measurement_id'], ['measurements.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_measurement_history_measurement_id', 'measurement_history', ['measurement_id'])

    # Add review fields to measurements table
    op.add_column(
        'measurements',
        sa.Column('is_rejected', sa.Boolean(), nullable=False, server_default=sa.text('false')),
    )
    op.add_column(
        'measurements',
        sa.Column('rejection_reason', sa.Text(), nullable=True),
    )
    op.add_column(
        'measurements',
        sa.Column('review_notes', sa.Text(), nullable=True),
    )
    op.add_column(
        'measurements',
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        'measurements',
        sa.Column('original_geometry', postgresql.JSONB(), nullable=True),
    )
    op.add_column(
        'measurements',
        sa.Column('original_quantity', sa.Float(), nullable=True),
    )
    op.create_index('ix_measurements_is_rejected', 'measurements', ['is_rejected'])


def downgrade() -> None:
    op.drop_index('ix_measurements_is_rejected', table_name='measurements')
    op.drop_column('measurements', 'original_quantity')
    op.drop_column('measurements', 'original_geometry')
    op.drop_column('measurements', 'reviewed_at')
    op.drop_column('measurements', 'review_notes')
    op.drop_column('measurements', 'rejection_reason')
    op.drop_column('measurements', 'is_rejected')

    op.drop_index('ix_measurement_history_measurement_id', table_name='measurement_history')
    op.drop_table('measurement_history')
