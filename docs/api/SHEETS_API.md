# Sheets API Reference

## Overview

The Sheets API provides an optimized endpoint for fetching all project sheets grouped by discipline, plus endpoints for updating page display metadata, relevance, and batch scale operations. These endpoints power the workspace sheet tree navigation.

## Endpoints

### Get Project Sheets

```
GET /projects/{project_id}/sheets
```

Returns all relevant pages for a project, grouped by discipline/group_name, with classification, scale, and measurement count data pre-joined in a single query.

**Path Parameters**:
| Parameter | Type | Description |
|---|---|---|
| `project_id` | UUID | Project identifier |

**Response** `200 OK`:
```json
{
  "groups": [
    {
      "group_name": "Structural",
      "sheets": [
        {
          "id": "550e8400-e29b-41d4-a716-446655440001",
          "document_id": "550e8400-e29b-41d4-a716-446655440000",
          "page_number": 1,
          "sheet_number": "S-101",
          "title": "Foundation Plan",
          "display_name": null,
          "display_order": null,
          "group_name": null,
          "discipline": "Structural",
          "page_type": "plan",
          "classification": "structural_plan",
          "classification_confidence": 0.95,
          "scale_text": "1/4\" = 1'-0\"",
          "scale_value": 48.0,
          "scale_calibrated": true,
          "scale_detection_method": "ocr_pattern",
          "measurement_count": 12,
          "thumbnail_url": "https://minio.example.com/...?X-Amz-Signature=...",
          "image_url": "https://minio.example.com/...?X-Amz-Signature=...",
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

**Notes**:
- Only pages with `is_relevant = true` are included
- Groups are sorted alphabetically by `group_name`
- Sheets within groups use natural sort: `display_order` → `sheet_number` → `page_number`
- `thumbnail_url` and `image_url` are presigned URLs (3600s expiry)
- TIFF images are served as PNG via automatic key conversion
- Measurement count is computed via a subquery to avoid N+1

**Error Responses**:
| Status | Description |
|---|---|
| `404` | Project not found |

---

### Update Page Display

```
PUT /pages/{page_id}/display
```

Update display metadata for a page (custom name, sort order, group assignment).

**Path Parameters**:
| Parameter | Type | Description |
|---|---|---|
| `page_id` | UUID | Page identifier |

**Request Body** (all fields optional):
```json
{
  "display_name": "Foundation Plan (Revised)",
  "display_order": 5,
  "group_name": "Foundations"
}
```

**Response** `200 OK`:
```json
{
  "status": "success",
  "page_id": "uuid",
  "display_name": "Foundation Plan (Revised)",
  "display_order": 5,
  "group_name": "Foundations"
}
```

**Notes**:
- Only provided fields are updated (partial update)
- `display_order` takes priority in natural sort ordering

---

### Update Page Relevance

```
PUT /pages/{page_id}/relevance
```

Include or exclude a page from the sheet tree. Irrelevant pages are hidden from the workspace.

**Path Parameters**:
| Parameter | Type | Description |
|---|---|---|
| `page_id` | UUID | Page identifier |

**Request Body**:
```json
{
  "is_relevant": false
}
```

**Response** `200 OK`:
```json
{
  "status": "success",
  "page_id": "uuid",
  "is_relevant": false
}
```

---

### Batch Update Scale

```
POST /pages/batch-scale
```

Apply the same scale to multiple pages at once. Useful when multiple sheets share the same scale.

**Request Body**:
```json
{
  "page_ids": [
    "550e8400-e29b-41d4-a716-446655440001",
    "550e8400-e29b-41d4-a716-446655440002"
  ],
  "scale_value": 48.0,
  "scale_text": "1/4\" = 1'-0\"",
  "scale_unit": "foot"
}
```

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `page_ids` | UUID[] | Yes | — | Pages to update |
| `scale_value` | float | Yes | — | Scale factor |
| `scale_text` | string | No | null | Human-readable scale |
| `scale_unit` | string | No | `"foot"` | Scale unit |

**Response** `200 OK`:
```json
{
  "status": "success",
  "updated_pages": ["uuid-1", "uuid-2"],
  "count": 2,
  "missing_ids": []
}
```

**Notes**:
- All updated pages are set to `scale_calibrated = true`, `scale_detection_method = "manual_calibration"`
- Missing page IDs are reported in `missing_ids` but don't cause failure
- Batch applied flag stored in `scale_calibration_data` JSON

## Response Schemas

### SheetInfoResponse

| Field | Type | Description |
|---|---|---|
| `id` | UUID | Page ID |
| `document_id` | UUID | Parent document ID |
| `page_number` | int | Page number in document |
| `sheet_number` | string? | Sheet number (e.g., "S-101") |
| `title` | string? | Sheet title |
| `display_name` | string? | Custom display name |
| `display_order` | int? | Manual sort order |
| `group_name` | string? | Custom group assignment |
| `discipline` | string? | Auto-detected discipline |
| `page_type` | string? | Page type (plan, detail, schedule, etc.) |
| `classification` | string? | Full classification label |
| `classification_confidence` | float? | Classification confidence (0-1) |
| `scale_text` | string? | Human-readable scale text |
| `scale_value` | float? | Numeric scale factor |
| `scale_calibrated` | bool | Whether scale is confirmed |
| `scale_detection_method` | string? | How scale was detected |
| `measurement_count` | int | Number of measurements on this page |
| `thumbnail_url` | string? | Presigned thumbnail URL |
| `image_url` | string? | Presigned full-size image URL |
| `width` | int | Image width in pixels |
| `height` | int | Image height in pixels |
| `is_relevant` | bool | Whether page appears in sheet tree |
