# News Scraper And Disease Report Design

## Context

The project needs to monitor public animal-health news sources and turn relevant
articles into structured records for disease screening. Gefluegelnews is the
first source, but the ingestion design must support additional news sources
later.

The first version will:

- Backfill all Gefluegelnews article pages listed in the sitemap.
- Store raw HTML locally as scraped ground-truth artifacts.
- Parse all available article metadata and cleaned article text.
- Filter articles that may relate to animal disease with deterministic rules.
- Extract preliminary structured reports with a rule-based extractor.
- Leave a clear boundary for later LLM-based enrichment.

## Source Findings

`https://www.gefluegelnews.de/robots.txt` allows crawling and points to
`https://www.gefluegelnews.de/sitemap.xml`.

The sitemap currently contains about 3,569 article URLs under `/article/...`.
The `/news/rss` endpoint provides recent article metadata, but the sitemap is
the correct discovery source for a full historical backfill.

Article pages are server-rendered and include extractable fields such as title,
canonical URL, publication date, category, meta description, keywords, image
URL, body text, author, image credit, and source attribution.

## Architecture

Implement a small source-agnostic ingestion framework with source-specific
adapters. Gefluegelnews will be the first adapter.

Each news source should implement the same conceptual contract:

```python
class NewsSourceScraper(Protocol):
    source_id: str
    source_name: str

    def discover(self) -> Iterable[DiscoveredArticle]: ...
    def fetch(self, article: DiscoveredArticle) -> FetchedArticle: ...
    def parse(self, fetched: FetchedArticle) -> NewsArticle: ...
```

Source-specific code owns URL discovery, HTTP fetch details, and HTML selectors.
Shared disease filtering and report extraction consume normalized `NewsArticle`
records only.

## Data Flow

Expose explicit pipeline stages so each step can be rerun independently:

1. `discover gefluegelnews`: fetch the sitemap and produce an article URL
   manifest.
2. `fetch gefluegelnews`: download missing or changed article HTML with polite
   rate limiting and resumable behavior.
3. `parse gefluegelnews`: parse cached HTML into normalized article records.
4. `filter-disease gefluegelnews`: score article relevance using glossary and
   rule matches.
5. `extract-reports gefluegelnews --method rules`: create preliminary
   `DiseaseReport` records.
6. Later, `extract-reports gefluegelnews --method llm`: enrich records through
   an LLM extractor behind the same interface.

Parsing should use cached HTML as its primary input after the fetch stage. This
allows parser and extraction improvements without repeated website requests.

## Local Artifacts

Use per-source directories under `data/unstructured/<source_id>/`.

For Gefluegelnews:

- `data/unstructured/gefluegelnews/raw_html/`: raw cached article HTML. This is
  a local artifact and should not be committed.
- `data/unstructured/gefluegelnews/manifest.jsonl`: discovered URL manifest and
  fetch metadata.
- `data/unstructured/gefluegelnews/articles.jsonl`: parsed `NewsArticle`
  records.
- `data/unstructured/gefluegelnews/disease_articles.jsonl`: filtered
  disease-related article records with relevance evidence.
- `data/unstructured/gefluegelnews/disease_reports.jsonl`: extracted
  `DiseaseReport` records.

The manifest should include URL, canonical URL when known, fetched timestamp,
HTTP status, content hash, and local raw HTML path.

## Normalized Article Model

`NewsArticle` should include all fields needed for provenance, QA, filtering, and
later extraction:

- `source_id`
- `source_name`
- `source_link`
- `canonical_url`
- `title`
- `description`
- `keywords`
- `publication_date`
- `retrieved_at`
- `category`
- `author`
- `image_url`
- `image_credit`
- `source_attribution`
- `partner_content`
- `fulltext`
- `raw_html_path`
- `content_hash`

`fulltext` stores a cleaned Markdown representation of the article content, not
raw HTML.

## Disease Filtering

The first filter is deterministic and auditable. It should use terms from
`docs/Glossary.md` plus source-relevant German terms such as `Vogelgrippe`,
`Gefluegelpest`, `Geflügelpest`, `H5N1`, `Newcastle`, `Tierseuche`,
`Biosicherheit`, `Impfung`, `Ausbruch`, `Sperrzone`, and `Keulung`.

Filtering returns a `DiseaseRelevance` record with:

- `article_source_link`
- `is_relevant`
- `score`
- `matched_terms`
- `evidence_snippets`
- `filter_version`

This makes false positives and false negatives reviewable.

## LiNDAS/RDF Alignment

The LiNDAS proof of concept in `lindas/RDFPoC` defines the semantic target for
scraped news output. The relevant ontology version is
`lindas/RDFPoC/ontology/adis-reference/v0.1.1/`.

The scraper should align with these RDF classes and properties:

- `ts:SourceDocument`: the scraped news article as a source document.
- `ts:sourceDocumentTitle`: article title.
- `ts:sourceURL`: original news URL for QA traceability.
- `ts:EvidenceSnippet`: evidence used for filtering or extraction.
- `ts:snippetText`: evidence text.
- `ts:PaffSituationStatement`: current unstructured extraction statement class.
  The name is PAFF-specific, but the modelling pattern fits news-derived
  candidate statements.
- `ts:OutbreakSituation`: normalized disease-country-month situation.
- `ts:hasSituationKey`: stable situation key.
- `ts:situationDisease`: normalized disease concept.
- `ts:situationCountry`: normalized country/location concept.
- `ts:situationMonth`: `YYYY-MM` situation month.
- `ts:hasExtractionConfidence`: SKOS concept such as `tss:confidence-low`,
  `tss:confidence-medium`, `tss:confidence-high`, or
  `tss:confidence-unknown`.
- `ts:hasExtractionStatus`: SKOS concept such as `tss:status-candidate`,
  `tss:status-needs-review`, `tss:status-reviewed`, `tss:status-rejected`, or
  `tss:status-published`.
- `ts:hasRelevanceAssessment`, `ts:hasSeverityAssessment`,
  `ts:hasReachAssessment`: assessment nodes with normalized SKOS levels and raw
  evidence/rationale text.
- `ts:hasPreventionMeasure`: prevention/control/consequence measures extracted
  from source text.
- `ts:hasResearchReference`: scientific, surveillance, legal, or other
  references mentioned by the source.

The scraper keeps JSONL as its first output format, but field names should be
chosen so RDF export to this model is direct. Raw article strings are retained
alongside normalized concept IDs because the ontology explicitly uses a
raw-plus-normalized modelling pattern.

## DiseaseReport Model

`DiseaseReport` is the media-derived candidate extraction dataclass. It keeps
ADIS-compatible event fields where practical, but its primary semantic role is a
candidate situation statement extracted from a `NewsArticle`. Most fields are
nullable because media articles often omit official outbreak details.

Required provenance and article fields:

- `report_id`
- `source_id`
- `source_name`
- `source_document_id`
- `source_document_title`
- `source_link`
- `source_publication_date`
- `source_retrieved_at`
- `fulltext`
- `raw_html_path`
- `content_hash`
- `extraction_method`
- `extraction_version`
- `extraction_status`
- `extraction_confidence`
- `evidence_snippets`

`source_link` maps to `ts:sourceURL`. `fulltext` stores the cleaned Markdown
representation of the article. `raw_html_path` points to the local scraped
ground-truth artifact and is not an RDF upload field.

Situation fields:

- `situation_key`
- `situation_month`
- `country_or_territory`
- `country_concept_id`
- `disease_name`
- `disease_concept_id`
- `disease_type`
- `disease_type_concept_id`
- `is_in_europe`

ADIS-like event fields:

- `country_or_territory`
- `administrative_division_level_1`
- `administrative_division_level_2`
- `administrative_division_level_3`
- `location`
- `latitude`
- `longitude`
- `approximate_location`
- `disease_name`
- `disease_type`
- `species`
- `production_type`
- `wildlife_type`
- `epidemiological_unit`
- `susceptible`
- `cases`
- `dead`
- `killed`
- `slaughtered`
- `vaccinated`
- `suspicion_start_date`
- `confirmation_date`
- `end_date`
- `status`
- `clinical_signs`
- `diagnostic_tests`
- `necropsy`
- `test_name`
- `result_date`
- `result_type`
- `control_measures`

Assessment and screening fields:

- `rule_relevance_score`
- `rule_matched_terms`
- `rule_disease_type`
- `rule_control_measures`
- `relevance_level`
- `relevance_rationale`
- `raw_relevance_evidence`
- `severity_level`
- `severity_rationale`
- `raw_severity_evidence`
- `reach_level`
- `reach_rationale`
- `has_consequences`
- `consequences`
- `prevention_measures`
- `research_references`

The `rule_*` fields are deterministic CLI evidence generated by
`ts extract-reports`. They are not final semantic interpretation: they preserve
the filter score/terms, exact subtype regex hits such as `H5N1`, and coarse
control-measure term hits for audit and later resolution.

`is_in_europe` and `has_consequences` are nullable booleans. They should be
`None` when the article does not provide enough evidence. In the current split,
`ts extract-reports` leaves these enrichment fields unset; the interpreter or a
resolver should populate them from evidence-backed semantic extraction.
`consequences` stores a short string description of reported impacts, measures,
restrictions, economic effects, trade effects, public-health implications, or
other relevant consequences.

`prevention_measures` should be a list of extracted control, prevention, or
mitigation statements. In RDF export these map to `ts:PreventionMeasure`.
`consequences` remains as a human-friendly summary for analyst QA. If the same
text contains both a consequence and a control measure, store it in both fields
with the same evidence snippet.

`evidence_snippets` should be structured objects, not plain strings:

- `snippet_id`
- `text`
- `source_link`
- `locator`
- `matched_terms`

For news articles, `locator` can be a paragraph index, heading path, or another
stable source-text locator. `ts:sourceSlideNumber` is PAFF-specific and should
not be populated for news.

## Extraction Strategy

The rule-based extractor should populate only fields it can support from article
text or metadata. It should include evidence snippets for extracted values where
possible.

The later LLM extractor should implement the same interface and emit the same
`DiseaseReport` schema. It should preserve provenance and evidence, and it
should not overwrite deterministic fields without recording the extraction
method and version.

## Error Handling And Operational Constraints

- Respect `robots.txt`.
- Use a clear User-Agent.
- Apply configurable request timeout, retry count, and fetch delay.
- Resume safely from existing manifest and raw HTML cache.
- Do not fail the entire backfill on one bad article.
- Record fetch and parse failures with URL, error type, message, and timestamp.
- Avoid storing secrets or credentials.
- Keep raw HTML and generated backfill artifacts out of git unless explicitly
  requested.

## Testing

Tests should avoid live network calls. Use small checked-in HTML fixtures derived
from representative article structures and test:

- Sitemap URL filtering from local XML.
- Article parsing into `NewsArticle`.
- Markdown text cleanup.
- Disease keyword matching and evidence snippets.
- Rule-based `DiseaseReport` extraction for known disease examples.
- Resume behavior for already cached HTML.

## Implementation Notes

- Exact CLI framework and command names should follow existing project patterns.
- Artifact file formats can start as JSONL and add CSV exports if needed for
  analyst workflows.
- LLM provider configuration is deferred until the rule-based pipeline exists.
