#!/usr/bin/env python3
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from rdflib import Graph, Namespace, RDF

TS = Namespace("https://data.tierseuchen-screener.example.org/ontology/adis#")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")


def month_of(lit):
    if lit is None:
        return None
    s = str(lit)
    if len(s) >= 7 and s[4] == "-":
        return s[:7]
    return None


def main():
    root = Path('/home/Dave/.openclaw/workspace-govtech')
    files = [
        root / 'data/rdf/adis/adis-events.ttl',
        root / 'data/rdf/adis/adis-situations.ttl',
        root / 'data/rdf/adis/adis-skos-generated.ttl',
        root / 'data/rdf/adis/adis-source-rows.ttl',
    ]
    g = Graph()
    for f in files:
        g.parse(f, format='turtle')

    events = set(g.subjects(RDF.type, TS.OutbreakEvent))
    situations = set(g.subjects(RDF.type, TS.OutbreakSituation))
    source_rows = set(g.subjects(RDF.type, TS.SourceRow))

    # skos by scheme
    scheme_counts = Counter()
    for c in g.subjects(RDF.type, SKOS.Concept):
        for s in g.objects(c, SKOS.inScheme):
            scheme_counts[str(s)] += 1

    # situation links
    orphan_events = []
    multi_link_events = []
    incoming = defaultdict(int)
    for e in events:
        links = list(g.objects(e, TS.belongsToSituation))
        if len(links) == 0:
            orphan_events.append(str(e))
        if len(links) > 1:
            multi_link_events.append(str(e))
        for s in links:
            incoming[s] += 1

    orphan_situations = [str(s) for s in situations if incoming[s] == 0]

    # situation key checks
    key_re = re.compile(r'^[a-z0-9\-]+\|[a-z0-9\-]+\|(\d{4}-\d{2}|unknown)$')
    situation_issues = []
    for s in situations:
        key = list(g.objects(s, TS.hasSituationKey))
        mon = list(g.objects(s, TS.situationMonth))
        dis = list(g.objects(s, TS.situationDisease))
        cty = list(g.objects(s, TS.situationCountry))
        if not key or not mon or not dis or not cty:
            situation_issues.append((str(s), 'missing required fields'))
            continue
        if not key_re.match(str(key[0])):
            situation_issues.append((str(s), f'bad key format: {key[0]}'))

    # date rule checks
    date_violations = []
    fallback_counts = Counter()
    for e in events:
        sit = next(iter(g.objects(e, TS.belongsToSituation)), None)
        if sit is None:
            continue
        sm = next(iter(g.objects(sit, TS.situationMonth)), None)
        sm = str(sm) if sm is not None else None
        c = next(iter(g.objects(e, TS.confirmationDate)), None)
        s = next(iter(g.objects(e, TS.suspicionStartDate)), None)
        sub = next(iter(g.objects(e, TS.submissionDate)), None)
        exp = month_of(c)
        source = 'confirmation'
        if exp is None:
            exp = month_of(s); source = 'suspicion'
        if exp is None:
            exp = month_of(sub); source = 'submitted'
        if exp is None:
            exp = 'unknown'; source = 'unknown'
        fallback_counts[source] += 1
        if sm != exp:
            date_violations.append((str(e), sm, exp, source))

    # coordinates
    with_coords = missing_coords = invalid_coords = 0
    for e in events:
        loc = next(iter(g.objects(e, TS.occursAt)), None)
        if loc is None:
            missing_coords += 1
            continue
        lat = next(iter(g.objects(loc, TS.latitude)), None)
        lon = next(iter(g.objects(loc, TS.longitude)), None)
        if lat is None or lon is None:
            missing_coords += 1
            continue
        try:
            la, lo = float(str(lat)), float(str(lon))
            if not (-90 <= la <= 90 and -180 <= lo <= 180):
                invalid_coords += 1
            else:
                with_coords += 1
        except Exception:
            invalid_coords += 1

    # raw + normalized
    raw_presence = Counter()
    norm_presence = Counter()
    for e in events:
        if list(g.objects(e, TS.countryLabel)): raw_presence['raw_country'] += 1
        if list(g.objects(e, TS.rawEventStatusLabel)): raw_presence['raw_status'] += 1
        if list(g.objects(e, TS.hasDisease)): norm_presence['disease'] += 1
        if list(g.objects(e, TS.hasEventStatus)): norm_presence['event_status'] += 1
        if list(g.objects(e, TS.belongsToSituation)): norm_presence['situation_link'] += 1

    # species via event hasSpecies
    for e in events:
        if list(g.objects(e, TS.hasSpecies)): norm_presence['species'] += 1

    # frontend readiness
    marker_capable = with_coords
    marker_capable_resolvable = 0
    for e in events:
        loc = next(iter(g.objects(e, TS.occursAt)), None)
        lat = next(iter(g.objects(loc, TS.latitude)), None) if loc else None
        lon = next(iter(g.objects(loc, TS.longitude)), None) if loc else None
        if lat is not None and lon is not None and list(g.objects(e, TS.belongsToSituation)):
            marker_capable_resolvable += 1

    report = {
        'counts': {
            'events': len(events),
            'situations': len(situations),
            'source_rows': len(source_rows),
            'skos_by_scheme': dict(scheme_counts),
        },
        'situation_links': {
            'orphan_events': len(orphan_events),
            'multi_link_events': len(multi_link_events),
            'orphan_situations': len(orphan_situations),
        },
        'situation_key_issues': situation_issues[:50],
        'date_rule': {
            'violations': len(date_violations),
            'fallback_counts': dict(fallback_counts),
        },
        'coordinates': {
            'with_coords': with_coords,
            'missing_coords': missing_coords,
            'invalid_coords': invalid_coords,
        },
        'raw_normalized': {
            'raw_presence': dict(raw_presence),
            'normalized_presence': dict(norm_presence),
        },
        'frontend_readiness': {
            'marker_capable_events': marker_capable,
            'marker_capable_events_resolvable_to_situation': marker_capable_resolvable,
        },
    }

    out = root / 'reports/qa'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'adis-rdf-qa-report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')

    md = [
        '# ADIS RDF QA Report',
        f"- Events: {len(events)}",
        f"- Situations: {len(situations)}",
        f"- Source rows: {len(source_rows)}",
        f"- Orphan events: {len(orphan_events)}",
        f"- Orphan situations: {len(orphan_situations)}",
        f"- Date rule violations: {len(date_violations)}",
        f"- Coordinates: with={with_coords}, missing={missing_coords}, invalid={invalid_coords}",
        f"- Marker-capable resolvable events: {marker_capable_resolvable}/{marker_capable}",
        '',
        '## SKOS concepts by scheme',
    ]
    for k,v in sorted(scheme_counts.items()):
        md.append(f"- {k}: {v}")
    md.append('')
    md.append('## Fallback counts')
    for k,v in fallback_counts.items():
        md.append(f"- {k}: {v}")

    (out / 'adis-rdf-qa-report.md').write_text('\n'.join(md), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
