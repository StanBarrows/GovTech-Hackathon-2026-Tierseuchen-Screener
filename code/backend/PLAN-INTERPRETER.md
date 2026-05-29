# Interpreter Refactor Plan

## Goal

Refactor the interpreter layer so it enriches `disease_reports.jsonl` by filling the existing `DiseaseReport` semantic fields, without changing the Turtle/RDF schema and without adding parallel fields that later need merging.

## Constraints

- Do not change RDF/Turtle vocabulary, predicates, classes, or export shape.
- Do not add new output fields like `llm_disease_name`, `Disease`, `consequence.politisch`, etc. unless they are internal-only and removed before writing output.
- The interpreter output JSONL must remain compatible with the existing `DiseaseReport` / RDF export flow.
- Preserve all existing `ts-screener extract-reports` candidate/provenance fields: IDs, source metadata, fulltext, evidence snippets, `rule_*` fields, extraction status/confidence.
- Only populate existing semantic fields already present on `DiseaseReport`.

## Interpreter Should Populate

Map LLM extraction into existing fields:

- `disease_name`
- `disease_type`
- `country_or_territory`
- `is_in_europe`
- `relevance_level`
- `relevance_rationale`
- `severity_level`
- `severity_rationale`
- `reach_level`
- `reach_rationale`
- `has_consequences`
- `consequences`
- `control_measures`
- `prevention_measures`
- Optional event fields when explicitly stated: `species`, `cases`, `dead`, `killed`, `slaughtered`, `vaccinated`, `confirmation_date`, `result_date`, `status`, etc.

## Prompt Change

Update `code/backend/interpreter/SystemPrompt.md` so the model returns exactly the existing `DiseaseReport` semantic field names, not a separate schema with `Disease`, `DiseaseSubtype`, `InEurope`, or nested `consequence`.

## Pipeline Change

Update `code/backend/interpreter/interpreter.py` so JSONL mode:

1. Reads each candidate report.
2. Sends only the relevant text plus useful rule evidence to the model: `fulltext`, `source_document_title`, `rule_matched_terms`, `rule_disease_type`, `rule_control_measures`, `evidence_snippets`.
3. Parses the model response.
4. Merges only allowed existing semantic fields back into the original record.
5. Preserves all original candidate/provenance fields unchanged.
6. Writes enriched records that can go directly into existing RDF export.

## Avoid

- No separate embedding/enrichment field namespace for now.
- No duplicated semantic fields.
- No schema migration.
- No RDF export changes unless a bug prevents existing fields from exporting.
- No model guesses: require explicit evidence or `null`.

## Validation

Add or update a small test/fixture proving:

- Candidate fields remain unchanged.
- Interpreter fills existing semantic fields.
- No unexpected keys are written.
- Enriched output can be passed to current RDF export without schema changes.
