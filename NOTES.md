# Notes

## Gefluegelnews fetch backfill behavior

- Root cause found 2026-05-29: `ts-screener run-all --source gefluegelnews`
  was slow because discovery can refresh `manifest.jsonl` with discovery-only
  rows. When fetch metadata is absent, the fetch stage previously ignored local
  `articles.jsonl` and deterministic `raw_html/` cache files, so it attempted a
  full sitemap refetch.
- Normal Gefluegelnews runs are intentionally capped in `config.yaml`; use
  `--limit 0` only when a full historical backfill is deliberate.
