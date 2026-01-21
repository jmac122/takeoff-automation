# Frontend Viewer Rendering

How the TakeoffViewer displays page images and scale overlays.

## Component Architecture

```mermaid
flowchart TD
    subgraph Pages["Pages"]
        ROUTE["/projects/:id/takeoff"] --> TV[TakeoffViewer]
    end

    subgraph Components["Components"]
        TV --> VH[ViewerHeader]
        TV --> CS[ClassificationSidebar]
        TV --> CANVAS[Konva Stage/Canvas]
        
        VH --> ZOOM[Zoom Controls]
        VH --> SCALE_BTN[Show Scale Location]
        
        CS --> PAGE_LIST[Page Thumbnails]
        CS --> SCALE_INFO[Scale Information]
    end

    subgraph Canvas["Canvas Layers"]
        CANVAS --> IMG_LAYER[Image Layer]
        CANVAS --> OVERLAY_LAYER[Overlay Layer]
        
        IMG_LAYER --> PAGE_IMG[Page Image]
        OVERLAY_LAYER --> SCALE_BOX[Scale Bbox Highlight]
        OVERLAY_LAYER --> MEASUREMENTS[Measurement Shapes]
    end

    style Pages fill:#e3f2fd
    style Components fill:#fff8e1
    style Canvas fill:#e8f5e9
```

## Image Loading Flow

```mermaid
sequenceDiagram
    participant User
    participant TV as TakeoffViewer
    participant API as Backend API
    participant MinIO as MinIO Storage

    User->>TV: Navigate to page
    TV->>API: GET /pages/{id}
    API-->>TV: Page metadata (image_key, scale_calibration_data)
    
    TV->>API: GET /pages/{id}/image
    API->>MinIO: Download image
    MinIO-->>API: Image bytes
    API-->>TV: Image data
    
    TV->>TV: Load into Konva Image
    TV->>TV: Apply zoom/pan state
    TV->>TV: Render scale overlay if enabled
```

## Scale Overlay Rendering

```mermaid
flowchart TD
    subgraph Data["Data Source"]
        PAGE[Page Object] --> SCD[scale_calibration_data]
        SCD --> BEST[best_scale]
        BEST --> BBOX[bbox: {x, y, width, height}]
    end

    subgraph State["React State"]
        SHOW[showScaleLocation: boolean]
        ZOOM[canvasControls.zoom]
    end

    subgraph Render["Konva Rendering"]
        BBOX --> RECT[Konva.Rect]
        SHOW --> COND{Show overlay?}
        COND -->|Yes| RECT
        COND -->|No| HIDDEN[Not rendered]
        
        RECT --> STYLE[Style:<br/>fill: green 15% opacity<br/>stroke: green<br/>strokeWidth: 3/zoom]
    end

    style Data fill:#e3f2fd
    style State fill:#fff8e1
    style Render fill:#e8f5e9
```

## Coordinate Handling

```mermaid
flowchart LR
    subgraph Storage["Stored Coordinates"]
        BBOX[bbox from DB<br/>x: 2100, y: 2850<br/>width: 150, height: 20]
    end

    subgraph Canvas["Canvas Rendering"]
        STAGE[Konva Stage]
        LAYER[Konva Layer]
        RECT[Konva.Rect]
        
        STAGE --> LAYER --> RECT
    end

    subgraph Transform["Transformations"]
        ZOOM[User zoom: 0.5x]
        PAN[User pan: offset]
    end

    BBOX --> |Direct use| RECT
    ZOOM --> |Handled by Konva| STAGE
    PAN --> |Handled by Konva| STAGE

    NOTE[Note: Bbox coordinates are used directly.<br/>Konva handles zoom/pan transformations.]

    style Storage fill:#e3f2fd
    style Canvas fill:#e8f5e9
    style Transform fill:#fff8e1
```

**Key Point:** The bbox coordinates from `scale_calibration_data` are in the same coordinate space as the stored image. No transformation is needed - Konva handles zoom/pan at the Stage level.

## TakeoffViewer State

```mermaid
stateDiagram-v2
    [*] --> Loading: Mount component
    Loading --> Ready: Page data loaded
    Loading --> Error: API error
    
    Ready --> Zooming: User zooms
    Zooming --> Ready: Zoom complete
    
    Ready --> Panning: User drags
    Panning --> Ready: Pan complete
    
    Ready --> ShowScale: Toggle scale overlay
    ShowScale --> Ready: Toggle off
    
    Ready --> PageChange: Select different page
    PageChange --> Loading: Fetch new page
```

## Component Props Flow

```mermaid
flowchart TD
    subgraph TakeoffViewer
        PAGE_DATA[pageData from API]
        CONTROLS[canvasControls state]
        SHOW_SCALE[showScaleLocation state]
    end

    subgraph ViewerHeader
        VH_ZOOM[zoom value]
        VH_SCALE_BTN[onToggleScaleLocation]
    end

    subgraph KonvaCanvas
        STAGE[Stage: width, height, scale]
        IMAGE[Image: page image]
        RECT[Rect: scale bbox]
    end

    PAGE_DATA --> |scale_calibration_data| RECT
    CONTROLS --> |zoom| STAGE
    CONTROLS --> |zoom| VH_ZOOM
    SHOW_SCALE --> |visible| RECT
    SHOW_SCALE --> VH_SCALE_BTN

    style TakeoffViewer fill:#e3f2fd
    style ViewerHeader fill:#fff8e1
    style KonvaCanvas fill:#e8f5e9
```

## Key Files

| File | Purpose |
|------|---------|
| `frontend/src/pages/TakeoffViewer.tsx` | Main viewer component, canvas setup |
| `frontend/src/components/viewer/ViewerHeader.tsx` | Toolbar with zoom, scale toggle |
| `frontend/src/components/viewer/ClassificationSidebar.tsx` | Page list, scale info display |
| `frontend/src/hooks/useScaleDetection.ts` | Scale detection API calls |
