from __future__ import annotations

import argparse
from pathlib import Path

from govtech_tierseuchen.config import load_config, resolve_config_path
from govtech_tierseuchen.enrichment import enrich_source


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract semantic DiseaseReport fields from JSONL candidates."
    )
    parser.add_argument("source", choices=sorted(load_config().sources))
    parser.add_argument("--data-dir", default=None)
    parser.add_argument("--prompt", default=None)
    parser.add_argument("--output", default=None)
    parser.add_argument("--progress-every", type=int, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    config = load_config()
    parser = build_parser()
    args = parser.parse_args(argv)
    data_dir = resolve_config_path(args.data_dir or config.scraper.data_dir, config)
    result = enrich_source(
        data_dir=data_dir,
        source=args.source,
        config=config,
        prompt_path=Path(args.prompt) if args.prompt else None,
        output_path=Path(args.output) if args.output else None,
        progress_every=args.progress_every,
    )
    print(
        f"enriched {result.record_count} records for {args.source} "
        f"to {result.output_path}"
    )
    if result.error_count:
        print(f"{result.error_count} enrichment errors recorded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
