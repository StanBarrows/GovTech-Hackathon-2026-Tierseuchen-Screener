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

## DiseaseReport Model

`DiseaseReport` is the ADIS-like media-derived report dataclass. It should keep
ADIS-compatible field names where practical, while allowing nulls because media
articles often omit official outbreak details.

Required provenance and article fields:

- `report_id`
- `source_id`
- `source_name`
- `source_link`
- `source_publication_date`
- `source_retrieved_at`
- `fulltext`
- `extraction_method`
- `extraction_version`
- `confidence`
- `evidence_snippets`

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

Extended screening fields:

- `is_in_europe`
- `has_consequences`
- `consequences`

`is_in_europe` and `has_consequences` are nullable booleans. They should be
`None` when the article does not provide enough evidence. `consequences` stores
a short string description of reported impacts, measures, restrictions,
economic effects, trade effects, public-health implications, or other relevant
consequences.

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
