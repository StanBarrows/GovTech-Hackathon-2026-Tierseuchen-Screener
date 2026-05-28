# GraphDB PoC: ADIS ↔ PAFF linkage via OutbreakSituation

## Purpose
Fast demo bundle showing how ADIS outbreak events and PAFF candidate statements connect through shared `ts:OutbreakSituation`.

## Load files (recommended order)
1. `load/00-ontology.ttl`
2. `load/01-skos-core.ttl`
3. `load/02-skos-generated-adis.ttl`
4. `load/10-adis-events.ttl`
5. `load/11-adis-situations.ttl`
6. `load/12-adis-source-rows.ttl`
7. `load/20-paff-candidate-sample.ttl`

Use **default graph** for this PoC (simplest demo path).

## Connection model
`ts:OutbreakEvent` -> `ts:belongsToSituation` -> `ts:OutbreakSituation` <- `ts:describesSituation` <- `ts:PaffSituationStatement` <- `ts:extractedFromSource` <- `ts:PaffReport`

## First query to run
- `queries/01-counts.rq` (sanity check)
- then `queries/03-marker-to-paff-report.rq` for end-to-end linkage

## Expected result
For event:
`https://data.tierseuchen-screener.example.org/data/event_de-hpai-non-p-2026-06u4a`

You should get linked situation + PAFF statement + PAFF report + evidence snippet + relevance/severity/reach + prevention text.
