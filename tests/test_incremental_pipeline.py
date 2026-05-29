from datetime import date, datetime, timezone

from govtech_tierseuchen import cli
from govtech_tierseuchen.cli import build_parser, main
from govtech_tierseuchen.config import load_config
from govtech_tierseuchen.enrichment import enrich_source
from govtech_tierseuchen.jsonl import read_jsonl, write_jsonl
from govtech_tierseuchen.models import FetchedArticle, NewsArticle


def _news_article(source_link: str, title: str, content_hash: str) -> NewsArticle:
    return NewsArticle(
        source_id="gefluegelnews",
        source_name="Gefluegelnews",
        source_link=source_link,
        canonical_url=source_link,
        title=title,
        description=None,
        keywords=[],
        publication_date=date(2026, 5, 28),
        retrieved_at=datetime(2026, 5, 28, 12, 0, tzinfo=timezone.utc),
        category=None,
        author=None,
        image_url=None,
        image_credit=None,
        source_attribution=None,
        partner_content=None,
        fulltext=f"{title} fulltext",
        raw_html_path="raw.html",
        content_hash=content_hash,
    )


def _candidate_record(report_id: str, content_hash: str) -> dict:
    return {
        "report_id": report_id,
        "source_id": "gefluegelnews",
        "source_name": "Gefluegelnews",
        "source_document_id": f"source_document:{report_id}",
        "source_document_title": report_id,
        "source_link": f"https://www.gefluegelnews.de/article/{report_id}",
        "source_publication_date": "2026-05-20",
        "source_retrieved_at": "2026-05-28T12:00:00+00:00",
        "fulltext": f"{report_id} H5N1 fulltext",
        "raw_html_path": "raw.html",
        "content_hash": content_hash,
        "extraction_method": "rules",
        "extraction_version": "rules-v1",
        "extraction_status": "candidate",
        "extraction_confidence": "medium",
        "evidence_snippets": [],
        "rule_relevance_score": 1,
        "rule_matched_terms": ["H5N1"],
        "rule_disease_type": "H5N1",
        "rule_control_measures": [],
        "prevention_measures": [],
        "research_references": [],
    }


def test_discover_merges_existing_manifest_rows(monkeypatch, tmp_path):
    current_link = "https://www.gefluegelnews.de/article/current"
    old_link = "https://www.gefluegelnews.de/article/old"
    write_jsonl(
        tmp_path / "gefluegelnews" / "manifest.jsonl",
        [
            {
                "source_link": current_link,
                "last_modified": "2026-05-28T00:00:03+00:00",
                "raw_html_path": "gefluegelnews/raw_html/current.html",
                "content_hash": "hash-current",
                "status_code": 200,
            },
            {
                "source_link": old_link,
                "last_modified": "2026-05-20T00:00:03+00:00",
                "raw_html_path": "gefluegelnews/raw_html/old.html",
                "content_hash": "hash-old",
                "status_code": 200,
            },
        ],
    )
    sitemap_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url>
        <loc>{current_link}</loc>
        <lastmod>2026-05-28T00:00:03+00:00</lastmod>
      </url>
    </urlset>
    """

    def fake_fetch_url(source_link, timeout_seconds):
        return 200, sitemap_xml

    monkeypatch.setattr("govtech_tierseuchen.gefluegelnews.fetch_url", fake_fetch_url)

    exit_code = main(["discover", "gefluegelnews", "--data-dir", str(tmp_path)])

    rows = read_jsonl(tmp_path / "gefluegelnews" / "manifest.jsonl")
    assert exit_code == 0
    assert [row["source_link"] for row in rows] == [current_link, old_link]
    assert rows[0]["content_hash"] == "hash-current"
    assert rows[0]["status_code"] == 200


def test_fetch_skips_current_cached_article_on_second_run(monkeypatch, tmp_path):
    source_link = "https://www.gefluegelnews.de/article/current"
    write_jsonl(
        tmp_path / "gefluegelnews" / "manifest.jsonl",
        [
            {
                "source_link": source_link,
                "last_modified": "2026-05-28T00:00:03+00:00",
            }
        ],
    )
    calls = []

    def fake_fetch_and_cache_article(
        base_dir,
        source_link,
        fetched_at,
        timeout_seconds,
        delay_seconds,
    ):
        calls.append(source_link)
        raw_path = base_dir / "gefluegelnews" / "raw_html" / "current.html"
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_text("<html>current</html>", encoding="utf-8")
        return FetchedArticle(
            source_id="gefluegelnews",
            source_name="Gefluegelnews",
            source_link=source_link,
            fetched_at=fetched_at,
            status_code=200,
            raw_html_path=str(raw_path),
            content_hash="hash-current",
            canonical_url=source_link,
        )

    monkeypatch.setattr(
        "govtech_tierseuchen.gefluegelnews.fetch_and_cache_article",
        fake_fetch_and_cache_article,
    )

    assert (
        main(
            [
                "fetch",
                "gefluegelnews",
                "--data-dir",
                str(tmp_path),
                "--delay-seconds",
                "0",
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "fetch",
                "gefluegelnews",
                "--data-dir",
                str(tmp_path),
                "--delay-seconds",
                "0",
            ]
        )
        == 0
    )

    rows = read_jsonl(tmp_path / "gefluegelnews" / "manifest.jsonl")
    assert calls == [source_link]
    assert rows[0]["content_hash"] == "hash-current"
    assert (tmp_path / "pipeline_state.sqlite").exists()


def test_cli_force_reprocesses_current_fetch(monkeypatch, tmp_path):
    source_link = "https://www.gefluegelnews.de/article/current"
    raw_path = tmp_path / "gefluegelnews" / "raw_html" / "current.html"
    raw_path.parent.mkdir(parents=True)
    raw_path.write_text("<html>current</html>", encoding="utf-8")
    write_jsonl(
        tmp_path / "gefluegelnews" / "manifest.jsonl",
        [
            {
                "source_link": source_link,
                "last_modified": "2026-05-28T00:00:03+00:00",
                "raw_html_path": str(raw_path),
                "content_hash": "hash-current",
            }
        ],
    )
    calls = []

    def fake_fetch_and_cache_article(
        base_dir,
        source_link,
        fetched_at,
        timeout_seconds,
        delay_seconds,
    ):
        calls.append(source_link)
        return FetchedArticle(
            source_id="gefluegelnews",
            source_name="Gefluegelnews",
            source_link=source_link,
            fetched_at=fetched_at,
            status_code=200,
            raw_html_path=str(raw_path),
            content_hash=f"hash-current-{len(calls)}",
            canonical_url=source_link,
        )

    monkeypatch.setattr(
        "govtech_tierseuchen.gefluegelnews.fetch_and_cache_article",
        fake_fetch_and_cache_article,
    )

    assert (
        main(
            [
                "fetch",
                "gefluegelnews",
                "--data-dir",
                str(tmp_path),
                "--delay-seconds",
                "0",
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "fetch",
                "gefluegelnews",
                "--data-dir",
                str(tmp_path),
                "--delay-seconds",
                "0",
                "--force",
            ]
        )
        == 0
    )

    assert calls == [source_link]


def test_parse_reuses_unchanged_article_output(monkeypatch, tmp_path):
    first_link = "https://www.gefluegelnews.de/article/first"
    second_link = "https://www.gefluegelnews.de/article/second"
    first_raw = tmp_path / "gefluegelnews" / "raw_html" / "first.html"
    second_raw = tmp_path / "gefluegelnews" / "raw_html" / "second.html"
    first_raw.parent.mkdir(parents=True)
    first_raw.write_text("<html>first</html>", encoding="utf-8")
    second_raw.write_text("<html>second</html>", encoding="utf-8")
    write_jsonl(
        tmp_path / "gefluegelnews" / "manifest.jsonl",
        [
            {
                "source_link": first_link,
                "raw_html_path": str(first_raw),
                "content_hash": "hash-first",
                "title_seed": "First",
            },
            {
                "source_link": second_link,
                "raw_html_path": str(second_raw),
                "content_hash": "hash-second",
                "title_seed": "Second",
            },
        ],
    )

    def first_parse(source, row, raw_path):
        return _news_article(row["source_link"], row["title_seed"], row["content_hash"])

    monkeypatch.setattr(cli, "_parse_row_for_source", first_parse)
    assert main(["parse", "gefluegelnews", "--data-dir", str(tmp_path)]) == 0

    write_jsonl(
        tmp_path / "gefluegelnews" / "manifest.jsonl",
        [
            {
                "source_link": first_link,
                "raw_html_path": str(first_raw),
                "content_hash": "hash-first",
                "title_seed": "First",
            },
            {
                "source_link": second_link,
                "raw_html_path": str(second_raw),
                "content_hash": "hash-second-updated",
                "title_seed": "Second updated",
            },
        ],
    )

    def second_parse(source, row, raw_path):
        if row["source_link"] == first_link:
            raise AssertionError("unchanged article was parsed again")
        return _news_article(row["source_link"], row["title_seed"], row["content_hash"])

    monkeypatch.setattr(cli, "_parse_row_for_source", second_parse)
    assert main(["parse", "gefluegelnews", "--data-dir", str(tmp_path)]) == 0

    rows = read_jsonl(tmp_path / "gefluegelnews" / "articles.jsonl")
    assert [row["title"] for row in rows] == ["First", "Second updated"]


def test_enrich_source_reuses_unchanged_enriched_records(tmp_path):
    config = load_config()
    source_dir = tmp_path / "gefluegelnews"
    first = _candidate_record("first", "hash-first")
    second = _candidate_record("second", "hash-second")
    write_jsonl(source_dir / "disease_reports.jsonl", [first])

    enrich_source(
        data_dir=tmp_path,
        source="gefluegelnews",
        config=config,
        extractor=lambda record: {"disease_name": "Existing disease"},
    )

    write_jsonl(source_dir / "disease_reports.jsonl", [first, second])
    calls = []

    def fake_extract(record):
        if record["report_id"] == "first":
            raise AssertionError("unchanged report was enriched again")
        calls.append(record["report_id"])
        return {"disease_name": "New disease"}

    result = enrich_source(
        data_dir=tmp_path,
        source="gefluegelnews",
        config=config,
        extractor=fake_extract,
    )

    rows = read_jsonl(source_dir / "disease_reports.enriched.jsonl")
    assert result.record_count == 2
    assert calls == ["second"]
    assert [row["disease_name"] for row in rows] == ["Existing disease", "New disease"]


def test_enrich_source_reprocesses_when_prompt_changes(tmp_path):
    config = load_config()
    source_dir = tmp_path / "gefluegelnews"
    prompt_path = tmp_path / "prompt.md"
    prompt_path.write_text("prompt v1", encoding="utf-8")
    record = _candidate_record("first", "hash-first")
    write_jsonl(source_dir / "disease_reports.jsonl", [record])

    enrich_source(
        data_dir=tmp_path,
        source="gefluegelnews",
        config=config,
        prompt_path=prompt_path,
        extractor=lambda record: {"disease_name": "Prompt v1 disease"},
    )

    prompt_path.write_text("prompt v2", encoding="utf-8")
    calls = []

    def fake_extract(record):
        calls.append(record["report_id"])
        return {"disease_name": "Prompt v2 disease"}

    enrich_source(
        data_dir=tmp_path,
        source="gefluegelnews",
        config=config,
        prompt_path=prompt_path,
        extractor=fake_extract,
    )

    rows = read_jsonl(source_dir / "disease_reports.enriched.jsonl")
    assert calls == ["first"]
    assert rows[0]["disease_name"] == "Prompt v2 disease"


def test_enrich_source_retries_previous_error_for_unchanged_input(tmp_path):
    config = load_config()
    source_dir = tmp_path / "gefluegelnews"
    record = _candidate_record("first", "hash-first")
    write_jsonl(source_dir / "disease_reports.jsonl", [record])

    enrich_source(
        data_dir=tmp_path,
        source="gefluegelnews",
        config=config,
        extractor=lambda record: (_ for _ in ()).throw(ValueError("bad model json")),
    )

    result = enrich_source(
        data_dir=tmp_path,
        source="gefluegelnews",
        config=config,
        extractor=lambda record: {"disease_name": "Recovered disease"},
    )

    rows = read_jsonl(source_dir / "disease_reports.enriched.jsonl")
    assert result.record_count == 1
    assert rows[0]["disease_name"] == "Recovered disease"
    assert "_error" not in rows[0]


def test_parser_accepts_force_for_incremental_commands():
    parser = build_parser(load_config())

    assert parser.parse_args(["fetch", "gefluegelnews", "--force"]).force is True
    assert parser.parse_args(["enrich", "gefluegelnews", "--force"]).force is True
    assert parser.parse_args(["run-all", "--force"]).force is True
