# Sheet Navigation (Phase A)

## Overview

Sheet navigation provides a grouped, searchable tree of construction plan sheets in the workspace left panel. It displays all relevant pages from uploaded documents, grouped by discipline, with scale status indicators and measurement counts.

## User Interface

```
┌────────────────────────────────┐
│  🔍 Search sheets...           │
│  [Tree] [Thumbnails]           │
├────────────────────────────────┤
│                                │
│  ▼ Structural (4)             │
│    S-101  Foundation Plan  ⚡  │
│    S-102  Framing Plan    ⚡  │
│    S-103  Details         ⚠   │
│    S-104  Schedules       —   │
│                                │
│  ▼ Architectural (3)          │
│    A-101  Floor Plan      ⚡  │
│    A-102  Elevations      ⚡  │
│    A-103  Sections        ⚡  │
│                                │
│  ▸ MEP (2)                    │
│                                │
│  ▸ Unclassified (1)          │
│                                │
└────────────────────────────────┘
```

## Features

### Grouped Sheet Tree
- Sheets are grouped by `group_name` → `discipline` → `"Unclassified"`
- Groups are sorted alphabetically
- Within groups, sheets use natural sort: `display_order` → `sheet_number` → `page_number`
- Groups can be expanded/collapsed individually

### Natural Sort
The backend `_natural_sort_key()` function sorts sheet numbers intelligently:
- `S-1` before `S-2` before `S-10` (not lexicographic `S-1`, `S-10`, `S-2`)
- Sheets with `display_order` set are sorted first (priority 0)
- Then by `sheet_number` with natural ordering (priority 1)
- Then by `page_number` as fallback (priority 2)

### Search Filtering
- Text input filters sheets by name across all groups
- Matched groups remain expanded while filtering
- Search state stored in `sheetSearchQuery` in the workspace store

### View Modes
Two display modes, toggled via buttons:
- **Tree view**: Hierarchical list with expand/collapse (default)
- **Thumbnail view**: Grid of page thumbnails

### Scale Status Badges
Each sheet displays a `ScaleBadge` indicating calibration confidence:

| Status | Color | Meaning |
|---|---|---|
| Calibrated | Green | Scale confirmed by user or high-confidence detection |
| Detected | Yellow | Scale auto-detected but not yet confirmed |
| No Scale | Gray | No scale information available |

### State Persistence
Expanded/collapsed group state is persisted to localStorage per project:
```typescript
const LS_KEY = `sheet-tree-state-${projectId}`;
```

This prevents state leaks between projects and restores the user's preferred tree state across sessions.

### Context Menu
Right-click on a sheet opens a context menu with sheet-level operations.

### Keyboard Navigation
Arrow keys navigate between sheets within the tree.

## Backend API

### GET `/projects/{project_id}/sheets`

Returns all relevant pages grouped by discipline with pre-joined data to avoid N+1 queries.

**Query Strategy**:
```sql
SELECT pages.*, COALESCE(measurement_counts.count, 0) AS measurement_count
FROM pages
JOIN documents ON pages.document_id = documents.id
LEFT JOIN (
    SELECT page_id, COUNT(*) AS count
    FROM measurements
    GROUP BY page_id
) measurement_counts ON pages.id = measurement_counts.page_id
WHERE documents.project_id = :project_id
  AND pages.is_relevant = TRUE
ORDER BY pages.page_number
```

**Response Schema**:
```json
{
  "groups": [
    {
      "group_name": "Structural",
      "sheets": [
        {
          "id": "uuid",
          "document_id": "uuid",
          "page_number": 1,
          "sheet_number": "S-101",
          "title": "Foundation Plan",
          "display_name": null,
          "display_order": null,
          "group_name": null,
          "discipline": "Structural",
          "classification": "structural_plan",
          "classification_confidence": 0.95,
          "scale_text": "1/4\" = 1'-0\"",
          "scale_value": 48.0,
          "scale_calibrated": true,
          "scale_detection_method": "ocr_pattern",
          "measurement_count": 12,
          "thumbnail_url": "https://minio.../presigned",
          "image_url": "https://minio.../presigned",
          "width": 3400,
          "height": 2200,
          "is_relevant": true
        }
      ]
    }
  ],
  "total": 10
}
```

### PUT `/pages/{page_id}/display`

Update display metadata for a page:
```json
{
  "display_name": "Foundation Plan (Revised)",
  "display_order": 5,
  "group_name": "Foundations"
}
```

### PUT `/pages/{page_id}/relevance`

Include/exclude a page from the sheet tree:
```json
{
  "is_relevant": false
}
```

### POST `/pages/batch-scale`

Apply the same scale to multiple pages:
```json
{
  "page_ids": ["uuid-1", "uuid-2"],
  "scale_value": 48.0,
  "scale_text": "1/4\" = 1'-0\"",
  "scale_unit": "foot"
}
```

## Image Handling

### TIFF to PNG Conversion
The sheets endpoint converts TIFF storage keys to PNG for web viewing:
```python
def _get_viewer_image_key(image_key: str) -> str:
    if image_key.endswith(".tiff"):
        return image_key.removesuffix(".tiff") + ".png"
    return image_key
```

### Presigned URLs
All image and thumbnail URLs are presigned with 3600-second expiry. The frontend preloads images before displaying them on the canvas.

### Image Preloading (Frontend)
```typescript
// TakeoffWorkspace.tsx — prevents race conditions during sheet switching
useEffect(() => {
  if (activeSheet?.image_url) {
    setIsLoadingSheetImage(true);
    let stale = false;
    const img = new Image();
    img.onload = () => { if (!stale) setIsLoadingSheetImage(false); };
    img.onerror = () => { if (!stale) setIsLoadingSheetImage(false); };
    img.src = activeSheet.image_url;
    return () => { stale = true; };
  }
}, [activeSheet?.image_url]);
```

The `stale` flag prevents the callback from firing if the user switches sheets before the image finishes loading.

## Key Files

| File | Purpose |
|---|---|
| `frontend/src/components/sheets/SheetTree.tsx` | Main sheet tree component |
| `frontend/src/components/sheets/ThumbnailStrip.tsx` | Thumbnail grid view |
| `frontend/src/components/sheets/ScaleBadge.tsx` | Scale status indicator |
| `frontend/src/components/sheets/SheetContextMenu.tsx` | Right-click menu |
| `frontend/src/api/sheets.ts` | API client for sheet endpoints |
| `backend/app/api/routes/sheets.py` | Sheet tree API routes |

## Testing

### Frontend Tests (`SheetTree.test.tsx`)
10 tests covering:
- Grouped rendering by discipline
- Sheet selection updates store
- Scale badge display
- No-scale indicator
- Expand/collapse persistence in localStorage
- Keyboard navigation
- Search filtering
- Empty project handling
- Loading state
- Thumbnail view toggle
