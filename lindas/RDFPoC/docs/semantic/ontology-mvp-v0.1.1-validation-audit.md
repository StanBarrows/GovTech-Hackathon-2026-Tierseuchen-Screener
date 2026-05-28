# Ontology MVP v0.1.1 Validation Audit

Date: 2026-05-28
Scope: consistency + testability audit before converter implementation

Audited files
- ontology/adis-reference/v0.1.1/adis-reference-ontology.ttl
- ontology/adis-reference/v0.1.1/adis-reference-skos.ttl
- ontology/adis-reference/v0.1.1/adis-reference-shapes-draft.ttl
- ontology/adis-reference/v0.1.1/examples/adis-sample-events.ttl
- ontology/adis-reference/v0.1.1/examples/paff-sample-extraction.ttl
- ontology/adis-reference/v0.1.1/queries/map-marker-to-paff-report.rq

## 1) Turtle syntax validity
Result: **valid after small blocking fixes**.

Blocking issues found
- `examples/adis-sample-events.ttl` used prefixed names with slashes (e.g., `tsd:situation/...`) which is invalid Turtle syntax.
- `examples/paff-sample-extraction.ttl` used prefixed names with slashes (e.g., `tsd:report/...`) which is invalid Turtle syntax.

Fix applied
- Replaced slash-based local names with underscore-safe local names (e.g., `tsd:situation_hpai_non_p_wild_birds_de_2026_01`).

Post-fix parse checks
- ontology ttl: OK
- skos ttl: OK
- shapes ttl: OK
- adis examples ttl: OK
- paff examples ttl: OK

## 2) Prefix consistency (`ts-skos` vs `tss`)
Result: **consistent internally, naming mismatch externally**.

- Files use `tss:` prefix for SKOS concept namespace (`https://data.tierseuchen-screener.example.org/skos/`).
- Requested label `ts-skos:*` is conceptually equivalent but not the literal prefix used in files.
- This is non-blocking (prefix label is syntactic sugar), but for team clarity consider aliasing with a `ts-skos:` prefix in future revisions.

## 3) Classes/properties used in examples defined in ontology
Result: **pass**.

- All `ts:` classes/properties referenced in both example files are declared in `adis-reference-ontology.ttl`.

## 4) SKOS concepts used in examples exist in SKOS file
Result: **pass**.

Examples reference these concepts which are present:
- `tss:hpai_non_p_wild_birds`
- `tss:asf_wild_boar`
- `tss:mtbc`
- `tss:confidence-medium`
- `tss:status-candidate`
- `tss:relevance-high`
- `tss:severity-medium`
- `tss:reach-regional`

## 5) Required PAFF assessment schemes
Result: **pass** (all six present).

Present schemes:
- relevance-levels
- severity-levels
- reach-levels
- extraction-confidence-levels
- extraction-status-values
- research-link-types

## 6) Every ADIS OutbreakEvent links to one OutbreakSituation
Result: **pass in sample**.

- 5/5 sample `ts:OutbreakEvent` instances have `ts:belongsToSituation` exactly once.

## 7) Situation month derived from ADIS confirmation date
Result: **pass in sample**.

Checked examples:
- DE-HPAI...xsyaz confirmation 2026-01-30 -> situationMonth 2026-01
- DE-HPAI...yy25e confirmation 2026-02-02 -> situationMonth 2026-02
- FR-MTBC...1gtxn confirmation 2026-03-20 -> situationMonth 2026-03
- HU-ASF...l0iz2 confirmation 2026-03-31 -> situationMonth 2026-03
- PL-HPAI(P)...jqn1t confirmation 2026-04-14 -> situationMonth 2026-04

## 8) Every PAFF PaffSituationStatement links to one OutbreakSituation
Result: **pass in sample**.

- `tsd:stmt_asf_germany` has `ts:describesSituation` to one `ts:OutbreakSituation`.

## 9) SPARQL query run against example data
Result: **works with event binding supplied**.

- The provided query is parameterized and expects an event binding.
- Test run with `VALUES ?event { <...event_de_hpai_non_p_2026_xsyaz> }` returned rows successfully.
- Non-blocking improvement: include a commented ready-to-run `VALUES` block in the query file for quick testing.

## 10) SHACL funnel executable vs conceptual
Result: **executable as draft structural checks**.

- Shapes are syntactically valid SHACL and can be run by SHACL engines.
- Current shapes validate structural presence only (intended).
- For production-grade runs, recommended upgrades:
  1. Add `sh:class` constraints for object targets.
  2. Add controlled-vocabulary checks (`sh:in` or node constraints against scheme membership).
  3. Add stricter cardinalities for one-to-one links where required.
  4. Add profile separation for candidate/reviewed/published graphs.

---

## Blocking issues found/fixed
1. Invalid Turtle prefixed names with `/` in both example TTLs -> fixed.

## Remaining non-blocking issues
- Prefix naming (`tss` vs `ts-skos`) could be harmonized for readability.
- Query usability could improve with an in-file example `VALUES` binding.
- Some ontology domains are permissive by design (MVP); can be tightened in v0.2.

## Overall readiness assessment
**v0.1.1 is ready for first ADIS CSV -> RDF converter implementation**, with the expectation that:
- converter emits candidate data preserving raw + normalized pattern,
- situation key/month uses confirmation-date-first fallback logic,
- SHACL is used as structural gate, not truth validation.
