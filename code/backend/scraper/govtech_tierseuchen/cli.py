from __future__ import annotations

import argparse
import hashlib
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from rich.console import Console
from rich.logging import RichHandler
from rich.progress import (
    BarColumn,
    Progress,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)

from govtech_tierseuchen.config import (
    AppConfig,
    SourceConfig,
    load_config,
    resolve_config_path,
)
from govtech_tierseuchen.jsonl import to_jsonable
from govtech_tierseuchen.models import ParseError
from govtech_tierseuchen.state import PipelineState, stable_fingerprint

LOGGER = logging.getLogger(__name__)
SOURCE_PIPELINE_STAGES = (
    "discover",
    "fetch",
    "parse",
    "filter-disease",
    "extract-reports",
    "enrich",
)
RUN_ALL_STEP_COUNT = len(SOURCE_PIPELINE_STAGES) + 1
FETCH_METADATA_FIELDS = {
    "fetched_at",
    "status_code",
    "raw_html_path",
    "content_hash",
    "canonical_url",
    "fetch_error_type",
    "fetch_error_message",
    "fetch_error_at",
}


def build_parser(config: AppConfig | None = None) -> argparse.ArgumentParser:
    config = config or load_config()
    parser = argparse.ArgumentParser(prog="ts-screener")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in config.scraper.commands:
        subparser = subparsers.add_parser(command)
        subparser.add_argument("source", choices=sorted(config.sources))
        _add_common_options(subparser)
    enrich_parser = subparsers.add_parser("enrich")
    enrich_parser.add_argument("source", choices=sorted(config.sources))
    enrich_parser.add_argument("--data-dir", default=None)
    enrich_parser.add_argument("--output", default=None)
    enrich_parser.add_argument("--prompt", default=None)
    enrich_parser.add_argument("--progress-every", type=int, default=None)
    enrich_parser.add_argument(
        "--force",
        action="store_true",
        help="Reprocess records even when the incremental state is current.",
    )
    export_parser = subparsers.add_parser("export-final")
    export_parser.add_argument(
        "--source",
        dest="sources",
        action="append",
        choices=sorted(config.sources),
        default=[],
        help="Source to export. Repeat to export multiple sources. Defaults to all sources.",
    )
    export_parser.add_argument("--data-dir", default=None)
    export_parser.add_argument("--rdf-output", default=None)
    export_parser.add_argument("--csv-output", default=None)
    run_all_parser = subparsers.add_parser("run-all")
    run_all_parser.add_argument(
        "--source",
        dest="sources",
        action="append",
        choices=sorted(config.sources),
        default=[],
        help="Source to run. Repeat to run multiple sources. Defaults to all sources.",
    )
    _add_common_options(run_all_parser)
    run_all_parser.add_argument("--rdf-output", default=None)
    run_all_parser.add_argument("--csv-output", default=None)
    return parser


def _add_common_options(subparser: argparse.ArgumentParser) -> None:
    subparser.add_argument("--data-dir", default=None)
    subparser.add_argument("--timeout-seconds", type=float, default=None)
    subparser.add_argument("--delay-seconds", type=float, default=None)
    subparser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum records to process; use 0 to disable a source default limit.",
    )
    subparser.add_argument(
        "--force",
        action="store_true",
        help="Reprocess records even when the incremental state is current.",
    )


def main(argv: list[str] | None = None) -> int:
    config = load_config()
    console = Console()
    _configure_logging(console, config)
    parser = build_parser(config)
    args = parser.parse_args(argv)
    data_dir = resolve_data_dir(args.data_dir, config)
    if args.command == "run-all":
        sources = args.sources or sorted(config.sources)
        rdf_output_path = resolve_final_rdf_path(args.rdf_output, config)
        csv_output_path = resolve_final_csv_path(args.csv_output, config)
        return _run_all(
            data_dir=data_dir,
            rdf_output_path=rdf_output_path,
            csv_output_path=csv_output_path,
            sources=sources,
            timeout_seconds=args.timeout_seconds,
            delay_seconds=args.delay_seconds,
            limit=args.limit,
            force=args.force,
            console=console,
            config=config,
        )
    if args.command == "export-final":
        sources = args.sources or sorted(config.sources)
        return _export_final(
            data_dir,
            resolve_final_rdf_path(args.rdf_output, config),
            sources,
            resolve_final_csv_path(args.csv_output, config),
            console,
            config,
        )

    source_config = config.sources[args.source]
    timeout_seconds, delay_seconds, limit = _resolve_source_options(
        getattr(args, "timeout_seconds", None),
        getattr(args, "delay_seconds", None),
        getattr(args, "limit", None),
        source_config,
    )
    if args.command == "discover":
        return _discover(data_dir, args.source, timeout_seconds, limit, console, config)
    if args.command == "fetch":
        return _fetch(
            data_dir,
            args.source,
            timeout_seconds,
            delay_seconds,
            limit,
            args.force,
            console,
            config,
        )
    if args.command == "parse":
        return _parse(data_dir, args.source, limit, args.force, console, config)
    if args.command == "filter-disease":
        return _filter_disease(data_dir, args.source, args.force, console, config)
    if args.command == "extract-reports":
        return _extract_reports(data_dir, args.source, args.force, console, config)
    if args.command == "enrich":
        output_path = resolve_config_path(args.output, config) if args.output else None
        prompt_path = resolve_config_path(args.prompt, config) if args.prompt else None
        return _enrich(
            data_dir,
            args.source,
            console,
            config,
            output_path=output_path,
            prompt_path=prompt_path,
            progress_every=args.progress_every,
            force=args.force,
        )
    parser.error(f"Unknown command {args.command}")
    return 2


def _resolve_source_options(
    timeout_seconds: float | None,
    delay_seconds: float | None,
    limit: int | None,
    source_config: SourceConfig,
) -> tuple[float, float, int | None]:
    resolved_timeout_seconds = (
        timeout_seconds
        if timeout_seconds is not None
        else source_config.timeout_seconds
    )
    resolved_delay_seconds = (
        delay_seconds if delay_seconds is not None else source_config.delay_seconds
    )
    if limit == 0:
        resolved_limit = None
    else:
        resolved_limit = limit if limit is not None else source_config.limit
    return resolved_timeout_seconds, resolved_delay_seconds, resolved_limit


def resolve_data_dir(value: str | None, config: AppConfig) -> Path:
    return resolve_config_path(value or config.scraper.data_dir, config)


def resolve_final_rdf_path(value: str | None, config: AppConfig) -> Path:
    return resolve_config_path(value or config.scraper.final_rdf_output, config)


def resolve_final_csv_path(value: str | None, config: AppConfig) -> Path:
    return resolve_config_path(value or config.scraper.final_csv_output, config)


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


def _merge_manifest_rows(
    discovered_rows: list[dict[str, Any]], existing_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    existing_by_link = {
        row["source_link"]: row for row in existing_rows if row.get("source_link")
    }
    discovered_links = set()
    merged = []
    for discovered in discovered_rows:
        source_link = discovered.get("source_link")
        if not source_link:
            continue
        discovered_links.add(source_link)
        existing = existing_by_link.get(source_link, {})
        if existing.get("last_modified") == discovered.get("last_modified"):
            base = existing
        else:
            base = {
                key: value
                for key, value in existing.items()
                if key not in FETCH_METADATA_FIELDS
            }
        merged.append({**base, **discovered})
    merged.extend(
        row
        for row in existing_rows
        if row.get("source_link") and row["source_link"] not in discovered_links
    )
    return merged


def _record_source_link(row: dict[str, Any]) -> str:
    return str(row.get("source_link") or "")


def _nested_article_source_link(row: dict[str, Any]) -> str:
    article = row.get("article")
    if isinstance(article, dict):
        return _record_source_link(article)
    return ""


def _fetch_fingerprint(row: dict[str, Any]) -> str:
    return stable_fingerprint(
        {
            "source_link": row.get("source_link"),
            "last_modified": row.get("last_modified"),
        }
    )


def _parse_fingerprint(row: dict[str, Any]) -> str:
    return stable_fingerprint(
        {
            "source_link": row.get("source_link"),
            "raw_html_path": row.get("raw_html_path"),
            "content_hash": row.get("content_hash"),
        }
    )


def _filter_fingerprint(row: dict[str, Any], config: AppConfig) -> str:
    return stable_fingerprint(
        {
            "article": row,
            "disease_filter": config.disease_filter,
        }
    )


def _extract_fingerprint(row: dict[str, Any], config: AppConfig) -> str:
    return stable_fingerprint(
        {
            "article": row,
            "disease_filter": config.disease_filter,
            "disease_reports": config.disease_reports,
        }
    )


def _cached_raw_artifact_is_safe(
    row: dict[str, Any], data_dir: Path, source: str, config: AppConfig
) -> bool:
    raw_path_value = row.get("raw_html_path")
    if not raw_path_value or not row.get("content_hash"):
        return False
    raw_path = _resolve_raw_artifact_path(Path(raw_path_value), data_dir)
    return _is_relative_to(raw_path, config.source_dir(data_dir, source)) and (
        raw_path.exists()
    )


def _fetch_metadata_from_existing_articles(
    article_rows: list[dict[str, Any]],
    data_dir: Path,
    source: str,
    config: AppConfig,
) -> dict[str, dict[str, Any]]:
    metadata_by_link = {}
    for article in article_rows:
        source_link = _record_source_link(article)
        if not source_link or not _cached_raw_artifact_is_safe(
            article, data_dir, source, config
        ):
            continue
        metadata = {
            "raw_html_path": article["raw_html_path"],
            "content_hash": article["content_hash"],
        }
        if article.get("retrieved_at"):
            metadata["fetched_at"] = article["retrieved_at"]
        if article.get("canonical_url"):
            metadata["canonical_url"] = article["canonical_url"]
        if article.get("status_code") is not None:
            metadata["status_code"] = article["status_code"]
        metadata_by_link[source_link] = metadata
    return metadata_by_link


def _merge_cached_fetch_metadata(
    row: dict[str, Any], metadata: dict[str, Any] | None
) -> dict[str, Any]:
    if not metadata:
        return row
    merged = dict(row)
    for key, value in metadata.items():
        if not merged.get(key):
            merged[key] = value
    return merged


def _raw_artifact_path_for_source(
    source: str, data_dir: Path, source_link: str
) -> Path:
    if source == "gefluegelnews":
        from govtech_tierseuchen.gefluegelnews import raw_html_path

        return raw_html_path(data_dir, source_link)
    if source == "padi_web":
        from govtech_tierseuchen.padi_web import raw_json_path

        return raw_json_path(data_dir, source_link)
    raise ValueError(f"Unsupported source: {source}")


def _fetch_metadata_from_raw_cache(
    row: dict[str, Any], data_dir: Path, source: str, config: AppConfig
) -> dict[str, Any] | None:
    source_link = _record_source_link(row)
    if not source_link:
        return None
    raw_path = _raw_artifact_path_for_source(source, data_dir, source_link)
    raw_path_row = {"raw_html_path": str(raw_path), "content_hash": "cached"}
    if not _cached_raw_artifact_is_safe(raw_path_row, data_dir, source, config):
        return None
    try:
        content_hash = hashlib.sha256(raw_path.read_bytes()).hexdigest()
    except OSError:
        return None
    return {
        "raw_html_path": str(raw_path),
        "content_hash": content_hash,
    }


def _fetcher_for_source(source: str) -> Callable[..., Any]:
    if source == "gefluegelnews":
        from govtech_tierseuchen.gefluegelnews import fetch_and_cache_article

        return fetch_and_cache_article
    if source == "padi_web":
        from govtech_tierseuchen.padi_web import fetch_and_cache_article

        return fetch_and_cache_article
    raise ValueError(f"Unsupported source: {source}")


def _parse_row_for_source(source: str, row: dict, raw_path: Path) -> Any:
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


def _discover(
    data_dir: Path,
    source: str,
    timeout_seconds: float,
    limit: int | None,
    console: Console,
    config: AppConfig,
) -> int:
    from govtech_tierseuchen.jsonl import read_jsonl, write_jsonl

    try:
        articles = _discover_articles(source, timeout_seconds, limit, console)
    except Exception as exc:
        LOGGER.debug("Discovery failed for %s", source, exc_info=True)
        console.print(f"[red]Discovery failed for {source}: {exc}[/red]")
        return 1

    if limit is not None:
        articles = articles[:limit]
    manifest_path = config.output_path(data_dir, source, "manifest")
    discovered_rows = [to_jsonable(article) for article in articles]
    rows = _merge_manifest_rows(discovered_rows, read_jsonl(manifest_path))
    write_jsonl(manifest_path, rows)
    console.print(f"[green]Discovered {len(articles)} {source} article URLs[/green]")
    return 0


def _discover_articles(
    source: str,
    timeout_seconds: float,
    limit: int | None,
    console: Console,
) -> list[Any]:
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
        seen_page_urls: set[str] = set()
        page_number = 0
        while next_url:
            if next_url in seen_page_urls:
                LOGGER.warning("Stopping repeated PADI pagination URL: %s", next_url)
                break
            seen_page_urls.add(next_url)
            page_number += 1
            console.print(
                f"[cyan]Fetching PADI discovery page {page_number} "
                f"({len(articles)} articles found so far)[/cyan]"
            )
            _, payload = fetch_json(next_url, timeout_seconds=timeout_seconds)
            page_articles, next_url = parse_article_page(
                payload, discovered_at=datetime.now(UTC)
            )
            articles.extend(page_articles)
            if limit is not None and len(articles) >= limit:
                articles = articles[:limit]
                break
    else:
        raise ValueError(f"Unsupported source: {source}")

    if limit is not None:
        articles = articles[:limit]
    return articles


def _run_all(
    data_dir: Path,
    rdf_output_path: Path,
    csv_output_path: Path,
    sources: list[str],
    timeout_seconds: float | None,
    delay_seconds: float | None,
    limit: int | None,
    force: bool,
    console: Console,
    config: AppConfig,
) -> int:
    source_options = {
        source: _resolve_source_options(
            timeout_seconds,
            delay_seconds,
            limit,
            config.sources[source],
        )
        for source in sources
    }
    for source in sources:
        console.print(
            f"[bold]Running {RUN_ALL_STEP_COUNT} pipeline steps for {source}[/bold]"
        )

    if len(sources) > 1:
        exit_code = _run_parallel_ingest_stages(
            data_dir=data_dir,
            sources=sources,
            source_options=source_options,
            force=force,
            console=console,
            config=config,
        )
        if exit_code != 0:
            return exit_code
        start_index = 3
        stages = SOURCE_PIPELINE_STAGES[2:]
    else:
        start_index = 1
        stages = SOURCE_PIPELINE_STAGES

    for source in sources:
        resolved_timeout_seconds, resolved_delay_seconds, resolved_limit = (
            source_options[source]
        )
        for index, stage in enumerate(stages, start=start_index):
            console.print(
                f"[cyan]{source}: step {index}/{RUN_ALL_STEP_COUNT} {stage}[/cyan]"
            )
            if stage == "discover":
                exit_code = _discover(
                    data_dir,
                    source,
                    resolved_timeout_seconds,
                    resolved_limit,
                    console,
                    config,
                )
            elif stage == "fetch":
                exit_code = _fetch(
                    data_dir,
                    source,
                    resolved_timeout_seconds,
                    resolved_delay_seconds,
                    resolved_limit,
                    force,
                    console,
                    config,
                )
            elif stage == "parse":
                exit_code = _parse(
                    data_dir, source, resolved_limit, force, console, config
                )
            elif stage == "filter-disease":
                exit_code = _filter_disease(data_dir, source, force, console, config)
            elif stage == "extract-reports":
                exit_code = _extract_reports(data_dir, source, force, console, config)
            elif stage == "enrich":
                exit_code = _enrich(data_dir, source, console, config, force)
            else:
                raise ValueError(f"Unsupported pipeline stage: {stage}")
            if exit_code != 0:
                console.print(
                    f"[red]Stopped at {stage} for {source} with exit code {exit_code}[/red]"
                )
                return exit_code
    console.print(
        f"[cyan]final: step {RUN_ALL_STEP_COUNT}/{RUN_ALL_STEP_COUNT} export-final[/cyan]"
    )
    exit_code = _export_final(
        data_dir,
        rdf_output_path,
        sources,
        csv_output_path,
        console,
        config,
    )
    if exit_code != 0:
        console.print(f"[red]Stopped at export-final with exit code {exit_code}[/red]")
        return exit_code
    source_label = "source" if len(sources) == 1 else "sources"
    console.print(
        f"[green]Completed {RUN_ALL_STEP_COUNT} pipeline steps for {len(sources)} {source_label}[/green]"
    )
    return 0


def _run_parallel_ingest_stages(
    data_dir: Path,
    sources: list[str],
    source_options: dict[str, tuple[float, float, int | None]],
    force: bool,
    console: Console,
    config: AppConfig,
) -> int:
    for stage in ("discover", "fetch"):
        console.print(f"[cyan]Running {stage} for {len(sources)} sources[/cyan]")
        with ThreadPoolExecutor(max_workers=len(sources)) as executor:
            futures = {}
            for source in sources:
                resolved_timeout_seconds, resolved_delay_seconds, resolved_limit = (
                    source_options[source]
                )
                console.print(
                    f"[cyan]{source}: step {SOURCE_PIPELINE_STAGES.index(stage) + 1}/{RUN_ALL_STEP_COUNT} {stage}[/cyan]"
                )
                if stage == "discover":
                    future = executor.submit(
                        _discover,
                        data_dir,
                        source,
                        resolved_timeout_seconds,
                        resolved_limit,
                        console,
                        config,
                    )
                else:
                    future = executor.submit(
                        _fetch,
                        data_dir,
                        source,
                        resolved_timeout_seconds,
                        resolved_delay_seconds,
                        resolved_limit,
                        force,
                        console,
                        config,
                    )
                futures[future] = source
            for future in as_completed(futures):
                source = futures[future]
                try:
                    exit_code = future.result()
                except Exception as exc:
                    LOGGER.debug("%s failed for %s", stage, source, exc_info=True)
                    console.print(f"[red]{stage} failed for {source}: {exc}[/red]")
                    return 1
                if exit_code != 0:
                    console.print(
                        f"[red]Stopped at {stage} for {source} with exit code {exit_code}[/red]"
                    )
                    return exit_code
    return 0


def _fetch(
    data_dir: Path,
    source: str,
    timeout_seconds: float,
    delay_seconds: float,
    limit: int | None,
    force: bool,
    console: Console,
    config: AppConfig,
) -> int:
    from govtech_tierseuchen.jsonl import read_jsonl, write_jsonl

    fetch_and_cache_article = _fetcher_for_source(source)
    manifest_path = config.output_path(data_dir, source, "manifest")
    rows = read_jsonl(manifest_path)
    cached_fetch_metadata = _fetch_metadata_from_existing_articles(
        read_jsonl(config.output_path(data_dir, source, "articles")),
        data_dir,
        source,
        config,
    )
    selected_rows = rows if limit is None else rows[:limit]
    untouched_rows = [] if limit is None else rows[limit:]
    fetched_rows = []
    fetched_count = 0
    skipped_count = 0
    state = PipelineState.from_data_dir(data_dir)
    state_updates: list[tuple[str, str]] = []

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
            record_key = _record_source_link(row)
            row = _merge_cached_fetch_metadata(
                row, cached_fetch_metadata.get(record_key)
            )
            row = _merge_cached_fetch_metadata(
                row, _fetch_metadata_from_raw_cache(row, data_dir, source, config)
            )
            fingerprint = _fetch_fingerprint(row)
            if (
                record_key
                and not force
                and _cached_raw_artifact_is_safe(row, data_dir, source, config)
            ):
                fetched_rows.append(row)
                state_updates.append((record_key, fingerprint))
                skipped_count += 1
                progress.advance(task)
                continue

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
                if record_key:
                    state_updates.append((record_key, fingerprint))
                fetched_count += 1
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
    state.mark_many(source=source, stage="fetch", records=state_updates)
    suffix = f"; skipped {skipped_count} current" if skipped_count else ""
    console.print(
        f"[green]Fetched {fetched_count} of {len(rows)} manifest entries{suffix}[/green]"
    )
    return 0


def _parse(
    data_dir: Path,
    source: str,
    limit: int | None,
    force: bool,
    console: Console,
    config: AppConfig,
) -> int:
    from govtech_tierseuchen.jsonl import read_jsonl, write_jsonl
    from govtech_tierseuchen.models import ParseError

    manifest = read_jsonl(config.output_path(data_dir, source, "manifest"))
    rows = manifest if limit is None else manifest[:limit]
    existing_articles = {
        _record_source_link(row): row
        for row in read_jsonl(config.output_path(data_dir, source, "articles"))
        if _record_source_link(row)
    }
    existing_parse_errors = {
        _record_source_link(row): row
        for row in read_jsonl(config.output_path(data_dir, source, "parse_errors"))
        if _record_source_link(row)
    }
    state = PipelineState.from_data_dir(data_dir)
    state_updates: list[tuple[str, str]] = []
    parsed = []
    parse_errors = []
    for row in rows:
        record_key = _record_source_link(row)
        fingerprint = _parse_fingerprint(row)
        if record_key and not force:
            stored_fingerprint = state.fingerprint_for(
                source=source, stage="parse", record_key=record_key
            )
            state_current = stored_fingerprint == fingerprint
            bootstrap_current = (
                stored_fingerprint is None
                and record_key in existing_articles
                and existing_articles[record_key].get("content_hash")
                == row.get("content_hash")
            )
            if state_current or bootstrap_current:
                if record_key in existing_articles:
                    parsed.append(existing_articles[record_key])
                    state_updates.append((record_key, fingerprint))
                    continue
                if record_key in existing_parse_errors:
                    parse_errors.append(existing_parse_errors[record_key])
                    state_updates.append((record_key, fingerprint))
                    continue

        raw_path_value = row.get("raw_html_path")
        if not raw_path_value:
            parse_errors.append(
                _parse_error_for_row(
                    row, "", "MissingRawPath", "Missing raw artifact path"
                )
            )
            continue
        raw_html_path = _resolve_raw_artifact_path(Path(raw_path_value), data_dir)
        if not _is_relative_to(raw_html_path, config.source_dir(data_dir, source)):
            parse_errors.append(
                _parse_error_for_row(
                    row,
                    str(raw_html_path),
                    "UnsafeRawPath",
                    "Raw artifact path is outside the source data directory",
                )
            )
            continue
        if not raw_html_path.exists():
            parse_errors.append(
                _parse_error_for_row(
                    row,
                    str(raw_html_path),
                    "MissingRawFile",
                    "Raw artifact path does not exist",
                )
            )
            continue
        try:
            parsed.append(_parse_row_for_source(source, row, raw_html_path))
            if record_key:
                state_updates.append((record_key, fingerprint))
        except (KeyError, TypeError, ValueError) as exc:
            parse_errors.append(
                ParseError(
                    source_link=row.get("source_link", ""),
                    raw_html_path=str(raw_html_path),
                    error_type=type(exc).__name__,
                    message=str(exc),
                    occurred_at=datetime.now(UTC),
                )
            )
            if record_key:
                state_updates.append((record_key, fingerprint))
    write_jsonl(config.output_path(data_dir, source, "articles"), parsed)
    write_jsonl(config.output_path(data_dir, source, "parse_errors"), parse_errors)
    state.mark_many(source=source, stage="parse", records=state_updates)
    console.print(
        f"[green]Parsed {len(parsed)} articles[/green]; "
        f"[yellow]{len(parse_errors)} parse errors[/yellow]"
    )
    return 0


def _parse_error_for_row(
    row: dict[str, Any], raw_html_path: str, error_type: str, message: str
) -> ParseError:
    return ParseError(
        source_link=row.get("source_link", ""),
        raw_html_path=raw_html_path,
        error_type=error_type,
        message=message,
        occurred_at=datetime.now(UTC),
    )


def _resolve_raw_artifact_path(path: Path, data_dir: Path) -> Path:
    if path.is_absolute():
        return path.resolve()
    return (data_dir / path).resolve()


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def _filter_disease(
    data_dir: Path, source: str, force: bool, console: Console, config: AppConfig
) -> int:
    from govtech_tierseuchen.disease_filter import assess_disease_relevance
    from govtech_tierseuchen.jsonl import read_jsonl, write_jsonl
    from govtech_tierseuchen.models import news_article_from_dict

    article_rows = read_jsonl(config.output_path(data_dir, source, "articles"))
    existing_relevant = {
        _nested_article_source_link(row): row
        for row in read_jsonl(config.output_path(data_dir, source, "disease_articles"))
        if _nested_article_source_link(row)
    }
    state = PipelineState.from_data_dir(data_dir)
    state_updates: list[tuple[str, str]] = []
    relevant = []
    for row in article_rows:
        record_key = _record_source_link(row)
        fingerprint = _filter_fingerprint(row, config)
        if record_key and not force:
            stored_fingerprint = state.fingerprint_for(
                source=source, stage="filter-disease", record_key=record_key
            )
            state_current = stored_fingerprint == fingerprint
            bootstrap_current = (
                stored_fingerprint is None
                and record_key in existing_relevant
                and (
                    existing_relevant[record_key].get("article", {}).get("content_hash")
                    == row.get("content_hash")
                )
            )
            if state_current or bootstrap_current:
                if record_key in existing_relevant:
                    relevant.append(existing_relevant[record_key])
                state_updates.append((record_key, fingerprint))
                continue

        article = news_article_from_dict(row)
        relevance = assess_disease_relevance(article)
        if relevance.is_relevant:
            relevant.append({"article": article, "relevance": relevance})
        if record_key:
            state_updates.append((record_key, fingerprint))
    write_jsonl(config.output_path(data_dir, source, "disease_articles"), relevant)
    state.mark_many(source=source, stage="filter-disease", records=state_updates)
    console.print(
        f"[green]Filtered {len(relevant)} disease-relevant articles from {len(article_rows)} parsed articles[/green]"
    )
    return 0


def _extract_reports(
    data_dir: Path, source: str, force: bool, console: Console, config: AppConfig
) -> int:
    from govtech_tierseuchen.disease_filter import assess_disease_relevance
    from govtech_tierseuchen.disease_reports import extract_report_rules
    from govtech_tierseuchen.jsonl import read_jsonl, write_jsonl
    from govtech_tierseuchen.models import news_article_from_dict

    article_rows = read_jsonl(config.output_path(data_dir, source, "articles"))
    existing_reports = {
        _record_source_link(row): row
        for row in read_jsonl(config.output_path(data_dir, source, "disease_reports"))
        if _record_source_link(row)
    }
    state = PipelineState.from_data_dir(data_dir)
    state_updates: list[tuple[str, str]] = []
    reports = []
    for row in article_rows:
        record_key = _record_source_link(row)
        fingerprint = _extract_fingerprint(row, config)
        if record_key and not force:
            stored_fingerprint = state.fingerprint_for(
                source=source, stage="extract-reports", record_key=record_key
            )
            state_current = stored_fingerprint == fingerprint
            bootstrap_current = (
                stored_fingerprint is None
                and record_key in existing_reports
                and existing_reports[record_key].get("content_hash")
                == row.get("content_hash")
            )
            if state_current or bootstrap_current:
                if record_key in existing_reports:
                    reports.append(existing_reports[record_key])
                state_updates.append((record_key, fingerprint))
                continue

        article = news_article_from_dict(row)
        relevance = assess_disease_relevance(article)
        if relevance.is_relevant:
            reports.append(extract_report_rules(article, relevance))
        if record_key:
            state_updates.append((record_key, fingerprint))
    write_jsonl(config.output_path(data_dir, source, "disease_reports"), reports)
    state.mark_many(source=source, stage="extract-reports", records=state_updates)
    console.print(
        f"[green]Extracted {len(reports)} candidate DiseaseReport records[/green]"
    )
    return 0


def _enrich(
    data_dir: Path,
    source: str,
    console: Console,
    config: AppConfig,
    force: bool = False,
    *,
    output_path: Path | None = None,
    prompt_path: Path | None = None,
    progress_every: int | None = None,
) -> int:
    from govtech_tierseuchen.enrichment import enrich_source

    try:
        result = enrich_source(
            data_dir=data_dir,
            source=source,
            config=config,
            output_path=output_path,
            prompt_path=prompt_path,
            progress_every=progress_every,
            force=force,
        )
    except (FileNotFoundError, OSError, RuntimeError) as exc:
        console.print(f"[red]Enrichment failed for {source}: {exc}[/red]")
        return 1
    console.print(
        "[green]Enriched "
        f"{result.record_count} DiseaseReport records for {source} "
        f"to {result.output_path}[/green]"
    )
    if result.error_count:
        console.print(
            f"[yellow]{result.error_count} enrichment errors recorded[/yellow]"
        )
    return 0


def _export_final(
    data_dir: Path,
    rdf_output_path: Path,
    sources: list[str],
    csv_output_path: Path,
    console: Console,
    config: AppConfig,
) -> int:
    from govtech_tierseuchen.csv_export import (
        export_records_to_csv,
        export_records_to_frontend_reports_csv,
    )
    from govtech_tierseuchen.jsonl import read_jsonl
    from govtech_tierseuchen.rdf_export import (
        disease_report_from_dict,
        export_disease_reports_to_rdf,
    )

    rows = []
    for source in sources:
        rows.extend(
            read_jsonl(config.output_path(data_dir, source, "enriched_disease_reports"))
        )
    if not rows:
        console.print(
            "[red]No enriched DiseaseReport records found for final export[/red]"
        )
        return 1
    reports = [disease_report_from_dict(row) for row in rows]
    rdf_result = export_disease_reports_to_rdf(reports, rdf_output_path)
    csv_result = export_records_to_csv(rows, csv_output_path)
    frontend_csv_result = export_records_to_frontend_reports_csv(rows, csv_output_path)
    console.print(
        "[green]Exported final outputs for "
        f"{rdf_result.report_count} DiseaseReport records: "
        f"{rdf_result.triple_count} RDF triples to {rdf_result.output_path}, "
        f"{csv_result.record_count} CSV rows to {csv_result.output_path}, "
        f"{frontend_csv_result.record_count} frontend report CSV rows to "
        f"{frontend_csv_result.output_path}[/green]"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
