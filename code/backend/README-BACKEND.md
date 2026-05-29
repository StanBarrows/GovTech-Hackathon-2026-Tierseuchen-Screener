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
so the `ts` CLI does not need to be installed globally.

## Pipeline Overview

The backend has two layers with separate responsibilities:

1. Scraper / `ts` CLI: deterministic ingestion, parsing, candidate selection,
   provenance, stable IDs, and rule evidence.
2. Interpreter: LLM-based semantic enrichment of existing `DiseaseReport`
   fields, using candidate records as input.

The intended data flow is:

```text
manifest.jsonl
  -> raw_html/ or raw_json/
  -> articles.jsonl
  -> disease_articles.jsonl
  -> disease_reports.jsonl          # candidate/provenance layer
  -> disease_reports.enriched.jsonl # interpreter semantic layer
  -> disease_reports.jsonl          # promoted enriched records for RDF export
  -> lindas/data/rdf/<source>/<source>.ttl
```

Keep the Turtle/RDF schema stable for now. The interpreter should fill existing
`DiseaseReport` fields instead of creating parallel fields that later need to be
merged or removed.

## Run Scraper

Run the full deterministic scraper pipeline for all configured sources:

```bash
uv run ts run-all
```

Select one or more sources with repeatable `--source` options:

```bash
uv run ts run-all --source gefluegelnews --source padi_web
```

`run-all` executes discovery, fetching, parsing, disease filtering, report
extraction, and QA RDF export in order. It prints the current source and stage
before each step. When multiple sources are selected, discovery runs for those
sources concurrently, then fetching runs concurrently; the later local
transformation stages stay ordered per source. `fetch` still shows its article
download progress bar.

```bash
uv run ts discover gefluegelnews
uv run ts fetch gefluegelnews --limit 25 --delay-seconds 1
uv run ts parse gefluegelnews
uv run ts filter-disease gefluegelnews
uv run ts extract-reports gefluegelnews
```

```bash
uv run ts discover padi_web
uv run ts fetch padi_web --limit 100 --delay-seconds 0.5
uv run ts parse padi_web
uv run ts filter-disease padi_web
uv run ts extract-reports padi_web
```

Use `--data-dir <path>` to override the default `data/unstructured`.
Use `ts fetch --limit <n>` to fetch only the first `n` manifest entries.
`ts fetch` shows a progress bar while downloading articles.
Use `--rdf-dir <path>` with `ts export-rdf` to override the default
`lindas/data/rdf` output root. The `ts export-rdf` command writes
`<source>.qa.ttl` for scraper QA only; the production RDF export is expected to
come from the interpreter-enriched records.

Defaults live in `config.yaml` at the repository root. Relative paths in that
file resolve from the repository root, so the default output directory is always
`data/unstructured` and the default RDF output directory is always
`lindas/data/rdf`, even when `ts` is run from a subdirectory.

Operator-tunable scraper settings belong in `config.yaml`: source base URLs,
source article/API paths, user agents, timeouts, delays, limits, discovery
query parameters, output filenames, disease filter terms, snippet limits, and
report confidence thresholds. Keep parser mechanics, schema/RDF namespaces,
HTML selectors, and stable ID/hash formatting in code.

## Run Interpreter

The interpreter lives in `code/backend/interpreter`. It reads JSONL candidate
records with `fulltext`, calls the configured LLM, and writes JSONL records with
the original candidate fields preserved plus semantic fields filled in.

Run it from the interpreter directory so its local credential/config files are
found:

```bash
cd code/backend/interpreter
uv run python interpreter.py \
  -s SystemPrompt.md \
  -e disease \
  -i ../../../data/unstructured/gefluegelnews/disease_reports.jsonl \
  -o ../../../data/unstructured/gefluegelnews/disease_reports.enriched.jsonl \
  --progress-every 10
```

After QA, return to the repository root and promote the enriched file for RDF
export:

```bash
cd ../../..
cp data/unstructured/gefluegelnews/disease_reports.jsonl \
  data/unstructured/gefluegelnews/disease_reports.candidate.jsonl
cp data/unstructured/gefluegelnews/disease_reports.enriched.jsonl \
  data/unstructured/gefluegelnews/disease_reports.jsonl
uv run ts export-rdf gefluegelnews
```

Do the same for `padi_web` by replacing the source folder and command argument.

## Outputs

Generated files live under `data/unstructured/<source>/`:

- `manifest.jsonl`: discovered and fetched article metadata
- `raw_html/`: cached article HTML for Gefluegelnews
- `raw_json/`: cached API detail payloads for PADI-web
- `articles.jsonl`: parsed articles with Markdown `fulltext`
- `parse_errors.jsonl`: parser failures that did not stop the batch
- `disease_articles.jsonl`: disease-relevant articles with evidence
- `disease_reports.jsonl`: candidate `DiseaseReport` records
- `disease_reports.enriched.jsonl`: interpreter-enriched `DiseaseReport`
  records for QA before promotion
- `disease_reports.candidate.jsonl`: optional backup of the pre-enrichment
  candidate records

### Artifact Flow

`articles.jsonl` is the parsed article layer: `ts parse` reads fetched metadata
and cached source content, then writes normalized article records with fields
such as title, publication date, metadata, and Markdown `fulltext`.

`disease_articles.jsonl` is the relevance-inspection layer: `ts filter-disease`
reads `articles.jsonl`, keeps only articles that match disease terms, and stores
each article together with matched terms, score, and evidence snippets.

`disease_reports.jsonl` is the candidate layer: `ts extract-reports` reads
`articles.jsonl`, re-runs the same relevance filter, and turns relevant articles
into stable `DiseaseReport` candidates. This layer intentionally keeps source
provenance, stable IDs, publication/retrieval dates, full text, evidence
snippets, filter score/terms, exact rule hits such as H5N1 subtype mentions, and
coarse rule control-measure hints. Semantic enrichment fields such as final
disease/country resolution, consequence interpretation, prevention
classification, severity, and reach are left empty for the interpreter/enrichment
layer. `ts extract-reports` does not currently read `disease_articles.jsonl`;
that file is an inspectable side artifact for checking why articles were
considered relevant.

PADI-web additionally caches API detail payloads under `raw_json/`. These local
scraper artifacts are ignored by git.

### Contract

`ts extract-reports` owns fields that are deterministic and auditable:

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

Scraper QA RDF export files are written under `lindas/data/rdf/<source>/`, for
example `lindas/data/rdf/padi_web/padi_web.qa.ttl`:

- `<source>.qa.ttl`: QA Turtle for news documents, extraction
  candidates, evidence snippets, and any enriched outbreak situations,
  assessments, consequences, prevention measures, or research references present
  in the input records

The final LiNDAS-ready `<source>.ttl` export is owned by the interpreter flow,
after semantic enrichment has been reviewed and promoted.

## Verify

```bash
uv run pytest tests/test_gefluegelnews.py tests/test_disease_pipeline.py tests/test_rdf_export.py -v
uv run ruff check code/backend/scraper tests
```
