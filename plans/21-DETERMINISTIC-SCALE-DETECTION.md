# 21 — Tier-1 Deterministic Scale Detection

> **Status:** Scoping / dev handoff
> **Priority:** MEDIUM-HIGH — cost/latency reduction on every ingested sheet, zero new capability risk
> **Effort estimate:** 1–2 days
> **Depends on:** Nothing; synergizes with 20-VECTOR-PDF-EXTRACTION.md (both read the PDF text layer)
> **Design reference (no code ported):** OpenConstructionERP `backend/app/modules/takeoff/scale_detect.py` — reference for the tiering rationale and plausibility-band idea only

---

## 1. Problem Statement

`ScaleDetector.detect_scale()` (`backend/app/services/scale_detector.py`, ~line 276) currently runs strategies in this order:

1. **Vision LLM** (PRIMARY — an API call per page)
2. Parse pre-detected OCR scale texts (fallback)
3. Regex search of full OCR text (fallback)
4. Graphical scale bar detection (fallback)

The deterministic machinery already exists and is good: `ScaleParser.parse_scale_text()` handles architectural (`1/4" = 1'-0"`), engineering (`1" = 20'`), and ratio (`1:100`) notations, and `Page` stores `ocr_text` + `ocr_blocks` and a `scale_source` enum-ish string (`vision_llm`, `ocr_predetected`, `ocr_pattern_match`, `manual_calibration`, `scale_bar`).

The problem is ordering and input: the expensive, non-deterministic LLM path runs **first** on every page, even though most CAD-generated sheets carry the scale note as machine-readable text — either in the PDF's native text layer (never currently consulted for scale) or in OCR output. Reading text the architect already typed is free, instant, and exact; the LLM should be the fallback, not the primary.

## 2. Feature Overview

Reorder scale detection into explicit tiers and add the PDF native text layer as a tier-1 input:

- **Tier 1 (deterministic, free):** parse scale notations from (a) the PDF native text layer extracted via PyMuPDF `page.get_text()` — new input, populated at ingestion; and (b) existing `ocr_text` / pre-detected scale texts. If exactly one plausible, unambiguous scale results → accept, done. No network call.
- **Tier 2 (deterministic, cheap):** graphical scale-bar detection (existing `ScaleBarDetector`).
- **Tier 3 (LLM, expensive):** the existing vision path — invoked **only** when tiers 1–2 fail or produce conflicting candidates.

Nothing about the manual calibration workflow, the scale warning banner, or the frontend changes behaviorally except that detection completes faster and `scale_source` more often reads `pdf_text` / `ocr_pattern_match` than `vision_llm`.

## 3. Detailed Requirements

### 3.1 PDF text layer capture

- During document processing, extract per-page native text (`page.get_text("text")`) and store it. Options, in preference order: (a) merge into the existing `ocr_text` only when OCR is skipped, (b) a new nullable `pdf_text` Text column on `Page` (one small migration — cleaner provenance; recommended). Pages with `vector_text_count == 0` (see 20) store null.
- Extraction runs inside the isolated parser child once `22-ISOLATED-PDF-PARSING.md` lands; until then, inline in the worker as today's fitz calls are.

### 3.2 Tier-1 parser hardening (`ScaleParser` extensions, same file)

- **Plausibility band:** reject parsed ratios outside a configurable band (~1:1 to 1:10000 equivalent). Six-figure "ratios" from part numbers/coordinates and 1:0 malformations must never surface as candidates.
- **Multi-candidate handling:** collect *all* distinct parsed scales from the page text. Rules:
  - 1 unique scale (dedup by ratio) → confident tier-1 result (`confidence` ~0.9, `scale_source="pdf_text"` or `"ocr_pattern_match"` per input source).
  - Multiple distinct scales (detail sheets: plan at 1/4", details at 1"/3") → do NOT auto-pick. Return all as candidates, `needs_calibration=True`, and surface them in the calibration dialog as one-click options (frontend: extend the existing scale calibration dialog's data source — candidates arrive via the existing detection result payload).
  - "AS NOTED"/"NTS"/"NOT TO SCALE" tokens → recognize explicitly and short-circuit to `needs_calibration=True` without ever invoking the LLM (the LLM cannot do better than the sheet's own declaration).
- **Location bbox:** when a tier-1 hit came from OCR text, reuse the existing OCR-block bbox matching (already implemented in the LLM path for pixel-perfect bboxes) so the MapPin scale-location display keeps working. Native-PDF-text hits can carry a bbox from `page.get_text("words")` word rectangles, transformed to image pixel space with the same render-scale transform specified in 20 §3.3.

### 3.3 Orchestration change

- Restructure `detect_scale()` into the tier order above. Preserve the return contract (`parsed_scales`, `scale_bars`, `best_scale`, `needs_calibration`) so `scale_tasks.py` and the frontend need no changes beyond the candidate-list UI addition.
- Config flag `SCALE_LLM_FALLBACK_ENABLED` (default true) and a per-call `force_llm` option (the toolbar's explicit "Auto detect scale via AI" button should still honor the user's intent and go straight to tier 3).
- Log which tier resolved each page (structured log field `scale_tier`) — this is the measurement instrument for the acceptance criterion below.

## 4. Out of Scope

- Any change to manual draw-to-calibrate, scale badge, or warning banner UX.
- Per-viewport/multi-region scales on a single sheet (one scale per page remains the data model).
- Title-block-region-restricted parsing (possible future refinement using the existing title block region feature to disambiguate multi-scale sheets).

## 5. Acceptance Criteria

1. On a corpus of representative CAD-generated sheets (assemble ~20 from existing test projects), ≥ 70% resolve at tier 1 with zero LLM calls, with parsed ratios matching manual verification.
2. Scanned sheets with no text layer and no OCR hits fall through to tiers 2–3 exactly as today (no regression on the existing scale-detection integration tests).
3. A sheet whose text contains "SCALE: AS NOTED" plus three detail scales produces multiple candidates, no auto-applied scale, and candidate options in the calibration dialog.
4. Part-number/coordinate noise (e.g. "1:250000", "3:1000000") never appears as a scale candidate (plausibility-band unit tests).
5. The toolbar AI-detect button still forces the vision path.
6. `scale_source` values are accurate per tier; existing consumers of `scale_source` unaffected.

## 6. Testing Requirements

- Unit (`test_scale_parser_tiers.py`): notation matrix (arch/eng/ratio × spacing/casing variants), plausibility band edges, multi-candidate dedup, AS-NOTED short-circuit — all pure-string tests, no DB/PDF.
- Unit: pdf-text extraction + word-bbox transform against a generated fixture PDF.
- Integration: tier orchestration with a mocked LLM client asserting call counts (0 for tier-1-resolvable input; 1 when forced or on fallthrough).

## 7. Risks

- **False confidence from stale notes:** a title block may declare a scale that doesn't match the plotted sheet (re-plotted/fit-to-page prints). Mitigation: tier-1 confidence stays below manual calibration's; the existing scale warning/verification UX remains; consider (future) cross-checking tier-1 result against a detected scale bar when both exist.
- **Text-layer soup:** CAD exports sometimes emit text as individual characters or curves; parse tolerance for whitespace-fragmented notations (`1 / 4 " = 1 ' - 0 "`) should be covered in the notation matrix tests.
