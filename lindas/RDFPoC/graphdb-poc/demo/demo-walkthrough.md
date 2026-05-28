# Demo Walkthrough (5 minutes)

1. Load all files from `graphdb-poc/load/` in the README order.
2. Run `queries/01-counts.rq` to show data loaded.
3. Run `queries/02-situations-with-event-counts.rq` to show ADIS situation aggregation.
4. Pick demo event (already embedded in Query 3):
   - `https://data.tierseuchen-screener.example.org/data/event_de-hpai-non-p-2026-06u4a`
5. Run `queries/03-marker-to-paff-report.rq`.
6. Explain returned chain:
   - ADIS event -> shared situation -> PAFF statement -> PAFF report -> evidence snippet.
7. Highlight value:
   - structured ADIS outbreak facts
   - unstructured PAFF context linked to same disease-country-month situation
   - candidate extraction status + confidence
   - traceable evidence snippets
   - no publication claim, no hallucinated authoritative facts
