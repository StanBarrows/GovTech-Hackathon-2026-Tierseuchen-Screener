from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path


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
    write_jsonl(data_dir / "gefluegelnews" / "manifest.jsonl", articles)
    return 0


def _fetch(
    data_dir: Path, timeout_seconds: float, delay_seconds: float, limit: int | None
) -> int:
    from govtech_tierseuchen.gefluegelnews import fetch_and_cache_article
    from govtech_tierseuchen.jsonl import read_jsonl, write_jsonl

    manifest_path = data_dir / "gefluegelnews" / "manifest.jsonl"
    rows = read_jsonl(manifest_path)
    selected_rows = rows if limit is None else rows[:limit]
    untouched_rows = [] if limit is None else rows[limit:]
    fetched_rows = []
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
    from govtech_tierseuchen.gefluegelnews import parse_article_html
    from govtech_tierseuchen.jsonl import read_jsonl, write_jsonl
    from govtech_tierseuchen.models import ParseError

    manifest = read_jsonl(data_dir / "gefluegelnews" / "manifest.jsonl")
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
    write_jsonl(data_dir / "gefluegelnews" / "articles.jsonl", parsed)
    write_jsonl(data_dir / "gefluegelnews" / "parse_errors.jsonl", parse_errors)
    return 0


def _filter_disease(data_dir: Path) -> int:
    from govtech_tierseuchen.disease_filter import assess_disease_relevance
    from govtech_tierseuchen.jsonl import read_jsonl, write_jsonl
    from govtech_tierseuchen.models import news_article_from_dict

    articles = [
        news_article_from_dict(row)
        for row in read_jsonl(data_dir / "gefluegelnews" / "articles.jsonl")
    ]
    relevant = []
    for article in articles:
        relevance = assess_disease_relevance(article)
        if relevance.is_relevant:
            relevant.append({"article": article, "relevance": relevance})
    write_jsonl(data_dir / "gefluegelnews" / "disease_articles.jsonl", relevant)
    return 0


def _extract_reports(data_dir: Path) -> int:
    from govtech_tierseuchen.disease_filter import assess_disease_relevance
    from govtech_tierseuchen.disease_reports import extract_report_rules
    from govtech_tierseuchen.jsonl import read_jsonl, write_jsonl
    from govtech_tierseuchen.models import news_article_from_dict

    articles = [
        news_article_from_dict(row)
        for row in read_jsonl(data_dir / "gefluegelnews" / "articles.jsonl")
    ]
    reports = []
    for article in articles:
        relevance = assess_disease_relevance(article)
        if relevance.is_relevant:
            reports.append(extract_report_rules(article, relevance))
    write_jsonl(data_dir / "gefluegelnews" / "disease_reports.jsonl", reports)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
