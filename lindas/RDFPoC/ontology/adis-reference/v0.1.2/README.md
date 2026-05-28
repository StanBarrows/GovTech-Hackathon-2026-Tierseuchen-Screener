ADIS Reference Ontology MVP v0.1.1

Purpose
- This package updates ontology MVP v0.1 with modelling cleanup and extensions for PAFF/unstructured-text extraction scenarios.
- It remains ADIS-derived, but now supports a unified reference target for:
  1) structured ADIS rows
  2) candidate facts extracted from PAFF-like presentations via LLM.

Important
- Not an official ADIS/BLV/WOAH ontology.
- Hackathon-provisional namespaces and concept schemes.
- LLM-extracted statements are candidate-level only, never authoritative without review.

Files
- adis-reference-ontology.ttl: OWL/RDFS core + PAFF/unstructured extraction classes/properties.
- adis-reference-skos.ttl: SKOS schemes incl. relevance/severity/reach/prevention/extraction confidence+status.
- adis-reference-shapes-draft.ttl: draft SHACL lifecycle shapes (candidate -> reviewed -> published + PAFF extraction assessments).
- examples/adis-sample-events.ttl: ADIS structured examples carried forward.
- examples/paff-sample-extraction.ttl: PAFF candidate extraction modelling example.

Key modelling pattern: raw + normalized
- Preserve raw source values/snippets (e.g., ts:rawEventStatusLabel, ts:snippetText).
- Add normalized links to SKOS concepts (e.g., ts:hasEventStatus, ts:hasReachLevel).
- Keep provenance and evidence links for every extracted candidate.

Deferred
- No production extraction pipeline.
- No broad external mappings.
- No final authority alignment (GBIF/WOAH/etc.) yet.
