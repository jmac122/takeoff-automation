# 23 — Element-to-Cost Matching (Condition → Cost Item Suggestions)

> **Status:** Scoping / dev handoff
> **Priority:** MEDIUM — usability multiplier for the assembly system
> **Effort estimate:** 3–4 days
> **Depends on:** 19-COST-DATABASE-SEEDING.md (matching requires a populated `cost_items` table)
> **Design reference (no code ported):** OpenConstructionERP `backend/app/modules/cost_match/matcher.py` — reference for the scoring-factor design only; our matcher is original code

---

## 1. Problem Statement

After 19 lands, the cost database has ~7,000 items, but connecting them to takeoff work is still fully manual: an estimator creates a condition ("4\" slab on grade"), opens the Cost tab, creates an assembly, and hunts for each component through a typeahead. The obvious assist is missing: **given a condition's name, scope, and unit, suggest the most likely cost items (and assembly templates) automatically, ranked with an explainable confidence.**

This is the pattern proven in the reference project's cost-match module: deterministic, auditable text matching first; anything smarter only as a fallback; suggestions always human-confirmed — which matches the review philosophy already running through this codebase (AI drafts, human approves).

## 2. Feature Overview

A pure, deterministic matching service plus one endpoint plus suggestion UI:

- `match(query_text, query_unit, candidates) -> ranked [(item, confidence, factors)]`
- `GET /api/v1/cost-items/match?q=<text>&unit=<unit>&limit=10`
- Cost tab: when a condition has no assembly yet, show a "Suggested items" panel (and matching assembly templates) with one-click add. Confidence shown as a band (High / Review / —), with a hover explanation built from the factors.

An optional LLM-assisted stage 2 is explicitly deferred (see §4) — ship deterministic first, measure, then decide.

## 3. Detailed Requirements

### 3.1 Matching core — `backend/app/services/cost_match.py`

Pure module, no I/O, no DB (same testability contract as `formula_engine.py`). Pipeline:

1. **Normalize:** casefold, strip accents/punctuation, collapse whitespace, normalize common construction abbreviations via a curated synonym map (`conc`→`concrete`, `reinf`→`reinforced`, `SOG`→`slab on grade`, `ftg`→`footing`, `CIP`→`cast in place`, `rebar`→`reinforcing steel`, …). The synonym map is a data structure in the module, unit-tested, and the main thing that will grow over time.
2. **Tokenize to concept tokens:** drop stopwords; keep dimension tokens (`4"`, `#5`, `3000psi`) as tokens — they're discriminative in construction naming.
3. **Score** each candidate:
   - `query_coverage` = fraction of query concept tokens present in the candidate (dominant factor — a candidate covering everything the user typed is strong)
   - `term_overlap` = overlap coefficient `|Q∩C| / min(|Q|,|C|)` (rewards focused candidates over catch-all descriptions)
   - `unit_factor` = multiplier from unit compatibility (see 3.2): compatible → 1.0, unknown → ~0.9, hard dimension mismatch (area vs volume) → ~0.3 so a wrong-dimension item can never look confident
   - `confidence = (w1·query_coverage + w2·term_overlap) · unit_factor` with starting weights ~0.65/0.35; normalized-exact-string equality short-circuits to 1.0
   - Return `factors` alongside the score — every suggestion must be explainable ("matched 3/4 terms; units compatible (SF≈m2)").
4. **Bands** (config): High ≥ 0.75, Review ≥ 0.45, below → no-match with a hint ("try including the material, e.g. 'concrete'").

### 3.2 Unit-dimension table

Small shared mapping (used here and available to 19's alt-unit logic): each unit string → physical dimension (`length`: LF, m; `area`: SF, m2; `volume`: CY, m3; `count`: EA; `mass`: kg, t; `time`: hr, Machine hours; `energy`: kwh). Compatibility = same dimension. Lives in `cost_match.py` or `app/utils/units.py`; imperial/metric bridging factors already specified in 19 §4.1.

### 3.3 Candidate retrieval + endpoint

- Service wrapper narrows the DB candidate set before scoring (score all 7k rows is ~fine at this size, but still: prefilter with `ILIKE` on any query token OR matching `category`, cap at ~500 candidates, then score in Python). Route in `backend/app/api/routes/cost_items.py` (created in 19).
- Also match **assembly templates**: score the query against `AssemblyTemplate` names with the same core and return them in a separate array — suggesting a whole template ("4\" Slab on Grade" template) beats suggesting components one at a time.
- Response shape: `{ items: [{cost_item, confidence, band, factors, explanation}], templates: [...] }`.

### 3.4 Frontend

- Cost tab, condition without assembly: "Suggestions" block calling the endpoint with `q = condition.name (+ scope/category tokens)`, `unit = condition.unit`. Template suggestions render as "Create assembly from template" one-clicks (existing from-template flow); item suggestions add-as-component into a new blank assembly.
- Component editor: the 19 typeahead gains a "suggested" section at the top when the query is empty, seeded from the condition name.
- Confidence chips: High = filled, Review = outline; hover shows the explanation string. **Never auto-apply** — a suggestion below Review isn't shown at all.

## 4. Out of Scope (explicitly deferred)

- **Semantic/embedding or LLM-assisted matching** (stage 2): only worth building if measured deterministic hit-rate is insufficient. If pursued later: LLM re-rank of the top-50 deterministic candidates, or pgvector embeddings on `cost_items.name` — a separate scoped doc when the time comes.
- Matching for measurements/pages (this doc is condition-level only).
- Multilingual synonym handling (reference project needs it; a US concrete estimating tool doesn't yet).
- Learning from accept/reject history (log the decisions — see §5.5 — so the option exists later).

## 5. Acceptance Criteria

1. Golden-set test: a curated fixture of ~30 realistic condition names (from concrete scope: slabs, footings, piers, walls, curbs, rebar, formwork…) each mapped to expected top-3 CWICR items; ≥ 80% of cases rank an expected item in the top 3, and no hard unit-dimension mismatch ever appears in High band.
2. Exact-name queries return that item at confidence 1.0, first.
3. Endpoint p95 < 300 ms against the seeded 7k-row table.
4. Suggestions panel appears only for conditions without an assembly; one-click template creation works end-to-end; nothing is ever applied without a click.
5. Every rendered suggestion has a human-readable explanation derived from `factors`.
6. Suggestion accept/reject events are recorded (simple structured log or lightweight table) for future tuning — no UI for this data yet.

## 6. Testing Requirements

- Unit (`test_cost_match.py`): normalization (accents, punctuation, abbreviation map), tokenization incl. dimension tokens, each scoring factor in isolation, band edges, exact short-circuit, unit-mismatch suppression, empty/adversarial input (regex metacharacters, 1-char queries).
- Integration: endpoint with seeded fixture items — prefilter correctness, template matching, response shape.
- Frontend: suggestions render/gating, one-click add flows (RTL/Vitest per existing patterns).

## 7. Risks

- **Synonym-map coverage is the whole game** for a term-based matcher; seed it from the condition-template vocabulary already in the codebase and expand from real usage (that's what the accept/reject log is for).
- **CWICR naming style** is translated-European and verbose ("Personnel: 1 person-hour/machine-hour") — expect the golden-set exercise to force normalization rules for colons/slashes and to justify the coverage-dominant weighting.
- **Over-trust in High band:** pricing follows the suggestion; keep the "reference pricing" framing from 19 §7 in the same UI.
