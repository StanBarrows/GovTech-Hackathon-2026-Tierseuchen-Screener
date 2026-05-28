# Backend Scraper

Prototype news-ingestion pipeline for animal disease screening. The current
source adapter is `gefluegelnews`.

## Run

```bash
uv run ts discover gefluegelnews
uv run ts fetch gefluegelnews --limit 25 --delay-seconds 1
uv run ts parse gefluegelnews
uv run ts filter-disease gefluegelnews
uv run ts extract-reports gefluegelnews
```

Use `--data-dir <path>` to override the default `data/unstructured`.
Use `ts fetch --limit <n>` to fetch only the first `n` manifest entries.
`ts fetch` shows a progress bar while downloading articles.

Defaults live in `config.yaml` at the repository root. Relative paths in that
file resolve from the repository root, so the default output directory is always
`data/unstructured` even when `ts` is run from a subdirectory.

## Outputs

Generated files live under `data/unstructured/gefluegelnews/`:

- `manifest.jsonl`: discovered and fetched article metadata
- `raw_html/`: cached article HTML
- `articles.jsonl`: parsed articles with Markdown `fulltext`
- `parse_errors.jsonl`: parser failures that did not stop the batch
- `disease_articles.jsonl`: disease-relevant articles with evidence
- `disease_reports.jsonl`: candidate `DiseaseReport` records

These local artifacts are ignored by git.

## Verify

```bash
uv run pytest tests/test_gefluegelnews.py tests/test_disease_pipeline.py -v
uv run ruff check code/backend/scraper tests
```
