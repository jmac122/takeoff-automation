# 22 — Crash-Isolated PDF Parsing

> **Status:** Scoping / dev handoff
> **Priority:** MEDIUM — robustness/hardening; becomes HIGH before any multi-user or hosted deployment
> **Effort estimate:** 2–3 days
> **Depends on:** Nothing. 20 (vector extraction) and 21 (pdf-text capture) should run inside this once available.
> **Design reference (no code ported):** OpenConstructionERP `backend/app/modules/takeoff/pdf_extract_worker.py` — reference for the failure analysis and process contract only

---

## 1. Problem Statement

All PDF/TIFF parsing runs **in-process** today: `backend/app/utils/pdf_utils.py` imports `fitz` (PyMuPDF) directly and is called from `DocumentProcessor.process_document()` inside Celery workers (`workers/document_tasks.py`). Celery is configured with `task_time_limit=3600`, `task_soft_time_limit=3000`, `worker_prefetch_multiplier=1`, concurrency 2 — but **no memory cap of any kind**.

Failure modes this leaves open (the reference project hit exactly these in production):

- A **vector-dense CAD sheet** drives PyMuPDF/pdf2image memory past available RAM → the kernel OOM-killer SIGKILLs the worker child mid-task with **no traceback**. The task dies silently (TaskTracker record stuck in STARTED), and under memory pressure the OOM-killer may take unrelated processes (API, Redis) instead.
- A **malformed/hostile PDF** segfaults the native MuPDF C layer → same silent-death class. Uploads are user-controlled input feeding a native-code parser; this is also a hardening concern, not just a reliability one.
- A pathological parse **hangs** until the 1-hour hard limit, occupying one of only two worker slots.

## 2. Feature Overview

Move every PDF-parsing operation into a **short-lived, resource-capped child process** with a strict JSON contract, so the worst any document can do is kill its own child, which the caller observes as a clean, reportable failure:

```
Celery worker ──spawn──▶ python -m app.utils.pdf_worker <op> <args>
                          │  self-caps RLIMIT_AS (POSIX)
                          │  wall-clock timeout enforced by parent
                          ▼
              stdout: one JSON object (or exit≠0 + stderr reason)
```

Parent behavior on child failure: mark the document/page/task FAILED with a specific, user-visible reason ("This PDF could not be parsed safely — page 12 exceeded memory limits"), release the worker slot, keep serving.

## 3. Detailed Requirements

### 3.1 Child module — `backend/app/utils/pdf_worker.py`

- Runnable as `python -m app.utils.pdf_worker <operation> <input_path> [options-json]`. Imports **stdlib + parsers only** (fitz/PIL lazily inside the op) — no DB, no app settings, no web stack, so it starts fast and can't hold DB connections hostage.
- Operations (mirroring today's `pdf_utils.py` public functions and the new 20/21 needs):
  - `page-count` (PDF and TIFF)
  - `render-pages` — rasterize page range to PNGs at the 1568px convention, writing to a supplied temp dir (images don't cross the pipe; only their paths do)
  - `extract-text` — native text layer per page (feeds 21)
  - `vector-stats` / `vector-drawings` — path/text counts and raw primitives (feeds 20)
  - `validate` — structural validation
- Self-limits at startup: `resource.setrlimit(RLIMIT_AS, cap)` on POSIX (containers are Linux; guard the import for dev-on-Windows). Cap configurable, default ~2 GB.
- Output contract: single JSON object on stdout; hard failure → short reason on stderr + non-zero exit. An unreadable-but-not-crashing PDF exits 0 with an explicit `{"ok": false, "reason": ...}` so "corrupt file" and "parser crashed" are distinguishable.

### 3.2 Parent wrapper — same file or `pdf_utils.py`

- `run_pdf_worker(op, path, *, timeout, mem_cap) -> WorkerResult` using `subprocess.run` with `timeout=`; on `TimeoutExpired` kill the process group. Translate the three outcomes (ok / parse-failure / crash) into typed results.
- Refactor existing `pdf_utils.py` callers (`DocumentProcessor.validate_file`, `get_page_count`, `process_document` page rendering) to go through the wrapper. Keep the current in-process functions available behind a config flag `PDF_ISOLATED_PARSING` (default true) for debugging.
- Settings: `PDF_WORKER_MEM_CAP_MB` (2048), `PDF_WORKER_TIMEOUT_S` (per-op defaults: validate 30s, page-count 30s, render 120s/batch, text 60s, vector 120s).

### 3.3 Celery-level backstop

Independent of the child-process work, set `worker_max_memory_per_child` (e.g. 1.5 GB) in `workers/celery_app.py` so a slow leak in any task recycles the worker child after task completion rather than growing forever. This is a two-line config change; do it first.

### 3.4 Failure surfacing

- Document processing already tracks per-document status; ensure a child failure sets FAILED with the reason string, TaskTracker records the error (existing `error_message` field), and the frontend's document status view shows it (existing failure UI — verify copy).
- Structured logging: op, duration, peak-exit status, reason — enough to spot which uploads stress the caps.

## 4. Out of Scope

- Sandboxing beyond rlimits (seccomp, separate container) — not warranted at current threat model; revisit if hosting publicly.
- TIFF processing via PIL is a lower-risk surface (pure-Python + libtiff) — include in the worker for uniformity (`page-count`, `render`) but don't block the feature on it.
- Windows support for RLIMIT (dev machines) — the flag falls back to timeout-only isolation there.

## 5. Acceptance Criteria

1. A crafted "PDF bomb" fixture (huge page dimensions / decompression bomb) fails cleanly: document status FAILED with a memory-cap reason, worker process alive, subsequent uploads process normally — demonstrated in an integration test.
2. A truncated/garbage PDF yields the "could not parse" outcome (not a crash outcome) and the upload UI shows the failure state.
3. A hang simulation (child that sleeps past timeout — test-only op or monkeypatched) is killed at the timeout, task FAILED, slot released.
4. Normal-path regression: full existing document ingestion test suite passes with `PDF_ISOLATED_PARSING=true`; per-document processing time increase is negligible (child startup is amortized by batching page renders).
5. `worker_max_memory_per_child` is active and visible in worker boot logs.

## 6. Testing Requirements

- Unit: contract tests invoking the child module in-process via its `main()` with fixture files — JSON shape per op, exit codes, the ok/parse-failure/crash distinction.
- Unit: parent wrapper outcome translation incl. timeout kill (fake child script).
- Integration: end-to-end ingestion with isolation on; bomb + garbage fixtures checked into `backend/tests/fixtures/` (generate the bomb programmatically in-test to keep the repo clean if preferred).

## 7. Risks

- **Throughput:** one child per op adds ~100–300 ms spawn overhead; batch page renders per call (already the natural shape of `process_document`) so overhead is per-document, not per-page.
- **Temp-dir hygiene:** rendered PNGs pass via temp paths; ensure cleanup in `finally` and on crash (parent owns the temp dir lifetime).
- **RLIMIT_AS vs PyMuPDF mmap behavior:** address-space caps can trip on legitimate large-but-fine documents; the cap is configurable per deployment, and the failure reason tells the operator which knob to turn.
