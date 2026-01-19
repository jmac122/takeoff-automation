# Database Schema - Phases 1A & 1B: Document Ingestion & OCR

## Overview

The database schema for Phase 1A implements a document-centric data model optimized for construction takeoff workflows. Built with SQLAlchemy 2.0 and PostgreSQL, the schema supports hierarchical organization of projects, documents, pages, and measurements.

## Schema Design Principles

### Core Design Decisions

1. **UUID Primary Keys**: All entities use UUIDv4 for global uniqueness and security
2. **Timestamp Auditing**: Automatic `created_at`/`updated_at` tracking on all entities
3. **Soft Deletes**: Cascade delete relationships to maintain referential integrity
4. **JSON Storage**: Flexible metadata storage for future extensibility
5. **Async Operations**: Designed for async SQLAlchemy operations

### Naming Conventions

- **Tables**: Plural, snake_case (e.g., `projects`, `documents`)
- **Columns**: snake_case (e.g., `project_id`, `file_size`)
- **Indexes**: Named with `ix_table_column` pattern
- **Constraints**: Named with `fk_table_column` pattern

## Entity Relationship Diagram

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│   Project   │       │  Document   │       │    Page     │
├─────────────┤       ├─────────────┤       ├─────────────┤
│ id (UUID)   │◄──────┤ project_id  │◄──────┤ document_id │
│ name        │       │ id (UUID)   │       │ id (UUID)   │
│ description │       │ filename    │       │ page_number │
│ client_name │       │ file_type   │       │ width       │
│ status      │       │ file_size   │       │ height      │
│ created_at  │       │ status      │       │ image_key   │
│ updated_at  │       │ page_count  │       │ thumbnail_key│
└─────────────┘       │ created_at  │       │ status      │
        │             │ updated_at  │       │ created_at  │
        │             └─────────────┘       │ updated_at  │
        │                     │             └─────────────┘
        ▼                     ▼                     │
┌─────────────┐       ┌─────────────┐             │
│  Condition  │       │    Page     │◄────────────┘
├─────────────┤       │ (extended)  │
│ id (UUID)   │◄──────┤             │
│ project_id  │       │ classification│
│ name        │       │ scale_*      │
│ unit        │       │ ocr_*        │
│ unit_cost   │       └─────────────┘
│ created_at  │
│ updated_at  │
└─────────────┘
        │
        ▼
┌─────────────┐
│ Measurement │
├─────────────┤
│ id (UUID)   │
│ page_id     │
│ condition_id│
│ geometry_type│
│ geometry_data│
│ quantity    │
│ area        │
│ perimeter   │
│ notes       │
│ created_at  │
│ updated_at  │
└─────────────┘
```

## Table Definitions

### Base Classes

#### UUIDMixin
```sql
-- Provides UUID primary key for all entities
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- All tables inherit UUID primary key
id UUID PRIMARY KEY DEFAULT uuid_generate_v4()
```

#### TimestampMixin
```sql
-- Automatic timestamp tracking
created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
```

### Projects Table

```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    client_name VARCHAR(255),
    status VARCHAR(50) NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'in_progress', 'completed', 'archived')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX ix_projects_status ON projects(status);
CREATE INDEX ix_projects_client_name ON projects(client_name);
CREATE INDEX ix_projects_created_at ON projects(created_at);
```

**Constraints:**
- `status` must be one of: 'draft', 'in_progress', 'completed', 'archived'

**Indexes:**
- Status for filtering active projects
- Client name for search
- Created date for sorting

### Documents Table

```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    filename VARCHAR(500) NOT NULL,
    original_filename VARCHAR(500) NOT NULL,
    file_type VARCHAR(10) NOT NULL CHECK (file_type IN ('pdf', 'tiff')),
    file_size BIGINT NOT NULL CHECK (file_size > 0),
    mime_type VARCHAR(100) NOT NULL,
    storage_key VARCHAR(500) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'uploaded'
        CHECK (status IN ('uploaded', 'processing', 'ready', 'error')),
    page_count INTEGER,
    processing_error TEXT,
    processing_metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX ix_documents_project_id ON documents(project_id);
CREATE INDEX ix_documents_status ON documents(status);
CREATE INDEX ix_documents_file_type ON documents(file_type);
CREATE INDEX ix_documents_created_at ON documents(created_at);

-- Foreign Key Constraints
ALTER TABLE documents
ADD CONSTRAINT fk_documents_project_id
FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;
```

**Constraints:**
- `file_type` must be 'pdf' or 'tiff'
- `file_size` must be positive
- `status` must be valid processing state
- `page_count` is set after processing

**Relationships:**
- One-to-many with Pages
- Many-to-one with Projects

### Pages Table

```sql
CREATE TABLE pages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL CHECK (page_number > 0),
    width INTEGER NOT NULL CHECK (width > 0),
    height INTEGER NOT NULL CHECK (height > 0),
    dpi INTEGER NOT NULL DEFAULT 150 CHECK (dpi > 0),
    image_key VARCHAR(500) NOT NULL,
    thumbnail_key VARCHAR(500),

    -- AI processing fields (Phase 2+)
    classification VARCHAR(100),
    classification_confidence FLOAT CHECK (classification_confidence >= 0 AND classification_confidence <= 1),
    title VARCHAR(500),
    sheet_number VARCHAR(50),

    -- Scale detection (Phase 2B)
    scale_text VARCHAR(100),
    scale_value FLOAT,
    scale_unit VARCHAR(20) DEFAULT 'foot',
    scale_calibrated BOOLEAN DEFAULT FALSE,
    scale_calibration_data JSONB,

    -- OCR data (Phase 1B)
    ocr_text TEXT,
    ocr_blocks JSONB,

    -- Processing status
    status VARCHAR(50) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'processing', 'ready', 'error')),
    processing_error TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Ensure unique page numbers per document
    UNIQUE(document_id, page_number)
);

-- Indexes
CREATE INDEX ix_pages_document_id ON pages(document_id);
CREATE INDEX ix_pages_page_number ON pages(document_id, page_number);
CREATE INDEX ix_pages_status ON pages(status);
CREATE INDEX ix_pages_classification ON pages(classification);
CREATE INDEX ix_pages_scale_calibrated ON pages(scale_calibrated);

-- Foreign Key Constraints
ALTER TABLE pages
ADD CONSTRAINT fk_pages_document_id
FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE;
```

**Constraints:**
- `page_number` must be positive
- `width`/`height` must be positive
- `dpi` must be positive
- `classification_confidence` must be 0-1
- `status` must be valid processing state
- Unique constraint on `(document_id, page_number)`

**Relationships:**
- Many-to-one with Documents
- One-to-many with Measurements

### Conditions Table

```sql
CREATE TABLE conditions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    unit VARCHAR(50) NOT NULL,
    unit_cost FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX ix_conditions_project_id ON conditions(project_id);
CREATE INDEX ix_conditions_name ON conditions(name);
CREATE INDEX ix_conditions_unit ON conditions(unit);

-- Foreign Key Constraints
ALTER TABLE conditions
ADD CONSTRAINT fk_conditions_project_id
FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;
```

**Relationships:**
- Many-to-one with Projects
- One-to-many with Measurements

### Measurements Table

```sql
CREATE TABLE measurements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    page_id UUID NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
    condition_id UUID NOT NULL REFERENCES conditions(id) ON DELETE CASCADE,
    geometry_type VARCHAR(50) NOT NULL
        CHECK (geometry_type IN ('polygon', 'polyline', 'line', 'point')),
    geometry_data JSONB NOT NULL,
    quantity FLOAT NOT NULL,
    area FLOAT,
    perimeter FLOAT,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX ix_measurements_page_id ON measurements(page_id);
CREATE INDEX ix_measurements_condition_id ON measurements(condition_id);
CREATE INDEX ix_measurements_geometry_type ON measurements(geometry_type);

-- Foreign Key Constraints
ALTER TABLE measurements
ADD CONSTRAINT fk_measurements_page_id
FOREIGN KEY (page_id) REFERENCES pages(id) ON DELETE CASCADE;

ALTER TABLE measurements
ADD CONSTRAINT fk_measurements_condition_id
FOREIGN KEY (condition_id) REFERENCES conditions(id) ON DELETE CASCADE;
```

**Constraints:**
- `geometry_type` must be valid geometry type
- `quantity` must be positive (calculated measurement)
- `geometry_data` stores coordinate arrays/polygons

**Relationships:**
- Many-to-one with Pages
- Many-to-one with Conditions

## Migration Scripts

### Initial Migration (Alembic)

```python
# alembic/versions/71104d86fe9c_initial_schema.py
"""Initial schema with projects, documents, pages, conditions, measurements."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # Create projects table
    op.create_table('projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('client_name', sa.String(255), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, default='draft'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'))
    )

    # Create indexes for projects
    op.create_index('ix_projects_status', 'projects', ['status'])
    op.create_index('ix_projects_client_name', 'projects', ['client_name'])
    op.create_index('ix_projects_created_at', 'projects', ['created_at'])

    # ... additional table creation and indexing
```

## Data Types and Constraints

### PostgreSQL-Specific Types

- **UUID**: Globally unique identifiers using `uuid-ossp` extension
- **JSONB**: Binary JSON storage for flexible metadata
- **TIMESTAMP WITH TIME ZONE**: UTC timestamps with timezone awareness

### Check Constraints

```sql
-- Status validation
CHECK (status IN ('draft', 'in_progress', 'completed', 'archived'))

-- File type validation
CHECK (file_type IN ('pdf', 'tiff'))

-- Positive number constraints
CHECK (file_size > 0)
CHECK (page_number > 0)
CHECK (width > 0)
CHECK (height > 0)
CHECK (dpi > 0)

-- Confidence score validation
CHECK (classification_confidence >= 0 AND classification_confidence <= 1)

-- Geometry type validation
CHECK (geometry_type IN ('polygon', 'polyline', 'line', 'point'))
```

## Indexing Strategy

### Primary Indexes
- UUID primary keys (automatically indexed)
- Foreign key columns (automatically indexed)

### Custom Indexes

```sql
-- Performance indexes
CREATE INDEX ix_projects_status ON projects(status);
CREATE INDEX ix_projects_created_at ON projects(created_at);
CREATE INDEX ix_documents_project_id ON documents(project_id);
CREATE INDEX ix_documents_status ON documents(status);
CREATE INDEX ix_pages_document_id ON pages(document_id);
CREATE INDEX ix_pages_classification ON pages(classification);

-- Composite indexes for common queries
CREATE INDEX ix_pages_page_number ON pages(document_id, page_number);
CREATE INDEX ix_measurements_page_condition ON measurements(page_id, condition_id);
```

## Query Patterns

### Common Queries

#### Get Project with Documents
```sql
SELECT p.*, json_agg(d.*) as documents
FROM projects p
LEFT JOIN documents d ON p.id = d.project_id
WHERE p.id = $1
GROUP BY p.id;
```

#### Get Document with Pages
```sql
SELECT d.*, json_agg(p.*) as pages
FROM documents d
LEFT JOIN pages p ON d.id = p.document_id
WHERE d.id = $1
GROUP BY d.id
ORDER BY p.page_number;
```

#### Get Measurements for Project
```sql
SELECT m.*, p.page_number, c.name as condition_name
FROM measurements m
JOIN pages p ON m.page_id = p.id
JOIN conditions c ON m.condition_id = c.id
WHERE c.project_id = $1;
```

### Performance Considerations

#### Partitioning Strategy (Future)
- Partition documents by project_id
- Partition pages by document_id
- Partition measurements by page_id

#### Connection Pooling
```python
# SQLAlchemy async engine configuration
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,              # Maximum connections
    max_overflow=30,           # Overflow connections
    pool_pre_ping=True,        # Health checks
    pool_recycle=3600,         # Recycle connections hourly
)
```

## Backup and Recovery

### Backup Strategy
```bash
# Full database backup
pg_dump -h localhost -U postgres takeoff > backup.sql

# Schema-only backup
pg_dump -h localhost -U postgres --schema-only takeoff > schema.sql

# Data-only backup
pg_dump -h localhost -U postgres --data-only takeoff > data.sql
```

### Point-in-Time Recovery
```sql
-- Enable WAL archiving
ALTER SYSTEM SET wal_level = replica;
ALTER SYSTEM SET archive_mode = on;
ALTER SYSTEM SET archive_command = 'cp %p /var/lib/postgresql/archive/%f';
```

## Monitoring and Maintenance

### Table Statistics
```sql
-- Update table statistics
ANALYZE projects;
ANALYZE documents;
ANALYZE pages;

-- View table sizes
SELECT schemaname, tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Index Usage
```sql
SELECT schemaname, tablename, indexname,
       idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

## Future Schema Extensions

### Phase 1B: OCR Text Extraction
```sql
-- Add full-text search capabilities
ALTER TABLE pages ADD COLUMN search_vector tsvector;
CREATE INDEX ix_pages_search ON pages USING gin(search_vector);

-- OCR confidence scores
ALTER TABLE pages ADD COLUMN ocr_confidence FLOAT;
```

### Phase 2A: Page Classification
```sql
-- Classification metadata
ALTER TABLE pages ADD COLUMN classification_metadata JSONB;
ALTER TABLE pages ADD COLUMN ai_model_version VARCHAR(50);
```

### Phase 2B: Scale Detection
```sql
-- Calibration points storage
ALTER TABLE pages ADD COLUMN calibration_points JSONB;
ALTER TABLE pages ADD COLUMN measurement_accuracy FLOAT;
```

### Phase 3A: Advanced Measurements
```sql
-- Measurement relationships
ALTER TABLE measurements ADD COLUMN parent_measurement_id UUID;
ALTER TABLE measurements ADD CONSTRAINT fk_measurements_parent
    FOREIGN KEY (parent_measurement_id) REFERENCES measurements(id);

-- Measurement groups
ALTER TABLE measurements ADD COLUMN group_id UUID;
CREATE INDEX ix_measurements_group ON measurements(group_id);
```

## Migration Strategy

### Alembic Configuration
```ini
# alembic.ini
[alembic]
script_location = alembic
sqlalchemy.url = postgresql://user:pass@localhost/takeoff

[post_write_hooks]
hooks = black
black.type = console_scripts
black.entrypoint = black
black.options = -l 79 REVISION_SCRIPT_FILENAME
```

### Migration Commands
```bash
# Create new migration
alembic revision --autogenerate -m "add_new_feature"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1

# Check current version
alembic current
```

## Testing

### Schema Tests
```python
def test_table_creation():
    """Test that all tables can be created."""
    Base.metadata.create_all(bind=engine)

    # Verify tables exist
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    expected_tables = {'projects', 'documents', 'pages', 'conditions', 'measurements'}
    assert expected_tables.issubset(set(tables))

def test_constraints():
    """Test database constraints."""
    # Test foreign key constraints
    # Test check constraints
    # Test unique constraints
```

### Performance Tests
```python
def test_query_performance():
    """Test query performance with realistic data."""
    # Insert test data
    # Measure query execution time
    # Verify indexes are used
```

## Phase 1B: OCR Data Storage

### OCR Text Columns

Phase 1B adds OCR-related columns to the `pages` table:

```sql
-- OCR data columns (added in Phase 1B)
ALTER TABLE pages ADD COLUMN ocr_text TEXT;
ALTER TABLE pages ADD COLUMN ocr_blocks JSONB;
```

**OCR Fields:**
- `ocr_text` - Full extracted text from the page (searchable)
- `ocr_blocks` - Structured OCR data including:
  - Individual text blocks with positions
  - Detected scales
  - Detected sheet numbers
  - Detected titles
  - Title block parsed data

### OCR Blocks JSON Structure

```json
{
  "blocks": [
    {
      "text": "FOUNDATION PLAN",
      "confidence": 0.98,
      "bounding_box": {
        "x": 100,
        "y": 50,
        "width": 400,
        "height": 60
      }
    }
  ],
  "detected_scales": ["1/4\" = 1'-0\""],
  "detected_sheet_numbers": ["A1.01"],
  "detected_titles": ["FOUNDATION PLAN"],
  "title_block": {
    "sheet_number": "A1.01",
    "sheet_title": "FOUNDATION PLAN",
    "project_name": "Downtown Office Building",
    "project_number": "2024-001",
    "date": "01/15/2024",
    "revision": "A",
    "scale": "1/4\" = 1'-0\"",
    "drawn_by": "JD",
    "checked_by": "MS"
  }
}
```

### Full-Text Search Indexes

Phase 1B adds PostgreSQL full-text search capabilities:

```sql
-- Full-text search index (GIN)
CREATE INDEX idx_pages_ocr_text_search 
ON pages 
USING gin(to_tsvector('english', COALESCE(ocr_text, '')));

-- Trigram index for fuzzy matching
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX idx_pages_ocr_text_trgm 
ON pages 
USING gin(ocr_text gin_trgm_ops);
```

**Index Benefits:**
- Fast full-text search across all page text
- Fuzzy matching for typos and variations
- Relevance ranking with `ts_rank`
- Supports complex search queries

### Search Query Example

```sql
-- Search for pages containing "foundation"
SELECT p.id, p.document_id, p.page_number, p.title, p.sheet_number,
       ts_rank(to_tsvector('english', COALESCE(p.ocr_text, '')), 
               plainto_tsquery('english', 'foundation')) as rank
FROM pages p
JOIN documents d ON p.document_id = d.id
WHERE d.project_id = '550e8400-e29b-41d4-a716-446655440000'
  AND to_tsvector('english', COALESCE(p.ocr_text, '')) 
      @@ plainto_tsquery('english', 'foundation')
ORDER BY rank DESC
LIMIT 50;
```

### Migration History

**Phase 1B Migrations:**
- `d707bfb8a266_add_fulltext_search.py` - Full-text search indexes

**Applied Migrations:**
```bash
# Check current migration status
alembic current

# Apply Phase 1B migrations
alembic upgrade head
```

---

This database schema provides a solid foundation for the construction takeoff platform, with proper normalization, indexing, full-text search capabilities, and extensibility for future phases.

**Last Updated:** January 19, 2026 - Phase 1B Complete