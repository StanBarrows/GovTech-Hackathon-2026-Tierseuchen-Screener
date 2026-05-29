#!/usr/bin/env python3
import csv
import hashlib
import re
from collections import defaultdict
from pathlib import Path
from rdflib import Graph, Namespace, Literal, RDF, SKOS, XSD

TS = Namespace("https://data.tierseuchen-screener.example.org/ontology/adis#")
TSD = Namespace("https://data.tierseuchen-screener.example.org/data/")
TSS = Namespace("https://data.tierseuchen-screener.example.org/skos/")


def slug(s: str) -> str:
    if s is None:
        return "unknown"
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "unknown"


def parse_date(v: str):
    if not v or v in ("NaN", "N/A"):
        return None
    return v


def parse_decimal(v: str):
    if not v or v in ("NaN", "N/A"):
        return None
    return v.replace(",", ".")


def ensure_concept(g, scheme, concept_uri, label, cls=None):
    g.add((scheme, RDF.type, SKOS.ConceptScheme))
    g.add((concept_uri, RDF.type, SKOS.Concept))
    g.add((concept_uri, SKOS.inScheme, scheme))
    g.add((concept_uri, SKOS.prefLabel, Literal(label)))
    if cls is not None:
        g.add((concept_uri, RDF.type, cls))


def main():
    root = Path("/home/Dave/.openclaw/workspace-govtech")
    csv_path = (
        root
        / "GovTech-Hackathon-2026-Tierseuchen-Screener/data/structured/adis/adis-outbreaks-20260519.csv"
    )

    out_dir = root / "data/rdf/adis"
    out_dir.mkdir(parents=True, exist_ok=True)
    rep_dir = root / "reports/conversion"
    rep_dir.mkdir(parents=True, exist_ok=True)

    g_events = Graph()
    g_events.bind("ts", TS)
    g_events.bind("tsd", TSD)
    g_situations = Graph()
    g_situations.bind("ts", TS)
    g_situations.bind("tsd", TSD)
    g_skos = Graph()
    g_skos.bind("ts", TS)
    g_skos.bind("tss", TSS)
    g_skos.bind("skos", SKOS)
    g_rows = Graph()
    g_rows.bind("ts", TS)
    g_rows.bind("tsd", TSD)

    counts = defaultdict(int)

    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            counts["rows"] += 1
            ref = (row.get("Reference") or "").strip()
            if not ref:
                counts["skipped"] += 1
                continue

            evt = TSD[f"event_{slug(ref)}"]
            g_events.add((evt, RDF.type, TS.OutbreakEvent))
            g_events.add((evt, TS.referenceId, Literal(ref)))
            if row.get("National reference") and row.get("National reference") != "NaN":
                g_events.add(
                    (evt, TS.nationalReferenceId, Literal(row["National reference"]))
                )

            # raw fields
            raw_map = {
                "country": "Country/Territory",
                "disease": "Disease name",
                "disease_type": "Disease type",
                "species": "Species 1",
                "status": "Status Continuing/Resolved",
                "pertinence": "Pertinence",
                "result": "Result type 1",
            }
            if row.get(raw_map["country"]):
                g_events.add((evt, TS.countryLabel, Literal(row[raw_map["country"]])))
            if row.get(raw_map["status"]):
                g_events.add(
                    (evt, TS.rawEventStatusLabel, Literal(row[raw_map["status"]]))
                )
            if row.get(raw_map["pertinence"]):
                g_events.add(
                    (evt, TS.rawPertinenceLabel, Literal(row[raw_map["pertinence"]]))
                )

            # dates + fallback
            c = parse_date(row.get("Confirmation date"))
            s = parse_date(row.get("Suspicion/Start date"))
            sub = parse_date(row.get("Submitted on"))
            if c:
                g_events.add((evt, TS.confirmationDate, Literal(c, datatype=XSD.date)))
                month = c[:7]
            else:
                counts["missing_confirmation"] += 1
                if s:
                    month = s[:7]
                    counts["fallback"] += 1
                elif sub:
                    month = sub[:7]
                    counts["fallback"] += 1
                else:
                    month = "unknown"
                    counts["fallback"] += 1
            if s:
                g_events.add(
                    (evt, TS.suspicionStartDate, Literal(s, datatype=XSD.date))
                )
            if sub:
                g_events.add((evt, TS.submissionDate, Literal(sub, datatype=XSD.date)))

            # disease concept
            disease_label = (row.get("Disease name") or "unknown").strip()
            disease_slug = slug(disease_label)
            disease_c = TSS[disease_slug]
            g_events.add((evt, TS.hasDisease, disease_c))
            ensure_concept(
                g_skos, TSS["diseases"], disease_c, disease_label, TS.Disease
            )

            # subtype
            subtype = (row.get("Disease type") or "").strip()
            if subtype and subtype != "NaN":
                st_c = TSS[slug(subtype)]
                g_events.add((evt, TS.hasDiseaseSubtype, st_c))
                ensure_concept(
                    g_skos, TSS["disease_subtypes"], st_c, subtype, TS.DiseaseSubtype
                )

            # country concept
            country = (row.get("Country/Territory") or "unknown").strip()
            country_slug = slug(country)
            country_c = TSS[f"country-{country_slug}"]
            ensure_concept(g_skos, TSS["countries"], country_c, country)

            # location
            loc_key = slug(
                f"{row.get('Location', '')}-{row.get('Administrative division level 1', '')}-{row.get('Administrative division level 2', '')}-{row.get('Administrative division level 3', '')}"
            )
            loc = TSD[f"loc_{loc_key}"]
            g_events.add((evt, TS.occursAt, loc))
            g_events.add((loc, RDF.type, TS.Location))
            for p, col in [
                (TS.locationLabel, "Location"),
                (TS.adminLevel1Label, "Administrative division level 1"),
                (TS.adminLevel2Label, "Administrative division level 2"),
                (TS.adminLevel3Label, "Administrative division level 3"),
            ]:
                v = row.get(col)
                if v and v != "NaN":
                    g_events.add((loc, p, Literal(v)))
            lat = parse_decimal(row.get("Latitude"))
            lon = parse_decimal(row.get("Longitude"))
            if lat and lon:
                g_events.add((loc, TS.latitude, Literal(lat, datatype=XSD.decimal)))
                g_events.add((loc, TS.longitude, Literal(lon, datatype=XSD.decimal)))
            else:
                counts["missing_coords"] += 1

            # species/status/result/pertinence/unit skos
            species = (row.get("Species 1") or "").strip()
            if species and species != "NaN":
                sc = TSS[f"species-{slug(species)}"]
                g_events.add((evt, TS.hasSpecies, sc))
                ensure_concept(g_skos, TSS["species"], sc, species, TS.Species)
            status = (row.get("Status Continuing/Resolved") or "").strip()
            if status and status != "NaN":
                st = TSS[f"status-{slug(status)}"]
                g_events.add((evt, TS.hasEventStatus, st))
                ensure_concept(g_skos, TSS["event-status"], st, status)
            result = (row.get("Result type 1") or "").strip()
            if result and result != "NaN":
                rs = TSS[f"result-{slug(result)}"]
                ensure_concept(g_skos, TSS["result-status"], rs, result)
            pert = (row.get("Pertinence") or "").strip()
            if pert and pert != "NaN":
                pc = TSS[f"pertinence-{slug(pert)}"]
                g_events.add((evt, TS.hasPertinence, pc))
                ensure_concept(g_skos, TSS["pertinence-values"], pc, pert)
            mu = (row.get("Measuring unit 1") or "").strip()
            if mu and mu != "NaN":
                m = TSD[f"meas_{slug(ref)}"]
                g_events.add((evt, TS.hasMeasurement, m))
                g_events.add((m, RDF.type, TS.Measurement))
                mc = TSS[f"unit-{slug(mu)}"]
                g_events.add((m, TS.hasMeasuringUnit, mc))
                g_events.add((m, TS.rawMeasuringUnitLabel, Literal(mu)))
                ensure_concept(g_skos, TSS["measuring-units"], mc, mu)

            for col, prop in [
                ("Susceptible 1", TS.susceptibleCount),
                ("Cases 1", TS.casesCount),
                ("Dead 1", TS.deadCount),
                ("Killed 1", TS.killedCount),
                ("Slaughtered 1", TS.slaughteredCount),
                ("Vaccinated 1", TS.vaccinatedCount),
            ]:
                v = (row.get(col) or "").strip()
                if v and v not in ("NaN", "N/A") and "m" in locals():
                    try:
                        g_events.add((m, prop, Literal(int(float(v)))))
                    except:
                        pass

            # source row
            row_hash = hashlib.sha1((ref + str(counts["rows"])).encode()).hexdigest()[
                :12
            ]
            srow = TSD[f"source_row_{row_hash}"]
            g_rows.add((srow, RDF.type, TS.SourceRow))
            g_rows.add((srow, TS.referenceId, Literal(ref)))
            g_events.add((evt, TS.hasSourceRow, srow))

            # situation
            sk = f"{disease_slug}|{country_slug}|{month}"
            suri = TSD[f"situation_{slug(sk)}"]
            g_situations.add((suri, RDF.type, TS.OutbreakSituation))
            g_situations.add((suri, TS.hasSituationKey, Literal(sk)))
            g_situations.add((suri, TS.situationDisease, disease_c))
            g_situations.add(
                (suri, TS.situationCountry, TSD[f"country_{country_slug}"])
            )
            if month != "unknown":
                g_situations.add(
                    (suri, TS.situationMonth, Literal(month, datatype=XSD.gYearMonth))
                )
            else:
                g_situations.add((suri, TS.situationMonth, Literal("unknown")))
            g_events.add((evt, TS.belongsToSituation, suri))

            counts["events"] += 1

    # counts from graphs
    counts["situations"] = len(
        set(g_situations.subjects(RDF.type, TS.OutbreakSituation))
    )
    counts["disease_concepts"] = len(set(g_skos.subjects(RDF.type, TS.Disease)))
    counts["species_concepts"] = len(set(g_skos.subjects(RDF.type, TS.Species)))

    g_events.serialize(out_dir / "adis-events.ttl", format="turtle")
    g_situations.serialize(out_dir / "adis-situations.ttl", format="turtle")
    g_skos.serialize(out_dir / "adis-skos-generated.ttl", format="turtle")
    g_rows.serialize(out_dir / "adis-source-rows.ttl", format="turtle")

    summary = f"""# ADIS CSV -> RDF conversion summary\n\n- rows read: {counts["rows"]}\n- events generated: {counts["events"]}\n- situations generated: {counts["situations"]}\n- disease concepts: {counts["disease_concepts"]}\n- species concepts: {counts["species_concepts"]}\n- rows with missing confirmation date: {counts["missing_confirmation"]}\n- rows using fallback date: {counts["fallback"]}\n- rows with missing coordinates: {counts["missing_coords"]}\n- skipped rows: {counts["skipped"]}\n"""
    (rep_dir / "adis-conversion-summary.md").write_text(summary, encoding="utf-8")
    print(summary)


if __name__ == "__main__":
    main()
