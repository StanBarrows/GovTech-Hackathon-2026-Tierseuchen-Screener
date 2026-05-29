from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
import time
import tomllib

from govtech_tierseuchen import cli
from govtech_tierseuchen.cli import build_parser, main, resolve_data_dir
from govtech_tierseuchen.config import load_config
from govtech_tierseuchen.gefluegelnews import (
    cache_html,
    fetch_and_cache_article,
    parse_article_html,
    parse_sitemap_articles,
)
from govtech_tierseuchen.jsonl import read_jsonl, write_jsonl
from govtech_tierseuchen.models import FetchedArticle


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
    assert articles[0].source_link.endswith(
        "/polen-wird-zum-vogelgrippe-hotspot-europas"
    )
    assert articles[0].last_modified == datetime(
        2026, 5, 28, 0, 0, 3, tzinfo=timezone.utc
    )


def test_gefluegelnews_discover_stage_writes_limited_manifest(monkeypatch, tmp_path):
    sitemap_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url><loc>https://www.gefluegelnews.de/article/one</loc></url>
      <url><loc>https://www.gefluegelnews.de/article/two</loc></url>
    </urlset>
    """

    def fake_fetch_url(source_link, timeout_seconds):
        return 200, sitemap_xml

    monkeypatch.setattr("govtech_tierseuchen.gefluegelnews.fetch_url", fake_fetch_url)

    exit_code = main(
        ["discover", "gefluegelnews", "--data-dir", str(tmp_path), "--limit", "1"]
    )

    rows = read_jsonl(tmp_path / "gefluegelnews" / "manifest.jsonl")
    assert exit_code == 0
    assert [row["source_link"] for row in rows] == [
        "https://www.gefluegelnews.de/article/one"
    ]


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
    assert (
        article.canonical_url
        == "https://www.gefluegelnews.de/article/polen-wird-zum-vogelgrippe-hotspot-europas"
    )
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
    assert (
        fetched.content_hash
        == "a59b59fbb5480ba00678a3cfc2fbe83cdb21c88460ba97be599b94ecc9031ec5"
    )


def test_fetch_and_cache_article_rejects_non_gefluegelnews_article_url(tmp_path):
    fetched = fetch_and_cache_article(
        base_dir=tmp_path,
        source_link="file:///etc/passwd",
        fetched_at=datetime(2026, 5, 28, 12, 0, tzinfo=timezone.utc),
        timeout_seconds=1,
        delay_seconds=0,
    )

    assert fetched.error_type == "InvalidSourceUrl"
    assert "www.gefluegelnews.de" in fetched.message


def test_cli_parser_accepts_pipeline_stage_and_source():
    parser = build_parser()
    args = parser.parse_args(
        ["discover", "gefluegelnews", "--data-dir", "data/unstructured"]
    )

    assert args.command == "discover"
    assert args.source == "gefluegelnews"
    assert args.data_dir == "data/unstructured"
    assert parser.prog == "ts-screener"


def test_package_exposes_ts_screener_console_script_only():
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert pyproject["project"]["scripts"] == {
        "ts-screener": "govtech_tierseuchen.cli:main"
    }


def test_cli_parser_accepts_enrich_and_export_final_commands():
    parser = build_parser()
    enrich_args = parser.parse_args(
        ["enrich", "gefluegelnews", "--data-dir", "data/unstructured"]
    )
    export_args = parser.parse_args(
        ["export-final", "--source", "gefluegelnews", "--source", "padi_web"]
    )

    assert enrich_args.command == "enrich"
    assert enrich_args.source == "gefluegelnews"
    assert enrich_args.data_dir == "data/unstructured"
    assert export_args.command == "export-final"
    assert export_args.sources == ["gefluegelnews", "padi_web"]


def test_cli_parser_accepts_fetch_limit():
    parser = build_parser()
    args = parser.parse_args(["fetch", "gefluegelnews", "--limit", "5"])

    assert args.command == "fetch"
    assert args.source == "gefluegelnews"
    assert args.limit == 5


def test_cli_parser_accepts_run_all_source_options():
    parser = build_parser()
    args = parser.parse_args(
        ["run-all", "--source", "gefluegelnews", "--source", "padi_web"]
    )

    assert args.command == "run-all"
    assert args.sources == ["gefluegelnews", "padi_web"]


def test_run_all_executes_all_pipeline_steps_for_selected_sources(
    monkeypatch, tmp_path, capsys
):
    calls = []

    def record(stage_name, source_index=1):
        def fake_stage(*args):
            calls.append((stage_name, args[source_index]))
            return 0

        return fake_stage

    monkeypatch.setattr(cli, "_discover", record("discover"))
    monkeypatch.setattr(cli, "_fetch", record("fetch"))
    monkeypatch.setattr(cli, "_parse", record("parse"))
    monkeypatch.setattr(cli, "_filter_disease", record("filter-disease"))
    monkeypatch.setattr(cli, "_extract_reports", record("extract-reports"))
    monkeypatch.setattr(cli, "_enrich", record("enrich"))

    def fake_export_final(*args):
        calls.append(("export-final", tuple(args[2])))
        return 0

    monkeypatch.setattr(cli, "_export_final", fake_export_final)

    exit_code = main(
        [
            "run-all",
            "--source",
            "padi_web",
            "--data-dir",
            str(tmp_path),
            "--delay-seconds",
            "0",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert calls == [
        ("discover", "padi_web"),
        ("fetch", "padi_web"),
        ("parse", "padi_web"),
        ("filter-disease", "padi_web"),
        ("extract-reports", "padi_web"),
        ("enrich", "padi_web"),
        ("export-final", ("padi_web",)),
    ]
    assert "Running 7 pipeline steps for padi_web" in captured.out
    assert "Completed 7 pipeline steps for 1 source" in captured.out


def test_run_all_runs_discover_and_fetch_in_parallel_for_multiple_sources(
    monkeypatch, tmp_path
):
    calls = []

    def slow_record(stage_name, source_index=1):
        def fake_stage(*args):
            source = args[source_index]
            calls.append((f"{stage_name}-start", source))
            time.sleep(0.02)
            calls.append((f"{stage_name}-end", source))
            return 0

        return fake_stage

    monkeypatch.setattr(cli, "_discover", slow_record("discover"))
    monkeypatch.setattr(cli, "_fetch", slow_record("fetch"))
    monkeypatch.setattr(cli, "_parse", lambda *args: 0)
    monkeypatch.setattr(cli, "_filter_disease", lambda *args: 0)
    monkeypatch.setattr(cli, "_extract_reports", lambda *args: 0)
    monkeypatch.setattr(cli, "_enrich", lambda *args: 0)
    monkeypatch.setattr(cli, "_export_final", lambda *args: 0)

    exit_code = main(
        [
            "run-all",
            "--source",
            "gefluegelnews",
            "--source",
            "padi_web",
            "--data-dir",
            str(tmp_path),
            "--delay-seconds",
            "0",
        ]
    )

    discover_start_positions = [
        index for index, call in enumerate(calls) if call[0] == "discover-start"
    ]
    discover_end_positions = [
        index for index, call in enumerate(calls) if call[0] == "discover-end"
    ]
    fetch_start_positions = [
        index for index, call in enumerate(calls) if call[0] == "fetch-start"
    ]
    fetch_end_positions = [
        index for index, call in enumerate(calls) if call[0] == "fetch-end"
    ]

    assert exit_code == 0
    assert len(discover_start_positions) == 2
    assert len(fetch_start_positions) == 2
    assert max(discover_start_positions) < min(discover_end_positions)
    assert max(fetch_start_positions) < min(fetch_end_positions)


def test_run_all_returns_nonzero_when_parallel_ingest_worker_raises(
    monkeypatch, tmp_path, capsys
):
    def fake_discover(*args):
        if args[1] == "padi_web":
            raise RuntimeError("discovery exploded")
        return 0

    monkeypatch.setattr(cli, "_discover", fake_discover)

    exit_code = main(
        [
            "run-all",
            "--source",
            "gefluegelnews",
            "--source",
            "padi_web",
            "--data-dir",
            str(tmp_path),
            "--delay-seconds",
            "0",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "discover failed for padi_web" in captured.out
    assert "discovery exploded" in captured.out


def test_default_config_resolves_data_dir_from_repo_root(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    config = load_config()
    data_dir = resolve_data_dir(None, config)

    assert data_dir.is_absolute()
    assert data_dir.name == "unstructured"
    assert data_dir.parent.name == "data"
    assert data_dir.parent.parent == config.project_root


def test_cli_parser_leaves_request_defaults_for_selected_source_resolution():
    config = load_config()
    parser = build_parser(config)
    args = parser.parse_args(["fetch", "gefluegelnews"])

    assert args.timeout_seconds is None
    assert args.delay_seconds is None
    assert args.limit is None


def test_limit_zero_overrides_source_default_to_unbounded():
    config = load_config()

    _, _, limit = cli._resolve_source_options(
        timeout_seconds=None,
        delay_seconds=None,
        limit=0,
        source_config=config.sources["gefluegelnews"],
    )

    assert limit is None


def test_config_exposes_source_url_validation_and_confidence_thresholds():
    config = load_config()

    assert config.sources["gefluegelnews"].article_path_prefix == "/article/"
    assert config.sources["gefluegelnews"].limit == 300
    assert config.sources["padi_web"].articles_api_path == "/en/articles/api/"
    assert config.disease_reports.confidence_thresholds == {
        "high": 4,
        "medium": 2,
        "low": 1,
    }


def test_fetch_stage_reports_limited_progress(monkeypatch, tmp_path, capsys):
    calls = []
    manifest_rows = [
        {"source_link": "https://www.gefluegelnews.de/article/one"},
        {"source_link": "https://www.gefluegelnews.de/article/two"},
        {"source_link": "https://www.gefluegelnews.de/article/three"},
    ]
    write_jsonl(tmp_path / "gefluegelnews" / "manifest.jsonl", manifest_rows)

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
            raw_html_path=str(base_dir / "gefluegelnews" / "raw_html" / "fake.html"),
            content_hash="abc123",
            canonical_url=source_link,
        )

    monkeypatch.setattr(
        "govtech_tierseuchen.gefluegelnews.fetch_and_cache_article",
        fake_fetch_and_cache_article,
    )

    exit_code = main(
        [
            "fetch",
            "gefluegelnews",
            "--data-dir",
            str(tmp_path),
            "--limit",
            "2",
            "--delay-seconds",
            "0",
        ]
    )

    captured = capsys.readouterr()
    rows = read_jsonl(tmp_path / "gefluegelnews" / "manifest.jsonl")
    assert exit_code == 0
    assert calls == [
        "https://www.gefluegelnews.de/article/one",
        "https://www.gefluegelnews.de/article/two",
    ]
    assert rows[0]["status_code"] == 200
    assert rows[1]["status_code"] == 200
    assert "status_code" not in rows[2]
    assert "Fetched 2 of 3 manifest entries" in captured.out


def test_enrich_cli_resolves_relative_prompt_and_output_from_project_root(
    monkeypatch, tmp_path
):
    config = load_config()
    seen = {}

    def fake_enrich_source(**kwargs):
        seen.update(kwargs)
        return SimpleNamespace(
            record_count=0,
            output_path=kwargs["output_path"],
            error_count=0,
        )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "govtech_tierseuchen.enrichment.enrich_source", fake_enrich_source
    )

    exit_code = main(
        [
            "enrich",
            "gefluegelnews",
            "--data-dir",
            str(tmp_path),
            "--prompt",
            "code/backend/interpreter/SystemPromptGN.md",
            "--output",
            "data/unstructured/gefluegelnews/custom.enriched.jsonl",
        ]
    )

    assert exit_code == 0
    assert (
        seen["prompt_path"]
        == config.project_root / "code/backend/interpreter/SystemPromptGN.md"
    )
    assert (
        seen["output_path"]
        == config.project_root / "data/unstructured/gefluegelnews/custom.enriched.jsonl"
    )


def test_discover_stage_returns_nonzero_on_network_failure(
    monkeypatch, tmp_path, capsys
):
    def fail_fetch_url(source_link, timeout_seconds):
        raise OSError("network down")

    monkeypatch.setattr("govtech_tierseuchen.gefluegelnews.fetch_url", fail_fetch_url)

    exit_code = main(["discover", "gefluegelnews", "--data-dir", str(tmp_path)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Discovery failed for gefluegelnews" in captured.out
    assert "network down" in captured.out


def test_parse_stage_skips_bad_html_and_writes_parse_error(tmp_path):
    good = cache_html(
        base_dir=tmp_path,
        source_link="https://www.gefluegelnews.de/article/good",
        html="""
        <section id="detailpage">
          <div id="main">
            <h1>Guter Artikel</h1>
            <div class="text"><p>Vogelgrippe in Polen.</p></div>
          </div>
        </section>
        """,
        status_code=200,
        fetched_at=datetime(2026, 5, 28, 12, 0, tzinfo=timezone.utc),
    )
    bad = cache_html(
        base_dir=tmp_path,
        source_link="https://www.gefluegelnews.de/article/bad",
        html="<html><body>no article title</body></html>",
        status_code=200,
        fetched_at=datetime(2026, 5, 28, 12, 0, tzinfo=timezone.utc),
    )
    write_jsonl(
        tmp_path / "gefluegelnews" / "manifest.jsonl",
        [
            {
                "source_link": good.source_link,
                "raw_html_path": good.raw_html_path,
                "content_hash": good.content_hash,
                "fetched_at": good.fetched_at.isoformat(),
            },
            {
                "source_link": bad.source_link,
                "raw_html_path": bad.raw_html_path,
                "content_hash": bad.content_hash,
                "fetched_at": bad.fetched_at.isoformat(),
            },
        ],
    )

    exit_code = main(["parse", "gefluegelnews", "--data-dir", str(tmp_path)])

    assert exit_code == 0
    articles = read_jsonl(tmp_path / "gefluegelnews" / "articles.jsonl")
    parse_errors = read_jsonl(tmp_path / "gefluegelnews" / "parse_errors.jsonl")
    assert [article["title"] for article in articles] == ["Guter Artikel"]
    assert parse_errors[0]["source_link"] == bad.source_link
    assert parse_errors[0]["error_type"] == "ValueError"


def test_parse_stage_records_missing_raw_path_and_missing_file(tmp_path):
    write_jsonl(
        tmp_path / "gefluegelnews" / "manifest.jsonl",
        [
            {"source_link": "https://www.gefluegelnews.de/article/no-path"},
            {
                "source_link": "https://www.gefluegelnews.de/article/missing",
                "raw_html_path": str(
                    tmp_path / "gefluegelnews" / "raw_html" / "gone.html"
                ),
            },
        ],
    )

    exit_code = main(["parse", "gefluegelnews", "--data-dir", str(tmp_path)])

    parse_errors = read_jsonl(tmp_path / "gefluegelnews" / "parse_errors.jsonl")
    assert exit_code == 0
    assert [error["error_type"] for error in parse_errors] == [
        "MissingRawPath",
        "MissingRawFile",
    ]


def test_parse_stage_records_type_error_from_malformed_manifest_row(tmp_path):
    fetched = cache_html(
        base_dir=tmp_path,
        source_link="https://www.gefluegelnews.de/article/malformed",
        html="""
        <section id="detailpage">
          <div id="main">
            <h1>Malformed metadata</h1>
            <div class="text"><p>Vogelgrippe in Polen.</p></div>
          </div>
        </section>
        """,
        status_code=200,
        fetched_at=datetime(2026, 5, 28, 12, 0, tzinfo=timezone.utc),
    )
    write_jsonl(
        tmp_path / "gefluegelnews" / "manifest.jsonl",
        [
            {
                "source_link": fetched.source_link,
                "raw_html_path": fetched.raw_html_path,
                "content_hash": fetched.content_hash,
                "fetched_at": None,
            }
        ],
    )

    exit_code = main(["parse", "gefluegelnews", "--data-dir", str(tmp_path)])

    articles = read_jsonl(tmp_path / "gefluegelnews" / "articles.jsonl")
    parse_errors = read_jsonl(tmp_path / "gefluegelnews" / "parse_errors.jsonl")
    assert exit_code == 0
    assert articles == []
    assert parse_errors[0]["error_type"] == "TypeError"


def test_parse_stage_rejects_raw_paths_outside_source_directory(tmp_path):
    outside_path = tmp_path / "outside.html"
    outside_path.write_text("<html><title>Outside</title></html>", encoding="utf-8")
    write_jsonl(
        tmp_path / "gefluegelnews" / "manifest.jsonl",
        [
            {
                "source_link": "https://www.gefluegelnews.de/article/outside",
                "raw_html_path": str(outside_path),
            }
        ],
    )

    exit_code = main(["parse", "gefluegelnews", "--data-dir", str(tmp_path)])

    articles = read_jsonl(tmp_path / "gefluegelnews" / "articles.jsonl")
    parse_errors = read_jsonl(tmp_path / "gefluegelnews" / "parse_errors.jsonl")
    assert exit_code == 0
    assert articles == []
    assert parse_errors[0]["error_type"] == "UnsafeRawPath"
