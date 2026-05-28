# PADI-web News Source Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add PADI-web as a second news datasource whose records flow through the existing discovery, fetch/cache, parse, disease-filter, `DiseaseReport`, and RDF export stages.

**Architecture:** Add a `padi_web` source adapter beside `gefluegelnews.py` under the current package path `code/backend/scraper/govtech_tierseuchen/`. Register the source in `config.yaml`, then refactor only the source-specific CLI stages (`discover`, `fetch`, `parse`) to dispatch by source while preserving the current config-driven parser, `config.output_path(...)`, Rich progress output, parse-error handling, downstream filtering, report extraction, and `export-rdf`.

**Tech Stack:** Python 3.13, `uv run`, standard library HTTP/JSON for the PADI adapter, existing dataclasses/JSONL helpers, `pyyaml`, `rich`, `rdflib`, pytest.

---

## Current Repo Context

The scraper package is not under `src/`. The active package path is:

- `code/backend/scraper/govtech_tierseuchen/`

The CLI is exposed through the console script:

```bash
uv run ts ...
```

`build_parser()` is config-driven:

- Commands come from `config.yaml` under `scraper.commands`.
- Source choices come from `config.yaml` under `sources`.
- Output paths should go through `config.output_path(data_dir, source, file_key)`.

Existing source stages:

- `discover`, `fetch`, and `parse` currently import `gefluegelnews` directly.
- `filter-disease`, `extract-reports`, and `export-rdf` already operate on `source` plus config output paths and should remain source-agnostic.

Existing generated Gefluegelnews artifacts are ignored. PADI adds a `raw_json/` cache directory, so `.gitignore` must be expanded.

## Source Analysis

The supplied PADI-web URL is server-rendered Django HTML that mounts a Vue `article-list` component. The useful article data is not in the initial HTML cards; the Vue bundle calls public JSON endpoints:

- List/search: `https://padi-web.cirad.fr/en/articles/api/`
- Detail: `https://padi-web.cirad.fr/en/articles/api/<article_id>/`
- Detail with sentence segmentation: `https://padi-web.cirad.fr/en/articles/api/<article_id>/?serializer=sentences`
- Detail with expanded keywords: `https://padi-web.cirad.fr/en/articles/api/<article_id>/?serializer=keywords`

On 2026-05-28, the supplied query with `published_after=2026-05-21`, `general_labels_per_task[Relevance]=1`, `is_archived=0`, and descending `published_at` returned public JSON with `count=294`. Adding `source_category=Avian Influenza` returned `count=63`. The API supports pagination via `page`, `per_page`, and `next`.

Important list/detail fields:

- `id`: PADI article identifier, e.g. `4PYSCRQ6ZV`.
- `url` / `external_id`: original publisher URL.
- `title`, `text`: PADI normalized English title/text. List `text` may be truncated.
- `sentences`: available with `serializer=sentences`; use these for full text and future evidence locators.
- `source_title`, `source_text`, `source_lang`: original-language title/text when PADI translated an article.
- `lang`, `probability_lang`: normalized language and confidence.
- `published_at`, `created_at`: publication and PADI ingestion timestamps.
- `country`, `continent`: PADI location classification.
- `source`: publisher domain.
- `rssfeed.source_category`: disease/topic category such as `Avian Influenza`.
- `machine_classification_labels`: labels such as `Relevant`, `Outbreak declaration`, `General information`, `Preventive and control measures`, `Economic and political consequences`, and sentiment.
- `keyword_synonyms`: IDs in list/detail responses; expanded metadata is available through `serializer=keywords` if needed later.

Trade-offs for v1:

- Cache PADI JSON as the raw artifact and normalize it into the existing `NewsArticle` dataclass.
- Do not fetch original publisher URLs in v1. PADI already aggregates many external hosts; direct downstream scraping would add robots, paywall, consent, parser, and security surface.
- Treat PADI labels as metadata/evidence, not ground truth. Keep local disease filtering and rule-based report extraction active so both sources are comparable.
- Keep the current `raw_html_path` field for cached JSON paths. The name is HTML-specific, but renaming it now would touch models, tests, JSONL, and RDF export. Defer a future `raw_artifact_path` cleanup.
- Use the original publisher URL as `NewsArticle.source_link` and `canonical_url`, while the manifest and cache key use the PADI API detail URL. This keeps `DiseaseReport.source_link` useful to users and RDF consumers.

## File Structure

- Create: `code/backend/scraper/govtech_tierseuchen/padi_web.py`
  - PADI API URL construction, source URL validation, paginated discovery helpers, detail fetch/cache, and `NewsArticle` normalization.
- Modify: `code/backend/scraper/govtech_tierseuchen/cli.py`
  - Add small source dispatch helpers for `discover`, `fetch`, and `parse`; keep config-driven source choices and current downstream stages.
- Modify: `config.yaml`
  - Add `sources.padi_web` with output directory and default request settings.
- Create: `tests/test_padi_web.py`
  - Fixture tests for URL construction, page parsing, URL validation, cache writing, JSON normalization, CLI config registration, fetch/parse stages, and RDF export path.
- Modify: `.gitignore`
  - Ignore `data/unstructured/*/raw_json/`.
- Modify: `code/backend/README.md`
  - Add PADI usage and output notes using `uv run ts ...`.
- Optionally modify: top-level `README.md`
  - Only if it repeats scraper source details that should mention PADI.

Generated PADI files remain local:

- `data/unstructured/padi_web/manifest.jsonl`
- `data/unstructured/padi_web/raw_json/*.json`
- `data/unstructured/padi_web/articles.jsonl`
- `data/unstructured/padi_web/parse_errors.jsonl`
- `data/unstructured/padi_web/disease_articles.jsonl`
- `data/unstructured/padi_web/disease_reports.jsonl`
- `lindas/data/rdf/padi_web/padi_web.ttl`

## Task 1: PADI Adapter Discovery Helpers

**Files:**
- Create: `code/backend/scraper/govtech_tierseuchen/padi_web.py`
- Create: `tests/test_padi_web.py`

- [ ] **Step 1: Write failing discovery tests**

Create `tests/test_padi_web.py` with:

```python
from datetime import datetime, timezone

from govtech_tierseuchen.padi_web import (
    build_articles_api_url,
    parse_article_page,
)


def test_build_articles_api_url_preserves_relevance_and_date_filters():
    url = build_articles_api_url(
        page=2,
        per_page=25,
        published_after="2026-05-21",
        source_category="Avian Influenza",
    )

    assert url.startswith("https://padi-web.cirad.fr/en/articles/api/?")
    assert "page=2" in url
    assert "per_page=25" in url
    assert "published_after=2026-05-21" in url
    assert "source_category=Avian+Influenza" in url
    assert "general_labels_per_task%5BRelevance%5D=1" in url
    assert "is_archived=0" in url
    assert "ordering=-published_at" in url


def test_parse_article_page_returns_discovered_articles_and_next_page():
    payload = {
        "count": 2,
        "next": "https://padi-web.cirad.fr/en/articles/api/?page=2&per_page=1",
        "previous": None,
        "results": [
            {
                "id": "4PYSCRQ6ZV",
                "url": "https://www.poultryworld.net/example",
                "title": "Meeting the ongoing challenge of avian influenza in the UK",
                "published_at": "2026-05-28T08:42:19",
                "rssfeed": {"source_category": "Avian Influenza"},
            },
            {
                "id": "KL8XFJ6ZOY",
                "url": "https://www.vidal.fr/example",
                "title": "West Nile virus update",
                "published_at": "2026-05-28T12:54:49",
                "rssfeed": {"source_category": "WEST NILE VIRUS"},
            },
        ],
    }

    articles, next_url = parse_article_page(
        payload,
        discovered_at=datetime(2026, 5, 28, 12, 0, tzinfo=timezone.utc),
    )

    assert next_url == "https://padi-web.cirad.fr/en/articles/api/?page=2&per_page=1"
    assert [article.source_id for article in articles] == ["padi_web", "padi_web"]
    assert articles[0].source_link == "https://padi-web.cirad.fr/en/articles/api/4PYSCRQ6ZV/"
    assert articles[0].last_modified == datetime(2026, 5, 28, 8, 42, 19, tzinfo=timezone.utc)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```bash
uv run pytest tests/test_padi_web.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'govtech_tierseuchen.padi_web'`.

- [ ] **Step 3: Implement discovery helpers**

Create `code/backend/scraper/govtech_tierseuchen/padi_web.py`:

```python
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlencode

from govtech_tierseuchen.models import DiscoveredArticle

SOURCE_ID = "padi_web"
SOURCE_NAME = "PADI-web"
BASE_URL = "https://padi-web.cirad.fr"
ARTICLES_API_URL = f"{BASE_URL}/en/articles/api/"
DEFAULT_USER_AGENT = "GovTech-Tierseuchen prototype scraper (+local research; PADI public API)"


def build_articles_api_url(
    *,
    page: int = 1,
    per_page: int = 100,
    published_after: str | None = None,
    source_category: str | None = None,
) -> str:
    params: dict[str, str | int] = {
        "page": page,
        "per_page": per_page,
        "general_labels_per_task[Relevance]": 1,
        "is_archived": 0,
        "ordering": "-published_at",
        "order_by[key]": "published_at",
        "order_by[order]": "-",
    }
    if published_after:
        params["published_after"] = published_after
    if source_category:
        params["source_category"] = source_category
    return f"{ARTICLES_API_URL}?{urlencode(params)}"


def parse_article_page(
    payload: dict[str, Any],
    discovered_at: datetime,
) -> tuple[list[DiscoveredArticle], str | None]:
    articles = []
    for row in payload.get("results", []):
        article_id = str(row["id"])
        articles.append(
            DiscoveredArticle(
                source_id=SOURCE_ID,
                source_name=SOURCE_NAME,
                source_link=f"{ARTICLES_API_URL}{article_id}/",
                discovered_at=discovered_at,
                last_modified=_parse_padi_datetime(row.get("published_at")),
            )
        )
    return articles, payload.get("next")


def _parse_padi_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed
```

- [ ] **Step 4: Run discovery tests**

Run:

```bash
uv run pytest tests/test_padi_web.py -v
```

Expected: PASS.

## Task 2: PADI Detail Fetch, Validation, And Cache

**Files:**
- Modify: `code/backend/scraper/govtech_tierseuchen/padi_web.py`
- Modify: `tests/test_padi_web.py`

- [ ] **Step 1: Write failing cache and validation tests**

Append to `tests/test_padi_web.py`:

```python
from pathlib import Path

from govtech_tierseuchen.padi_web import (
    cache_article_json,
    fetch_and_cache_article,
    raw_json_path,
)


def test_raw_json_path_uses_padi_article_id(tmp_path):
    path = raw_json_path(tmp_path, "https://padi-web.cirad.fr/en/articles/api/4PYSCRQ6ZV/")

    assert path == tmp_path / "padi_web" / "raw_json" / "4PYSCRQ6ZV.json"


def test_cache_article_json_writes_payload_and_hash(tmp_path):
    fetched = cache_article_json(
        base_dir=tmp_path,
        source_link="https://padi-web.cirad.fr/en/articles/api/4PYSCRQ6ZV/",
        payload={"id": "4PYSCRQ6ZV", "title": "Example"},
        status_code=200,
        fetched_at=datetime(2026, 5, 28, 12, 0, tzinfo=timezone.utc),
    )

    raw_path = Path(fetched.raw_html_path)
    assert raw_path.exists()
    assert raw_path.read_text(encoding="utf-8").startswith("{")
    assert fetched.source_id == "padi_web"
    assert fetched.canonical_url == "https://padi-web.cirad.fr/en/articles/api/4PYSCRQ6ZV/"
    assert fetched.content_hash


def test_fetch_and_cache_article_rejects_non_padi_api_url(tmp_path):
    fetched = fetch_and_cache_article(
        base_dir=tmp_path,
        source_link="file:///etc/passwd",
        fetched_at=datetime(2026, 5, 28, 12, 0, tzinfo=timezone.utc),
        timeout_seconds=1,
        delay_seconds=0,
    )

    assert fetched.error_type == "InvalidSourceUrl"
    assert "padi-web.cirad.fr" in fetched.message
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```bash
uv run pytest tests/test_padi_web.py -v
```

Expected: FAIL with missing `cache_article_json`, `raw_json_path`, or `fetch_and_cache_article`.

- [ ] **Step 3: Implement fetch/cache helpers**

Add to `code/backend/scraper/govtech_tierseuchen/padi_web.py`:

```python
import hashlib
import json
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from govtech_tierseuchen.models import FetchedArticle, FetchError


def article_id_from_source_link(source_link: str) -> str:
    return urlparse(source_link).path.rstrip("/").rsplit("/", 1)[-1]


def raw_json_path(base_dir: Path, source_link: str) -> Path:
    return base_dir / SOURCE_ID / "raw_json" / f"{article_id_from_source_link(source_link)}.json"


def fetch_json(
    source_link: str,
    timeout_seconds: float,
    user_agent: str = DEFAULT_USER_AGENT,
) -> tuple[int, dict[str, Any]]:
    request = Request(
        source_link,
        headers={"User-Agent": user_agent, "Accept": "application/json"},
    )
    with urlopen(request, timeout=timeout_seconds) as response:
        status = getattr(response, "status", 200)
        data = response.read()
    return status, json.loads(data.decode("utf-8"))


def cache_article_json(
    base_dir: Path,
    source_link: str,
    payload: dict[str, Any],
    status_code: int,
    fetched_at: datetime,
) -> FetchedArticle:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    path = raw_json_path(base_dir, source_link)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encoded)
    return FetchedArticle(
        source_id=SOURCE_ID,
        source_name=SOURCE_NAME,
        source_link=source_link,
        fetched_at=fetched_at,
        status_code=status_code,
        raw_html_path=str(path),
        content_hash=hashlib.sha256(encoded).hexdigest(),
        canonical_url=payload.get("url") or source_link,
    )


def fetch_and_cache_article(
    base_dir: Path,
    source_link: str,
    fetched_at: datetime,
    timeout_seconds: float,
    delay_seconds: float,
) -> FetchedArticle | FetchError:
    validation_error = _validate_article_source_link(source_link)
    if validation_error is not None:
        return FetchError(
            source_link=source_link,
            error_type="InvalidSourceUrl",
            message=validation_error,
            occurred_at=fetched_at,
        )
    try:
        status, payload = fetch_json(
            f"{source_link}?serializer=sentences",
            timeout_seconds=timeout_seconds,
        )
        fetched = cache_article_json(base_dir, source_link, payload, status, fetched_at)
        if delay_seconds > 0:
            time.sleep(delay_seconds)
        return fetched
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        return FetchError(
            source_link=source_link,
            error_type=type(exc).__name__,
            message=str(exc),
            occurred_at=fetched_at,
        )


def _validate_article_source_link(source_link: str) -> str | None:
    parsed = urlparse(source_link)
    requirement = (
        "PADI-web article API URLs must use https, be hosted on "
        "padi-web.cirad.fr, and use the /en/articles/api/<id>/ path."
    )
    if parsed.scheme != "https":
        return requirement
    if parsed.netloc != "padi-web.cirad.fr":
        return requirement
    if not parsed.path.startswith("/en/articles/api/"):
        return requirement
    if not article_id_from_source_link(source_link):
        return requirement
    return None
```

- [ ] **Step 4: Run cache and validation tests**

Run:

```bash
uv run pytest tests/test_padi_web.py -v
```

Expected: PASS.

## Task 3: Normalize PADI JSON To NewsArticle

**Files:**
- Modify: `code/backend/scraper/govtech_tierseuchen/padi_web.py`
- Modify: `tests/test_padi_web.py`

- [ ] **Step 1: Write failing parser test**

Append to `tests/test_padi_web.py`:

```python
from govtech_tierseuchen.padi_web import parse_article_payload


def test_parse_article_payload_normalizes_detail_json_to_news_article(tmp_path):
    raw_path = tmp_path / "padi_web" / "raw_json" / "4PYSCRQ6ZV.json"
    payload = {
        "id": "4PYSCRQ6ZV",
        "title": "Meeting the ongoing challenge of avian influenza in the UK",
        "text": "Short list text",
        "sentences": [
            {"computed_text": "The UK has suffered its third worst outbreak of HPAI."},
            {"computed_text": "More than 3.8 million birds have been culled or died."},
        ],
        "url": "https://www.poultryworld.net/health/example/",
        "source": "www.poultryworld.net",
        "published_at": "2026-05-28T08:42:19",
        "created_at": "2026-05-28T16:35:14.562107",
        "country": "GB",
        "continent": "EU",
        "lang": "EN",
        "source_lang": None,
        "rssfeed": {"source_category": "Avian Influenza", "name": "AVIAN_INFLUENZA3_EN"},
        "machine_classification_labels": [
            {"name_en": "Relevant", "task": 1},
            {"name_en": "Outbreak declaration", "task": 3},
        ],
    }

    article = parse_article_payload(
        payload=payload,
        source_link="https://padi-web.cirad.fr/en/articles/api/4PYSCRQ6ZV/",
        raw_json_path=raw_path,
        content_hash="abc123",
        retrieved_at=datetime(2026, 5, 28, 17, 0, tzinfo=timezone.utc),
    )

    assert article.source_id == "padi_web"
    assert article.source_name == "PADI-web"
    assert article.source_link == "https://www.poultryworld.net/health/example/"
    assert article.canonical_url == "https://www.poultryworld.net/health/example/"
    assert article.publication_date.isoformat() == "2026-05-28"
    assert article.category == "Avian Influenza"
    assert article.author == "www.poultryworld.net"
    assert article.keywords == [
        "Relevant",
        "Outbreak declaration",
        "country:GB",
        "continent:EU",
        "lang:EN",
    ]
    assert article.fulltext == (
        "# Meeting the ongoing challenge of avian influenza in the UK\n\n"
        "The UK has suffered its third worst outbreak of HPAI.\n\n"
        "More than 3.8 million birds have been culled or died."
    )
    assert article.raw_html_path == str(raw_path)
```

- [ ] **Step 2: Run the parser test to verify it fails**

Run:

```bash
uv run pytest tests/test_padi_web.py::test_parse_article_payload_normalizes_detail_json_to_news_article -v
```

Expected: FAIL with missing `parse_article_payload`.

- [ ] **Step 3: Implement parser**

Add to `code/backend/scraper/govtech_tierseuchen/padi_web.py`:

```python
from datetime import date

from govtech_tierseuchen.models import NewsArticle


def parse_article_payload(
    payload: dict[str, Any],
    source_link: str,
    raw_json_path: Path,
    content_hash: str,
    retrieved_at: datetime,
) -> NewsArticle:
    title = str(payload.get("title") or payload.get("source_title") or "").strip()
    if not title:
        raise ValueError(f"Could not parse PADI article title from {source_link}")
    canonical_url = str(payload.get("url") or payload.get("external_id") or source_link)
    country = payload.get("country")
    continent = payload.get("continent")
    lang = payload.get("lang")
    keywords = [
        *_label_names(payload.get("machine_classification_labels", [])),
        *([f"country:{country}"] if country else []),
        *([f"continent:{continent}"] if continent else []),
        *([f"lang:{lang}"] if lang else []),
    ]
    rssfeed = payload.get("rssfeed") if isinstance(payload.get("rssfeed"), dict) else {}
    return NewsArticle(
        source_id=SOURCE_ID,
        source_name=SOURCE_NAME,
        source_link=canonical_url,
        canonical_url=canonical_url,
        title=title,
        description=_clean_html_description(payload.get("description")),
        keywords=keywords,
        publication_date=_parse_padi_date(payload.get("published_at")),
        retrieved_at=retrieved_at,
        category=rssfeed.get("source_category"),
        author=payload.get("source"),
        image_url=None,
        image_credit=None,
        source_attribution=f"PADI-web article {payload.get('id')} from {payload.get('source')}",
        partner_content=None,
        fulltext=_to_markdown(title, payload),
        raw_html_path=str(raw_json_path),
        content_hash=content_hash,
    )


def _label_names(labels: list[dict[str, Any]]) -> list[str]:
    names = []
    for label in labels:
        name = label.get("name_en") or label.get("name")
        if name and name not in names:
            names.append(str(name))
    return names


def _parse_padi_date(value: str | None) -> date | None:
    parsed = _parse_padi_datetime(value)
    return parsed.date() if parsed else None


def _to_markdown(title: str, payload: dict[str, Any]) -> str:
    sentence_texts = [
        str(sentence.get("computed_text", "")).strip()
        for sentence in payload.get("sentences", [])
        if str(sentence.get("computed_text", "")).strip()
    ]
    body = sentence_texts or [str(payload.get("text", "")).strip()]
    return "\n\n".join([f"# {title}", *[part for part in body if part]])


def _clean_html_description(value: str | None) -> str | None:
    if not value:
        return None
    return " ".join(str(value).replace("\n", " ").split())
```

- [ ] **Step 4: Run parser tests**

Run:

```bash
uv run pytest tests/test_padi_web.py -v
```

Expected: PASS.

## Task 4: Register Source In Config And CLI Parser

**Files:**
- Modify: `config.yaml`
- Modify: `tests/test_padi_web.py`

- [ ] **Step 1: Write failing config/CLI test**

Append to `tests/test_padi_web.py`:

```python
from govtech_tierseuchen.cli import build_parser
from govtech_tierseuchen.config import load_config


def test_config_and_cli_parser_accept_padi_web_source():
    config = load_config()
    assert config.sources["padi_web"].output_dir == "padi_web"

    parser = build_parser(config)
    args = parser.parse_args(
        ["discover", "padi_web", "--data-dir", "data/unstructured", "--limit", "10"]
    )

    assert args.command == "discover"
    assert args.source == "padi_web"
    assert args.limit == 10
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
uv run pytest tests/test_padi_web.py::test_config_and_cli_parser_accept_padi_web_source -v
```

Expected: FAIL with `KeyError: 'padi_web'` or parser source-choice rejection.

- [ ] **Step 3: Add PADI source config**

Modify `config.yaml`:

```yaml
sources:
  gefluegelnews:
    output_dir: gefluegelnews
    timeout_seconds: 20.0
    delay_seconds: 1.0
    limit:
  padi_web:
    output_dir: padi_web
    timeout_seconds: 20.0
    delay_seconds: 0.5
    limit:
```

Do not hardcode source choices in `build_parser()`. It already uses `choices=sorted(config.sources)`.

- [ ] **Step 4: Run the config/CLI test**

Run:

```bash
uv run pytest tests/test_padi_web.py::test_config_and_cli_parser_accept_padi_web_source -v
```

Expected: PASS.

## Task 5: Source Dispatch For Discover, Fetch, And Parse

**Files:**
- Modify: `code/backend/scraper/govtech_tierseuchen/cli.py`
- Modify: `tests/test_padi_web.py`

- [ ] **Step 1: Write failing CLI stage tests**

Append to `tests/test_padi_web.py`:

```python
import json

from govtech_tierseuchen.cli import main
from govtech_tierseuchen.jsonl import read_jsonl, write_jsonl
from govtech_tierseuchen.models import FetchedArticle


def test_padi_discover_stage_writes_limited_manifest(monkeypatch, tmp_path):
    payload = {
        "next": None,
        "results": [
            {"id": "AAA111", "published_at": "2026-05-28T08:42:19"},
            {"id": "BBB222", "published_at": "2026-05-28T09:42:19"},
        ],
    }

    def fake_fetch_json(source_link, timeout_seconds):
        return 200, payload

    monkeypatch.setattr("govtech_tierseuchen.padi_web.fetch_json", fake_fetch_json)

    exit_code = main(["discover", "padi_web", "--data-dir", str(tmp_path), "--limit", "1"])

    rows = read_jsonl(tmp_path / "padi_web" / "manifest.jsonl")
    assert exit_code == 0
    assert len(rows) == 1
    assert rows[0]["source_link"] == "https://padi-web.cirad.fr/en/articles/api/AAA111/"


def test_padi_fetch_stage_uses_padi_adapter(monkeypatch, tmp_path):
    calls = []
    write_jsonl(
        tmp_path / "padi_web" / "manifest.jsonl",
        [{"source_link": "https://padi-web.cirad.fr/en/articles/api/AAA111/"}],
    )

    def fake_fetch_and_cache_article(
        base_dir,
        source_link,
        fetched_at,
        timeout_seconds,
        delay_seconds,
    ):
        calls.append(source_link)
        return FetchedArticle(
            source_id="padi_web",
            source_name="PADI-web",
            source_link=source_link,
            fetched_at=fetched_at,
            status_code=200,
            raw_html_path=str(base_dir / "padi_web" / "raw_json" / "AAA111.json"),
            content_hash="abc123",
            canonical_url="https://publisher.example/article",
        )

    monkeypatch.setattr(
        "govtech_tierseuchen.padi_web.fetch_and_cache_article",
        fake_fetch_and_cache_article,
    )

    exit_code = main(["fetch", "padi_web", "--data-dir", str(tmp_path), "--delay-seconds", "0"])

    rows = read_jsonl(tmp_path / "padi_web" / "manifest.jsonl")
    assert exit_code == 0
    assert calls == ["https://padi-web.cirad.fr/en/articles/api/AAA111/"]
    assert rows[0]["status_code"] == 200
    assert rows[0]["canonical_url"] == "https://publisher.example/article"


def test_padi_parse_stage_reads_cached_json_and_writes_articles(tmp_path):
    raw_dir = tmp_path / "padi_web" / "raw_json"
    raw_dir.mkdir(parents=True)
    raw_path = raw_dir / "AAA111.json"
    raw_path.write_text(
        json.dumps(
            {
                "id": "AAA111",
                "title": "Avian influenza report",
                "sentences": [{"computed_text": "HPAI outbreak in the UK."}],
                "url": "https://publisher.example/article",
                "source": "publisher.example",
                "published_at": "2026-05-28T08:42:19",
                "rssfeed": {"source_category": "Avian Influenza"},
                "machine_classification_labels": [{"name_en": "Relevant"}],
            }
        ),
        encoding="utf-8",
    )
    write_jsonl(
        tmp_path / "padi_web" / "manifest.jsonl",
        [
            {
                "source_link": "https://padi-web.cirad.fr/en/articles/api/AAA111/",
                "raw_html_path": str(raw_path),
                "content_hash": "abc123",
                "fetched_at": "2026-05-28T12:00:00+00:00",
            }
        ],
    )

    exit_code = main(["parse", "padi_web", "--data-dir", str(tmp_path)])

    articles = read_jsonl(tmp_path / "padi_web" / "articles.jsonl")
    parse_errors = read_jsonl(tmp_path / "padi_web" / "parse_errors.jsonl")
    assert exit_code == 0
    assert articles[0]["source_id"] == "padi_web"
    assert articles[0]["source_link"] == "https://publisher.example/article"
    assert "HPAI outbreak" in articles[0]["fulltext"]
    assert parse_errors == []
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```bash
uv run pytest tests/test_padi_web.py -v
```

Expected: discovery/fetch/parse stage tests fail because `cli.py` still imports Gefluegelnews unconditionally.

- [ ] **Step 3: Add source dispatch helpers without changing config-driven parser**

Modify `code/backend/scraper/govtech_tierseuchen/cli.py`.

Add imports near the existing imports:

```python
import json
from typing import Any, Callable
```

Add helper functions above `_discover`:

```python
def _fetcher_for_source(source: str) -> Callable[..., Any]:
    if source == "gefluegelnews":
        from govtech_tierseuchen.gefluegelnews import fetch_and_cache_article

        return fetch_and_cache_article
    if source == "padi_web":
        from govtech_tierseuchen.padi_web import fetch_and_cache_article

        return fetch_and_cache_article
    raise ValueError(f"Unsupported source: {source}")


def _parse_row_for_source(source: str, row: dict, raw_path: Path):
    retrieved_at = datetime.fromisoformat(
        row.get("fetched_at", datetime.now(UTC).isoformat())
    )
    if source == "gefluegelnews":
        from govtech_tierseuchen.gefluegelnews import parse_article_html

        html = raw_path.read_text(encoding="utf-8")
        return parse_article_html(
            html=html,
            source_link=row["source_link"],
            raw_html_path=raw_path,
            content_hash=row.get("content_hash", ""),
            retrieved_at=retrieved_at,
        )
    if source == "padi_web":
        from govtech_tierseuchen.padi_web import parse_article_payload

        payload = json.loads(raw_path.read_text(encoding="utf-8"))
        return parse_article_payload(
            payload=payload,
            source_link=row["source_link"],
            raw_json_path=raw_path,
            content_hash=row.get("content_hash", ""),
            retrieved_at=retrieved_at,
        )
    raise ValueError(f"Unsupported source: {source}")
```

Replace `_discover(...)` with source-aware behavior that preserves `config.output_path(...)` and the current console output:

```python
def _discover(
    data_dir: Path,
    source: str,
    timeout_seconds: float,
    console: Console,
    config: AppConfig,
) -> int:
    from govtech_tierseuchen.jsonl import write_jsonl

    if source == "gefluegelnews":
        from govtech_tierseuchen.gefluegelnews import (
            SITEMAP_URL,
            fetch_url,
            parse_sitemap_articles,
        )

        _, xml = fetch_url(SITEMAP_URL, timeout_seconds=timeout_seconds)
        articles = parse_sitemap_articles(
            xml.encode("utf-8"), discovered_at=datetime.now(UTC)
        )
    elif source == "padi_web":
        from govtech_tierseuchen.padi_web import (
            build_articles_api_url,
            fetch_json,
            parse_article_page,
        )

        articles = []
        next_url: str | None = build_articles_api_url()
        while next_url:
            _, payload = fetch_json(next_url, timeout_seconds=timeout_seconds)
            page_articles, next_url = parse_article_page(
                payload, discovered_at=datetime.now(UTC)
            )
            articles.extend(page_articles)
    else:
        raise ValueError(f"Unsupported source: {source}")

    write_jsonl(config.output_path(data_dir, source, "manifest"), articles)
    console.print(f"[green]Discovered {len(articles)} {source} article URLs[/green]")
    return 0
```

In `_fetch(...)`, replace the direct Gefluegelnews import and call:

```python
fetch_and_cache_article = _fetcher_for_source(source)
```

Keep the existing loop, progress bar, merge logic, and manifest write.

In `_parse(...)`, remove the direct `parse_article_html` import and replace the body of the `try` block with:

```python
parsed.append(_parse_row_for_source(source, row, raw_html_path))
```

Keep the existing `ParseError` write behavior.

- [ ] **Step 4: Run source stage tests**

Run:

```bash
uv run pytest tests/test_gefluegelnews.py tests/test_padi_web.py -v
```

Expected: PASS.

## Task 6: PADI Through Downstream Pipeline And RDF Export

**Files:**
- Modify: `tests/test_padi_web.py`
- Modify: `code/backend/scraper/govtech_tierseuchen/cli.py` only if tests expose a source-specific assumption.

- [ ] **Step 1: Add downstream pipeline and RDF export tests**

Append to `tests/test_padi_web.py`:

```python
def test_padi_articles_flow_through_filter_extract_and_export_rdf(tmp_path):
    write_jsonl(
        tmp_path / "padi_web" / "articles.jsonl",
        [
            {
                "source_id": "padi_web",
                "source_name": "PADI-web",
                "source_link": "https://publisher.example/article",
                "canonical_url": "https://publisher.example/article",
                "title": "HPAI outbreak in Poland",
                "description": None,
                "keywords": ["Relevant", "Outbreak declaration"],
                "publication_date": "2026-05-28",
                "retrieved_at": "2026-05-28T12:00:00+00:00",
                "category": "Avian Influenza",
                "author": "publisher.example",
                "image_url": None,
                "image_credit": None,
                "source_attribution": "PADI-web article AAA111 from publisher.example",
                "partner_content": None,
                "fulltext": "# HPAI outbreak in Poland\n\nHPAI outbreak in Poland led to restriction zones.",
                "raw_html_path": "raw.json",
                "content_hash": "abc123",
            }
        ],
    )

    data_dir = tmp_path
    rdf_dir = tmp_path / "lindas" / "data" / "rdf"
    assert main(["filter-disease", "padi_web", "--data-dir", str(data_dir)]) == 0
    assert main(["extract-reports", "padi_web", "--data-dir", str(data_dir)]) == 0
    assert (
        main(
            [
                "export-rdf",
                "padi_web",
                "--data-dir",
                str(data_dir),
                "--rdf-dir",
                str(rdf_dir),
            ]
        )
        == 0
    )

    disease_articles = read_jsonl(tmp_path / "padi_web" / "disease_articles.jsonl")
    reports = read_jsonl(tmp_path / "padi_web" / "disease_reports.jsonl")
    assert len(disease_articles) == 1
    assert reports[0]["source_id"] == "padi_web"
    assert reports[0]["source_link"] == "https://publisher.example/article"
    assert (rdf_dir / "padi_web" / "padi_web.ttl").exists()
```

- [ ] **Step 2: Run downstream tests**

Run:

```bash
uv run pytest tests/test_padi_web.py tests/test_disease_pipeline.py tests/test_rdf_export.py -v
```

Expected: PASS.

## Task 7: Ignore Files And Documentation

**Files:**
- Modify: `.gitignore`
- Modify: `code/backend/README.md`
- Optionally modify: `README.md`

- [ ] **Step 1: Ignore PADI raw JSON caches**

Add to `.gitignore`:

```gitignore
data/unstructured/*/raw_json/
```

Do not remove existing Gefluegelnews artifact rules.

- [ ] **Step 2: Update backend README**

In `code/backend/README.md`, change the source description to:

```markdown
Prototype news-ingestion pipeline for animal disease screening. The current
source adapters are `gefluegelnews` and `padi_web`.
```

Add PADI commands after the Gefluegelnews commands:

```bash
uv run ts discover padi_web
uv run ts fetch padi_web --limit 100 --delay-seconds 0.5
uv run ts parse padi_web
uv run ts filter-disease padi_web
uv run ts extract-reports padi_web
uv run ts export-rdf padi_web
```

Update output notes to mention:

```markdown
PADI-web additionally caches API detail payloads under `raw_json/`.
Finalized RDF export files are written under `lindas/data/rdf/<source>/`,
for example `lindas/data/rdf/padi_web/padi_web.ttl`.
```

- [ ] **Step 3: Update top-level README only if needed**

If top-level `README.md` lists only Gefluegelnews as the scraper source, add a one-line mention of `padi_web` and use `uv run ts`, not `uv run govtech-tierseuchen`.

- [ ] **Step 4: Run formatting, lint, and tests**

Run:

```bash
uv run ruff format code/backend/scraper tests
uv run ruff check code/backend/scraper tests
uv run pytest
```

Expected: all pass.

## Self-Review Checklist

- The plan uses the active package path `code/backend/scraper/govtech_tierseuchen/`.
- The plan does not hardcode parser source choices; it registers `padi_web` through `config.yaml`.
- Existing `gefluegelnews` tests remain expected to pass.
- PADI fetch validates the API URL before network access.
- PADI parse reads cached JSON, not HTML.
- Downstream `filter-disease`, `extract-reports`, and `export-rdf` use the existing source-agnostic paths.
- README examples use `uv run ts`.
- `.gitignore` ignores `raw_json/`.

## Suggested Commit

```bash
git add code/backend/scraper/govtech_tierseuchen/padi_web.py code/backend/scraper/govtech_tierseuchen/cli.py config.yaml tests/test_padi_web.py .gitignore code/backend/README.md README.md docs/superpowers/plans/2026-05-28-padi-web-news-source.md
git commit -m "feat(scraper): add PADI-web source"
```
