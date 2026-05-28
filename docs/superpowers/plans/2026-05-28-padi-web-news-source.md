# PADI-web News Source Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add PADI-web as a second news datasource whose records flow through the same discovery, fetch/cache, parse, disease-filter, and `DiseaseReport` candidate stages as Gefluegelnews.

**Architecture:** Implement a `padi_web` source adapter beside `gefluegelnews.py`, using PADI-web's public JSON API instead of rendered HTML scraping. Discovery pages the `/en/articles/api/` endpoint with configured search parameters, fetch caches each article detail JSON under `data/unstructured/padi_web/raw_json/`, and parse normalizes cached JSON into the existing `NewsArticle` dataclass so downstream filtering and extraction can remain source-agnostic.

**Tech Stack:** Python 3.13, `uv run`, standard library only, dataclasses, `urllib.request`, JSON, JSONL, pytest fixture tests.

---

## Source Analysis

The supplied page is server-rendered Django HTML that mounts a Vue `article-list` component. The useful article data is not in the initial card markup; the Vue bundle calls these public JSON endpoints:

- List/search: `https://padi-web.cirad.fr/en/articles/api/`
- Detail: `https://padi-web.cirad.fr/en/articles/api/<article_id>/`
- Detail with sentence segmentation: `https://padi-web.cirad.fr/en/articles/api/<article_id>/?serializer=sentences`
- Detail with expanded keywords: `https://padi-web.cirad.fr/en/articles/api/<article_id>/?serializer=keywords`

The supplied query with `published_after=2026-05-21`, `general_labels_per_task[Relevance]=1`, `is_archived=0`, and descending `published_at` returned public JSON with `count=294` on 2026-05-28. Filtering `source_category=Avian Influenza` returned `count=63`. The API supports pagination via `page`, `per_page`, and `next`.

Important fields in list/detail results:

- `id`: PADI article identifier, e.g. `4PYSCRQ6ZV`.
- `url` / `external_id`: original publisher URL.
- `title`, `text`: PADI normalized English title/text. List `text` may be truncated; detail with `serializer=sentences` returns full sentence records.
- `source_title`, `source_text`, `source_lang`: original-language title/text when PADI has translated the article.
- `lang`, `probability_lang`: normalized language and confidence.
- `published_at`, `created_at`: publication and PADI ingestion timestamps.
- `country`, `continent`: PADI location classification.
- `source`: publisher domain.
- `rssfeed.source_category`: disease/topic category such as `Avian Influenza`.
- `machine_classification_labels`: includes labels such as `Relevant`, `Outbreak declaration`, `General information`, `Preventive and control measures`, `Economic and political consequences`, and sentiment.
- `keyword_synonyms`: IDs in list/detail responses; expanded keyword metadata is available via `serializer=keywords`.
- `sentences`: only present with `serializer=sentences`; useful for evidence locators.

Trade-offs:

- Use PADI normalized JSON as the source artifact for v1. This avoids fragile scraping of many downstream publisher layouts and still preserves original publisher URL in `source_link`.
- Do not call original publisher URLs in v1. That would add many external hosts, paywall/consent variability, robots concerns, and more parser work.
- Treat PADI labels as metadata/evidence, not ground truth. Keep the local disease filter and report extraction stages active so PADI and Gefluegelnews are comparable.
- The existing `NewsArticle.raw_html_path` field is HTML-named. For the smallest source-agnostic change, store the cached PADI JSON path there for now and document it in tests. A later model cleanup can rename this to `raw_artifact_path`.

## File Structure

- Create: `src/govtech_tierseuchen/padi_web.py`
  - PADI API URL construction, paginated discovery, detail fetch/cache, JSON parsing, and `NewsArticle` normalization.
- Modify: `src/govtech_tierseuchen/cli.py`
  - Accept `padi_web` as a source and dispatch source-specific `discover`, `fetch`, and `parse` handlers.
- Create: `tests/test_padi_web.py`
  - Local fixture tests for API page parsing, cache file naming, detail normalization, and CLI source acceptance.
- Modify: `.gitignore`
  - Ignore generated `data/unstructured/padi_web/` cache and JSONL outputs if not already covered.
- Modify later if implementation exposes usage: `README.md`
  - Add concise PADI-web CLI examples after tests pass.

Generated files remain local:

- `data/unstructured/padi_web/manifest.jsonl`
- `data/unstructured/padi_web/raw_json/*.json`
- `data/unstructured/padi_web/articles.jsonl`
- `data/unstructured/padi_web/disease_articles.jsonl`
- `data/unstructured/padi_web/disease_reports.jsonl`

## Task 1: PADI Discovery From API Pages

**Files:**
- Create: `src/govtech_tierseuchen/padi_web.py`
- Create: `tests/test_padi_web.py`

- [ ] **Step 1: Write the failing discovery tests**

Add to `tests/test_padi_web.py`:

```python
from datetime import datetime, timezone

from govtech_tierseuchen.padi_web import build_articles_api_url, parse_article_page


def test_build_articles_api_url_preserves_relevance_and_date_filters():
    url = build_articles_api_url(page=2, per_page=25, published_after="2026-05-21")

    assert url.startswith("https://padi-web.cirad.fr/en/articles/api/?")
    assert "page=2" in url
    assert "per_page=25" in url
    assert "published_after=2026-05-21" in url
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

- [ ] **Step 3: Implement minimal discovery helpers**

Create `src/govtech_tierseuchen/padi_web.py`:

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

- [ ] **Step 4: Run the discovery tests**

Run:

```bash
uv run pytest tests/test_padi_web.py -v
```

Expected: PASS.

## Task 2: PADI Detail Fetch And Cache

**Files:**
- Modify: `src/govtech_tierseuchen/padi_web.py`
- Modify: `tests/test_padi_web.py`

- [ ] **Step 1: Write failing cache tests**

Append to `tests/test_padi_web.py`:

```python
from pathlib import Path

from govtech_tierseuchen.padi_web import cache_article_json, raw_json_path


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
    assert fetched.content_hash
```

- [ ] **Step 2: Run the cache tests to verify they fail**

Run:

```bash
uv run pytest tests/test_padi_web.py -v
```

Expected: FAIL with missing `cache_article_json` / `raw_json_path`.

- [ ] **Step 3: Implement JSON fetch/cache helpers**

Add to `src/govtech_tierseuchen/padi_web.py`:

```python
import hashlib
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from govtech_tierseuchen.models import FetchedArticle, FetchError


def article_id_from_source_link(source_link: str) -> str:
    path = urlparse(source_link).path.rstrip("/")
    return path.rsplit("/", 1)[-1]


def raw_json_path(base_dir: Path, source_link: str) -> Path:
    return base_dir / SOURCE_ID / "raw_json" / f"{article_id_from_source_link(source_link)}.json"


def fetch_json(source_link: str, timeout_seconds: float, user_agent: str = DEFAULT_USER_AGENT) -> tuple[int, dict[str, Any]]:
    request = Request(source_link, headers={"User-Agent": user_agent, "Accept": "application/json"})
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
) -> FetchedArticle | FetchError:
    try:
        status, payload = fetch_json(f"{source_link}?serializer=sentences", timeout_seconds=timeout_seconds)
        return cache_article_json(base_dir, source_link, payload, status, fetched_at)
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        return FetchError(
            source_link=source_link,
            error_type=type(exc).__name__,
            message=str(exc),
            occurred_at=fetched_at,
        )
```

- [ ] **Step 4: Run the cache tests**

Run:

```bash
uv run pytest tests/test_padi_web.py -v
```

Expected: PASS.

## Task 3: Normalize PADI JSON To NewsArticle

**Files:**
- Modify: `src/govtech_tierseuchen/padi_web.py`
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
    assert article.keywords == ["Relevant", "Outbreak declaration", "country:GB", "continent:EU", "lang:EN"]
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

Add to `src/govtech_tierseuchen/padi_web.py`:

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
    labels = _label_names(payload.get("machine_classification_labels", []))
    country = payload.get("country")
    continent = payload.get("continent")
    lang = payload.get("lang")
    keywords = [
        *labels,
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

- [ ] **Step 4: Run the parser tests**

Run:

```bash
uv run pytest tests/test_padi_web.py -v
```

Expected: PASS.

## Task 4: CLI Source Dispatch

**Files:**
- Modify: `src/govtech_tierseuchen/cli.py`
- Modify: `tests/test_padi_web.py`

- [ ] **Step 1: Write failing CLI test**

Append to `tests/test_padi_web.py`:

```python
from govtech_tierseuchen.cli import build_parser


def test_cli_parser_accepts_padi_web_source():
    parser = build_parser()
    args = parser.parse_args(["discover", "padi_web", "--data-dir", "data/unstructured", "--limit", "10"])

    assert args.command == "discover"
    assert args.source == "padi_web"
    assert args.limit == 10
```

- [ ] **Step 2: Run the CLI test to verify it fails**

Run:

```bash
uv run pytest tests/test_padi_web.py::test_cli_parser_accepts_padi_web_source -v
```

Expected: FAIL because `padi_web` is not an accepted source.

- [ ] **Step 3: Refactor CLI dispatch by source**

Modify `src/govtech_tierseuchen/cli.py` so:

```python
subparser.add_argument("source", choices=["gefluegelnews", "padi_web"])
subparser.add_argument("--published-after", default=None)
subparser.add_argument("--source-category", default=None)
```

Then update command dispatch:

```python
if args.command == "discover":
    return _discover(args.source, data_dir, args.timeout_seconds, args.limit, args.published_after, args.source_category)
if args.command == "fetch":
    return _fetch(args.source, data_dir, args.timeout_seconds, args.delay_seconds, args.limit)
if args.command == "parse":
    return _parse(args.source, data_dir, args.limit)
if args.command == "filter-disease":
    return _filter_disease(args.source, data_dir)
if args.command == "extract-reports":
    return _extract_reports(args.source, data_dir)
```

Implement source branches with current Gefluegelnews behavior preserved and PADI-web behavior added:

```python
def _discover(
    source: str,
    data_dir: Path,
    timeout_seconds: float,
    limit: int | None,
    published_after: str | None,
    source_category: str | None,
) -> int:
    from govtech_tierseuchen.jsonl import write_jsonl

    if source == "gefluegelnews":
        from govtech_tierseuchen.gefluegelnews import SITEMAP_URL, fetch_url, parse_sitemap_articles

        _, xml = fetch_url(SITEMAP_URL, timeout_seconds=timeout_seconds)
        articles = parse_sitemap_articles(xml.encode("utf-8"), discovered_at=datetime.now(UTC))
        write_jsonl(data_dir / source / "manifest.jsonl", articles if limit is None else articles[:limit])
        return 0

    if source == "padi_web":
        from govtech_tierseuchen.padi_web import build_articles_api_url, fetch_json, parse_article_page

        discovered = []
        next_url: str | None = build_articles_api_url(
            page=1,
            per_page=100,
            published_after=published_after,
            source_category=source_category,
        )
        while next_url and (limit is None or len(discovered) < limit):
            _, payload = fetch_json(next_url, timeout_seconds=timeout_seconds)
            articles, next_url = parse_article_page(payload, discovered_at=datetime.now(UTC))
            discovered.extend(articles)
        write_jsonl(data_dir / source / "manifest.jsonl", discovered if limit is None else discovered[:limit])
        return 0

    raise ValueError(f"Unsupported source: {source}")
```

Apply the same source-branching pattern in `_fetch`, `_parse`, `_filter_disease`, and `_extract_reports`, with the latter two reading/writing `data_dir / source / ...` instead of hardcoded `gefluegelnews`.

- [ ] **Step 4: Run CLI tests**

Run:

```bash
uv run pytest tests/test_gefluegelnews.py tests/test_padi_web.py -v
```

Expected: PASS.

## Task 5: End-To-End Local Fixture Coverage

**Files:**
- Modify: `tests/test_padi_web.py`
- Modify: `src/govtech_tierseuchen/cli.py` only if the test exposes wiring gaps.

- [ ] **Step 1: Add a narrow fixture-style pipeline test**

Append to `tests/test_padi_web.py`:

```python
import json

from govtech_tierseuchen.jsonl import read_jsonl, write_jsonl
from govtech_tierseuchen.padi_web import cache_article_json, parse_article_payload


def test_padi_cached_json_can_be_written_to_articles_jsonl(tmp_path):
    payload = {
        "id": "4PYSCRQ6ZV",
        "title": "Meeting the ongoing challenge of avian influenza in the UK",
        "sentences": [{"computed_text": "The UK has suffered an outbreak of HPAI."}],
        "url": "https://www.poultryworld.net/health/example/",
        "source": "www.poultryworld.net",
        "published_at": "2026-05-28T08:42:19",
        "rssfeed": {"source_category": "Avian Influenza"},
        "machine_classification_labels": [{"name_en": "Relevant"}],
    }
    fetched = cache_article_json(
        base_dir=tmp_path,
        source_link="https://padi-web.cirad.fr/en/articles/api/4PYSCRQ6ZV/",
        payload=payload,
        status_code=200,
        fetched_at=datetime(2026, 5, 28, 12, 0, tzinfo=timezone.utc),
    )
    cached_payload = json.loads(Path(fetched.raw_html_path).read_text(encoding="utf-8"))
    article = parse_article_payload(
        payload=cached_payload,
        source_link=fetched.source_link,
        raw_json_path=Path(fetched.raw_html_path),
        content_hash=fetched.content_hash,
        retrieved_at=fetched.fetched_at,
    )

    write_jsonl(tmp_path / "padi_web" / "articles.jsonl", [article])
    rows = read_jsonl(tmp_path / "padi_web" / "articles.jsonl")

    assert rows[0]["source_id"] == "padi_web"
    assert rows[0]["title"] == "Meeting the ongoing challenge of avian influenza in the UK"
    assert "outbreak of HPAI" in rows[0]["fulltext"]
```

- [ ] **Step 2: Run all scraper tests**

Run:

```bash
uv run pytest tests/test_gefluegelnews.py tests/test_padi_web.py tests/test_disease_pipeline.py -v
```

Expected: PASS.

## Task 6: README And Gitignore

**Files:**
- Modify: `.gitignore`
- Modify: `README.md`

- [ ] **Step 1: Ignore generated PADI artifacts**

Add to `.gitignore` if no broader `data/unstructured/*/raw_*` rule already covers it:

```gitignore
data/unstructured/padi_web/
```

- [ ] **Step 2: Document PADI-web usage**

Add a concise README section near the existing scraper usage:

```markdown
### PADI-web source

PADI-web is ingested through its public article JSON API and cached locally as JSON before normalization into the shared `NewsArticle` pipeline.

```bash
uv run govtech-tierseuchen discover padi_web --published-after 2026-05-21 --source-category "Avian Influenza" --limit 100
uv run govtech-tierseuchen fetch padi_web --limit 100
uv run govtech-tierseuchen parse padi_web
uv run govtech-tierseuchen filter-disease padi_web
uv run govtech-tierseuchen extract-reports padi_web
```

Generated PADI cache and JSONL outputs live under `data/unstructured/padi_web/` and are not committed.
```

- [ ] **Step 3: Run formatting, lint, and tests**

Run:

```bash
uv run ruff format .
uv run ruff check .
uv run pytest
```

Expected: all pass.

## Open Questions Before Implementation

- Whether `source_link` on PADI-normalized `NewsArticle` should be the original publisher URL, as planned, or the PADI detail API URL. I recommend original publisher URL because `DiseaseReport.source_link` should take users to the source document.
- Whether to keep the default PADI filter broad (`Relevant` since `published_after`) or source-category scoped (`Avian Influenza`). I recommend making it configurable, with `--source-category "Avian Influenza"` in routine runs.
- Whether to promote PADI-specific metadata (`country`, `continent`, labels, sentence ids, source language) into new model fields. I recommend deferring that until a third source or RDF export needs it; for v1, preserve key metadata in `keywords`, `category`, `author`, `source_attribution`, and cached JSON.

## Suggested Commit

```bash
git add src/govtech_tierseuchen/padi_web.py src/govtech_tierseuchen/cli.py tests/test_padi_web.py .gitignore README.md docs/superpowers/plans/2026-05-28-padi-web-news-source.md
git commit -m "feat(scraper): add PADI-web source plan and adapter"
```
