from __future__ import annotations

import hashlib
import json
import logging
import time
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from govtech_tierseuchen.config import load_config
from govtech_tierseuchen.models import (
    DiscoveredArticle,
    FetchedArticle,
    FetchError,
    NewsArticle,
)

SOURCE_ID = "padi_web"
SOURCE_NAME = "PADI-web"


def _required_source_value(value: str | None, key: str) -> str:
    if value is None:
        raise RuntimeError(f"Missing {SOURCE_ID}.{key} in config.yaml")
    return value


_SOURCE_CONFIG = load_config().sources[SOURCE_ID]
BASE_URL = _required_source_value(_SOURCE_CONFIG.base_url, "base_url")
ARTICLES_API_PATH = _required_source_value(
    _SOURCE_CONFIG.articles_api_path, "articles_api_path"
)
ARTICLES_API_URL = f"{BASE_URL}{ARTICLES_API_PATH}"
ALLOWED_NETLOC = urlparse(BASE_URL).netloc
DEFAULT_USER_AGENT = _required_source_value(_SOURCE_CONFIG.user_agent, "user_agent")
RAW_SUBDIR = _required_source_value(_SOURCE_CONFIG.raw_subdir, "raw_subdir")
ARTICLE_SERIALIZER = _required_source_value(
    _SOURCE_CONFIG.article_serializer, "article_serializer"
)
DISCOVERY = _SOURCE_CONFIG.discovery or {}
DEFAULT_DISCOVERY_DAYS = int(DISCOVERY["published_after_days"])
DEFAULT_DISCOVERY_PER_PAGE = int(DISCOVERY["per_page"])
LOGGER = logging.getLogger(__name__)


def build_articles_api_url(
    *,
    page: int = 1,
    per_page: int = DEFAULT_DISCOVERY_PER_PAGE,
    published_after: str | None = None,
    source_category: str | None = None,
    today: date | None = None,
) -> str:
    if published_after is None:
        today = today or date.today()
        published_after = (today - timedelta(days=DEFAULT_DISCOVERY_DAYS)).isoformat()
    params: dict[str, str | int] = {
        "page": page,
        "per_page": per_page,
        "general_labels_per_task[Relevance]": DISCOVERY["relevance_label"],
        "is_archived": DISCOVERY["is_archived"],
        "ordering": DISCOVERY["ordering"],
        "order_by[key]": DISCOVERY["order_by_key"],
        "order_by[order]": DISCOVERY["order_by_order"],
    }
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
        if not isinstance(row, dict) or not row.get("id"):
            LOGGER.warning("Skipping malformed PADI article row without id")
            continue
        try:
            last_modified = _parse_padi_datetime(row.get("published_at"))
        except ValueError as exc:
            LOGGER.warning("Skipping malformed PADI article row: %s", exc)
            continue
        article_id = str(row["id"])
        articles.append(
            DiscoveredArticle(
                source_id=SOURCE_ID,
                source_name=SOURCE_NAME,
                source_link=f"{ARTICLES_API_URL}{article_id}/",
                discovered_at=discovered_at,
                last_modified=last_modified,
            )
        )
    return articles, _validated_page_url(payload.get("next"))


def article_id_from_source_link(source_link: str) -> str:
    path = urlparse(source_link).path
    if not path.startswith(ARTICLES_API_PATH):
        return ""
    suffix = path.removeprefix(ARTICLES_API_PATH).strip("/")
    if "/" in suffix:
        return ""
    return suffix


def raw_json_path(base_dir: Path, source_link: str) -> Path:
    return (
        base_dir
        / SOURCE_ID
        / RAW_SUBDIR
        / f"{article_id_from_source_link(source_link)}.json"
    )


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
            f"{source_link}?serializer={ARTICLE_SERIALIZER}",
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


def _validate_article_source_link(source_link: str) -> str | None:
    parsed = urlparse(source_link)
    requirement = (
        "PADI-web article API URLs must use https, be hosted on "
        f"{ALLOWED_NETLOC}, and use the {ARTICLES_API_PATH}<id>/ path."
    )
    if parsed.scheme != "https":
        return requirement
    if parsed.netloc != ALLOWED_NETLOC:
        return requirement
    if not parsed.path.startswith(ARTICLES_API_PATH):
        return requirement
    if not article_id_from_source_link(source_link):
        return requirement
    return None


def _validated_page_url(value: str | None) -> str | None:
    if not value:
        return None
    parsed = urlparse(value)
    if parsed.scheme != "https":
        return None
    if parsed.netloc != ALLOWED_NETLOC:
        return None
    if parsed.path != ARTICLES_API_PATH:
        return None
    return value


def _label_names(labels: list[dict[str, Any]]) -> list[str]:
    names = []
    for label in labels:
        name = label.get("name_en") or label.get("name")
        if name and name not in names:
            names.append(str(name))
    return names


def _parse_padi_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


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
