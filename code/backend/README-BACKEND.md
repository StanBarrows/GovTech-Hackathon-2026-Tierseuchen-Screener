# Backend Data Pipeline

Prototype ingestion, screening, enrichment, and export pipeline for animal
disease reports. The packaged CLI is `ts-screener`; the configured sources are
`gefluegelnews` and `padi_web`.

## Setup

From the repository root:

```bash
uv sync
```

Run backend commands through `uv run ...`; the project exposes the CLI from
`govtech_tierseuchen.cli`.

## Pipeline

```text
manifest.jsonl
  -> raw_html/ or raw_json/
  -> articles.jsonl
  -> disease_articles.jsonl
  -> disease_reports.jsonl
  -> disease_reports.enriched.jsonl
  -> lindas/data/rdf/tierseuchen-screener.ttl
  -> lindas/data/csv/disease_reports.csv
  -> lindas/data/csv/disease_reports_mock_data_.csv
```

The deterministic scraper owns discovery, fetching, parsing, relevance rules,
candidate IDs, provenance, and rule evidence. Enrichment calls the configured
OpenAI-compatible chat endpoint and fills semantic fields on the same
`DiseaseReport` schema. Keep the Turtle/RDF schema stable; do not add parallel
production fields such as `llm_disease_name`, `Disease`, or nested
`consequence.*` fields.

## Commands

Run the whole configured pipeline:

```bash
uv run ts-screener run-all
```

By default, stages reuse records whose upstream inputs have not changed. The
pipeline stores this small incremental state database at
`data/unstructured/pipeline_state.sqlite`; JSONL outputs remain complete and are
merged with any newly processed records.

Limit it to selected sources:

```bash
uv run ts-screener run-all --source gefluegelnews --source padi_web
```

Run stages manually:

```bash
uv run ts-screener discover gefluegelnews
uv run ts-screener fetch gefluegelnews --limit 25 --delay-seconds 1
uv run ts-screener parse gefluegelnews
uv run ts-screener filter-disease gefluegelnews
uv run ts-screener extract-reports gefluegelnews
uv run ts-screener enrich gefluegelnews
uv run ts-screener export-final
```

Use `padi_web` in place of `gefluegelnews` for the PADI source. `run-all`
executes discovery, fetch, parse, disease filtering, report extraction,
enrichment, and final RDF/CSV export. With multiple sources, discovery and fetch
run concurrently; later stages run per source in order.

Useful options:

- `--data-dir <path>` overrides `scraper.data_dir`.
- `--limit <n>` bounds discovery, fetching, parsing, or `run-all`; use
  `--limit 0` for an explicit full historical backfill when a source has a
  default cap.
- `--force` reprocesses records even when the incremental state is current.
- `--timeout-seconds <n>` and `--delay-seconds <n>` override source defaults.
- `--rdf-output <path>` and `--csv-output <path>` override final export paths.
- `enrich --output <path> --prompt <path> --progress-every <n>` overrides
  enrichment output, prompt, and progress logging.

Defaults live in repository-root `config.yaml`. Relative paths resolve from the
repository root, not from the current shell directory.

If Gefluegelnews shows unexpectedly few disease reports while `articles.jsonl`
contains many relevant-looking articles, rebuild the deterministic relevance
outputs before changing terms:

```bash
uv run ts-screener filter-disease gefluegelnews --force
uv run ts-screener extract-reports gefluegelnews --force
```

The incremental state can mark all articles current even when
`disease_articles.jsonl` or `disease_reports.jsonl` is stale from an earlier
partial run. Single weak terms such as `Biosicherheit`, `Tierseuche`,
`Ausbruch`, and `Keulung` can also create false positives; treat them as context
signals unless paired with a disease anchor.

## Sources

- `gefluegelnews`: discovers article URLs from the configured sitemap, caches
  article HTML under `raw_html/`, and parses article metadata/full text. The
  default run is capped in `config.yaml` to avoid refetching the full historical
  sitemap during normal `run-all`; pass `--limit 0` or a larger explicit limit
  when a backfill is intentional.
- `padi_web`: discovers recent relevant articles from the public PADI API,
  caches detail payloads under `raw_json/`, and parses sentence payloads into
  Markdown `fulltext`.

Both sources store the cached artifact path in the shared `raw_html_path` field
for the current `NewsArticle` and `DiseaseReport` schema, even when the artifact
is JSON.

## Outputs

Per-source files live under `data/unstructured/<source>/` by default:

- `manifest.jsonl`: discovered article metadata, then fetch metadata/errors
- `raw_html/` or `raw_json/`: cached source artifacts
- `articles.jsonl`: normalized parsed articles with Markdown `fulltext`
- `parse_errors.jsonl`: parse failures that did not stop the batch
- `disease_articles.jsonl`: inspectable disease-relevance hits and snippets
- `disease_reports.jsonl`: deterministic `DiseaseReport` candidates
- `disease_reports.enriched.jsonl`: candidates plus semantic fields

Final combined outputs:

- `lindas/data/rdf/tierseuchen-screener.ttl`
- `lindas/data/csv/disease_reports.csv` with the backend `DiseaseReport` fields
- `lindas/data/csv/disease_reports_mock_data_.csv` with the frontend `reports`
  table schema

`extract-reports` reads `articles.jsonl` and re-runs the relevance rules; it
does not consume `disease_articles.jsonl`. `export-final` reads enriched JSONL
from the selected sources and writes one combined Turtle file plus both combined
CSV files.

## Field Contract

Scraper-owned fields are deterministic and must be preserved by enrichment:

- Provenance: `source_id`, `source_name`, `source_link`,
  `source_document_id`, `source_document_title`, `source_publication_date`,
  `source_retrieved_at`, `raw_html_path`, `content_hash`, `fulltext`
- Candidate metadata: `report_id`, `extraction_method`,
  `extraction_version`, `extraction_status`, `extraction_confidence`
- Rule evidence: `evidence_snippets`, `raw_relevance_evidence`,
  `rule_relevance_score`, `rule_matched_terms`, `rule_disease_type`,
  `rule_control_measures`, `situation_month`

Enrichment may update only semantic `DiseaseReport` fields, including disease,
geography, situation key, species, counts, dates, status, diagnostics,
relevance/severity/reach assessments, consequences, control measures,
prevention measures, and research references. Unsupported fields should remain
`null` or empty lists.

## Enrichment

Configure live enrichment with the OpenRouter API key in `code/backend/.env`:

```bash
OPENROUTER_API_KEY="..."
```

`ts-screener enrich` sends candidate context, evidence snippets, rule hints, and
`fulltext` through the OpenAI SDK against OpenRouter's OpenAI-compatible
endpoint. Set `TS_SCREENER_LLM_BASE_URL` only when overriding the default
`https://openrouter.ai/api/v1` endpoint. LLM calls run in parallel using
`interpreter.workers` from `config.yaml` (default: `20`). It records per-record
extraction failures in `_error` and continues the batch. The legacy
`code/backend/interpreter/interpreter.py` script is a wrapper around the
packaged enrichment module.

## Verify

```bash
uv run ruff check code/backend/scraper tests
uv run pytest tests/test_gefluegelnews.py tests/test_padi_web.py tests/test_disease_pipeline.py tests/test_rdf_export.py tests/test_csv_export.py tests/test_enrichment.py -v
```
