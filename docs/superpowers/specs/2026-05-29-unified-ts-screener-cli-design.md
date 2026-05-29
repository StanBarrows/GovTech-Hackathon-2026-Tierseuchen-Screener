# Unified TS-Screener CLI Design

## Goal

Replace the separate scraper `ts` CLI and script-style LLM interpreter with one backend command named `ts-screener`. The unified CLI should support individual pipeline stages, a standalone enrichment step, and an end-to-end `run-all` command that produces the final RDF and CSV outputs.

## Decisions

- `ts-screener` replaces `ts`; no backward-compatible `ts` alias is needed.
- `ts-screener enrich` remains available as a standalone LLM enrichment step.
- `ts-screener run-all` runs deterministic ingestion, rule extraction, LLM enrichment, final RDF export, and final CSV export.
- The normal pipeline no longer writes intermediate QA Turtle files.
- Final RDF export is one combined Turtle file for all selected sources.
- Final CSV export is one combined CSV file for all selected sources.
- Documentation must be updated to show `uv run ts-screener ...`.

## Command Shape

The CLI keeps the current deterministic stages:

- `ts-screener discover <source>`
- `ts-screener fetch <source>`
- `ts-screener parse <source>`
- `ts-screener filter-disease <source>`
- `ts-screener extract-reports <source>`

The CLI adds LLM enrichment and final exports:

- `ts-screener enrich <source>`
- `ts-screener export-final --source <source> ...`

`ts-screener run-all` runs:

```text
discover -> fetch -> parse -> filter-disease -> extract-reports
-> enrich -> export-final
```

`run-all --source` stays repeatable. If no source is provided, all configured sources run.

## Architecture

The scraper package remains the importable backend package and owns the console script entry point. The interpreter code should become importable package code instead of a script that reads credentials at import time. That allows tests to import enrichment helpers without live model calls or local credential files.

The deterministic scraper stages keep their current responsibilities: discovery, fetching, parsing, rule-based filtering, rule-based `DiseaseReport` candidate extraction, provenance, stable IDs, and evidence fields.

The enrichment stage reads candidate `disease_reports.jsonl`, calls the configured OpenAI-compatible LLM client, merges only allowed semantic `DiseaseReport` fields into the original record, and writes `disease_reports.enriched.jsonl`. Scraper-owned fields must remain unchanged.

The final export stage reads enriched records from selected sources, writes one combined Turtle file and one combined CSV file, and creates parent directories as needed.

## Configuration

Existing scraper settings remain in `config.yaml`. Add only operator-tunable export and interpreter settings there, such as final RDF path, final CSV path, default prompt/schema paths, model name, endpoint environment variable names, timeouts, and progress settings.

Secrets must not be stored in `config.yaml`. API keys or tokens should come from environment variables or local ignored files. Importing the interpreter module must not attempt to read credentials or contact the model service.

## Output Contract

For each source:

- Candidate records remain in `data/unstructured/<source>/disease_reports.jsonl`.
- Enriched records are written to `data/unstructured/<source>/disease_reports.enriched.jsonl`.

Final combined outputs:

- Turtle: `lindas/data/rdf/tierseuchen-screener.ttl`
- CSV: `lindas/data/csv/disease_reports.csv`

The old normal-pipeline QA output `<source>.qa.ttl` is removed from `run-all`. If a developer-only debug export is needed later, it should be added as an explicit debug command, not as part of the primary pipeline.

## Error Handling

Network scraping errors and parse errors keep the existing non-fatal artifact behavior. Enrichment should preserve per-record errors in `_error` or a similarly explicit field while continuing the batch, because a single model failure should not discard other candidate records.

`run-all` should stop when a required stage returns a non-zero exit code. Final exports should only run after enrichment succeeds for the selected sources.

## Testing

Tests should cover:

- CLI parser uses `prog="ts-screener"`.
- `pyproject.toml` exposes only the `ts-screener` console script.
- `run-all` includes enrichment before final export.
- `enrich` can be tested with a fake extraction function and no live model call.
- Enrichment preserves scraper-owned fields and only merges allowed semantic fields.
- Final CSV export writes one combined file.
- Final RDF export writes one combined Turtle file and does not create `.qa.ttl` in the normal pipeline.
- README/backend docs use `uv run ts-screener`.
