# PAFF-to-Situation Linkage Dry Run Report

## Scope
Controlled linkage dry run only (no PDF pipeline, no LLM extraction, no scraping).

## Selected ADIS event
- Event IRI: `https://data.tierseuchen-screener.example.org/data/event_de-hpai-non-p-2026-06u4a`

## Selected shared situation
- Situation IRI: `https://data.tierseuchen-screener.example.org/data/situation_hpai-non-p-in-wild-birds-deutschland-2026-05`
- Situation key: `hpai-non-p-in-wild-birds|deutschland|2026-05`

## PAFF candidate graph created
- File: `data/rdf/paff/paff-candidate-sample.ttl`
- PaffReport IRI: `https://data.tierseuchen-screener.example.org/data/report_paff_2026_05_12`
- PaffSituationStatement IRI(s):
  - `https://data.tierseuchen-screener.example.org/data/stmt_paff_hpai_de_2026_05`
- EvidenceSnippet IRI(s):
  - `https://data.tierseuchen-screener.example.org/data/snip_paff_1`

## Linkage outcome
- `ts:PaffSituationStatement` successfully linked to existing ADIS `ts:OutbreakSituation` via `ts:describesSituation`.
- End-to-end path confirmed:
  - ADIS event -> `ts:belongsToSituation` -> shared situation
  - PAFF statement -> `ts:describesSituation` -> shared situation
  - PAFF statement -> `ts:extractedFromSource` -> PAFF report

## Query test
- Query used: adapted version of `ontology/adis-reference/v0.1.1/queries/map-marker-to-paff-report.rq` with a bound event IRI.
- Result: query returned expected linked PAFF data.
- Returned fields included:
  - clicked event
  - shared situation
  - PAFF statement
  - PAFF report
  - evidence snippet
  - relevance level
  - severity level
  - reach level
  - prevention measure text

## Candidate assessment values included
- Extraction status: `tss:status-candidate`
- Extraction confidence: `tss:confidence-medium`
- Relevance: `tss:relevance-high`
- Severity: `tss:severity-medium`
- Reach: `tss:reach-regional`
- Prevention measure: yes (candidate text + raw evidence)

## Research references
- None included (intentionally absent; no invented research links).

## Query changes needed
- Only runtime event binding (`VALUES ?event { ... }`) for test execution.
- No ontology/schema change needed for this dry run.

## Readiness for next step
- Result is ready for the next step: controlled generation of candidate PAFF RDF (still human-review gated).
