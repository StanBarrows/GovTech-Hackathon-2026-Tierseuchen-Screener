# Notes

## Gefluegelnews fetch backfill behavior

- Root cause found 2026-05-29: `ts-screener run-all --source gefluegelnews`
  was slow because discovery can refresh `manifest.jsonl` with discovery-only
  rows. When fetch metadata is absent, the fetch stage previously ignored local
  `articles.jsonl` and deterministic `raw_html/` cache files, so it attempted a
  full sitemap refetch.
- Normal Gefluegelnews runs are intentionally capped in `config.yaml`; use
  `--limit 0` only when a full historical backfill is deliberate.
- Relevance-count surprise found 2026-05-29: `articles.jsonl` had 3,553 parsed
  Gefluegelnews articles, but `disease_articles.jsonl` and
  `disease_reports.jsonl` had only 43 records while `pipeline_state.sqlite`
  marked all 3,553 `filter-disease`/`extract-reports` records current. The
  output files were stale/partial relative to the state. Force the deterministic
  stages (`filter-disease` and `extract-reports`) before investigating term
  recall; recomputing current rules found 983 relevant candidates.
- Known false-positive driver: the rules currently treat any single configured
  term as relevant. Weak context terms such as `Biosicherheit`, `Tierseuche`,
  `Ausbruch`, and `Keulung` can pull in symposium, insurance, market, or
  general biosecurity articles. Prefer requiring a strong disease anchor and
  using those weak terms only as score boosters.
