# Frontend Canvas Rendering

How the TakeoffWorkspace canvas displays page images, measurement overlays, and scale/calibration layers.

> **Note:** The legacy `TakeoffViewer` at `/documents/:id/pages/:id` is deprecated and shows a deprecation banner. All new development targets `TakeoffWorkspace`.

## Component Architecture

```mermaid
flowchart TD
    subgraph Pages["Pages"]
        ROUTE["/projects/:id/workspace"] --> TW[TakeoffWorkspace]
    end

    subgraph Components["Components"]
        TW --> TT[TopToolbar]
        TW --> PANELS[Panel Group]
        TW --> BSB[BottomStatusBar]
        TW --> SCD[ScaleCalibrationDialog]

        PANELS --> ST[SheetTree]
        PANELS --> CC[CenterCanvas]
        PANELS --> RP[RightPanel]

        TT --> ZOOM[Zoom Controls]
        TT --> SCALE_BTN[Scale: Set / Detect / Show Location]
        TT --> TB_BTN[Title Block: Toggle / Show Region]
        TT --> UNDO[Undo / Redo]
    end

    subgraph Canvas["Canvas Layers (Konva Stage)"]
        CC --> IMG_LAYER[Layer: Background Image]
        CC --> MEAS_LAYER[Layer: Measurement Overlays]
        CC --> PREVIEW_LAYER[Layer: Drawing Preview]
        CC --> CAL_LAYER[Layer: Calibration Overlay]
        CC --> TB_LAYER[Layer: Title Block Overlays]
        CC --> SCALE_LAYER[Layer: Scale Detection / Location]
        CC --> GHOST_LAYER[Layer: GhostPointLayer — AI predictions]

        MEAS_LAYER --> MSHAPE[MeasurementShape per measurement]
        PREVIEW_LAYER --> DPL[DrawingPreviewLayer]
        CAL_LAYER --> CALOL[CalibrationOverlay — amber dashed line]
    end

    subgraph HTML["HTML Overlays (above canvas)"]
        CC --> WARN[Scale Warning Banner]
        CC --> DET_BAN[ScaleDetectionBanner]
        CC --> CAL_BAN[Calibration Mode Banner]
        CC --> TB_BAN[Title Block Mode Banner]
        CC --> MPANEL[MeasurementsPanel]
        CC --> CTXMENU[MeasurementContextMenu]
    end

    style Pages fill:#e3f2fd
    style Components fill:#fff8e1
    style Canvas fill:#e8f5e9
    style HTML fill:#fce4ec
```

## Image Loading Flow

```mermaid
sequenceDiagram
    participant User
    participant TW as TakeoffWorkspace
    participant CC as CenterCanvas
    participant API as Backend API
    participant MinIO as MinIO Storage

    User->>TW: Select sheet in SheetTree
    TW->>TW: setActiveSheet(sheetId)
    TW->>API: GET /pages/{sheetId}
    API-->>TW: Page data (scale_calibration_data, title_block_region)

    CC->>API: GET /pages/{sheetId}/image (via usePageImage)
    API->>MinIO: Download image
    MinIO-->>API: Image bytes
    API-->>CC: HTMLImageElement

    CC->>CC: Load into Konva Image layer
    CC->>CC: Restore saved viewport or fit-to-page
    CC->>CC: Render measurement overlays
    CC->>CC: Render active overlays (scale, title block, etc.)
```

## Scale Calibration Rendering

```mermaid
flowchart TD
    subgraph Trigger["User Action"]
        BTN[TopToolbar: Set Scale] --> START[startCalibration]
    end

    subgraph Drawing["Calibration Drawing"]
        START --> MODE[isCalibrating = true]
        MODE --> CLICK1[Click: startDrawing point]
        CLICK1 --> MOVE[Mouse move: updateDrawing]
        MOVE --> CLICK2[Click: finishDrawing]
    end

    subgraph Overlay["CalibrationOverlay (Konva Layer)"]
        MOVE --> LINE[Dashed amber line: start → current]
        CLICK2 --> FINAL_LINE[Solid amber line: start → end]
    end

    subgraph Dialog["ScaleCalibrationDialog"]
        CLICK2 --> DIALOG[Opens dialog with pixel distance]
        DIALOG --> INPUT[User enters real distance + unit]
        INPUT --> SUBMIT[POST /pages/{id}/calibrate]
        SUBMIT --> DONE[Calibration saved, dialog closes]
    end

    style Trigger fill:#e3f2fd
    style Drawing fill:#fff8e1
    style Overlay fill:#e8f5e9
    style Dialog fill:#fce4ec
```

## Scale Detection Overlay

```mermaid
flowchart TD
    subgraph Data["Data Source"]
        PAGE[Page Object] --> SCD[scale_calibration_data]
        SCD --> BEST[best_scale]
        BEST --> BBOX[bbox: x, y, width, height]
        BEST --> TEXT[text: "1/4 inch = 1 foot"]
    end

    subgraph State["React State"]
        SHOW[showScaleLocation: boolean]
        DET[detectionResult: ScaleDetectionResult]
        HIGH[scaleHighlightBox: bbox]
    end

    subgraph Render["Konva Rendering"]
        BBOX --> RECT_LOC[Scale Location Rect — green, 15% opacity]
        SHOW --> COND1{Show location?}
        COND1 -->|Yes| RECT_LOC
        COND1 -->|No| HIDDEN1[Not rendered]

        HIGH --> RECT_DET[Detection Highlight Rect — amber, animated]
        DET --> BANNER[ScaleDetectionBanner — green bar above canvas]
    end

    style Data fill:#e3f2fd
    style State fill:#fff8e1
    style Render fill:#e8f5e9
```

## Title Block Rendering

```mermaid
flowchart TD
    subgraph Mode["Title Block Mode"]
        TOGGLE[TopToolbar: Title Block toggle] --> ACTIVE[isTitleBlockMode = true]
        ACTIVE --> CLICK[Mouse down: start draft rect]
        CLICK --> DRAG[Mouse move: update draft rect]
        DRAG --> RELEASE[Mouse up: finalize draft rect]
    end

    subgraph Overlays["Canvas Overlays"]
        DRAG --> DRAFT[Blue dashed Rect — draft region]
        RELEASE --> BANNER[Save banner appears: Save / Reset]
        SHOW_REGION[Show Region toggle] --> EXISTING[Green filled Rect — saved region]
    end

    subgraph Save["Save Flow"]
        BANNER --> SAVE[POST /documents/{id}/title-block-region]
        SAVE --> OCR[Backend re-runs OCR with new region]
        OCR --> POLL[pollUntil: wait for OCR completion]
        POLL --> DONE[Page data refreshed]
    end

    style Mode fill:#e3f2fd
    style Overlays fill:#fff8e1
    style Save fill:#e8f5e9
```

## Coordinate Handling

```mermaid
flowchart LR
    subgraph Storage["Stored Coordinates"]
        BBOX[bbox from DB<br/>x: 2100, y: 2850<br/>width: 150, height: 20]
        TB[title_block_region from DB<br/>normalized: 0-1 range]
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
        TB_CONV[Title block: normalized × image dimensions]
    end

    BBOX --> |Direct use| RECT
    TB --> |Multiply by sheet width/height| RECT
    ZOOM --> |Handled by Konva| STAGE
    PAN --> |Handled by Konva| STAGE

    style Storage fill:#e3f2fd
    style Canvas fill:#e8f5e9
    style Transform fill:#fff8e1
```

**Key Points:**
- Scale bbox coordinates are in image pixel space — used directly by Konva
- Title block region is stored as normalized (0-1) coordinates and converted to pixel coords by multiplying by sheet dimensions
- Konva handles zoom/pan transformations at the Stage level

## Canvas State Modes

```mermaid
stateDiagram-v2
    [*] --> Ready: Sheet loaded

    Ready --> Drawing: Select drawing tool
    Drawing --> Ready: Complete or cancel drawing

    Ready --> Calibrating: Click "Set Scale"
    Calibrating --> CalibDialog: Draw calibration line
    CalibDialog --> Ready: Submit or cancel

    Ready --> TitleBlockMode: Click "Title Block" toggle
    TitleBlockMode --> TitleBlockSave: Draw region
    TitleBlockSave --> Ready: Save or reset

    Ready --> ReviewMode: Toggle review mode
    ReviewMode --> Ready: Toggle off

    Ready --> Selecting: Click measurement
    Selecting --> Ready: Click empty area
    Selecting --> Moving: Drag measurement
    Moving --> Selecting: Drop
```

## Key Files

| File | Purpose |
|------|---------|
| `frontend/src/components/workspace/TakeoffWorkspace.tsx` | Layout orchestrator, scale/calibration/title block state management |
| `frontend/src/components/workspace/CenterCanvas.tsx` | Konva Stage with all layers, overlays, and event handling |
| `frontend/src/components/workspace/TopToolbar.tsx` | Toolbar with scale, title block, and drawing controls |
| `frontend/src/components/viewer/CalibrationOverlay.tsx` | Konva Layer: dashed amber calibration line |
| `frontend/src/components/viewer/ScaleDetectionBanner.tsx` | HTML: post-detection result banner |
| `frontend/src/components/viewer/MeasurementsPanel.tsx` | HTML: floating measurement list |
| `frontend/src/components/viewer/MeasurementShape.tsx` | Renders individual measurement geometry on Konva |
| `frontend/src/components/viewer/DrawingPreviewLayer.tsx` | Live drawing preview on Konva |
| `frontend/src/hooks/useScaleCalibration.ts` | Scale calibration line drawing state |
| `frontend/src/hooks/useScaleDetection.ts` | AI scale detection with polling |
| `frontend/src/hooks/usePageImage.ts` | Image loading for canvas display |
