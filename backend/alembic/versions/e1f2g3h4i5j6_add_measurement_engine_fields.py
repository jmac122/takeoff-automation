"""add_measurement_engine_fields

Revision ID: e1f2g3h4i5j6
Revises: b2c3d4e5f6g7
Create Date: 2026-01-20 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e1f2g3h4i5j6'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6g7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to add measurement engine fields."""
    
    # Update conditions table
    op.add_column('conditions', sa.Column('scope', sa.String(length=100), server_default='concrete', nullable=False))
    op.add_column('conditions', sa.Column('category', sa.String(length=100), nullable=True))
    op.add_column('conditions', sa.Column('measurement_type', sa.String(length=50), nullable=False, server_default='linear'))
    op.add_column('conditions', sa.Column('color', sa.String(length=20), server_default='#3B82F6', nullable=False))
    op.add_column('conditions', sa.Column('line_width', sa.Integer(), server_default='2', nullable=False))
    op.add_column('conditions', sa.Column('fill_opacity', sa.Float(), server_default='0.3', nullable=False))
    op.add_column('conditions', sa.Column('depth', sa.Float(), nullable=True))
    op.add_column('conditions', sa.Column('thickness', sa.Float(), nullable=True))
    op.add_column('conditions', sa.Column('total_quantity', sa.Float(), server_default='0.0', nullable=False))
    op.add_column('conditions', sa.Column('measurement_count', sa.Integer(), server_default='0', nullable=False))
    op.add_column('conditions', sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False))
    op.add_column('conditions', sa.Column('extra_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    
    # Update default unit values for existing records
    op.execute("UPDATE conditions SET unit = 'LF' WHERE unit IS NULL OR unit = ''")
    
    # Update measurements table - replace old fields with new ones
    # First, add new columns
    op.add_column('measurements', sa.Column('unit', sa.String(length=50), nullable=False, server_default='LF'))
    op.add_column('measurements', sa.Column('pixel_length', sa.Float(), nullable=True))
    op.add_column('measurements', sa.Column('pixel_area', sa.Float(), nullable=True))
    op.add_column('measurements', sa.Column('is_ai_generated', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('measurements', sa.Column('ai_confidence', sa.Float(), nullable=True))
    op.add_column('measurements', sa.Column('ai_model', sa.String(length=100), nullable=True))
    op.add_column('measurements', sa.Column('is_modified', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('measurements', sa.Column('is_verified', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('measurements', sa.Column('extra_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    
    # Change geometry_data from JSON to JSONB
    op.alter_column('measurements', 'geometry_data',
                    existing_type=sa.JSON(),
                    type_=postgresql.JSONB(astext_type=sa.Text()),
                    existing_nullable=False)
    
    # Drop old columns that are no longer needed
    op.drop_column('measurements', 'area')
    op.drop_column('measurements', 'perimeter')
    
    # Drop old unit_cost column from conditions
    op.drop_column('conditions', 'unit_cost')


def downgrade() -> None:
    """Downgrade schema to remove measurement engine fields."""
    
    # Restore conditions table
    op.add_column('conditions', sa.Column('unit_cost', sa.Float(), nullable=True))
    op.drop_column('conditions', 'extra_metadata')
    op.drop_column('conditions', 'sort_order')
    op.drop_column('conditions', 'measurement_count')
    op.drop_column('conditions', 'total_quantity')
    op.drop_column('conditions', 'thickness')
    op.drop_column('conditions', 'depth')
    op.drop_column('conditions', 'fill_opacity')
    op.drop_column('conditions', 'line_width')
    op.drop_column('conditions', 'color')
    op.drop_column('conditions', 'measurement_type')
    op.drop_column('conditions', 'category')
    op.drop_column('conditions', 'scope')
    
    # Restore measurements table
    op.add_column('measurements', sa.Column('perimeter', sa.Float(), nullable=True))
    op.add_column('measurements', sa.Column('area', sa.Float(), nullable=True))
    
    op.alter_column('measurements', 'geometry_data',
                    existing_type=postgresql.JSONB(astext_type=sa.Text()),
                    type_=sa.JSON(),
                    existing_nullable=False)
    
    op.drop_column('measurements', 'extra_metadata')
    op.drop_column('measurements', 'is_verified')
    op.drop_column('measurements', 'is_modified')
    op.drop_column('measurements', 'ai_model')
    op.drop_column('measurements', 'ai_confidence')
    op.drop_column('measurements', 'is_ai_generated')
    op.drop_column('measurements', 'pixel_area')
    op.drop_column('measurements', 'pixel_length')
    op.drop_column('measurements', 'unit')
