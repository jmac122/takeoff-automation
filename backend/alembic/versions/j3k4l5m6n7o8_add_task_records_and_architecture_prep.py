"""add_task_records_and_architecture_prep

Revision ID: j3k4l5m6n7o8
Revises: i2j3k4l5m6n7
Create Date: 2026-02-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'j3k4l5m6n7o8'
down_revision: Union[str, Sequence[str], None] = 'i2j3k4l5m6n7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # === PART 1: TaskRecord table ===
    op.create_table(
        'task_records',
        sa.Column('task_id', sa.String(255), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True),
                   sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=True),
        sa.Column('task_type', sa.String(100), nullable=False),
        sa.Column('task_name', sa.String(255), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='PENDING'),
        sa.Column('progress_percent', sa.Float(), nullable=True, server_default='0'),
        sa.Column('progress_step', sa.String(255), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('result_summary', postgresql.JSONB(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_traceback', sa.Text(), nullable=True),
        sa.Column('task_metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_task_records_project_status', 'task_records', ['project_id', 'status'])
    op.create_index('ix_task_records_project_type', 'task_records', ['project_id', 'task_type'])

    # === PART 2A: Document revision tracking columns ===
    op.add_column('documents', sa.Column('revision_number', sa.String(20), nullable=True))
    op.add_column('documents', sa.Column('revision_date', sa.Date(), nullable=True))
    op.add_column('documents', sa.Column('revision_label', sa.String(100), nullable=True))
    op.add_column('documents', sa.Column('supersedes_document_id',
                   postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('documents', sa.Column('is_latest_revision', sa.Boolean(),
                   server_default='true', nullable=False))
    op.create_foreign_key(
        'fk_documents_supersedes_document_id',
        'documents', 'documents',
        ['supersedes_document_id'], ['id'],
        ondelete='SET NULL',
    )

    # === PART 2B: Page columns — sheet_title + vector PDF detection ===
    op.add_column('pages', sa.Column('sheet_title', sa.String(255), nullable=True))
    op.add_column('pages', sa.Column('is_vector', sa.Boolean(),
                   server_default='false', nullable=False))
    op.add_column('pages', sa.Column('has_extractable_geometry', sa.Boolean(),
                   server_default='false', nullable=False))
    op.add_column('pages', sa.Column('vector_path_count', sa.Integer(), nullable=True))
    op.add_column('pages', sa.Column('vector_text_count', sa.Integer(), nullable=True))
    op.add_column('pages', sa.Column('pdf_origin', sa.String(50), nullable=True))

    # === PART 2C: Condition spatial grouping columns ===
    op.add_column('conditions', sa.Column('building', sa.String(100), nullable=True))
    op.add_column('conditions', sa.Column('area', sa.String(100), nullable=True))
    op.add_column('conditions', sa.Column('elevation', sa.String(50), nullable=True))


def downgrade() -> None:
    # Condition columns
    op.drop_column('conditions', 'elevation')
    op.drop_column('conditions', 'area')
    op.drop_column('conditions', 'building')

    # Page columns
    op.drop_column('pages', 'pdf_origin')
    op.drop_column('pages', 'vector_text_count')
    op.drop_column('pages', 'vector_path_count')
    op.drop_column('pages', 'has_extractable_geometry')
    op.drop_column('pages', 'is_vector')
    op.drop_column('pages', 'sheet_title')

    # Document columns
    op.drop_constraint('fk_documents_supersedes_document_id', 'documents', type_='foreignkey')
    op.drop_column('documents', 'is_latest_revision')
    op.drop_column('documents', 'supersedes_document_id')
    op.drop_column('documents', 'revision_label')
    op.drop_column('documents', 'revision_date')
    op.drop_column('documents', 'revision_number')

    # TaskRecord table
    op.drop_index('ix_task_records_project_type', 'task_records')
    op.drop_index('ix_task_records_project_status', 'task_records')
    op.drop_table('task_records')
