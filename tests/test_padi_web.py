import json
from datetime import date, datetime, timezone
from pathlib import Path

from govtech_tierseuchen.cli import build_parser, main
from govtech_tierseuchen.config import load_config
from govtech_tierseuchen.jsonl import read_jsonl, write_jsonl
from govtech_tierseuchen.models import FetchedArticle
from govtech_tierseuchen.padi_web import (
    build_articles_api_url,
    cache_article_json,
    fetch_and_cache_article,
    parse_article_page,
    parse_article_payload,
    raw_json_path,
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


def test_build_articles_api_url_defaults_to_recent_bounded_discovery_window():
    url = build_articles_api_url(today=date(2026, 5, 28))

    assert "per_page=25" in url
    assert "published_after=2026-05-21" in url


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
    assert (
        articles[0].source_link
        == "https://padi-web.cirad.fr/en/articles/api/4PYSCRQ6ZV/"
    )
    assert articles[0].last_modified == datetime(
        2026, 5, 28, 8, 42, 19, tzinfo=timezone.utc
    )


def test_parse_article_page_skips_rows_with_missing_id_or_bad_date(caplog):
    payload = {
        "next": None,
        "results": [
            {"published_at": "2026-05-28T08:42:19"},
            {"id": "BADDATE", "published_at": "not-a-date"},
            {"id": "OK123", "published_at": "2026-05-28T08:42:19"},
        ],
    }

    articles, next_url = parse_article_page(
        payload,
        discovered_at=datetime(2026, 5, 28, 12, 0, tzinfo=timezone.utc),
    )

    assert next_url is None
    assert [article.source_link for article in articles] == [
        "https://padi-web.cirad.fr/en/articles/api/OK123/"
    ]
    assert "Skipping malformed PADI article row" in caplog.text


def test_parse_article_page_rejects_external_next_url():
    payload = {
        "next": "https://example.invalid/en/articles/api/?page=2",
        "results": [{"id": "AAA111", "published_at": "2026-05-28T08:42:19"}],
    }

    _, next_url = parse_article_page(
        payload,
        discovered_at=datetime(2026, 5, 28, 12, 0, tzinfo=timezone.utc),
    )

    assert next_url is None


def test_raw_json_path_uses_padi_article_id(tmp_path):
    path = raw_json_path(
        tmp_path, "https://padi-web.cirad.fr/en/articles/api/4PYSCRQ6ZV/"
    )

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
    assert (
        fetched.canonical_url == "https://padi-web.cirad.fr/en/articles/api/4PYSCRQ6ZV/"
    )
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


def test_fetch_and_cache_article_rejects_padi_list_api_url(tmp_path):
    fetched = fetch_and_cache_article(
        base_dir=tmp_path,
        source_link="https://padi-web.cirad.fr/en/articles/api/",
        fetched_at=datetime(2026, 5, 28, 12, 0, tzinfo=timezone.utc),
        timeout_seconds=1,
        delay_seconds=0,
    )

    assert fetched.error_type == "InvalidSourceUrl"
    assert "/en/articles/api/<id>/" in fetched.message


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
        "rssfeed": {
            "source_category": "Avian Influenza",
            "name": "AVIAN_INFLUENZA3_EN",
        },
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


def test_cli_uses_selected_source_defaults_for_padi_web(monkeypatch, tmp_path):
    config = load_config()
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
        calls.append((timeout_seconds, delay_seconds))
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

    parser = build_parser(config)
    args = parser.parse_args(["fetch", "padi_web"])
    assert args.timeout_seconds is None
    assert args.delay_seconds is None
    assert args.limit is None

    exit_code = main(["fetch", "padi_web", "--data-dir", str(tmp_path)])

    assert exit_code == 0
    assert calls == [
        (
            config.sources["padi_web"].timeout_seconds,
            config.sources["padi_web"].delay_seconds,
        )
    ]


def test_padi_discover_stage_writes_limited_manifest(monkeypatch, tmp_path):
    calls = []
    payload = {
        "next": None,
        "results": [
            {"id": "AAA111", "published_at": "2026-05-28T08:42:19"},
            {"id": "BBB222", "published_at": "2026-05-28T09:42:19"},
        ],
    }

    def fake_fetch_json(source_link, timeout_seconds):
        calls.append(source_link)
        return 200, payload

    monkeypatch.setattr("govtech_tierseuchen.padi_web.fetch_json", fake_fetch_json)

    exit_code = main(
        ["discover", "padi_web", "--data-dir", str(tmp_path), "--limit", "1"]
    )

    rows = read_jsonl(tmp_path / "padi_web" / "manifest.jsonl")
    assert exit_code == 0
    assert "per_page=25" in calls[0]
    assert "published_after=" in calls[0]
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

    exit_code = main(
        ["fetch", "padi_web", "--data-dir", str(tmp_path), "--delay-seconds", "0"]
    )

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


def test_padi_articles_flow_through_filter_extract_and_final_export(tmp_path):
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
    rdf_output = tmp_path / "lindas" / "data" / "rdf" / "tierseuchen-screener.ttl"
    csv_output = tmp_path / "lindas" / "data" / "csv" / "disease_reports.csv"
    assert main(["filter-disease", "padi_web", "--data-dir", str(data_dir)]) == 0
    assert main(["extract-reports", "padi_web", "--data-dir", str(data_dir)]) == 0
    write_jsonl(
        tmp_path / "padi_web" / "disease_reports.enriched.jsonl",
        read_jsonl(tmp_path / "padi_web" / "disease_reports.jsonl"),
    )
    assert (
        main(
            [
                "export-final",
                "--source",
                "padi_web",
                "--data-dir",
                str(data_dir),
                "--rdf-output",
                str(rdf_output),
                "--csv-output",
                str(csv_output),
            ]
        )
        == 0
    )

    disease_articles = read_jsonl(tmp_path / "padi_web" / "disease_articles.jsonl")
    reports = read_jsonl(tmp_path / "padi_web" / "disease_reports.jsonl")
    assert len(disease_articles) == 1
    assert reports[0]["source_id"] == "padi_web"
    assert reports[0]["source_link"] == "https://publisher.example/article"
    assert rdf_output.exists()
    assert csv_output.exists()
