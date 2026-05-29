# Backend Data Pipeline

Prototype news-ingestion and enrichment pipeline for animal disease screening.
The current source adapters are `gefluegelnews` and `padi_web`.

## Install `uv`

The scraper CLI is run through [`uv`](https://docs.astral.sh/uv/), which manages
the Python environment and installed project dependencies.

Install `uv` once on your machine:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then open a new shell or follow the installer instructions to add `uv` to your
`PATH`. From the repository root, install the dependencies declared by the
project:

```bash
uv sync
```

Run commands with `uv run ...`. `uv run` uses the managed project environment,
so the `ts-screener` CLI does not need to be installed globally.

## Pipeline Overview

The backend has two layers with separate responsibilities:

1. Deterministic scraper stages: ingestion, parsing, candidate selection,
   provenance, stable IDs, and rule evidence.
2. `ts-screener enrich`: LLM-based semantic enrichment of existing
   `DiseaseReport` fields, using candidate records as input.

The intended data flow is:

```text
manifest.jsonl
  -> raw_html/ or raw_json/
  -> articles.jsonl
  -> disease_articles.jsonl
  -> disease_reports.jsonl          # candidate/provenance layer
  -> disease_reports.enriched.jsonl # interpreter semantic layer
  -> lindas/data/rdf/tierseuchen-screener.ttl
  -> lindas/data/csv/disease_reports.csv
```

Keep the Turtle/RDF schema stable for now. The interpreter should fill existing
`DiseaseReport` fields instead of creating parallel fields that later need to be
merged or removed.

## Run Pipeline

Run the full pipeline for all configured sources:

```bash
uv run ts-screener run-all
```

Select one or more sources with repeatable `--source` options:

```bash
uv run ts-screener run-all --source gefluegelnews --source padi_web
```

`run-all` executes discovery, fetching, parsing, disease filtering, report
extraction, LLM enrichment, final RDF export, and final CSV export in order. It
prints the current source and stage before each step. When multiple sources are
selected, discovery runs for those sources concurrently, then fetching runs
concurrently; the later transformation stages stay ordered per source. `fetch`
still shows its article download progress bar.

```bash
uv run ts-screener discover gefluegelnews
uv run ts-screener fetch gefluegelnews --limit 25 --delay-seconds 1
uv run ts-screener parse gefluegelnews
uv run ts-screener filter-disease gefluegelnews
uv run ts-screener extract-reports gefluegelnews
uv run ts-screener enrich gefluegelnews
```

```bash
uv run ts-screener discover padi_web
uv run ts-screener fetch padi_web --limit 100 --delay-seconds 0.5
uv run ts-screener parse padi_web
uv run ts-screener filter-disease padi_web
uv run ts-screener extract-reports padi_web
uv run ts-screener enrich padi_web
```

Use `--data-dir <path>` to override the default `data/unstructured`.
Use `ts-screener fetch --limit <n>` to fetch only the first `n` manifest
entries. `ts-screener fetch` shows a progress bar while downloading articles.
Use `--rdf-output <path>` and `--csv-output <path>` with `run-all` or
`export-final` to override the final output files.

Defaults live in `config.yaml` at the repository root. Relative paths in that
file resolve from the repository root, so the default output directory is always
`data/unstructured`, the default final RDF file is
`lindas/data/rdf/tierseuchen-screener.ttl`, and the default final CSV file is
`lindas/data/csv/disease_reports.csv`, even when `ts-screener` is run from a
subdirectory.

Operator-tunable scraper settings belong in `config.yaml`: source base URLs,
source article/API paths, user agents, timeouts, delays, limits, discovery
query parameters, output filenames, disease filter terms, snippet limits, and
report confidence thresholds. Keep parser mechanics, schema/RDF namespaces,
HTML selectors, and stable ID/hash formatting in code.

## Run Enrichment

`ts-screener enrich` reads JSONL candidate records with `fulltext`, calls the
configured OpenAI-compatible LLM endpoint, and writes JSONL records with the
original candidate fields preserved plus semantic fields filled in.

Configure live enrichment with environment variables. The names are configured
in `config.yaml` and default to:

```bash
export TS_SCREENER_LLM_BASE_URL="https://example-llm-endpoint/v1"
export TS_SCREENER_LLM_API_KEY="..."
```

Run enrichment independently when needed:

```bash
uv run ts-screener enrich gefluegelnews
```

The legacy script at `code/backend/interpreter/interpreter.py` is now a thin
wrapper around the packaged enrichment code.

## Outputs

Generated files live under `data/unstructured/<source>/`:

- `manifest.jsonl`: discovered and fetched article metadata
- `raw_html/`: cached article HTML for Gefluegelnews
- `raw_json/`: cached API detail payloads for PADI-web
- `articles.jsonl`: parsed articles with Markdown `fulltext`
- `parse_errors.jsonl`: parser failures that did not stop the batch
- `disease_articles.jsonl`: disease-relevant articles with evidence
- `disease_reports.jsonl`: candidate `DiseaseReport` records
- `disease_reports.enriched.jsonl`: LLM-enriched `DiseaseReport` records

Final combined outputs:

- `lindas/data/rdf/tierseuchen-screener.ttl`
- `lindas/data/csv/disease_reports.csv`

### Artifact Flow

`articles.jsonl` is the parsed article layer: `ts-screener parse` reads fetched
metadata and cached source content, then writes normalized article records with
fields such as title, publication date, metadata, and Markdown `fulltext`.

`disease_articles.jsonl` is the relevance-inspection layer:
`ts-screener filter-disease` reads `articles.jsonl`, keeps only articles that
match disease terms, and stores each article together with matched terms, score,
and evidence snippets.

`disease_reports.jsonl` is the candidate layer:
`ts-screener extract-reports` reads `articles.jsonl`, re-runs the same relevance
filter, and turns relevant articles into stable `DiseaseReport` candidates.
This layer intentionally keeps source provenance, stable IDs,
publication/retrieval dates, full text, evidence snippets, filter score/terms,
exact rule hits such as H5N1 subtype mentions, and coarse rule control-measure
hints. Semantic enrichment fields such as final disease/country resolution,
consequence interpretation, prevention classification, severity, and reach are
left empty for the enrichment layer. `ts-screener extract-reports` does not
currently read `disease_articles.jsonl`; that file is an inspectable side
artifact for checking why articles were considered relevant.

PADI-web additionally caches API detail payloads under `raw_json/`. These local
scraper artifacts are ignored by git.

### Contract

`ts-screener extract-reports` owns fields that are deterministic and auditable:

- Source/provenance: `source_id`, `source_name`, `source_link`,
  `source_document_id`, `source_document_title`, `source_publication_date`,
  `source_retrieved_at`, `raw_html_path`, `content_hash`, `fulltext`
- Stable candidate metadata: `report_id`, `extraction_method`,
  `extraction_version`, `extraction_status`, `extraction_confidence`,
  `situation_month`
- Rule evidence: `evidence_snippets`, `raw_relevance_evidence`,
  `rule_relevance_score`, `rule_matched_terms`, `rule_disease_type`,
  `rule_control_measures`

The interpreter owns semantic fields that require reading comprehension:

- Disease and geography: `disease_name`, `disease_type`,
  `country_or_territory`, `is_in_europe`, admin/location fields
- Event facts when explicitly stated: `species`, `cases`, `dead`, `killed`,
  `slaughtered`, `vaccinated`, dates, status, diagnostics, etc.
- Assessments and impacts: `relevance_level`, `relevance_rationale`,
  `severity_level`, `severity_rationale`, `reach_level`, `reach_rationale`,
  `has_consequences`, `consequences`, `control_measures`,
  `prevention_measures`, `research_references`

The interpreter must preserve scraper-owned fields unchanged and must not write
parallel output fields such as `Disease`, `DiseaseSubtype`, `InEurope`,
`llm_disease_name`, or nested `consequence.*` fields in production JSONL. If a
field is not explicitly supported by the text, write `null` or an empty list as
appropriate.

`ts-screener export-final` reads selected sources'
`disease_reports.enriched.jsonl` files and writes one combined Turtle file plus
one combined CSV file. The normal pipeline does not write intermediate
per-source QA Turtle files.

## Verify

```bash
uv run pytest tests/test_gefluegelnews.py tests/test_disease_pipeline.py tests/test_rdf_export.py tests/test_csv_export.py tests/test_enrichment.py -v
uv run ruff check code/backend/scraper tests
```
