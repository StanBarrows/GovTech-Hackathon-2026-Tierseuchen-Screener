# Ontology MVP v0.1.1 Change Log

This final v0.1.1 version introduces a shared `ts:OutbreakSituation` bridge to connect structured ADIS row-level events with PAFF candidate situation statements.

- `ts:Event` is generic so both row-level and aggregate concepts can coexist.
- ADIS rows are modelled as `ts:OutbreakEvent` (fine-grained, point-like records).
- PAFF statements are modelled as `ts:PaffSituationStatement` (narrative/candidate level), not forced into row-level outbreak events.
- `ts:OutbreakSituation` solves the granularity mismatch by linking both sides.

Confirmation-date month rule
- Situation month uses ADIS `Confirmation date` first.
- Fallback order (documented): confirmation date -> suspicion/start date -> submitted date -> unknown.

Frontend linkage pattern
- Map marker click (one ADIS event) -> `ts:belongsToSituation` -> get `ts:PaffSituationStatement` via `ts:describesSituation` -> fetch PAFF report + evidence snippets.

SHACL scope
- SHACL validates structure and completeness only.
- It does not validate epidemiological truth.
- LLM-generated PAFF RDF remains candidate data.

PAFF SKOS schemes used
- `ts-skos:relevance-levels`
- `ts-skos:severity-levels`
- `ts-skos:reach-levels`
- `ts-skos:extraction-confidence-levels`
- `ts-skos:extraction-status-values`
- `ts-skos:research-link-types`

## 1) What changed from v0.1 to v0.1.1
- Fixed ontology header: removed invalid `ts: a rdfs:Class`; added `ts: a owl:Ontology` + version `0.1.1`.
- Added missing `skos:` usage in ontology alignment.
- Added normalized object properties for status/unit/pertinence concepts:
  - ts:hasEventStatus
  - ts:hasDiagnosisStatus
  - ts:hasResultStatus
  - ts:hasPertinence
  - ts:hasMeasuringUnit
- Added raw literal preservation properties:
  - ts:rawEventStatusLabel
  - ts:rawDiagnosisStatusLabel
  - ts:rawResultStatusLabel
  - ts:rawPertinenceLabel
  - ts:rawMeasuringUnitLabel
- Replaced incorrect `ts:performedBy` pattern with `ts:performedByLaboratory` (range ts:Laboratory).
- Added PAFF/unstructured extraction model extensions and example.

## 2) Why raw + normalized pattern was introduced
- Source values (ADIS and PAFF snippets) may be ambiguous or incomplete.
- Raw values preserve evidence and auditability.
- Normalized concept links support downstream querying, aggregation, and mapping consistency.
- This pattern enables controlled transformation without losing source wording.

## 3) How PAFF/LLM extraction fits into the ontology
- New classes: ts:PaffReport, ts:EvidenceSnippet, ts:ExtractionCandidate, ts:RelevanceAssessment, ts:SeverityAssessment, ts:ReachAssessment, ts:PreventionMeasure, ts:ResearchReference, ts:DerivedAssessmentRule.
- LLM output is modelled as candidate extraction entities linked to evidence snippets and source documents.
- No extracted statement is treated as published fact by default.

## 4) How Relevance, Severity, Reach, Prevention, Research, and PAFF date are modelled
- Relevance: ts:hasRelevanceAssessment + ts:hasRelevanceLevel + rationale/evidence literals.
- Severity: ts:hasSeverityAssessment + ts:hasSeverityLevel + rationale/evidence literals.
- Reach: ts:hasReachAssessment + ts:hasReachLevel + ts:derivedByRule + rationale.
- Prevention: ts:hasPreventionMeasure, ts:hasPreventionType, text + raw evidence.
- Research: ts:mentionsResearch -> ts:ResearchReference with title/URL/citation/evidence fields.
- PAFF date: ts:paffDate on ts:PaffReport.

## 5) Reach/Reichweite derived rule-based modelling
Reach is modelled as derived assessment (not raw source fact), with a rule artifact:
- same country + month + same adminLevel3 -> local
- differ adminLevel3 but same adminLevel2 -> regional
- differ adminLevel2 -> national
- insufficient data -> unknown

Represented via ts:DerivedAssessmentRule and linked by ts:derivedByRule.

## 6) What remains provisional
- Namespace, URIs, and concept schemes are hackathon-provisional.
- Severity/relevance/prevention concept definitions are not official standards.
- SHACL remains draft-level and intentionally minimal.

## 7) Can v0.1.1 serve as Schema Forge reference target?
- Yes, for MVP-level Schema Forge mapping and extraction-contract design.
- It is suitable for candidate extraction + review workflows.
- Before production usage: align authority vocabularies, harden SHACL, and validate semantics with domain mentors.
