# Frontend Filter Integration Brief

This brief explains how the dashboard frontend should integrate filters with the RDF/GraphDB PoC (ontology v0.1.2).

A. Data model overview
- Map markers = ts:OutbreakEvent (events with coordinates).
- Situation aggregation = ts:OutbreakSituation (disease-country-month grouping).
- PAFF context = ts:PaffSituationStatement (candidate statements linked to situations).

Path:
OutbreakEvent -> ts:belongsToSituation -> OutbreakSituation <- ts:describesSituation <- PaffSituationStatement

B. Recommended frontend filters (property -> SKOS scheme)
1. Disease / subtype
 - ts:hasDisease -> tss:diseases
 - ts:hasDiseaseSubtype -> tss:disease-subtypes
2. Animal context
 - ts:hasAnimalContext -> tss:animal-contexts
3. Wildlife type
 - ts:hasWildlifeType -> tss:wildlife-types
4. Production type
 - ts:hasProductionType -> tss:production-types
5. Production system
 - ts:hasProductionSystem -> tss:production-systems
6. Epidemiological unit
 - ts:hasEpidemiologicalUnit -> tss:epidemiological-units
7. Species
 - ts:hasSpecies -> tss:species
8. Event status
 - ts:hasEventStatus -> tss:event-status
9. Result status
 - ts:hasResultStatus -> tss:result-status
10. Pertinence
 - ts:hasPertinence -> tss:pertinence-values
11. Test / lab
 - ts:hasTestCategory -> tss:test-categories
 - ts:hasTestSubcategory -> tss:test-subcategories
 - ts:hasTestName -> tss:test-names
 - ts:hasTestType -> tss:test-types
 - ts:hasLaboratoryType -> tss:laboratory-types
12. PAFF assessments
 - ts:hasRelevanceLevel -> tss:relevance-levels
 - ts:hasSeverityLevel -> tss:severity-levels
 - ts:hasReachLevel -> tss:reach-levels
 - ts:hasExtractionConfidence -> tss:extraction-confidence-levels
 - ts:hasExtractionStatus -> tss:extraction-status-values
 - ts:hasResearchLinkType -> tss:research-link-types

C. Raw vs normalized rule
- Preserve raw fields for traceability (e.g., ts:rawDiseaseName, ts:rawDiseaseType).
- Frontend filters MUST use normalized SKOS IRIs (skos:Concept) and show skos:prefLabel for display.
- Example: filter by ts:hasDisease tss:hpai-non-p and ts:hasAnimalContext tss:animal-context-wild-birds.

D. SPARQL examples (short)
1) Map markers with coords + situation:

```sparql
PREFIX ts: <https://data.tierseuchen-screener.example.org/ontology/adis#>
SELECT ?event ?lat ?lon ?disease ?country ?confirmationDate ?situation
WHERE {
 ?event a ts:OutbreakEvent ; ts:occursAt ?loc ; ts:hasDisease ?disease ; ts:confirmationDate ?confirmationDate ; ts:belongsToSituation ?situation .
 ?loc ts:latitude ?lat ; ts:longitude ?lon .
 OPTIONAL { ?situation ts:situationCountry ?country }
}
```

2) Available disease filter values:
```sparql
PREFIX ts: <https://data.tierseuchen-screener.example.org/ontology/adis#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
SELECT DISTINCT ?disease ?label WHERE { ?s a ts:OutbreakEvent ; ts:hasDisease ?disease . ?disease skos:prefLabel ?label }
ORDER BY ?label
```

3) Markers filtered by disease & animal context (frontend will bind IRIs):
```sparql
PREFIX ts: <https://data.tierseuchen-screener.example.org/ontology/adis#>
SELECT ?event ?lat ?lon ?label WHERE {
  VALUES (?d ?ac) { ( <TSS:hpai-non-p> <TSS:animal-context-wild-birds> ) }
  ?event a ts:OutbreakEvent ; ts:hasDisease ?d ; ts:hasAnimalContext ?ac ; ts:occursAt ?loc .
  ?loc ts:latitude ?lat ; ts:longitude ?lon .
  ?d skos:prefLabel ?label .
}
```

4) Given an event, get PAFF context (use map-marker-to-paff-report.rq in repo):
- `lindas/RDFPoC/graphdb-poc/queries/03-marker-to-paff-report.rq`

5) PAFF assessment values for a situation:
```sparql
PREFIX ts: <https://data.tierseuchen-screener.example.org/ontology/adis#>
SELECT ?relevanceLevel ?severityLevel ?reachLevel WHERE {
 ?situation a ts:OutbreakSituation ; ts:hasSituationKey "hpai-non-p|de|2026-05" .
 OPTIONAL { ?situation ^ts:describesSituation ?stmt . ?stmt ts:hasRelevanceAssessment/ts:hasRelevanceLevel ?relevanceLevel }
 OPTIONAL { ?situation ^ts:describesSituation ?stmt . ?stmt ts:hasSeverityAssessment/ts:hasSeverityLevel ?severityLevel }
 OPTIONAL { ?situation ^ts:describesSituation ?stmt . ?stmt ts:hasReachAssessment/ts:hasReachLevel ?reachLevel }
}
```

E. Implementation guidance
- Use IRIs as internal filter values; show skos:prefLabel.
- Combine filters using `VALUES` or `FILTER IN`.
- Use `OPTIONAL` for fields that may be absent.
- Show extraction confidence/status on PAFF items.
- Prefer backend mediation for security and caching.

F. Known limitations
- SKOS concepts are provisional (v0.1.2), not official taxonomies.
- PAFF candidate RDF is PoC-level and requires human review.
- SHACL validates structure only.
- LLM extraction is not yet automated.

---

If you want, I can also create JSON examples for the frontend (response shape for markers and situation context).
