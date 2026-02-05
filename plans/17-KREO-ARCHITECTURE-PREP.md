# Kreo-Inspired Architecture Prep
## Schema Decisions and Interface Contracts for Post-MVP Features

> **Purpose**: Capture the architectural decisions that must be made NOW (during MVP development) to avoid painful migrations later, even though these features won't be built until post-MVP.
> **Features Covered**: Plan Overlay (Phase 7B), Vector PDF Extraction (Phase 9), Natural Language Query (Phase 10)
> **Source**: Competitive analysis of Kreo.net's technical architecture

---

## 1. Plan Overlay / Version Comparison (Phase 7B)

### What It Is

When a project receives addenda or revised drawings, the estimator needs to see what changed between Rev A and Rev B. Kreo offers a "Plan Overlay" feature that compares drawing versions side-by-side with an opacity slider. This is critical for real construction estimating where revisions happen constantly.

### Schema Decisions (Add to Phase 2 — Document Ingestion)

Add these columns to the `documents` table NOW. They cost nothing during ingestion but prevent a migration later.

```sql
-- Add to documents table
ALTER TABLE documents ADD COLUMN revision_number VARCHAR(20);
ALTER TABLE documents ADD COLUMN revision_date DATE;
ALTER TABLE documents ADD COLUMN revision_label VARCHAR(100); -- "Rev A", "Addendum 2", etc.
ALTER TABLE documents ADD COLUMN supersedes_document_id UUID REFERENCES documents(id) ON DELETE SET NULL;
ALTER TABLE documents ADD COLUMN is_latest_revision BOOLEAN DEFAULT TRUE;
```

**SQLAlchemy model additions** for `backend/app/models/document.py`:

```python
# Add to Document model
revision_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
revision_date: Mapped[date | None] = mapped_column(Date, nullable=True)
revision_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
supersedes_document_id: Mapped[uuid.UUID | None] = mapped_column(
    UUID(as_uuid=True),
    ForeignKey("documents.id", ondelete="SET NULL"),
    nullable=True,
)
is_latest_revision: Mapped[bool] = mapped_column(Boolean, default=True)

# Self-referential relationship
supersedes: Mapped["Document | None"] = relationship(
    "Document",
    remote_side="Document.id",
    foreign_keys=[supersedes_document_id],
)
```

### Page Matching Strategy

When comparing revisions, pages must be matched across documents. Strategy:

1. **By page number** (most reliable for construction plans)
2. **By title block content** (OCR-extracted sheet number like "S1.01")
3. **By visual similarity** (fallback for renumbered pages)

Add to `pages` table:

```sql
ALTER TABLE pages ADD COLUMN sheet_number VARCHAR(50); -- Extracted from title block: "S1.01"
ALTER TABLE pages ADD COLUMN sheet_title VARCHAR(255); -- "Foundation Plan"
```

These fields should be populated during OCR/classification (Phase 3A/3B) when title block text is extracted. No additional work needed — just store what's already being extracted.

### Interface Contract (Build in Phase 7B)

```
API:
  POST /api/documents/{id}/link-revision
    Body: { supersedes_document_id: UUID }
    → Links document as revision of another

  GET /api/documents/{id}/revisions
    → Returns chain: [Rev C, Rev B, Rev A] with timestamps

  GET /api/pages/{page_id}/compare/{other_page_id}
    → Returns comparison data for overlay view

Frontend:
  - RevisionChainPanel: shows document revision history
  - PlanOverlayView: dual-image viewer with opacity slider
  - DiffHighlightOverlay: marks added/removed/changed regions
```

### What to Build Now (Phase 2)
- [ ] Add revision columns to document model
- [ ] Add sheet_number/sheet_title to page model
- [ ] Store sheet numbers during OCR extraction
- [ ] Nothing else — the overlay UI comes in Phase 7B

---

## 2. Vector PDF Extraction (Phase 9)

### What It Is

Many construction PDFs are exported from CAD software (AutoCAD, Revit) and contain vector geometry — actual lines, arcs, and paths with real coordinates. Currently, your pipeline rasterizes everything to a 1568px image, losing this precision. Kreo "explicitly supports both vector and raster/scanned PDFs, with vector format preservation emphasized for accuracy."

For a concrete takeoff, vector extraction could mean measuring a slab boundary with sub-inch accuracy instead of ±6" from raster pixel mapping.

### Schema Decisions (Add to Phase 2 — Document Ingestion)

Add detection metadata during PDF ingestion. PyMuPDF can detect vector content in ~1ms per page.

```sql
-- Add to pages table
ALTER TABLE pages ADD COLUMN is_vector BOOLEAN DEFAULT FALSE;
ALTER TABLE pages ADD COLUMN has_extractable_geometry BOOLEAN DEFAULT FALSE;
ALTER TABLE pages ADD COLUMN vector_path_count INTEGER; -- # of vector paths detected
ALTER TABLE pages ADD COLUMN vector_text_count INTEGER; -- # of vector text objects
ALTER TABLE pages ADD COLUMN pdf_origin VARCHAR(50); -- 'autocad', 'revit', 'bluebeam', 'scanned', 'unknown'
```

**SQLAlchemy model additions** for `backend/app/models/page.py`:

```python
# Add to Page model
is_vector: Mapped[bool] = mapped_column(Boolean, default=False)
has_extractable_geometry: Mapped[bool] = mapped_column(Boolean, default=False)
vector_path_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
vector_text_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
pdf_origin: Mapped[str | None] = mapped_column(String(50), nullable=True)
```

### Detection Logic (Add to Phase 2 — Document Processing)

Add this to the document processor during page extraction. It's lightweight and adds <1ms per page:

```python
import fitz  # PyMuPDF

def detect_vector_content(page: fitz.Page) -> dict:
    """
    Detect whether a PDF page contains vector geometry.
    
    Call this during page extraction in document_processor.py.
    Returns metadata to store on the Page model.
    """
    # Get drawing instructions
    drawings = page.get_drawings()
    text_blocks = page.get_text("dict")["blocks"]
    
    # Count vector paths (lines, arcs, rects, curves)
    path_count = len(drawings)
    
    # Count text objects rendered as vector (not raster)
    text_count = sum(
        1 for block in text_blocks 
        if block.get("type") == 0  # text block (vs image block)
    )
    
    # Heuristic: if >50 vector paths, it's likely a CAD export
    is_vector = path_count > 50
    
    # Heuristic: extractable geometry means enough paths to
    # potentially derive measurements from (walls, boundaries, etc.)
    has_extractable = path_count > 100
    
    # Try to detect origin software from PDF metadata
    pdf_origin = "unknown"
    doc = page.parent
    metadata = doc.metadata
    creator = (metadata.get("creator", "") or "").lower()
    producer = (metadata.get("producer", "") or "").lower()
    
    if "autocad" in creator or "autocad" in producer:
        pdf_origin = "autocad"
    elif "revit" in creator:
        pdf_origin = "revit"
    elif "bluebeam" in creator or "bluebeam" in producer:
        pdf_origin = "bluebeam"
    elif path_count < 10 and any(
        block.get("type") == 1 for block in text_blocks
    ):
        pdf_origin = "scanned"
    
    return {
        "is_vector": is_vector,
        "has_extractable_geometry": has_extractable,
        "vector_path_count": path_count,
        "vector_text_count": text_count,
        "pdf_origin": pdf_origin,
    }
```

### Future Pipeline Architecture (Phase 9)

When Phase 9 is built, the measurement pipeline will branch:

```
PDF Page
    ├── is_vector=True → Vector Extraction Pipeline
    │   ├── Extract paths with PyMuPDF/pdfplumber
    │   ├── Convert PDF coordinates to page coordinates
    │   ├── Classify paths (wall, slab boundary, dimension line)
    │   ├── Generate high-precision measurements
    │   └── Merge with AI-detected elements
    │
    └── is_vector=False → Raster Pipeline (current)
        ├── Render to 1568px image
        ├── LLM-based element detection
        └── Pixel-to-feet conversion via scale
```

The key architectural principle: **vector extraction supplements, never replaces, the raster pipeline**. Even vector PDFs may have elements that are better detected by the LLM (hatching patterns, notes, symbols). The two pipelines should produce measurements that can be merged and deduplicated.

### What to Build Now (Phase 2)
- [ ] Add vector metadata columns to page model
- [ ] Call `detect_vector_content()` during page extraction
- [ ] Store results on the Page record
- [ ] Nothing else — the extraction pipeline comes in Phase 9

---

## 3. Natural Language Query / AI Assistant (Phase 10)

### What It Is

Kreo's "Caddie AI" integrates ChatGPT for natural language queries on drawings. For a concrete estimator, this means asking questions like "What's the total slab area?", "How many piers on the foundation plan?", or "What's the cost per square foot for building A?"

Since you're already multi-LLM, the query engine is straightforward once there's data to query. The hard part is building the right data access layer.

### Data Access Architecture

The AI assistant needs to query three data tiers:

```
Tier 1: Structured Data (SQL)
├── Measurements: quantities, areas, lengths by condition/page
├── Conditions: totals, counts, categories
├── Assemblies: costs, component breakdowns
├── Pages: classifications, scale values, sheet numbers
└── Documents: revision history, upload dates

Tier 2: Semi-Structured Data (JSON/Text)
├── OCR text from pages (dimension callouts, notes)
├── AI analysis notes and descriptions
├── Assembly formulas and component details
└── Measurement metadata and AI confidence scores

Tier 3: Visual Data (Images)
├── Page images for visual reference
├── Measurement overlays
└── Detection highlights
```

### Interface Contract (Build in Phase 10)

```
API:
  POST /api/projects/{id}/ask
    Body: { 
      question: "What's the total slab area?",
      context: { page_id?: UUID, condition_id?: UUID }
    }
    → Returns {
      answer: "The total slab on grade area is 42,350 SF across 3 pages.",
      sources: [
        { type: "measurement", id: "...", description: "Slab on Grade - S1.01" },
        { type: "measurement", id: "...", description: "Slab on Grade - S1.02" },
      ],
      sql_query?: "SELECT SUM(quantity) FROM measurements WHERE ...",
      confidence: 0.95
    }

  POST /api/projects/{id}/ask (multi-turn)
    Body: {
      question: "Break that down by page",
      conversation_id: "prev-conversation-id"
    }
    → Returns answer with per-page breakdown
```

### Query-to-SQL Translation Approach

Rather than full RAG (which requires embedding and vector search), the most effective approach for structured takeoff data is **query-to-SQL translation**:

1. User asks: "What's the total concrete volume for building A?"
2. System builds context: table schemas, column descriptions, sample data
3. LLM generates SQL: `SELECT SUM(m.quantity) FROM measurements m JOIN conditions c ON ... WHERE c.unit = 'CY' AND ...`
4. System executes query safely (read-only, parameterized)
5. LLM formats result into natural language answer

This is more reliable than RAG for structured data because the data is already in a queryable format. RAG is reserved for Tier 2 (OCR text search) and Tier 3 (visual queries).

### Schema Prep (Add to Phase 6 — Review Interface)

The main prep needed is making data more queryable:

```sql
-- Add to conditions table (may already exist)
ALTER TABLE conditions ADD COLUMN building VARCHAR(100); -- "Building A", "Building B"
ALTER TABLE conditions ADD COLUMN area VARCHAR(100); -- "Loading Dock", "Main Floor"
ALTER TABLE conditions ADD COLUMN elevation VARCHAR(50); -- "Ground Floor", "Level 2"
```

These spatial grouping fields let the AI answer questions like "What's the total for Building A?" or "Compare ground floor vs level 2 costs."

### UI Stub (Add to Phase 6)

Add a disabled "Ask AI" button in the project toolbar:

```tsx
// In ProjectToolbar.tsx or similar
<Button 
  variant="outline" 
  disabled 
  title="AI Assistant — coming soon"
>
  <MessageSquare className="h-4 w-4 mr-2" />
  Ask AI
</Button>
```

This costs nothing and signals the feature direction to your team and users.

### What to Build Now
- [ ] Add building/area/elevation fields to conditions model (Phase 4B)
- [ ] Add "Ask AI" disabled button to project toolbar (Phase 6)
- [ ] Nothing else — the query engine comes in Phase 10

---

## Summary: What to Do in Each Current Phase

| Current Phase | Architecture Prep to Add |
|---------------|-------------------------|
| **Phase 2: Document Ingestion** | Add `revision_*` columns to document model, add `is_vector` and `sheet_number` columns to page model, call `detect_vector_content()` during extraction |
| **Phase 3A: OCR** | Store extracted sheet numbers in `pages.sheet_number` |
| **Phase 3B: Classification** | Store sheet title in `pages.sheet_title` |
| **Phase 4B: Conditions** | Add `building`, `area`, `elevation` fields |
| **Phase 6: Review Interface** | Add disabled "Ask AI" button |

Total effort: ~2-3 hours of schema additions spread across existing phases. Zero new features to build, zero new UI to design. Just planting the right columns so the data is there when we need it.

---

## Kreo Features Explicitly Deferred

These were identified in the Kreo analysis but are not included in any phase:

| Feature | Reason for Deferral |
|---------|--------------------|
| **DWG/DXF/CAD Support** | Requires ODA membership ($1,500+/yr), complex parsing. Revisit if SaaS demand exists. |
| **Real-Time Collaboration** | WebSocket infrastructure, CRDT conflict resolution. Only needed for multi-user SaaS. |
| **2D to 3D/IFC Export** | Extremely complex. Out of scope for concrete takeoff. |
| **Revit Plugin** | Only relevant for BIM workflows, not concrete subcontractor use case. |
| **API Key Auth for External Consumers** | SaaS concern. Internal use only needs session auth. |
| **Activity Logging (Project-Level)** | Nice to have but the task_records table covers the most important audit trail. Revisit post-MVP. |
