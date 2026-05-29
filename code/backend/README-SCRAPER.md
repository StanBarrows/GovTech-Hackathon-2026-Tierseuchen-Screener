# Backend Scraper

Prototype news-ingestion pipeline for animal disease screening. The current
source adapters are `gefluegelnews` and `padi_web`.

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

Run scraper commands with `uv run ts ...`. `uv run` uses the managed project
environment, so the `ts` CLI does not need to be installed globally.

## Run

```bash
uv run ts discover gefluegelnews
uv run ts fetch gefluegelnews --limit 25 --delay-seconds 1
uv run ts parse gefluegelnews
uv run ts filter-disease gefluegelnews
uv run ts extract-reports gefluegelnews
uv run ts export-rdf gefluegelnews
```

```bash
uv run ts discover padi_web
uv run ts fetch padi_web --limit 100 --delay-seconds 0.5
uv run ts parse padi_web
uv run ts filter-disease padi_web
uv run ts extract-reports padi_web
uv run ts export-rdf padi_web
```

Use `--data-dir <path>` to override the default `data/unstructured`.
Use `ts fetch --limit <n>` to fetch only the first `n` manifest entries.
`ts fetch` shows a progress bar while downloading articles.
Use `--rdf-dir <path>` with `ts export-rdf` to override the default
`lindas/data/rdf` output root.

Defaults live in `config.yaml` at the repository root. Relative paths in that
file resolve from the repository root, so the default output directory is always
`data/unstructured` and the default RDF output directory is always
`lindas/data/rdf`, even when `ts` is run from a subdirectory.

## Outputs

Generated files live under `data/unstructured/<source>/`:

- `manifest.jsonl`: discovered and fetched article metadata
- `raw_html/`: cached article HTML for Gefluegelnews
- `raw_json/`: cached API detail payloads for PADI-web
- `articles.jsonl`: parsed articles with Markdown `fulltext`
- `parse_errors.jsonl`: parser failures that did not stop the batch
- `disease_articles.jsonl`: disease-relevant articles with evidence
- `disease_reports.jsonl`: candidate `DiseaseReport` records

### Artifact Flow

`articles.jsonl` is the parsed article layer: `ts parse` reads fetched metadata
and cached source content, then writes normalized article records with fields
such as title, publication date, metadata, and Markdown `fulltext`.

`disease_articles.jsonl` is the relevance-inspection layer: `ts filter-disease`
reads `articles.jsonl`, keeps only articles that match disease terms, and stores
each article together with matched terms, score, and evidence snippets.

`disease_reports.jsonl` is the structured candidate layer: `ts extract-reports`
reads `articles.jsonl`, re-runs the same relevance filter, and turns relevant
articles into candidate `DiseaseReport` records for RDF export. It does not
currently read `disease_articles.jsonl`; that file is an inspectable side
artifact for checking why articles were considered relevant.

PADI-web additionally caches API detail payloads under `raw_json/`. These local
scraper artifacts are ignored by git.

Finalized RDF export files are written under `lindas/data/rdf/<source>/`, for
example `lindas/data/rdf/padi_web/padi_web.ttl`:

- `<source>.ttl`: LiNDAS-ready Turtle for news documents, extraction
  candidates, evidence snippets, outbreak situations, assessments, consequences,
  prevention measures, and research references

## Verify

```bash
uv run pytest tests/test_gefluegelnews.py tests/test_disease_pipeline.py tests/test_rdf_export.py -v
uv run ruff check code/backend/scraper tests
```
