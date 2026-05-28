from __future__ import annotations

import argparse
import logging
from datetime import UTC, datetime
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler
from rich.progress import (
    BarColumn,
    Progress,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)

from govtech_tierseuchen.config import AppConfig, load_config, resolve_config_path

LOGGER = logging.getLogger(__name__)


def build_parser(config: AppConfig | None = None) -> argparse.ArgumentParser:
    config = config or load_config()
    default_source = next(iter(config.sources.values()))
    parser = argparse.ArgumentParser(prog="ts")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in config.scraper.commands:
        subparser = subparsers.add_parser(command)
        subparser.add_argument("source", choices=sorted(config.sources))
        subparser.add_argument("--data-dir", default=None)
        subparser.add_argument(
            "--timeout-seconds", type=float, default=default_source.timeout_seconds
        )
        subparser.add_argument(
            "--delay-seconds", type=float, default=default_source.delay_seconds
        )
        subparser.add_argument("--limit", type=int, default=default_source.limit)
        if command == "export-rdf":
            subparser.add_argument("--rdf-dir", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    config = load_config()
    console = Console()
    _configure_logging(console, config)
    parser = build_parser(config)
    args = parser.parse_args(argv)
    data_dir = resolve_data_dir(args.data_dir, config)
    if args.command == "discover":
        return _discover(data_dir, args.source, args.timeout_seconds, console, config)
    if args.command == "fetch":
        return _fetch(
            data_dir,
            args.source,
            args.timeout_seconds,
            args.delay_seconds,
            args.limit,
            console,
            config,
        )
    if args.command == "parse":
        return _parse(data_dir, args.source, args.limit, console, config)
    if args.command == "filter-disease":
        return _filter_disease(data_dir, args.source, console, config)
    if args.command == "extract-reports":
        return _extract_reports(data_dir, args.source, console, config)
    if args.command == "export-rdf":
        rdf_dir = resolve_rdf_dir(args.rdf_dir, config)
        return _export_rdf(data_dir, rdf_dir, args.source, console, config)
    parser.error(f"Unknown command {args.command}")
    return 2


def resolve_data_dir(value: str | None, config: AppConfig) -> Path:
    return resolve_config_path(value or config.scraper.data_dir, config)


def resolve_rdf_dir(value: str | None, config: AppConfig) -> Path:
    return resolve_config_path(value or config.scraper.rdf_output_dir, config)


def _configure_logging(console: Console, config: AppConfig) -> None:
    logging.basicConfig(
        level=getattr(logging, config.scraper.log_level.upper()),
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(console=console, markup=True, show_path=False, show_time=False)
        ],
        force=True,
    )


def _discover(
    data_dir: Path,
    source: str,
    timeout_seconds: float,
    console: Console,
    config: AppConfig,
) -> int:
    from govtech_tierseuchen.gefluegelnews import (
        SITEMAP_URL,
        fetch_url,
        parse_sitemap_articles,
    )
    from govtech_tierseuchen.jsonl import write_jsonl

    _, xml = fetch_url(SITEMAP_URL, timeout_seconds=timeout_seconds)
    articles = parse_sitemap_articles(
        xml.encode("utf-8"), discovered_at=datetime.now(UTC)
    )
    write_jsonl(config.output_path(data_dir, source, "manifest"), articles)
    console.print(
        f"[green]Discovered {len(articles)} Gefluegelnews article URLs[/green]"
    )
    return 0


def _fetch(
    data_dir: Path,
    source: str,
    timeout_seconds: float,
    delay_seconds: float,
    limit: int | None,
    console: Console,
    config: AppConfig,
) -> int:
    from govtech_tierseuchen.gefluegelnews import fetch_and_cache_article
    from govtech_tierseuchen.jsonl import read_jsonl, write_jsonl

    manifest_path = config.output_path(data_dir, source, "manifest")
    rows = read_jsonl(manifest_path)
    selected_rows = rows if limit is None else rows[:limit]
    untouched_rows = [] if limit is None else rows[limit:]
    fetched_rows = []

    with Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(
            config.scraper.progress_description, total=len(selected_rows)
        )
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
                LOGGER.warning(
                    "Fetch failed for %s: %s", row["source_link"], fetched.message
                )
                merged.update(
                    {
                        "fetch_error_type": fetched.error_type,
                        "fetch_error_message": fetched.message,
                        "fetch_error_at": fetched.occurred_at.isoformat(),
                    }
                )
            fetched_rows.append(merged)
            progress.advance(task)
    write_jsonl(manifest_path, [*fetched_rows, *untouched_rows])
    console.print(
        f"[green]Fetched {len(selected_rows)} of {len(rows)} manifest entries[/green]"
    )
    return 0


def _parse(
    data_dir: Path,
    source: str,
    limit: int | None,
    console: Console,
    config: AppConfig,
) -> int:
    from govtech_tierseuchen.gefluegelnews import parse_article_html
    from govtech_tierseuchen.jsonl import read_jsonl, write_jsonl
    from govtech_tierseuchen.models import ParseError

    manifest = read_jsonl(config.output_path(data_dir, source, "manifest"))
    rows = manifest if limit is None else manifest[:limit]
    parsed = []
    parse_errors = []
    for row in rows:
        raw_path_value = row.get("raw_html_path")
        if not raw_path_value:
            continue
        raw_html_path = Path(raw_path_value)
        if not raw_html_path.exists():
            continue
        html = raw_html_path.read_text(encoding="utf-8")
        try:
            parsed.append(
                parse_article_html(
                    html=html,
                    source_link=row["source_link"],
                    raw_html_path=raw_html_path,
                    content_hash=row.get("content_hash", ""),
                    retrieved_at=datetime.fromisoformat(
                        row.get("fetched_at", datetime.now(UTC).isoformat())
                    ),
                )
            )
        except (KeyError, ValueError) as exc:
            parse_errors.append(
                ParseError(
                    source_link=row.get("source_link", ""),
                    raw_html_path=str(raw_html_path),
                    error_type=type(exc).__name__,
                    message=str(exc),
                    occurred_at=datetime.now(UTC),
                )
            )
    write_jsonl(config.output_path(data_dir, source, "articles"), parsed)
    write_jsonl(config.output_path(data_dir, source, "parse_errors"), parse_errors)
    console.print(
        f"[green]Parsed {len(parsed)} articles[/green]; "
        f"[yellow]{len(parse_errors)} parse errors[/yellow]"
    )
    return 0


def _filter_disease(
    data_dir: Path, source: str, console: Console, config: AppConfig
) -> int:
    from govtech_tierseuchen.disease_filter import assess_disease_relevance
    from govtech_tierseuchen.jsonl import read_jsonl, write_jsonl
    from govtech_tierseuchen.models import news_article_from_dict

    articles = [
        news_article_from_dict(row)
        for row in read_jsonl(config.output_path(data_dir, source, "articles"))
    ]
    relevant = []
    for article in articles:
        relevance = assess_disease_relevance(article)
        if relevance.is_relevant:
            relevant.append({"article": article, "relevance": relevance})
    write_jsonl(config.output_path(data_dir, source, "disease_articles"), relevant)
    console.print(
        f"[green]Filtered {len(relevant)} disease-relevant articles from {len(articles)} parsed articles[/green]"
    )
    return 0


def _extract_reports(
    data_dir: Path, source: str, console: Console, config: AppConfig
) -> int:
    from govtech_tierseuchen.disease_filter import assess_disease_relevance
    from govtech_tierseuchen.disease_reports import extract_report_rules
    from govtech_tierseuchen.jsonl import read_jsonl, write_jsonl
    from govtech_tierseuchen.models import news_article_from_dict

    articles = [
        news_article_from_dict(row)
        for row in read_jsonl(config.output_path(data_dir, source, "articles"))
    ]
    reports = []
    for article in articles:
        relevance = assess_disease_relevance(article)
        if relevance.is_relevant:
            reports.append(extract_report_rules(article, relevance))
    write_jsonl(config.output_path(data_dir, source, "disease_reports"), reports)
    console.print(
        f"[green]Extracted {len(reports)} candidate DiseaseReport records[/green]"
    )
    return 0


def _export_rdf(
    data_dir: Path,
    rdf_dir: Path,
    source: str,
    console: Console,
    config: AppConfig,
) -> int:
    from govtech_tierseuchen.jsonl import read_jsonl
    from govtech_tierseuchen.rdf_export import (
        disease_report_from_dict,
        export_disease_reports_to_rdf,
    )

    rows = read_jsonl(config.output_path(data_dir, source, "disease_reports"))
    reports = [disease_report_from_dict(row) for row in rows]
    output_path = rdf_dir / config.sources[source].output_dir / f"{source}.ttl"
    result = export_disease_reports_to_rdf(reports, output_path)
    console.print(
        "[green]Exported "
        f"{result.report_count} DiseaseReport records as {result.triple_count} RDF triples "
        f"to {result.output_path}[/green]"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
