# 19 — Cost Database Seeding (CWICR Catalog Import)

> **Status:** Scoping / dev handoff
> **Priority:** HIGH — highest value-to-effort ratio of the five DDC-derived features
> **Effort estimate:** 1–2 days
> **Depends on:** Nothing (assembly system already complete)
> **Blocks:** 23-COST-MATCHING.md (matching needs a populated cost database)

---

## 1. Problem Statement

The assembly system (Phase 3 / `13-ASSEMBLY-SYSTEM.md`) is fully built: `Assembly`, `AssemblyComponent`, `AssemblyTemplate` models, formula engine, cost recalculation, and the Cost tab in the workspace RightPanel all work. However, the `cost_items` table — the master cost database that assembly components are supposed to draw unit costs from — is **empty**. Every unit cost must currently be typed by hand, which makes the costing workflow impractical for real estimating work.

The DataDrivenConstruction OpenConstructionERP repository ships extracted CWICR construction cost catalogs as plain CSV files that can seed this table with ~7,000 real resources (materials, equipment, labor, electricity rates), including a US-regionalized catalog priced in USD.

## 2. Source Data

Repository: `github.com/datadrivenconstruction/OpenConstructionERP` (design/data reference only — no code is ported; the import script is written from scratch in our codebase).

| File (in their `data/catalog/`) | Rows | Contents |
|---|---|---|
| `cwicr_resources_full.csv` | 7,024 | All resource types combined, base prices in EUR |
| `cwicr_materials.csv` | 4,808 | Materials (concrete, steel, wood, …) |
| `cwicr_equipments.csv` | 1,594 | Equipment & machinery |
| `cwicr_labors.csv` | 68 | Labor grades |
| `cwicr_operators.csv` | 42 | Machine operators |
| `cwicr_electricitys.csv` | 512 | Electricity consumption rates |
| `regions/DDC_CWICR_USA_USD_Catalog.csv` | ~7,187 | **US region, USD pricing** — primary import target |

USA catalog columns (verified against the actual file):
`resource_code, name, type, category, unit, price_avg, price_min, price_max, price_median, price_variants, currency, avg_cost_per_use, avg_qty_per_use, usage_count, used_in_work_items, parent_category, parent_collection, parent_department, parent_section, rec_rev`

**Licensing note:** the CSVs ship inside an AGPL-3.0 repository; the underlying CWICR database is DDC's own work (55,719 work items). Current use (public, non-monetized repo) is fine. If the project's distribution model ever changes, re-confirm data licensing with DDC (info@datadrivenconstruction.io) before shipping the data.

## 3. Current State (our codebase)

- **Model:** `CostItem` exists at `backend/app/models/assembly.py` (line ~69), table `cost_items`. Fields: `code` (String 50, indexed), `name` (String 255), `description` (Text), `item_type` (String 50, default "material"), `category`, `subcategory` (String 100), `unit` (String 50), `unit_cost` (Numeric 10,4), `alt_unit`, `alt_unit_cost`, `conversion_factor`, labor-rate fields, plus `extra_data` JSONB (renamed from `metadata` in Phase 9 housekeeping).
- **No seed data** exists for `cost_items`. (`AssemblyTemplate` seed data exists — follow that pattern.)
- **No API route** for cost-item search was found under `backend/app/api/routes/` — the assembly component editor has no cost-lookup source.
- Conditions use imperial units (`LF`, `SF`, `CY`, `EA` — see `backend/app/models/condition.py`), while CWICR units are metric (`kg`, `m3`, `Machine hours`, …).

## 4. Scope

### In scope
1. **Import script** `backend/scripts/seed_cost_items.py` (runnable via `docker compose exec api python -m scripts.seed_cost_items --file <csv> --source cwicr-usa`):
   - Parses the USA USD catalog CSV (and optionally the per-type CSVs).
   - Field mapping:
     - `resource_code` → `code`
     - `name` → `name`
     - `type` (Material/Equipment/Labor/Operator/Electricity) → `item_type` (lowercased; map `operator` → `labor` or keep as distinct `item_type` — decide once, document in the script)
     - `category` → `category`; `parent_collection` → `subcategory`
     - `unit` → `unit` (normalized, see below)
     - `price_avg` → `unit_cost`
     - `currency`, `price_min/max/median`, `parent_*` hierarchy, source file + import date → `extra_data` JSONB (provenance: `{"source": "DDC_CWICR_USA_USD", "imported_at": ..., "price_min": ..., ...}`)
   - **Idempotent:** upsert on `code`; re-running refreshes prices without duplicating rows. `--replace-source` flag deletes rows whose `extra_data.source` matches before re-import.
   - **Unit normalization:** map catalog unit strings to a canonical set (`m3`, `m2`, `m`, `kg`, `t`, `hr`, `ea`, `kwh`). Do NOT silently convert metric→imperial prices in the importer; store canonical metric units and populate `alt_unit`/`alt_unit_cost`/`conversion_factor` for the common imperial equivalents where the conversion is exact (e.g. `m3` ↔ `CY` factor 1.30795, `m2` ↔ `SF` factor 10.7639, `m` ↔ `LF` factor 3.28084). This keeps source data honest and makes imperial pricing available to the assembly UI.
   - Row-level validation: skip and log rows with missing name/unit/price; print an import summary (imported / updated / skipped).
2. **Search endpoint** — `GET /api/v1/cost-items?q=&item_type=&category=&limit=` in a new `backend/app/api/routes/cost_items.py` (or extend `assemblies.py` if preferred; follow existing router registration in `main.py`). Case-insensitive `ILIKE` search on `name`/`code`, filterable by `item_type` and `category`, paginated, ordered by relevance-ish (exact code match first, then name matches).
3. **Frontend wiring** — in the Cost tab's component editor (`RightPanel.tsx` cost tab / component add flow), add a typeahead that hits the search endpoint and, on selection, fills the component's `name`, `unit`, and `unit_cost` (using `alt_unit_cost` when the user's working unit is imperial and a conversion exists). Manual entry remains fully supported.
4. **Makefile/README target** — `make seed-costs` documented in `STATUS.md` common commands.

### Out of scope
- Automatic condition→cost-item matching (that is `23-COST-MATCHING.md`).
- Currency conversion service / FX rates (catalog is already USD; store `currency` in `extra_data`).
- Importing the 55k work-item assemblies (only the ~7k resource rows are in the public CSVs).
- Editing UI for cost items (DB-level maintenance via re-import is sufficient for now).

## 5. Acceptance Criteria

1. Running the seed script against the USA catalog populates ≥ 7,000 `cost_items` rows with non-zero `unit_cost`, correct `item_type` distribution (~4.8k material, ~1.6k equipment, remainder labor/operator/electricity), and provenance in `extra_data`.
2. Running the script twice produces no duplicates (row count unchanged on second run).
3. `GET /api/v1/cost-items?q=concrete&item_type=material` returns paginated matches in < 200 ms against the seeded table (add index on `name` if needed — `code` is already indexed).
4. In the workspace Cost tab, adding an assembly component via the typeahead fills name/unit/cost without manual typing.
5. Existing assembly tests still pass; new tests cover the importer (mapping, idempotency, bad-row skipping) and the search endpoint.

## 6. Testing Requirements

- `backend/tests/unit/test_cost_item_import.py` — mapping correctness against a small fixture CSV (5–10 rows covering each `type`, a bad row, a duplicate code), idempotent upsert, unit normalization + alt-unit conversion factors.
- `backend/tests/integration/test_cost_items_api.py` — search, filters, pagination, empty-result behavior.
- Frontend: typeahead test (debounced query, selection fills fields) per existing RTL/Vitest patterns.

## 7. Risks / Open Questions

- **Unit mismatch UX:** estimators think in LF/SF/CY/EA; catalog rows are metric. The alt-unit approach covers area/volume/length; items priced per `kg`/`t` have no natural imperial mapping — display as-is.
- **Price quality:** CWICR averages are broad-market statistical prices, not local quotes. UI should present them as *reference* pricing (consider a subtle "ref" badge sourced from `extra_data.source`).
- **`operator` and `electricity` types** don't exist in the current `item_type` vocabulary — confirm whether to fold into `labor`/`equipment` or extend the vocabulary (recommend extending; it's a free-text column).
