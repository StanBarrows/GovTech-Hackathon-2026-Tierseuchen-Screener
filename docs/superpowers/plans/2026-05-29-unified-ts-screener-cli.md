# Unified TS-Screener CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the separate scraper CLI and interpreter script flow with one `ts-screener` command that can run individual stages, standalone enrichment, and the complete pipeline with final RDF and CSV exports.

**Architecture:** Keep the existing scraper package as the packaged backend entry point. Move interpreter behavior into importable package code with injectable model calls. Export final enriched records through shared RDF and CSV helpers instead of writing intermediate QA Turtle during `run-all`.

**Tech Stack:** Python 3.13, `argparse`, `uv`, `pytest`, `ruff`, existing `rdflib`, existing JSONL helpers, optional OpenAI-compatible client loaded only inside live enrichment.

---

### Task 1: Rename CLI and Extend Parser

**Files:**
- Modify: `pyproject.toml`
- Modify: `code/backend/scraper/govtech_tierseuchen/cli.py`
- Modify: `tests/test_gefluegelnews.py`

- [ ] **Step 1: Write failing parser/package tests**

Add expectations that `build_parser().prog == "ts-screener"`, the console script key is `ts-screener`, `ts` is absent, and parser accepts `enrich` plus `export-final`.

- [ ] **Step 2: Run focused tests**

Run: `uv run pytest tests/test_gefluegelnews.py -v`

Expected before implementation: failures showing the old `ts` program name and missing commands.

- [ ] **Step 3: Implement parser rename and command scaffolding**

Change `[project.scripts]` to `ts-screener = "govtech_tierseuchen.cli:main"`, set parser `prog="ts-screener"`, add `enrich` and `export-final` parsers, and route them to placeholder helpers that will be completed in later tasks.

- [ ] **Step 4: Verify focused tests**

Run: `uv run pytest tests/test_gefluegelnews.py -v`

Expected after implementation: parser/package tests pass.

### Task 2: Add Importable Enrichment

**Files:**
- Create: `code/backend/scraper/govtech_tierseuchen/enrichment.py`
- Modify: `code/backend/interpreter/interpreter.py`
- Create: `tests/test_enrichment.py`

- [ ] **Step 1: Write failing enrichment tests**

Cover allowed semantic field merging, scraper-owned field preservation, unexpected model keys being dropped, per-record error preservation, and `enrich_source` writing `disease_reports.enriched.jsonl` using a fake extractor.

- [ ] **Step 2: Run focused tests**

Run: `uv run pytest tests/test_enrichment.py -v`

Expected before implementation: import or function-not-found failures.

- [ ] **Step 3: Implement importable enrichment module**

Add pure helpers for reading candidate records, building prompt text, merging allowed fields, extracting records with an injected callable, and writing enriched JSONL. Keep live OpenAI-compatible client setup inside a function called only by CLI execution.

- [ ] **Step 4: Update old interpreter script as wrapper**

Keep `code/backend/interpreter/interpreter.py` usable by delegating to the packaged enrichment command behavior, without reading credentials at import time.

- [ ] **Step 5: Verify focused tests**

Run: `uv run pytest tests/test_enrichment.py -v`

Expected after implementation: enrichment tests pass without live network calls.

### Task 3: Add Final RDF and CSV Exports

**Files:**
- Create: `code/backend/scraper/govtech_tierseuchen/csv_export.py`
- Modify: `code/backend/scraper/govtech_tierseuchen/rdf_export.py`
- Modify: `code/backend/scraper/govtech_tierseuchen/cli.py`
- Modify: `config.yaml`
- Modify: `tests/test_rdf_export.py`
- Create: `tests/test_csv_export.py`

- [ ] **Step 1: Write failing export tests**

Cover final combined RDF output path, combined CSV rows for multiple sources, stable CSV columns, and no `.qa.ttl` output in `run-all`.

- [ ] **Step 2: Run focused tests**

Run: `uv run pytest tests/test_rdf_export.py tests/test_csv_export.py -v`

Expected before implementation: missing CSV exporter and old QA path failures.

- [ ] **Step 3: Implement final exports**

Add `export_final` orchestration that reads selected sources' enriched records, writes `lindas/data/rdf/tierseuchen-screener.ttl`, and writes `lindas/data/csv/disease_reports.csv`. If no enriched records exist for the selected sources, return a non-zero exit code.

- [ ] **Step 4: Verify focused tests**

Run: `uv run pytest tests/test_rdf_export.py tests/test_csv_export.py -v`

Expected after implementation: export tests pass.

### Task 4: Wire Run-All

**Files:**
- Modify: `code/backend/scraper/govtech_tierseuchen/cli.py`
- Modify: `tests/test_gefluegelnews.py`

- [ ] **Step 1: Write failing orchestration test**

Update `run-all` expectations so selected sources run deterministic stages, then `enrich`, then one final export.

- [ ] **Step 2: Run focused tests**

Run: `uv run pytest tests/test_gefluegelnews.py -v`

Expected before implementation: old `export-rdf` stage appears or enrichment is missing.

- [ ] **Step 3: Implement orchestration**

Remove normal `export-rdf` from `PIPELINE_STAGES`, add enrichment and final export to `run-all`, keep `enrich <source>` callable independently, and keep deterministic stages individually callable.

- [ ] **Step 4: Verify focused tests**

Run: `uv run pytest tests/test_gefluegelnews.py -v`

Expected after implementation: orchestration tests pass.

### Task 5: Update Documentation and Verify

**Files:**
- Modify: `README.md`
- Modify: `code/backend/README-BACKEND.md`
- Modify: docs/tests that reference `uv run ts`

- [ ] **Step 1: Update docs**

Replace operator examples with `uv run ts-screener`, document `enrich`, document `run-all` as end-to-end, and document the final combined TTL/CSV outputs.

- [ ] **Step 2: Run docs search**

Run: `rg -n "uv run ts|prog=\"ts\"|\\.qa\\.ttl|export-rdf" README.md code/backend docs tests pyproject.toml`

Expected: no stale operator instructions for the old command or normal QA export, except historical design/plan docs where relevant.

- [ ] **Step 3: Run full backend verification**

Run: `uv run ruff format .`

Run: `uv run ruff check code/backend/scraper tests`

Run: `uv run pytest -v`

Expected: formatter clean, lint clean, tests pass.
