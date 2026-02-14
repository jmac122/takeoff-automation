# ForgeX Takeoffs - Project Status

**Last Updated:** February 12, 2026
**Current State:** All 9 phases complete.
**Branch:** `claude/create-phase-1-tasks-OBEE7`

---

## Quick Status

| Service | Status | Address |
|---------|--------|---------|
| PostgreSQL 16 | Running | localhost:5432 |
| Redis 7 | Running | localhost:6379 |
| MinIO | Running | localhost:9000 (API) / 9001 (Console) |
| FastAPI + Uvicorn | Running | http://localhost:8000 |
| Vite Dev Server | Running | http://localhost:5173 |
| Celery Worker | Running | concurrency=2 |

---

## Architecture

| Layer | Stack |
|-------|-------|
| **Backend** | FastAPI, SQLAlchemy (async), Alembic, Celery, Redis, PostgreSQL, MinIO |
| **Frontend** | React 18, TypeScript, Vite, react-konva, Zustand, React Query, Tailwind CSS |
| **AI/LLM** | Multi-provider: Anthropic (Claude Sonnet), OpenAI (GPT-4o), Google (Gemini 2.5 Flash), xAI (Grok Vision) |

---

## Completed Work

### Foundation (Pre-Phase)
- Document ingestion pipeline (PDF/TIFF upload, page splitting, OCR via Google Vision)
- Page classification (OCR-based default + LLM vision option)
- Scale detection (auto-detect 15+ formats + manual calibration)
- Multi-provider AI takeoff generation (`AITakeoffService`)
- Measurement engine (area, linear, count calculations)
- Conditions CRUD with color, unit, scope, category, templates
- Unified Task API (`TaskTracker`, `TaskRecord`, `useTaskPolling`)
- Export system backend (Excel, CSV, PDF, OST XML exporters + Celery worker)
- Three-panel workspace layout (`TakeoffWorkspace`)
- Sheet tree with grouping, conditions panel, properties inspector, quick create bar

### Phase 1: Canvas Migration (Konva.js in New Workspace)
- `CenterCanvas` replaced with `react-konva` Stage/Layer
- 7 drawing tools (select, line, polyline, polygon, rectangle, circle, point) in `TopToolbar`
- Measurement overlay rendering color-coded by condition
- Undo/redo with server sync
- Viewport persistence per sheet in `workspaceStore`
- Scale calibration dialog and overlay (draw-to-calibrate workflow)
- Scale warning banner for uncalibrated sheets
- Auto detect scale via AI (toolbar button + detection banner)
- Measurement duplication with 12px offset (context menu)
- Toggle measurement visibility (context menu show/hide)
- Bring to front / send to back z-ordering (context menu)
- Undo/redo toolbar buttons wired to canvas actions
- Title block mode (draw region, re-run OCR, save/reset)
- Scale location display toggle (MapPin overlay)
- Measurements list panel (per-sheet, filterable by condition)

### Phase 2: Enhanced Review Interface
- `MeasurementHistory` model with action audit trail
- Review service: approve, reject, modify, auto-accept batch, stats, navigation
- Review API: verify, reject, modify geometry, auto-accept, stats, next-unreviewed
- Review mode toggle with keyboard shortcuts (A = approve, R = reject, S = skip, E = edit)
- Confidence filtering slider + auto-accept button in toolbar
- Review stats in `BottomStatusBar`

### Phase 3: Assembly System
- `Assembly`, `AssemblyComponent`, `AssemblyTemplate`, `AssemblyTemplateItem` models
- Formula engine with AST-safe expression parsing (variables: quantity, depth, area, etc.)
- Assembly service: CRUD, template creation, cost recalculation with markup
- Full API: assembly CRUD, template endpoints, project cost summary
- "Cost" tab in `RightPanel` with inline editing

### Phase 4: Auto Count Feature
- Template matching service (OpenCV `matchTemplate`, scale/rotation tolerance)
- LLM similarity service (vision model fallback/validation)
- Auto count orchestrator (template match -> LLM validation -> NMS dedup)
- Celery task + API endpoint: `POST /pages/{id}/auto-count`
- Frontend: Auto Count button in TopToolbar

### Phase 5: Quick Adjust Tools
- Geometry adjuster: 7 operations (nudge, snap, extend, trim, offset, split, join)
- Single dispatch endpoint: `PUT /measurements/{id}/adjust`
- `QuickAdjustToolbar` floating component (appears on selection)
- `GridOverlay` SVG component (toggleable, configurable size)
- Keyboard shortcuts: Arrow keys (nudge), G (snap toggle), X (extend)

### Phase 6: AI Assist Layer
- **AutoTab:** `PredictNextPointService` with synchronous endpoint `POST /pages/{id}/predict-next-point` (768px downscale, <800ms target, silent failure)
- **GhostPointLayer:** Konva ghost overlay with pulsing cyan animation, Tab accept / Esc dismiss
- **Batch AI Inline:** AI Assist button triggers `autonomous_ai_takeoff_task` via Celery + `useTaskPolling`
- **Draft measurement styling:** Dashed stroke + 60% opacity for unverified AI-generated measurements
- **AI Confidence Visualization:** Palette toggle in toolbar, color-codes by confidence (green/yellow/red)

### Phase 7: Export & Reporting UI
- **Cost data classes:** `AssemblyCostData` dataclass in `base.py`, joinedload in `export_tasks.py`
- **Excel exporter:** Cost columns on Summary sheet (Unit Cost, Material, Labor, Total Cost, Markup Total) + "Cost Summary" sheet
- **PDF exporter:** Cost columns in summary table + project total with markup line
- **Frontend:** `ExportDropdown` component with 4 format options + cost/unverified toggles, `useExport` hook with polling + auto-download
- **Wired into** `TopToolbar` with loading state

### Phase 8: Plan Overlay / Version Comparison
- **Revision schema:** `DocumentResponse` extended with revision fields; `LinkRevisionRequest`, `RevisionChainItem`, `RevisionChainResponse`, `PageComparisonRequest/Response` schemas
- **API endpoints:** `PUT /documents/{id}/revision` (link), `GET /documents/{id}/revisions` (chain), `POST /documents/compare-pages` (image comparison)
- **Frontend:** `RevisionChainPanel` (timeline view + selection), `LinkRevisionDialog` (modal), `PlanOverlayView` (overlay/side-by-side/swipe modes with opacity slider)
- **Integration:** "Revisions" tab in `RightPanel`, overlay view in `TakeoffWorkspace`

### Phase 9: Housekeeping & Quality
- **STATUS.md** fully rewritten to reflect all phases
- **Dead file cleanup:** Removed 3 `.bak` files from `frontend/src/pages/`
- **Debug telemetry removal:** Removed 7 `fetch('http://127.0.0.1:7244/...')` blocks from `TakeoffViewer.tsx` and `MeasurementShape.tsx`
- **Old viewer deprecation:** Added deprecation banner on `TakeoffViewer` route
- **Migration audit:** Single head (`q5r6s7t8u9v0`), all branches merged, clean chain
- **Model fix:** Renamed reserved `metadata` attribute to `extra_data` in `CostItem`, `Assembly`, `AssemblyComponent` models (DB column unchanged)
- **10-feature workspace migration:** Migrated scale calibration, scale detection, scale warning, measurement duplication, visibility toggle, z-ordering, undo/redo wiring, title block mode, scale location display, and measurements panel from `TakeoffViewer` to `TakeoffWorkspace`

---

## Database

**22 Alembic migrations**, head: `q5r6s7t8u9v0`

### Key Models
| Model | Purpose |
|-------|---------|
| `Project` | Top-level container |
| `Document` | Uploaded PDF/TIFF with revision tracking fields |
| `Page` | Individual sheet with classification, scale, OCR |
| `Condition` | Takeoff line item with color, unit, scope |
| `Measurement` | Geometry + quantity, linked to condition and page |
| `MeasurementHistory` | Audit trail for review actions |
| `Assembly` | Cost breakdown linked 1:1 to condition |
| `AssemblyComponent` | Line item in assembly (material/labor/equipment) |
| `AssemblyTemplate` / `AssemblyTemplateItem` | Reusable cost templates |
| `ExportJob` | Async export tracking (status, file key, download URL) |
| `TaskRecord` | Unified async task status |
| `AutoCountResult` / `AutoCountDetection` | Auto count results |

---

## API Endpoints

### Projects
| Method | Path | Description |
|--------|------|-------------|
| POST | `/projects` | Create project |
| GET | `/projects` | List projects |
| GET | `/projects/{id}` | Get project |
| PUT | `/projects/{id}` | Update project |
| DELETE | `/projects/{id}` | Delete project |

### Documents
| Method | Path | Description |
|--------|------|-------------|
| POST | `/projects/{id}/documents` | Upload document |
| GET | `/projects/{id}/documents` | List documents |
| GET | `/documents/{id}` | Get document with pages |
| GET | `/documents/{id}/status` | Processing status |
| PUT | `/documents/{id}/title-block-region` | Set title block |
| DELETE | `/documents/{id}` | Delete document |
| PUT | `/documents/{id}/revision` | Link as revision |
| GET | `/documents/{id}/revisions` | Get revision chain |
| POST | `/documents/compare-pages` | Compare page images |

### Conditions
| Method | Path | Description |
|--------|------|-------------|
| POST | `/projects/{id}/conditions` | Create condition |
| GET | `/projects/{id}/conditions` | List conditions |
| GET | `/conditions/{id}` | Get condition |
| PUT | `/conditions/{id}` | Update condition |
| DELETE | `/conditions/{id}` | Delete condition |
| PATCH | `/conditions/{id}/visibility` | Toggle visibility |

### Measurements
| Method | Path | Description |
|--------|------|-------------|
| POST | `/conditions/{id}/measurements` | Create measurement |
| GET | `/measurements/{id}` | Get measurement |
| PUT | `/measurements/{id}` | Update measurement |
| DELETE | `/measurements/{id}` | Delete measurement |
| PUT | `/measurements/{id}/adjust` | Quick adjust (7 operations) |
| POST | `/measurements/{id}/approve` | Approve measurement |
| POST | `/measurements/{id}/reject` | Reject measurement |
| POST | `/measurements/{id}/modify` | Modify measurement |

### AI Takeoff
| Method | Path | Description |
|--------|------|-------------|
| POST | `/pages/{id}/ai-takeoff` | Targeted AI takeoff |
| POST | `/pages/{id}/autonomous-takeoff` | Autonomous AI takeoff |
| POST | `/batch-ai-takeoff` | Batch AI takeoff |
| POST | `/pages/{id}/predict-next-point` | AutoTab prediction |
| GET | `/providers` | Available LLM providers |

### Review
| Method | Path | Description |
|--------|------|-------------|
| POST | `/measurements/{id}/approve` | Approve measurement |
| POST | `/measurements/{id}/reject` | Reject measurement |
| POST | `/measurements/{id}/modify` | Modify measurement |
| GET | `/measurements/{id}/history` | Measurement history |
| POST | `/projects/{id}/measurements/auto-accept` | Batch auto-accept |
| GET | `/projects/{id}/review-stats` | Review statistics |
| GET | `/pages/{id}/measurements/next-unreviewed` | Next unreviewed |

### Auto Count
| Method | Path | Description |
|--------|------|-------------|
| POST | `/pages/{id}/auto-count` | Start auto count |
| GET | `/auto-count-sessions/{id}` | Get session details |
| GET | `/pages/{id}/auto-count-sessions` | List page sessions |
| POST | `/auto-count-detections/{id}/confirm` | Confirm detection |
| POST | `/auto-count-detections/{id}/reject` | Reject detection |
| POST | `/auto-count-sessions/{id}/bulk-confirm` | Bulk confirm |
| POST | `/auto-count-sessions/{id}/create-measurements` | Create measurements |

### Assemblies
| Method | Path | Description |
|--------|------|-------------|
| POST | `/conditions/{id}/assembly` | Create assembly |
| GET | `/conditions/{id}/assembly` | Get assembly |
| GET | `/assemblies/{id}` | Get assembly by ID |
| PUT | `/assemblies/{id}` | Update assembly |
| DELETE | `/assemblies/{id}` | Delete assembly |
| POST | `/assemblies/{id}/calculate` | Recalculate costs |
| POST | `/assemblies/{id}/lock` | Lock assembly |
| POST | `/assemblies/{id}/unlock` | Unlock assembly |
| POST | `/assemblies/{id}/components` | Add component |
| PUT | `/components/{id}` | Update component |
| DELETE | `/components/{id}` | Remove component |
| PUT | `/assemblies/{id}/components/reorder` | Reorder components |
| GET | `/assembly-templates` | List templates |
| GET | `/assembly-templates/{id}` | Get template |
| POST | `/formulas/validate` | Validate formula |
| GET | `/formulas/presets` | Formula presets |
| GET | `/formulas/help` | Formula documentation |
| GET | `/projects/{id}/cost-summary` | Project cost rollup |

### Exports
| Method | Path | Description |
|--------|------|-------------|
| POST | `/projects/{id}/export` | Start export (Excel/CSV/PDF/OST) |
| GET | `/exports/{id}` | Get export + download URL |
| GET | `/projects/{id}/exports` | List exports |
| DELETE | `/exports/{id}` | Delete export |

### Tasks
| Method | Path | Description |
|--------|------|-------------|
| GET | `/tasks/{id}/status` | Get task status |
| POST | `/tasks/{id}/register` | Register task |
| GET | `/projects/{id}/tasks` | List project tasks |

---

## Frontend Routes

| Route | Component | Status |
|-------|-----------|--------|
| `/projects` | `Projects` | Active |
| `/projects/:id` | `ProjectDetail` | Active |
| `/projects/:id/workspace` | `TakeoffWorkspace` | Active (primary) |
| `/projects/:id/documents/:id` | `DocumentDetail` | Active |
| `/documents/:id/pages/:id` | `TakeoffViewer` | Deprecated (banner shown) |

---

## Key Frontend Files

### Workspace (`frontend/src/components/workspace/`)
| File | Purpose |
|------|---------|
| `TakeoffWorkspace.tsx` | Three-panel resizable layout |
| `TopToolbar.tsx` | Drawing tools, zoom, grid, AI assist, review, confidence overlay |
| `CenterCanvas.tsx` | Konva Stage + measurement overlays + ghost layer |
| `BottomStatusBar.tsx` | Review stats, status indicators |
| `RightPanel.tsx` | Conditions panel + cost tab + revisions tab |
| `ExportDropdown.tsx` | Export format selector with options |
| `QuickAdjustToolbar.tsx` | Floating geometry adjustment tools |
| `GridOverlay.tsx` | SVG grid overlay |

### Hooks (`frontend/src/hooks/`)
| File | Purpose |
|------|---------|
| `useAutoTab.ts` | AutoTab prediction + accept/dismiss |
| `useAiAssist.ts` | Batch AI task management |
| `useExport.ts` | Export polling + auto-download |
| `useQuickAdjust.ts` | Geometry adjustment mutation + keyboard |
| `useKeyboardShortcuts.ts` | Global keyboard handler |
| `useTaskPolling.ts` | Reactive async task polling |
| `useReviewActions.ts` | Review approve/reject/skip |

### State (`frontend/src/stores/`)
| File | Purpose |
|------|---------|
| `workspaceStore.ts` | Zustand: viewport, tools, panels, review, AI, grid, selection |

---

## Common Commands

```bash
# Start all services
cd docker && docker compose up -d

# Health check
curl http://localhost:8000/api/v1/health

# Run migrations
cd docker && docker compose exec api alembic upgrade head

# Backend tests
cd backend && pytest tests/ -v --tb=short

# Frontend type-check + tests
cd frontend && npx tsc --noEmit && npm test -- --run

# View logs
docker logs forgex-api -f
docker logs forgex-worker -f
```
