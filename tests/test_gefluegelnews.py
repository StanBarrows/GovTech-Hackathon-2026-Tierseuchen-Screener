from datetime import datetime, timezone
from pathlib import Path

from govtech_tierseuchen.cli import build_parser, main
from govtech_tierseuchen.gefluegelnews import (
    cache_html,
    fetch_and_cache_article,
    parse_article_html,
    parse_sitemap_articles,
)
from govtech_tierseuchen.jsonl import read_jsonl, write_jsonl


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
