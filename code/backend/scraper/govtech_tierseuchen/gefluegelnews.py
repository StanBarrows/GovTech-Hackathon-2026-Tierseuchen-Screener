from __future__ import annotations

import hashlib
import re
import time
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from govtech_tierseuchen.models import (
    DiscoveredArticle,
    FetchedArticle,
    FetchError,
    NewsArticle,
)

SOURCE_ID = "gefluegelnews"
SOURCE_NAME = "Gefluegelnews"
BASE_URL = "https://www.gefluegelnews.de"
SITEMAP_URL = f"{BASE_URL}/sitemap.xml"
NEWS_RSS_URL = f"{BASE_URL}/news/rss"
DEFAULT_USER_AGENT = (
    "GovTech-Tierseuchen prototype scraper (+local research; respects robots.txt)"
)

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


def parse_sitemap_articles(
    data: bytes, discovered_at: datetime
) -> list[DiscoveredArticle]:
    root = ElementTree.fromstring(data)
    namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    discovered: dict[str, DiscoveredArticle] = {}

    for url_element in root.findall(".//sm:url", namespace):
        loc_element = url_element.find("sm:loc", namespace)
        if loc_element is None or loc_element.text is None:
            continue
        source_link = loc_element.text.strip()
        parsed = urlparse(source_link)
        if parsed.netloc != "www.gefluegelnews.de" or not parsed.path.startswith(
            "/article/"
        ):
            continue
        if source_link in discovered:
            continue

        lastmod_element = url_element.find("sm:lastmod", namespace)
        last_modified = None
        if lastmod_element is not None and lastmod_element.text:
            last_modified = _parse_datetime(lastmod_element.text.strip())
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
    safe_slug = "".join(
        char if char.isalnum() or char in "-_" else "-" for char in slug
    )[:120]
    return f"{safe_slug}-{digest[:12]}.html"


def raw_html_path(base_dir: Path, source_link: str) -> Path:
    return base_dir / SOURCE_ID / "raw_html" / cache_filename_for_url(source_link)


@dataclass
class _ParsedHtml:
    page_title: str | None = None
    canonical_url: str | None = None
    description: str | None = None
    keywords: list[str] = field(default_factory=list)
    image_url: str | None = None
    article_title: str | None = None
    date_text: str | None = None
    category: str | None = None
    body_parts: list[tuple[str, str]] = field(default_factory=list)
    author: str | None = None
    image_credit: str | None = None
    source_attribution: str | None = None


class _GefluegelnewsParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.result = _ParsedHtml()
        self._stack: list[tuple[str, dict[str, str]]] = []
        self._capture: str | None = None
        self._buffer: list[str] = []
        self._in_detail = False
        self._in_main = False
        self._in_text = False
        self._in_author = False
        self._author_depth: int | None = None
        self._image_credit_depth: int | None = None
        self._source_depth: int | None = None
        self._author_buffer: list[str] = []
        self._image_credit_buffer: list[str] = []
        self._source_buffer: list[str] = []
        self._strong_depth = 0
        self._body_part_had_strong = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {key: value or "" for key, value in attrs}
        self._stack.append((tag, attr))

        if tag == "meta":
            self._handle_meta(attr)
        elif tag == "link" and attr.get("rel") == "canonical" and attr.get("href"):
            self.result.canonical_url = attr["href"].strip()
        elif tag == "title":
            self._start_capture("page_title")
        elif tag == "section" and attr.get("id") == "detailpage":
            self._in_detail = True
        elif self._in_detail and tag == "div" and attr.get("id") == "main":
            self._in_main = True
        elif self._in_main and tag == "div" and attr.get("class") == "text":
            self._in_text = True
        elif self._in_main and tag == "div" and attr.get("class") == "author":
            self._in_author = True
            self._author_depth = len(self._stack)
            self._author_buffer = []
        elif self._in_author and tag == "div" and attr.get("class") == "images":
            self._image_credit_depth = len(self._stack)
            self._image_credit_buffer = []
        elif self._in_author and tag == "div" and attr.get("class") != "images":
            self._source_depth = len(self._stack)
            self._source_buffer = []
        elif self._in_main and tag == "h1":
            self._start_capture("article_title")
        elif (
            self._in_main and tag == "div" and attr.get("class") in {"date", "category"}
        ):
            self._start_capture(attr["class"])
        elif self._in_text and tag in {"p", "h2", "h3"}:
            self._body_part_had_strong = False
            self._start_capture(tag)
        elif self._in_text and tag == "strong":
            self._strong_depth += 1
            self._body_part_had_strong = True

    def handle_endtag(self, tag: str) -> None:
        text = _clean_text("".join(self._buffer))
        current_depth = len(self._stack)

        if tag == "title" and self._capture == "page_title":
            self.result.page_title = text or None
            self._stop_capture()
        elif tag == "h1" and self._capture == "article_title":
            self.result.article_title = text or None
            self._stop_capture()
        elif tag == "div" and self._capture == "date":
            self.result.date_text = text or None
            self._stop_capture()
        elif tag == "div" and self._capture == "category":
            self.result.category = text or None
            self._stop_capture()
        elif (
            self._in_text
            and self._capture in {"p", "h2", "h3"}
            and tag == self._capture
        ):
            if text:
                if self._capture == "p" and self._body_part_had_strong:
                    text = f"**{text}**"
                self.result.body_parts.append((self._capture, text))
            self._stop_capture()
        elif (
            self._in_author
            and tag == "div"
            and self._image_credit_depth == current_depth
        ):
            image_credit = _clean_text("".join(self._image_credit_buffer))
            self.result.image_credit = image_credit.replace("Bild:", "").strip() or None
            self._image_credit_depth = None
            self._image_credit_buffer = []
        elif self._in_author and tag == "div" and self._source_depth == current_depth:
            source_attribution = _clean_text("".join(self._source_buffer))
            self.result.source_attribution = (
                source_attribution.replace("Quelle:", "").strip() or None
            )
            self._source_depth = None
            self._source_buffer = []
        elif self._in_author and tag == "div" and self._author_depth == current_depth:
            self.result.author = _clean_text("".join(self._author_buffer)) or None
            self._author_depth = None
            self._in_author = False
            self._author_buffer = []

        if self._in_text and tag == "strong":
            self._strong_depth = max(0, self._strong_depth - 1)
        if self._in_text and tag == "div" and self._capture is None:
            self._in_text = False
        if (
            self._in_main
            and tag == "div"
            and self._stack
            and self._stack[-1][1].get("id") == "main"
        ):
            self._in_main = False
        if (
            self._in_detail
            and tag == "section"
            and self._stack
            and self._stack[-1][1].get("id") == "detailpage"
        ):
            self._in_detail = False
        if self._stack:
            self._stack.pop()

    def handle_data(self, data: str) -> None:
        if not data:
            return
        if self._in_author and self._image_credit_depth is not None:
            self._image_credit_buffer.append(data)
        elif self._in_author and self._source_depth is not None:
            self._source_buffer.append(data)
        elif self._in_author and self._author_depth is not None:
            self._author_buffer.append(data)
        elif self._capture:
            self._buffer.append(data)

    def _handle_meta(self, attr: dict[str, str]) -> None:
        name = attr.get("name")
        prop = attr.get("property")
        content = attr.get("content")
        if name == "description" and content:
            self.result.description = content.strip()
        elif name == "keywords" and content:
            self.result.keywords = [
                part.strip() for part in content.split(",") if part.strip()
            ]
        elif prop == "og:image" and content:
            self.result.image_url = content.strip()

    def _start_capture(self, capture: str) -> None:
        self._capture = capture
        self._buffer = []

    def _stop_capture(self) -> None:
        self._capture = None
        self._buffer = []


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
    title = parsed.article_title or parsed.page_title
    if not title:
        raise ValueError(f"Could not parse article title from {source_link}")
    canonical_url = parsed.canonical_url or source_link
    return NewsArticle(
        source_id=SOURCE_ID,
        source_name=SOURCE_NAME,
        source_link=source_link,
        canonical_url=canonical_url,
        title=title,
        description=parsed.description,
        keywords=parsed.keywords,
        publication_date=_parse_german_date(parsed.date_text)
        if parsed.date_text
        else None,
        retrieved_at=retrieved_at,
        category=parsed.category,
        author=parsed.author,
        image_url=parsed.image_url or _first_article_image_url(html),
        image_credit=parsed.image_credit,
        source_attribution=parsed.source_attribution,
        partner_content=None,
        fulltext=_to_markdown(title, parsed.body_parts),
        raw_html_path=str(raw_html_path),
        content_hash=content_hash,
    )


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


def fetch_url(
    source_link: str, timeout_seconds: float, user_agent: str = DEFAULT_USER_AGENT
) -> tuple[int, str]:
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
    validation_error = _validate_article_source_link(source_link)
    if validation_error is not None:
        return FetchError(
            source_link=source_link,
            error_type="InvalidSourceUrl",
            message=validation_error,
            occurred_at=fetched_at,
        )
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


def _validate_article_source_link(source_link: str) -> str | None:
    parsed = urlparse(source_link)
    requirement = (
        "Gefluegelnews article URLs must use https, be hosted on "
        "www.gefluegelnews.de, and use the /article/ path."
    )
    if parsed.scheme != "https":
        return requirement
    if parsed.netloc != "www.gefluegelnews.de":
        return requirement
    if not parsed.path.startswith("/article/"):
        return requirement
    return None


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


def _parse_german_date(value: str) -> date | None:
    match = re.search(r"(\d{1,2})\s+([A-Za-zÄÖÜäöüß]+)\s+(\d{4})", value)
    if not match:
        return None
    day = int(match.group(1))
    month = GERMAN_MONTHS[match.group(2)]
    year = int(match.group(3))
    return date(year, month, day)


def _first_article_image_url(html: str) -> str | None:
    match = re.search(
        r"<img\b[^>]*\bsrc=[\"']([^\"']+)[\"']", html, flags=re.IGNORECASE
    )
    if match is None:
        return None
    return urljoin(BASE_URL, match.group(1))
