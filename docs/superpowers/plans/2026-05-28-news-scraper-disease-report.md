# News Scraper Disease Report Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a source-agnostic news ingestion pipeline with Gefluegelnews as the first source, producing cached HTML, normalized articles, disease-filtered articles, and preliminary LiNDAS-aligned `DiseaseReport` candidate records.

**Architecture:** Add a small Python package under `src/govtech_tierseuchen/` with focused modules for shared models, JSONL I/O, source adapters, disease filtering, rule-based report extraction, and a CLI. The first implementation uses only the Python standard library so no dependency approval is required.

**Tech Stack:** Python 3.13, `uv run`, dataclasses, `urllib.request`, `xml.etree.ElementTree`, `html.parser`, `argparse`, JSONL files, pytest-style tests if pytest is available through the environment.

---

## File Structure

- Create: `src/govtech_tierseuchen/__init__.py`
  - Package marker and public version string.
- Create: `src/govtech_tierseuchen/models.py`
  - Dataclasses: `DiscoveredArticle`, `FetchedArticle`, `NewsArticle`, `EvidenceSnippet`, `DiseaseRelevance`, `DiseaseReport`, `PreventionMeasure`, `ResearchReference`, `FetchError`, `ParseError`.
- Create: `src/govtech_tierseuchen/jsonl.py`
  - JSONL read/write helpers for dataclasses and dictionaries.
- Create: `src/govtech_tierseuchen/gefluegelnews.py`
  - Gefluegelnews discovery, fetch manifest handling, HTML parsing, and cleaned Markdown extraction.
- Create: `src/govtech_tierseuchen/disease_filter.py`
  - Deterministic keyword matching and evidence snippet extraction.
- Create: `src/govtech_tierseuchen/disease_reports.py`
  - Rule-based extraction from `NewsArticle` plus `DiseaseRelevance` to `DiseaseReport`.
- Create: `src/govtech_tierseuchen/cli.py`
  - CLI stages: `discover`, `fetch`, `parse`, `filter-disease`, `extract-reports`.
- Create: `tests/test_gefluegelnews.py`
  - Local fixture-based tests for sitemap discovery and article parsing.
- Create: `tests/test_disease_pipeline.py`
  - Local tests for filtering and rule-based report extraction.
- Modify: `.gitignore`
  - Ignore local generated Gefluegelnews raw/cache/output artifacts.
- Modify: `README.md`
  - Add concise scraper usage section after implementation works.

Do not commit generated HTML, manifests, JSONL outputs, or local caches unless explicitly requested.

## Task 1: Core Dataclasses

**Files:**
- Create: `src/govtech_tierseuchen/__init__.py`
- Create: `src/govtech_tierseuchen/models.py`
- Test: `tests/test_disease_pipeline.py`

- [ ] **Step 1: Write the failing dataclass test**

Add this to `tests/test_disease_pipeline.py`:

```python
from datetime import date, datetime, timezone

from govtech_tierseuchen.models import DiseaseReport, EvidenceSnippet, NewsArticle, PreventionMeasure


def test_news_article_keeps_source_link_and_markdown_fulltext():
    article = NewsArticle(
        source_id="gefluegelnews",
        source_name="Gefluegelnews",
        source_link="https://www.gefluegelnews.de/article/example",
        canonical_url="https://www.gefluegelnews.de/article/example",
        title="Gefluegelpest: Beispiel",
        description="Kurztext",
        keywords=["Gefluegelpest", "H5N1"],
        publication_date=date(2026, 5, 20),
        retrieved_at=datetime(2026, 5, 28, 12, 0, tzinfo=timezone.utc),
        category="Biosicherheit",
        author="Gefluegelnews",
        image_url="https://www.gefluegelnews.de/storage/example.jpg",
        image_credit="Redaktion",
        source_attribution="Ministerium",
        partner_content=False,
        fulltext="# Gefluegelpest: Beispiel\n\nEin Ausbruch wurde gemeldet.",
        raw_html_path="data/unstructured/gefluegelnews/raw_html/example.html",
        content_hash="abc123",
    )

    assert article.source_link == "https://www.gefluegelnews.de/article/example"
    assert article.fulltext.startswith("# Gefluegelpest")
    assert article.keywords == ["Gefluegelpest", "H5N1"]


def test_disease_report_has_extended_screening_fields():
    report = DiseaseReport(
        report_id="gefluegelnews:example",
        source_id="gefluegelnews",
        source_name="Gefluegelnews",
        source_document_id="source_document:gefluegelnews:example",
        source_document_title="Gefluegelpest: Beispiel",
        source_link="https://www.gefluegelnews.de/article/example",
        source_publication_date=date(2026, 5, 20),
        source_retrieved_at=datetime(2026, 5, 28, 12, 0, tzinfo=timezone.utc),
        fulltext="Ein Ausbruch in Polen hat Sperrzonen zur Folge.",
        raw_html_path="data/unstructured/gefluegelnews/raw_html/example.html",
        content_hash="abc123",
        extraction_method="rules",
        extraction_version="rules-v1",
        extraction_status="candidate",
        extraction_confidence="medium",
        evidence_snippets=[
            EvidenceSnippet(
                snippet_id="snippet:example:1",
                text="Ausbruch in Polen",
                source_link="https://www.gefluegelnews.de/article/example",
                locator="p[1]",
                matched_terms=["Ausbruch", "Polen"],
            )
        ],
        situation_key="hpai|polen|2026-05",
        situation_month="2026-05",
        country_or_territory="Polen",
        country_concept_id="country-polen",
        disease_name="HPAI",
        disease_concept_id="hpai",
        is_in_europe=True,
        has_consequences=True,
        consequences="Sperrzonen wurden eingerichtet.",
        prevention_measures=[
            PreventionMeasure(
                text="Sperrzonen wurden eingerichtet.",
                prevention_type="restriction-zone",
                raw_evidence="Sperrzonen wurden eingerichtet.",
            )
        ],
    )

    assert report.source_link.endswith("/example")
    assert report.source_document_title == "Gefluegelpest: Beispiel"
    assert report.is_in_europe is True
    assert report.has_consequences is True
    assert report.consequences == "Sperrzonen wurden eingerichtet."
    assert report.evidence_snippets[0].locator == "p[1]"
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
uv run pytest tests/test_disease_pipeline.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'govtech_tierseuchen'`.

If `pytest` is not installed, stop and ask for approval to add `pytest` and `ruff` as dev dependencies with `uv add --dev pytest ruff`.

- [ ] **Step 3: Implement the package marker**

Create `src/govtech_tierseuchen/__init__.py`:

```python
"""Tools for animal disease news ingestion and report extraction."""

__version__ = "0.1.0"
```

- [ ] **Step 4: Implement the dataclasses**

Create `src/govtech_tierseuchen/models.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass(frozen=True)
class DiscoveredArticle:
    source_id: str
    source_name: str
    source_link: str
    discovered_at: datetime
    last_modified: datetime | None = None


@dataclass(frozen=True)
class FetchedArticle:
    source_id: str
    source_name: str
    source_link: str
    fetched_at: datetime
    status_code: int
    raw_html_path: str
    content_hash: str
    canonical_url: str | None = None


@dataclass(frozen=True)
class NewsArticle:
    source_id: str
    source_name: str
    source_link: str
    canonical_url: str
    title: str
    description: str | None
    keywords: list[str]
    publication_date: date | None
    retrieved_at: datetime
    category: str | None
    author: str | None
    image_url: str | None
    image_credit: str | None
    source_attribution: str | None
    partner_content: bool | None
    fulltext: str
    raw_html_path: str
    content_hash: str


@dataclass(frozen=True)
class DiseaseRelevance:
    article_source_link: str
    is_relevant: bool
    score: int
    matched_terms: list[str]
    evidence_snippets: list[EvidenceSnippet]
    filter_version: str


@dataclass(frozen=True)
class EvidenceSnippet:
    snippet_id: str
    text: str
    source_link: str
    locator: str | None = None
    matched_terms: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PreventionMeasure:
    text: str
    prevention_type: str | None = None
    raw_evidence: str | None = None


@dataclass(frozen=True)
class ResearchReference:
    title: str | None = None
    url: str | None = None
    citation_text: str | None = None
    link_type: str | None = None
    raw_evidence: str | None = None


@dataclass(frozen=True)
class DiseaseReport:
    report_id: str
    source_id: str
    source_name: str
    source_document_id: str
    source_document_title: str
    source_link: str
    source_publication_date: date | None
    source_retrieved_at: datetime
    fulltext: str
    raw_html_path: str
    content_hash: str
    extraction_method: str
    extraction_version: str
    extraction_status: str
    extraction_confidence: str
    evidence_snippets: list[EvidenceSnippet]
    situation_key: str | None = None
    situation_month: str | None = None
    country_or_territory: str | None = None
    country_concept_id: str | None = None
    administrative_division_level_1: str | None = None
    administrative_division_level_2: str | None = None
    administrative_division_level_3: str | None = None
    location: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    approximate_location: bool | None = None
    disease_name: str | None = None
    disease_concept_id: str | None = None
    disease_type: str | None = None
    disease_type_concept_id: str | None = None
    species: str | None = None
    production_type: str | None = None
    wildlife_type: str | None = None
    epidemiological_unit: str | None = None
    susceptible: int | None = None
    cases: int | None = None
    dead: int | None = None
    killed: int | None = None
    slaughtered: int | None = None
    vaccinated: int | None = None
    suspicion_start_date: date | None = None
    confirmation_date: date | None = None
    end_date: date | None = None
    status: str | None = None
    clinical_signs: bool | None = None
    diagnostic_tests: bool | None = None
    necropsy: bool | None = None
    test_name: str | None = None
    result_date: date | None = None
    result_type: str | None = None
    control_measures: list[str] = field(default_factory=list)
    relevance_level: str | None = None
    relevance_rationale: str | None = None
    raw_relevance_evidence: str | None = None
    severity_level: str | None = None
    severity_rationale: str | None = None
    raw_severity_evidence: str | None = None
    reach_level: str | None = None
    reach_rationale: str | None = None
    is_in_europe: bool | None = None
    has_consequences: bool | None = None
    consequences: str | None = None
    prevention_measures: list[PreventionMeasure] = field(default_factory=list)
    research_references: list[ResearchReference] = field(default_factory=list)


@dataclass(frozen=True)
class FetchError:
    source_link: str
    error_type: str
    message: str
    occurred_at: datetime


@dataclass(frozen=True)
class ParseError:
    source_link: str
    raw_html_path: str
    error_type: str
    message: str
    occurred_at: datetime
```

- [ ] **Step 5: Run the test to verify it passes**

Run:

```bash
uv run pytest tests/test_disease_pipeline.py -v
```

Expected: PASS for both tests.

## Task 2: JSONL Utilities

**Files:**
- Create: `src/govtech_tierseuchen/jsonl.py`
- Modify: `tests/test_disease_pipeline.py`

- [ ] **Step 1: Write the failing JSONL round-trip test**

Append this to `tests/test_disease_pipeline.py`:

```python
from dataclasses import dataclass
from datetime import date, datetime, timezone

from govtech_tierseuchen.jsonl import read_jsonl, write_jsonl


@dataclass(frozen=True)
class _ExampleRecord:
    name: str
    published: date
    retrieved_at: datetime
    tags: list[str]


def test_jsonl_round_trip_preserves_dates(tmp_path):
    path = tmp_path / "records.jsonl"
    records = [
        _ExampleRecord(
            name="one",
            published=date(2026, 5, 28),
            retrieved_at=datetime(2026, 5, 28, 12, 0, tzinfo=timezone.utc),
            tags=["HPAI"],
        )
    ]

    write_jsonl(path, records)

    assert read_jsonl(path) == [
        {
            "name": "one",
            "published": "2026-05-28",
            "retrieved_at": "2026-05-28T12:00:00+00:00",
            "tags": ["HPAI"],
        }
    ]
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
uv run pytest tests/test_disease_pipeline.py::test_jsonl_round_trip_preserves_dates -v
```

Expected: FAIL with `ModuleNotFoundError` for `govtech_tierseuchen.jsonl`.

- [ ] **Step 3: Implement JSONL helpers**

Create `src/govtech_tierseuchen/jsonl.py`:

```python
from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable


def _to_jsonable(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _to_jsonable(asdict(value))
    if isinstance(value, dict):
        return {key: _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, datetime | date):
        return value.isoformat()
    return value


def write_jsonl(path: Path, records: Iterable[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(_to_jsonable(record), ensure_ascii=False, sort_keys=True))
            handle.write("\n")


def append_jsonl(path: Path, records: Iterable[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(_to_jsonable(record), ensure_ascii=False, sort_keys=True))
            handle.write("\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]
```

- [ ] **Step 4: Run the test to verify it passes**

Run:

```bash
uv run pytest tests/test_disease_pipeline.py::test_jsonl_round_trip_preserves_dates -v
```

Expected: PASS.

## Task 3: Gefluegelnews Sitemap Discovery

**Files:**
- Create: `src/govtech_tierseuchen/gefluegelnews.py`
- Create: `tests/test_gefluegelnews.py`

- [ ] **Step 1: Write the failing sitemap discovery test**

Create `tests/test_gefluegelnews.py`:

```python
from datetime import datetime, timezone

from govtech_tierseuchen.gefluegelnews import parse_sitemap_articles


def test_parse_sitemap_articles_returns_only_article_urls():
    sitemap_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url>
        <loc>https://www.gefluegelnews.de/article/polen-wird-zum-vogelgrippe-hotspot-europas</loc>
        <lastmod>2026-05-28T00:00:03+00:00</lastmod>
      </url>
      <url>
        <loc>https://www.gefluegelnews.de/category/tierwohl</loc>
        <lastmod>2026-05-28T00:00:03+00:00</lastmod>
      </url>
      <url>
        <loc>https://www.gefluegelnews.de/article/polen-wird-zum-vogelgrippe-hotspot-europas</loc>
        <lastmod>2026-05-29T00:00:03+00:00</lastmod>
      </url>
    </urlset>
    """

    articles = parse_sitemap_articles(
        sitemap_xml.encode("utf-8"),
        discovered_at=datetime(2026, 5, 28, 12, 0, tzinfo=timezone.utc),
    )

    assert len(articles) == 1
    assert articles[0].source_id == "gefluegelnews"
    assert articles[0].source_link.endswith("/polen-wird-zum-vogelgrippe-hotspot-europas")
    assert articles[0].last_modified == datetime(2026, 5, 28, 0, 0, 3, tzinfo=timezone.utc)
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
uv run pytest tests/test_gefluegelnews.py::test_parse_sitemap_articles_returns_only_article_urls -v
```

Expected: FAIL with `ModuleNotFoundError` or missing `parse_sitemap_articles`.

- [ ] **Step 3: Implement sitemap parsing**

Create or update `src/govtech_tierseuchen/gefluegelnews.py`:

```python
from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse
from xml.etree import ElementTree

from govtech_tierseuchen.models import DiscoveredArticle

SOURCE_ID = "gefluegelnews"
SOURCE_NAME = "Gefluegelnews"
BASE_URL = "https://www.gefluegelnews.de"
SITEMAP_URL = f"{BASE_URL}/sitemap.xml"
NEWS_RSS_URL = f"{BASE_URL}/news/rss"


def parse_sitemap_articles(data: bytes, discovered_at: datetime) -> list[DiscoveredArticle]:
    root = ElementTree.fromstring(data)
    namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    discovered: dict[str, DiscoveredArticle] = {}

    for url_element in root.findall(".//sm:url", namespace):
        loc_element = url_element.find("sm:loc", namespace)
        if loc_element is None or loc_element.text is None:
            continue
        source_link = loc_element.text.strip()
        parsed = urlparse(source_link)
        if parsed.netloc != "www.gefluegelnews.de" or not parsed.path.startswith("/article/"):
            continue
        if source_link in discovered:
            continue

        lastmod_element = url_element.find("sm:lastmod", namespace)
        last_modified = _parse_datetime(lastmod_element.text.strip()) if lastmod_element is not None and lastmod_element.text else None
        discovered[source_link] = DiscoveredArticle(
            source_id=SOURCE_ID,
            source_name=SOURCE_NAME,
            source_link=source_link,
            discovered_at=discovered_at,
            last_modified=last_modified,
        )

    return sorted(discovered.values(), key=lambda article: article.source_link)


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def cache_filename_for_url(source_link: str) -> str:
    digest = hashlib.sha256(source_link.encode("utf-8")).hexdigest()
    slug = urlparse(source_link).path.rstrip("/").split("/")[-1]
    safe_slug = "".join(char if char.isalnum() or char in "-_" else "-" for char in slug)[:120]
    return f"{safe_slug}-{digest[:12]}.html"


def raw_html_path(base_dir: Path, source_link: str) -> Path:
    return base_dir / SOURCE_ID / "raw_html" / cache_filename_for_url(source_link)
```

- [ ] **Step 4: Run the test to verify it passes**

Run:

```bash
uv run pytest tests/test_gefluegelnews.py::test_parse_sitemap_articles_returns_only_article_urls -v
```

Expected: PASS.

## Task 4: Gefluegelnews Article Parser

**Files:**
- Modify: `src/govtech_tierseuchen/gefluegelnews.py`
- Modify: `tests/test_gefluegelnews.py`

- [ ] **Step 1: Write the failing parser test**

Append this to `tests/test_gefluegelnews.py`:

```python
from pathlib import Path

from govtech_tierseuchen.gefluegelnews import parse_article_html


def test_parse_article_html_extracts_metadata_and_markdown():
    html = """
    <html>
      <head>
        <title>Polen wird zum Vogelgrippe-Hotspot Europas</title>
        <meta name="description" content="Polen bleibt Europas Hotspot der Vogelgrippe." />
        <meta name="keywords" content="Vogelgrippe, H5N1, Polen" />
        <meta property="og:image" content="https://www.gefluegelnews.de/storage/example.jpg">
        <link rel="canonical" href="https://www.gefluegelnews.de/article/polen-wird-zum-vogelgrippe-hotspot-europas" />
      </head>
      <body>
        <section id="detailpage">
          <div class="container">
            <div class="row">
              <div class="col-md-8" id="main">
                <h1>Polen wird zum Vogelgrippe-Hotspot Europas</h1>
                <div class="specs">
                  <div class="date"><i></i>26 Mai 2026</div>
                  <div class="category"><i></i>Biosicherheit</div>
                </div>
                <img src="/storage/example_880x495.jpg" alt="Hühner" />
                <div class="share"><h6>Teile diesen Artikel</h6></div>
                <div class="text">
                  <p><strong>Polen bleibt Europas Hotspot der Vogelgrippe.</strong></p>
                  <h2>Viele Ausbrüche</h2>
                  <p>Bereits 140 H5N1-Ausbrüche trafen 2026 Geflügelbetriebe.</p>
                </div>
                <div class="author">
                  Geflügelnews
                  <div class="images"><span>Bild:</span> Redaktion</div>
                  <div><strong>Quelle:</strong> Behördenmeldung</div>
                </div>
              </div>
            </div>
          </div>
        </section>
      </body>
    </html>
    """

    article = parse_article_html(
        html=html,
        source_link="https://www.gefluegelnews.de/article/polen-wird-zum-vogelgrippe-hotspot-europas",
        raw_html_path=Path("data/unstructured/gefluegelnews/raw_html/example.html"),
        content_hash="abc123",
        retrieved_at=datetime(2026, 5, 28, 12, 0, tzinfo=timezone.utc),
    )

    assert article.title == "Polen wird zum Vogelgrippe-Hotspot Europas"
    assert article.canonical_url == "https://www.gefluegelnews.de/article/polen-wird-zum-vogelgrippe-hotspot-europas"
    assert article.description == "Polen bleibt Europas Hotspot der Vogelgrippe."
    assert article.keywords == ["Vogelgrippe", "H5N1", "Polen"]
    assert article.publication_date.isoformat() == "2026-05-26"
    assert article.category == "Biosicherheit"
    assert article.author == "Geflügelnews"
    assert article.image_credit == "Redaktion"
    assert article.source_attribution == "Behördenmeldung"
    assert article.fulltext == (
        "# Polen wird zum Vogelgrippe-Hotspot Europas\n\n"
        "**Polen bleibt Europas Hotspot der Vogelgrippe.**\n\n"
        "## Viele Ausbrüche\n\n"
        "Bereits 140 H5N1-Ausbrüche trafen 2026 Geflügelbetriebe."
    )
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
uv run pytest tests/test_gefluegelnews.py::test_parse_article_html_extracts_metadata_and_markdown -v
```

Expected: FAIL with missing `parse_article_html`.

- [ ] **Step 3: Implement the article parser**

Append this implementation to `src/govtech_tierseuchen/gefluegelnews.py`:

```python
import re
import hashlib
from dataclasses import dataclass, field
from html import unescape
from html.parser import HTMLParser

from govtech_tierseuchen.models import NewsArticle

GERMAN_MONTHS = {
    "Januar": 1,
    "Februar": 2,
    "März": 3,
    "Maerz": 3,
    "April": 4,
    "Mai": 5,
    "Juni": 6,
    "Juli": 7,
    "August": 8,
    "September": 9,
    "Oktober": 10,
    "November": 11,
    "Dezember": 12,
}


@dataclass
class _ParsedHtml:
    title: str | None = None
    canonical_url: str | None = None
    description: str | None = None
    keywords: list[str] = field(default_factory=list)
    image_url: str | None = None
    article_title: str | None = None
    date_text: str | None = None
    category: str | None = None
    body_parts: list[tuple[str, str]] = field(default_factory=list)
    author_text: str | None = None
    image_credit: str | None = None
    source_attribution: str | None = None


class _GefluegelnewsParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.result = _ParsedHtml()
        self._tag_stack: list[str] = []
        self._capture: str | None = None
        self._buffer: list[str] = []
        self._in_detail = False
        self._in_main = False
        self._in_text = False
        self._in_author = False
        self._in_image_credit = False
        self._source_next = False
        self._spec_index = 0
        self._strong_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = dict(attrs)
        self._tag_stack.append(tag)
        if tag == "meta":
            name = attr.get("name")
            prop = attr.get("property")
            content = attr.get("content")
            if name == "description" and content:
                self.result.description = content.strip()
            if name == "keywords" and content:
                self.result.keywords = [part.strip() for part in content.split(",") if part.strip()]
            if prop == "og:image" and content:
                self.result.image_url = content.strip()
        elif tag == "link" and attr.get("rel") == "canonical" and attr.get("href"):
            self.result.canonical_url = attr["href"].strip()
        elif tag == "section" and attr.get("id") == "detailpage":
            self._in_detail = True
        elif self._in_detail and tag == "div" and attr.get("id") == "main":
            self._in_main = True
        elif self._in_main and tag == "div" and attr.get("class") == "text":
            self._in_text = True
        elif self._in_main and tag == "div" and attr.get("class") == "author":
            self._in_author = True
            self._capture = "author"
            self._buffer = []
        elif self._in_author and tag == "div" and attr.get("class") == "images":
            self._in_image_credit = True
            self._buffer = []
        elif self._in_main and tag == "h1":
            self._capture = "article_title"
            self._buffer = []
        elif self._in_main and not self._in_text and tag == "div" and attr.get("class") in {"date", "category"}:
            self._capture = attr["class"]
            self._buffer = []
        elif self._in_text and tag in {"p", "h2", "h3"}:
            self._capture = tag
            self._buffer = []
        elif self._in_text and tag == "strong":
            self._strong_depth += 1

    def handle_endtag(self, tag: str) -> None:
        text = _clean_text("".join(self._buffer))
        if self._capture == "article_title" and tag == "h1":
            self.result.article_title = text
            self._capture = None
        elif self._capture == "date" and tag == "div":
            self.result.date_text = text
            self._capture = None
        elif self._capture == "category" and tag == "div":
            self.result.category = text
            self._capture = None
        elif self._in_text and self._capture in {"p", "h2", "h3"} and tag == self._capture:
            if text:
                self.result.body_parts.append((tag, text))
            self._capture = None
        elif self._in_author and self._in_image_credit and tag == "div":
            self.result.image_credit = text.replace("Bild:", "").strip() or None
            self._in_image_credit = False
        elif self._in_author and tag == "div" and self._source_next:
            self.result.source_attribution = text.replace("Quelle:", "").strip() or None
            self._source_next = False
        elif self._in_author and tag == "div":
            pass
        elif self._in_author and tag == "strong" and "Quelle:" in text:
            self._source_next = True
            self._buffer = []

        if self._in_text and tag == "strong":
            self._strong_depth = max(0, self._strong_depth - 1)
        if self._in_text and tag == "div":
            self._in_text = False
        if self._in_author and tag == "div" and self._tag_stack.count("div") <= 1:
            author = _clean_text("".join(self._buffer))
            self.result.author_text = author.split("Bild:")[0].split("Quelle:")[0].strip() or None
            self._in_author = False
        if self._tag_stack:
            self._tag_stack.pop()

    def handle_data(self, data: str) -> None:
        if not data:
            return
        if self._capture:
            if self._in_text and self._strong_depth and self._capture == "p":
                self._buffer.append(f"**{data}**")
            else:
                self._buffer.append(data)


def parse_article_html(
    html: str,
    source_link: str,
    raw_html_path: Path,
    content_hash: str,
    retrieved_at: datetime,
) -> NewsArticle:
    parser = _GefluegelnewsParser()
    parser.feed(html)
    parsed = parser.result
    title = parsed.article_title or parsed.title
    if not title:
        raise ValueError(f"Could not parse article title from {source_link}")
    canonical_url = parsed.canonical_url or source_link
    fulltext = _to_markdown(title, parsed.body_parts)
    return NewsArticle(
        source_id=SOURCE_ID,
        source_name=SOURCE_NAME,
        source_link=source_link,
        canonical_url=canonical_url,
        title=title,
        description=parsed.description,
        keywords=parsed.keywords,
        publication_date=_parse_german_date(parsed.date_text) if parsed.date_text else None,
        retrieved_at=retrieved_at,
        category=parsed.category,
        author=parsed.author_text,
        image_url=parsed.image_url,
        image_credit=parsed.image_credit,
        source_attribution=parsed.source_attribution,
        partner_content=None,
        fulltext=fulltext,
        raw_html_path=str(raw_html_path),
        content_hash=content_hash,
    )


def _clean_text(value: str) -> str:
    value = unescape(value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def _to_markdown(title: str, body_parts: list[tuple[str, str]]) -> str:
    parts = [f"# {title}"]
    for tag, text in body_parts:
        if tag == "h2":
            parts.append(f"## {text}")
        elif tag == "h3":
            parts.append(f"### {text}")
        else:
            parts.append(text)
    return "\n\n".join(part for part in parts if part)


def _parse_german_date(value: str):
    from datetime import date

    match = re.search(r"(\d{1,2})\s+([A-Za-zÄÖÜäöüß]+)\s+(\d{4})", value)
    if not match:
        return None
    day = int(match.group(1))
    month = GERMAN_MONTHS[match.group(2)]
    year = int(match.group(3))
    return date(year, month, day)
```

- [ ] **Step 4: Run the parser test**

Run:

```bash
uv run pytest tests/test_gefluegelnews.py::test_parse_article_html_extracts_metadata_and_markdown -v
```

Expected: PASS. If author/source parsing fails, adjust only the parser internals, not the expected external `NewsArticle` fields.

## Task 5: Deterministic Disease Filter

**Files:**
- Create: `src/govtech_tierseuchen/disease_filter.py`
- Modify: `tests/test_disease_pipeline.py`

- [ ] **Step 1: Write the failing disease filter test**

Append this to `tests/test_disease_pipeline.py`:

```python
from govtech_tierseuchen.disease_filter import assess_disease_relevance


def test_assess_disease_relevance_returns_matches_and_snippets():
    article = NewsArticle(
        source_id="gefluegelnews",
        source_name="Gefluegelnews",
        source_link="https://www.gefluegelnews.de/article/polen",
        canonical_url="https://www.gefluegelnews.de/article/polen",
        title="Polen wird zum Vogelgrippe-Hotspot Europas",
        description="H5N1-Ausbrüche treffen Geflügelbetriebe.",
        keywords=["Vogelgrippe", "H5N1"],
        publication_date=date(2026, 5, 26),
        retrieved_at=datetime(2026, 5, 28, 12, 0, tzinfo=timezone.utc),
        category="Biosicherheit",
        author="Gefluegelnews",
        image_url=None,
        image_credit=None,
        source_attribution=None,
        partner_content=False,
        fulltext="Polen bleibt Europas Hotspot der Vogelgrippe. Bereits 140 H5N1-Ausbrüche trafen Geflügelbetriebe.",
        raw_html_path="raw.html",
        content_hash="abc123",
    )

    relevance = assess_disease_relevance(article)

    assert relevance.is_relevant is True
    assert relevance.score >= 3
    assert "Vogelgrippe" in relevance.matched_terms
    assert "H5N1" in relevance.matched_terms
    assert any("Hotspot der Vogelgrippe" in snippet.text for snippet in relevance.evidence_snippets)
    assert relevance.evidence_snippets[0].source_link == article.source_link
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
uv run pytest tests/test_disease_pipeline.py::test_assess_disease_relevance_returns_matches_and_snippets -v
```

Expected: FAIL with missing `disease_filter`.

- [ ] **Step 3: Implement disease relevance matching**

Create `src/govtech_tierseuchen/disease_filter.py`:

```python
from __future__ import annotations

import re

from govtech_tierseuchen.models import DiseaseRelevance, EvidenceSnippet, NewsArticle

FILTER_VERSION = "rules-v1"

DISEASE_TERMS = [
    "HPAI",
    "H5N1",
    "H5N5",
    "Vogelgrippe",
    "Geflügelpest",
    "Gefluegelpest",
    "Aviäre Influenza",
    "Avian Influenza",
    "Newcastle",
    "Afrikanische Schweinepest",
    "ASP",
    "Lumpy Skin Disease",
    "Tierseuche",
    "Ausbruch",
    "Sperrzone",
    "Keulung",
    "Biosicherheit",
]


def assess_disease_relevance(article: NewsArticle) -> DiseaseRelevance:
    haystack = "\n".join(
        part
        for part in [
            article.title,
            article.description or "",
            " ".join(article.keywords),
            article.category or "",
            article.fulltext,
        ]
        if part
    )
    matched_terms = []
    snippets = []
    for term in DISEASE_TERMS:
        if re.search(re.escape(term), haystack, flags=re.IGNORECASE):
            matched_terms.append(term)
            snippet = _snippet_for_term(article.source_link, haystack, term)
            if snippet and all(existing.text != snippet.text for existing in snippets):
                snippets.append(snippet)
    score = len(matched_terms)
    return DiseaseRelevance(
        article_source_link=article.source_link,
        is_relevant=score > 0,
        score=score,
        matched_terms=matched_terms,
        evidence_snippets=snippets[:5],
        filter_version=FILTER_VERSION,
    )


def _snippet_for_term(source_link: str, text: str, term: str, radius: int = 90) -> EvidenceSnippet | None:
    match = re.search(re.escape(term), text, flags=re.IGNORECASE)
    if match is None:
        return None
    start = max(0, match.start() - radius)
    end = min(len(text), match.end() + radius)
    snippet_text = re.sub(r"\s+", " ", text[start:end]).strip()
    snippet_hash = hashlib.sha1(f"{source_link}|{term}|{start}".encode("utf-8")).hexdigest()[:12]
    return EvidenceSnippet(
        snippet_id=f"snippet:{snippet_hash}",
        text=snippet_text,
        source_link=source_link,
        locator=f"char[{start}:{end}]",
        matched_terms=[term],
    )
```

- [ ] **Step 4: Run the disease filter test**

Run:

```bash
uv run pytest tests/test_disease_pipeline.py::test_assess_disease_relevance_returns_matches_and_snippets -v
```

Expected: PASS.

## Task 6: Rule-Based DiseaseReport Extraction

**Files:**
- Create: `src/govtech_tierseuchen/disease_reports.py`
- Modify: `tests/test_disease_pipeline.py`

- [ ] **Step 1: Write the failing report extraction test**

Append this to `tests/test_disease_pipeline.py`:

```python
from govtech_tierseuchen.disease_filter import assess_disease_relevance
from govtech_tierseuchen.disease_reports import extract_report_rules


def test_extract_report_rules_populates_europe_and_consequences():
    article = NewsArticle(
        source_id="gefluegelnews",
        source_name="Gefluegelnews",
        source_link="https://www.gefluegelnews.de/article/polen",
        canonical_url="https://www.gefluegelnews.de/article/polen",
        title="Polen wird zum Vogelgrippe-Hotspot Europas",
        description="Polen bleibt Europas Hotspot der Vogelgrippe.",
        keywords=["Vogelgrippe", "H5N1"],
        publication_date=date(2026, 5, 26),
        retrieved_at=datetime(2026, 5, 28, 12, 0, tzinfo=timezone.utc),
        category="Biosicherheit",
        author="Gefluegelnews",
        image_url=None,
        image_credit=None,
        source_attribution="Behördenmeldung",
        partner_content=False,
        fulltext=(
            "Polen bleibt Europas Hotspot der Vogelgrippe. "
            "Bereits 140 H5N1-Ausbrüche trafen 2026 Geflügelbetriebe. "
            "Sperrzonen wurden eingerichtet und Betriebe mussten Tiere keulen."
        ),
        raw_html_path="raw.html",
        content_hash="abc123",
    )
    relevance = assess_disease_relevance(article)

    report = extract_report_rules(article, relevance)

    assert report.report_id == "gefluegelnews:polen"
    assert report.source_document_title == article.title
    assert report.source_link == article.source_link
    assert report.fulltext == article.fulltext
    assert report.situation_key == "hpai|polen|2026-05"
    assert report.situation_month == "2026-05"
    assert report.disease_name == "HPAI"
    assert report.disease_type == "H5N1"
    assert report.country_or_territory == "Polen"
    assert report.is_in_europe is True
    assert report.has_consequences is True
    assert "Sperrzonen" in report.consequences
    assert any(measure.prevention_type == "Keulung" for measure in report.prevention_measures)
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
uv run pytest tests/test_disease_pipeline.py::test_extract_report_rules_populates_europe_and_consequences -v
```

Expected: FAIL with missing `disease_reports`.

- [ ] **Step 3: Implement the rule-based extractor**

Create `src/govtech_tierseuchen/disease_reports.py`:

```python
from __future__ import annotations

import re
from urllib.parse import urlparse

from govtech_tierseuchen.models import DiseaseRelevance, DiseaseReport, NewsArticle, PreventionMeasure

EXTRACTION_VERSION = "rules-v1"
EUROPEAN_COUNTRIES = {
    "Albanien",
    "Andorra",
    "Belgien",
    "Bosnien",
    "Bulgarien",
    "Dänemark",
    "Deutschland",
    "Estland",
    "Finnland",
    "Frankreich",
    "Griechenland",
    "Irland",
    "Island",
    "Italien",
    "Kroatien",
    "Lettland",
    "Liechtenstein",
    "Litauen",
    "Luxemburg",
    "Malta",
    "Moldau",
    "Niederlande",
    "Norwegen",
    "Österreich",
    "Polen",
    "Portugal",
    "Rumänien",
    "Schweden",
    "Schweiz",
    "Serbien",
    "Slowakei",
    "Slowenien",
    "Spanien",
    "Tschechien",
    "Ukraine",
    "Ungarn",
    "Vereinigtes Königreich",
}

CONSEQUENCE_TERMS = {
    "Sperrzone": "Sperrzonen",
    "Sperrzonen": "Sperrzonen",
    "keulen": "Keulung",
    "gekeult": "Keulung",
    "Keulung": "Keulung",
    "Stallpflicht": "Stallpflicht",
    "Impfung": "Impfung",
    "Monitoring": "Monitoring",
    "Biosicherheit": "Biosicherheit",
    "Handel": "Handel",
    "Export": "Export",
}


def extract_report_rules(article: NewsArticle, relevance: DiseaseRelevance) -> DiseaseReport:
    text = f"{article.title}\n{article.description or ''}\n{article.fulltext}"
    country = _first_match(text, sorted(EUROPEAN_COUNTRIES))
    disease_name = _disease_name(text)
    disease_type = _first_regex(text, r"\bH[0-9]N[0-9]\b")
    control_measures = _control_measures(text)
    consequences = _consequence_sentence(article.fulltext)
    report_id = f"{article.source_id}:{urlparse(article.source_link).path.rstrip('/').split('/')[-1]}"
    return DiseaseReport(
        report_id=report_id,
        source_id=article.source_id,
        source_name=article.source_name,
        source_document_id=f"source_document:{report_id}",
        source_document_title=article.title,
        source_link=article.source_link,
        source_publication_date=article.publication_date,
        source_retrieved_at=article.retrieved_at,
        fulltext=article.fulltext,
        raw_html_path=article.raw_html_path,
        content_hash=article.content_hash,
        extraction_method="rules",
        extraction_version=EXTRACTION_VERSION,
        extraction_status="candidate",
        extraction_confidence=_confidence_level(relevance.score),
        evidence_snippets=relevance.evidence_snippets,
        situation_key=_situation_key(disease_name, country, article.publication_date),
        situation_month=article.publication_date.isoformat()[:7] if article.publication_date else None,
        country_or_territory=country,
        country_concept_id=f"country-{_slug(country)}" if country else None,
        disease_name=disease_name,
        disease_concept_id=_slug(disease_name) if disease_name else None,
        disease_type=disease_type,
        disease_type_concept_id=_slug(disease_type) if disease_type else None,
        control_measures=control_measures,
        relevance_level="high" if relevance.score >= 3 else "medium",
        raw_relevance_evidence="; ".join(snippet.text for snippet in relevance.evidence_snippets),
        is_in_europe=country in EUROPEAN_COUNTRIES if country else None,
        has_consequences=bool(consequences) if consequences is not None else None,
        consequences=consequences,
        prevention_measures=_prevention_measures(text),
    )


def _first_match(text: str, terms: list[str]) -> str | None:
    for term in terms:
        if re.search(rf"\b{re.escape(term)}\b", text, flags=re.IGNORECASE):
            return term
    return None


def _first_regex(text: str, pattern: str) -> str | None:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return match.group(0).upper() if match else None


def _disease_name(text: str) -> str | None:
    if re.search(r"Vogelgrippe|Geflügelpest|Gefluegelpest|HPAI|Aviäre Influenza", text, flags=re.IGNORECASE):
        return "HPAI"
    if re.search(r"Newcastle", text, flags=re.IGNORECASE):
        return "Newcastle Disease"
    if re.search(r"Afrikanische Schweinepest|\bASP\b", text, flags=re.IGNORECASE):
        return "ASP"
    if re.search(r"Lumpy Skin Disease|\bLSD\b", text, flags=re.IGNORECASE):
        return "LSD"
    return None


def _control_measures(text: str) -> list[str]:
    measures = []
    for term, normalized in CONSEQUENCE_TERMS.items():
        if re.search(re.escape(term), text, flags=re.IGNORECASE) and normalized not in measures:
            measures.append(normalized)
    return measures


def _prevention_measures(text: str) -> list[PreventionMeasure]:
    measures = []
    for term, normalized in CONSEQUENCE_TERMS.items():
        match = re.search(re.escape(term), text, flags=re.IGNORECASE)
        if match:
            sentence = _sentence_containing(text, match.start()) or match.group(0)
            measures.append(PreventionMeasure(text=sentence, prevention_type=normalized, raw_evidence=match.group(0)))
    return measures


def _consequence_sentence(text: str) -> str | None:
    sentences = re.split(r"(?<=[.!?])\s+", text.replace("\n", " "))
    for sentence in sentences:
        if any(re.search(re.escape(term), sentence, flags=re.IGNORECASE) for term in CONSEQUENCE_TERMS):
            return sentence.strip()
    return None


def _sentence_containing(text: str, index: int) -> str | None:
    sentences = re.split(r"(?<=[.!?])\s+", text.replace("\n", " "))
    cursor = 0
    for sentence in sentences:
        end = cursor + len(sentence)
        if cursor <= index <= end:
            return sentence.strip()
        cursor = end + 1
    return None


def _confidence_level(score: int) -> str:
    if score >= 4:
        return "high"
    if score >= 2:
        return "medium"
    if score >= 1:
        return "low"
    return "unknown"


def _situation_key(disease_name: str | None, country: str | None, publication_date) -> str | None:
    if not disease_name or not country or not publication_date:
        return None
    return f"{_slug(disease_name)}|{_slug(country)}|{publication_date.isoformat()[:7]}"


def _slug(value: str | None) -> str:
    if not value:
        return "unknown"
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return re.sub(r"-+", "-", value).strip("-") or "unknown"
```

- [ ] **Step 4: Run the report extraction test**

Run:

```bash
uv run pytest tests/test_disease_pipeline.py::test_extract_report_rules_populates_europe_and_consequences -v
```

Expected: PASS.

## Task 7: Fetching, Caching, And Manifest Support

**Files:**
- Modify: `src/govtech_tierseuchen/gefluegelnews.py`
- Modify: `tests/test_gefluegelnews.py`

- [ ] **Step 1: Write the failing cache test**

Append this to `tests/test_gefluegelnews.py`:

```python
from govtech_tierseuchen.gefluegelnews import cache_html


def test_cache_html_writes_raw_html_and_returns_fetched_article(tmp_path):
    fetched = cache_html(
        base_dir=tmp_path,
        source_link="https://www.gefluegelnews.de/article/example",
        html="<html>example</html>",
        status_code=200,
        fetched_at=datetime(2026, 5, 28, 12, 0, tzinfo=timezone.utc),
    )

    raw_path = Path(fetched.raw_html_path)
    assert raw_path.exists()
    assert raw_path.read_text(encoding="utf-8") == "<html>example</html>"
    assert fetched.content_hash == "a59b59fbb5480ba00678a3cfc2fbe83cdb21c88460ba97be599b94ecc9031ec5"
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
uv run pytest tests/test_gefluegelnews.py::test_cache_html_writes_raw_html_and_returns_fetched_article -v
```

Expected: FAIL with missing `cache_html`.

- [ ] **Step 3: Implement cache and HTTP fetch helpers**

Append this to `src/govtech_tierseuchen/gefluegelnews.py`:

```python
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from govtech_tierseuchen.models import FetchedArticle, FetchError

DEFAULT_USER_AGENT = "GovTech-Tierseuchen prototype scraper (+local research; respects robots.txt)"


def cache_html(
    base_dir: Path,
    source_link: str,
    html: str,
    status_code: int,
    fetched_at: datetime,
    canonical_url: str | None = None,
) -> FetchedArticle:
    encoded = html.encode("utf-8")
    content_hash = hashlib.sha256(encoded).hexdigest()
    path = raw_html_path(base_dir, source_link)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    return FetchedArticle(
        source_id=SOURCE_ID,
        source_name=SOURCE_NAME,
        source_link=source_link,
        fetched_at=fetched_at,
        status_code=status_code,
        raw_html_path=str(path),
        content_hash=content_hash,
        canonical_url=canonical_url,
    )


def fetch_url(source_link: str, timeout_seconds: float, user_agent: str = DEFAULT_USER_AGENT) -> tuple[int, str]:
    request = Request(source_link, headers={"User-Agent": user_agent})
    with urlopen(request, timeout=timeout_seconds) as response:
        status = getattr(response, "status", 200)
        data = response.read()
    return status, data.decode("utf-8", errors="replace")


def fetch_and_cache_article(
    base_dir: Path,
    source_link: str,
    fetched_at: datetime,
    timeout_seconds: float,
    delay_seconds: float,
) -> FetchedArticle | FetchError:
    try:
        status, html = fetch_url(source_link, timeout_seconds=timeout_seconds)
        fetched = cache_html(base_dir, source_link, html, status, fetched_at)
        if delay_seconds > 0:
            time.sleep(delay_seconds)
        return fetched
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        return FetchError(
            source_link=source_link,
            error_type=type(exc).__name__,
            message=str(exc),
            occurred_at=fetched_at,
        )
```

- [ ] **Step 4: Run the cache test**

Run:

```bash
uv run pytest tests/test_gefluegelnews.py::test_cache_html_writes_raw_html_and_returns_fetched_article -v
```

Expected: PASS. If the expected hash differs, compute the SHA-256 for the exact UTF-8 string and update the test only after confirming the implementation uses SHA-256.

## Task 8: CLI Pipeline

**Files:**
- Create: `src/govtech_tierseuchen/cli.py`
- Modify: `tests/test_gefluegelnews.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Write the failing CLI parser test**

Append this to `tests/test_gefluegelnews.py`:

```python
from govtech_tierseuchen.cli import build_parser


def test_cli_parser_accepts_pipeline_stage_and_source():
    parser = build_parser()
    args = parser.parse_args(["discover", "gefluegelnews", "--data-dir", "data/unstructured"])

    assert args.command == "discover"
    assert args.source == "gefluegelnews"
    assert args.data_dir == "data/unstructured"
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
uv run pytest tests/test_gefluegelnews.py::test_cli_parser_accepts_pipeline_stage_and_source -v
```

Expected: FAIL with missing `govtech_tierseuchen.cli`.

- [ ] **Step 3: Implement the CLI**

Create `src/govtech_tierseuchen/cli.py`:

```python
from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

from govtech_tierseuchen.disease_filter import assess_disease_relevance
from govtech_tierseuchen.disease_reports import extract_report_rules
from govtech_tierseuchen.gefluegelnews import (
    SITEMAP_URL,
    fetch_and_cache_article,
    fetch_url,
    parse_article_html,
    parse_sitemap_articles,
)
from govtech_tierseuchen.jsonl import read_jsonl, write_jsonl


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="govtech-tierseuchen")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ["discover", "fetch", "parse", "filter-disease", "extract-reports"]:
        subparser = subparsers.add_parser(command)
        subparser.add_argument("source", choices=["gefluegelnews"])
        subparser.add_argument("--data-dir", default="data/unstructured")
        subparser.add_argument("--timeout-seconds", type=float, default=20.0)
        subparser.add_argument("--delay-seconds", type=float, default=1.0)
        subparser.add_argument("--limit", type=int, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    data_dir = Path(args.data_dir)
    if args.command == "discover":
        return _discover(data_dir, args.timeout_seconds)
    if args.command == "fetch":
        return _fetch(data_dir, args.timeout_seconds, args.delay_seconds, args.limit)
    if args.command == "parse":
        return _parse(data_dir, args.limit)
    if args.command == "filter-disease":
        return _filter_disease(data_dir)
    if args.command == "extract-reports":
        return _extract_reports(data_dir)
    parser.error(f"Unknown command {args.command}")
    return 2


def _discover(data_dir: Path, timeout_seconds: float) -> int:
    _, xml = fetch_url(SITEMAP_URL, timeout_seconds=timeout_seconds)
    articles = parse_sitemap_articles(xml.encode("utf-8"), discovered_at=datetime.now(UTC))
    write_jsonl(data_dir / "gefluegelnews" / "manifest.jsonl", articles)
    return 0


def _fetch(data_dir: Path, timeout_seconds: float, delay_seconds: float, limit: int | None) -> int:
    manifest_path = data_dir / "gefluegelnews" / "manifest.jsonl"
    rows = read_jsonl(manifest_path)
    fetched_rows = []
    selected_rows = rows if limit is None else rows[:limit]
    untouched_rows = [] if limit is None else rows[limit:]
    for row in selected_rows:
        fetched = fetch_and_cache_article(
            base_dir=data_dir,
            source_link=row["source_link"],
            fetched_at=datetime.now(UTC),
            timeout_seconds=timeout_seconds,
            delay_seconds=delay_seconds,
        )
        merged = dict(row)
        if hasattr(fetched, "raw_html_path"):
            merged.update(
                {
                    "fetched_at": fetched.fetched_at.isoformat(),
                    "status_code": fetched.status_code,
                    "raw_html_path": fetched.raw_html_path,
                    "content_hash": fetched.content_hash,
                    "canonical_url": fetched.canonical_url,
                }
            )
        else:
            merged.update(
                {
                    "fetch_error_type": fetched.error_type,
                    "fetch_error_message": fetched.message,
                    "fetch_error_at": fetched.occurred_at.isoformat(),
                }
            )
        fetched_rows.append(merged)
    write_jsonl(manifest_path, [*fetched_rows, *untouched_rows])
    return 0


def _parse(data_dir: Path, limit: int | None) -> int:
    manifest = read_jsonl(data_dir / "gefluegelnews" / "manifest.jsonl")
    parsed = []
    for row in manifest[:limit]:
        raw_html_path = Path(row["raw_html_path"]) if "raw_html_path" in row else None
        if raw_html_path is None or not raw_html_path.exists():
            continue
        html = raw_html_path.read_text(encoding="utf-8")
        parsed.append(
            parse_article_html(
                html=html,
                source_link=row["source_link"],
                raw_html_path=raw_html_path,
                content_hash=row.get("content_hash", ""),
                retrieved_at=datetime.fromisoformat(row.get("fetched_at", datetime.now(UTC).isoformat())),
            )
        )
    write_jsonl(data_dir / "gefluegelnews" / "articles.jsonl", parsed)
    return 0


def _filter_disease(data_dir: Path) -> int:
    articles = read_jsonl(data_dir / "gefluegelnews" / "articles.jsonl")
    write_jsonl(data_dir / "gefluegelnews" / "disease_articles.jsonl", articles)
    return 0


def _extract_reports(data_dir: Path) -> int:
    articles = read_jsonl(data_dir / "gefluegelnews" / "articles.jsonl")
    write_jsonl(data_dir / "gefluegelnews" / "disease_reports.jsonl", articles)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Add package script to `pyproject.toml`**

Add this section to `pyproject.toml`:

```toml
[project.scripts]
govtech-tierseuchen = "govtech_tierseuchen.cli:main"
```

- [ ] **Step 5: Run the CLI parser test**

Run:

```bash
uv run pytest tests/test_gefluegelnews.py::test_cli_parser_accepts_pipeline_stage_and_source -v
```

Expected: PASS.

## Task 9: Complete CLI Stage Integration

**Files:**
- Modify: `src/govtech_tierseuchen/cli.py`
- Modify: `src/govtech_tierseuchen/models.py`
- Modify: `tests/test_disease_pipeline.py`

- [ ] **Step 1: Write failing dict restoration and pipeline test**

Append this to `tests/test_disease_pipeline.py`:

```python
from govtech_tierseuchen.models import news_article_from_dict


def test_news_article_from_dict_restores_dates():
    article = news_article_from_dict(
        {
            "source_id": "gefluegelnews",
            "source_name": "Gefluegelnews",
            "source_link": "https://example.test/article",
            "canonical_url": "https://example.test/article",
            "title": "Vogelgrippe",
            "description": None,
            "keywords": ["H5N1"],
            "publication_date": "2026-05-26",
            "retrieved_at": "2026-05-28T12:00:00+00:00",
            "category": "Biosicherheit",
            "author": None,
            "image_url": None,
            "image_credit": None,
            "source_attribution": None,
            "partner_content": False,
            "fulltext": "Vogelgrippe in Polen.",
            "raw_html_path": "raw.html",
            "content_hash": "abc",
        }
    )

    assert article.publication_date == date(2026, 5, 26)
    assert article.retrieved_at == datetime(2026, 5, 28, 12, 0, tzinfo=timezone.utc)
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
uv run pytest tests/test_disease_pipeline.py::test_news_article_from_dict_restores_dates -v
```

Expected: FAIL with missing `news_article_from_dict`.

- [ ] **Step 3: Add dict restoration helpers**

Append this to `src/govtech_tierseuchen/models.py`:

```python
def news_article_from_dict(row: dict) -> NewsArticle:
    publication_date = date.fromisoformat(row["publication_date"]) if row.get("publication_date") else None
    retrieved_at = datetime.fromisoformat(row["retrieved_at"])
    return NewsArticle(
        source_id=row["source_id"],
        source_name=row["source_name"],
        source_link=row["source_link"],
        canonical_url=row["canonical_url"],
        title=row["title"],
        description=row.get("description"),
        keywords=list(row.get("keywords") or []),
        publication_date=publication_date,
        retrieved_at=retrieved_at,
        category=row.get("category"),
        author=row.get("author"),
        image_url=row.get("image_url"),
        image_credit=row.get("image_credit"),
        source_attribution=row.get("source_attribution"),
        partner_content=row.get("partner_content"),
        fulltext=row["fulltext"],
        raw_html_path=row["raw_html_path"],
        content_hash=row["content_hash"],
    )
```

- [ ] **Step 4: Update CLI filter and extract stages**

Replace `_filter_disease()` and `_extract_reports()` in `src/govtech_tierseuchen/cli.py` with:

```python
def _filter_disease(data_dir: Path) -> int:
    from govtech_tierseuchen.models import news_article_from_dict

    articles = [news_article_from_dict(row) for row in read_jsonl(data_dir / "gefluegelnews" / "articles.jsonl")]
    relevant = []
    for article in articles:
        relevance = assess_disease_relevance(article)
        if relevance.is_relevant:
            relevant.append({"article": article, "relevance": relevance})
    write_jsonl(data_dir / "gefluegelnews" / "disease_articles.jsonl", relevant)
    return 0


def _extract_reports(data_dir: Path) -> int:
    from govtech_tierseuchen.models import news_article_from_dict

    articles = [news_article_from_dict(row) for row in read_jsonl(data_dir / "gefluegelnews" / "articles.jsonl")]
    reports = []
    for article in articles:
        relevance = assess_disease_relevance(article)
        if relevance.is_relevant:
            reports.append(extract_report_rules(article, relevance))
    write_jsonl(data_dir / "gefluegelnews" / "disease_reports.jsonl", reports)
    return 0
```

- [ ] **Step 5: Run the restoration test**

Run:

```bash
uv run pytest tests/test_disease_pipeline.py::test_news_article_from_dict_restores_dates -v
```

Expected: PASS.

## Task 10: Gitignore And README Usage

**Files:**
- Modify: `.gitignore`
- Modify: `README.md`

- [ ] **Step 1: Update `.gitignore`**

Add these lines to `.gitignore`:

```gitignore
# Local scraper artifacts
data/unstructured/*/raw_html/
data/unstructured/*/manifest.jsonl
data/unstructured/*/articles.jsonl
data/unstructured/*/disease_articles.jsonl
data/unstructured/*/disease_reports.jsonl
```

- [ ] **Step 2: Update README usage**

Append this section to `README.md`:

```markdown
## News Scraper Prototype

The news scraper is staged so discovery, fetching, parsing, filtering, and report
extraction can be rerun independently.

```bash
uv run govtech-tierseuchen discover gefluegelnews
uv run govtech-tierseuchen fetch gefluegelnews --delay-seconds 1
uv run govtech-tierseuchen parse gefluegelnews
uv run govtech-tierseuchen filter-disease gefluegelnews
uv run govtech-tierseuchen extract-reports gefluegelnews
```

Raw HTML and generated JSONL files are local artifacts under
`data/unstructured/<source_id>/` and are ignored by git by default.
```
```

- [ ] **Step 3: Verify docs mention source links and full text**

Run:

```bash
rg -n "source_link|fulltext|DiseaseReport|raw_html" README.md docs/superpowers/specs/2026-05-28-news-scraper-disease-report-design.md
```

Expected: Output includes all four terms.

## Task 11: Final Verification

**Files:**
- No new files.

- [ ] **Step 1: Run focused tests**

Run:

```bash
uv run pytest tests/test_gefluegelnews.py tests/test_disease_pipeline.py -v
```

Expected: all tests PASS.

- [ ] **Step 2: Run formatter if ruff is available**

Run:

```bash
uv run ruff format .
```

Expected: formatting completes successfully. If `ruff` is not installed, record that it could not be run and ask for approval before adding it.

- [ ] **Step 3: Run lint if ruff is available**

Run:

```bash
uv run ruff check .
```

Expected: lint passes. If `ruff` is not installed, record that it could not be run and ask for approval before adding it.

- [ ] **Step 4: Check git status**

Run:

```bash
git status --short
```

Expected: only planned files are changed. Generated raw HTML and JSONL outputs should not be listed.

- [ ] **Step 5: Suggested conventional commit**

If working on a feature branch, commit with:

```bash
git add .gitignore README.md pyproject.toml src/govtech_tierseuchen tests docs/superpowers/specs/2026-05-28-news-scraper-disease-report-design.md docs/superpowers/plans/2026-05-28-news-scraper-disease-report.md
git commit -m "feat(scraper): add news disease report pipeline"
```

If still on `main`, do not create a WIP commit. Ask whether to create a feature branch or commit directly.
