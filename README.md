# GovTech-Hackathon-2026-Tierseuchen-Screener

[Challenge-Link](https://govtech.digisus-lab.ch/project/20)




## Problem und Zielgruppe

Die internationale Tierseuchenlage verändert sich laufend und relevante Informationen sind auf viele unterschiedliche Quellen verteilt. Heute müssen Fachpersonen diese Informationen manuell suchen, lesen, bewerten und zusammenführen. Das ist zeitaufwendig, fehleranfällig und erschwert eine schnelle Reaktion auf neue Risiken.

Es besteht daher Bedarf an einem intelligenten System, das:

* internationale Quellen automatisch überwacht
* relevante Meldungen erkennt und strukturiert
* Trends und Risiken frühzeitig sichtbar macht
* Fachpersonen bei Lagebeurteilung und Risikoeinschätzung unterstützt

Das Problem betrifft insbesondere:

* Fachpersonen in Veterinärämtern und Tiergesundheitsdiensten
* Behörden im Bereich Tierseuchen, Landwirtschaft und Gesundheit
* Expertinnen und Experten für Risikobeurteilung
* Landwirtschafts- und Nutztierbetriebe indirekt
* Organisationen im Bereich Tiergesundheit und Monitoring
* Forschungseinrichtungen und Fachstellen für Epidemiologie

## (Nicht) verfügbare Daten

Unter `data/structured` befinden sich anonymisierte Datenexporte aus drei Tiergesundheitsdatenbanken: **ADIS**, **EMPRES-I** und **WAHIS** vor. Diese strukturierte Datensätze (`.csv`) können als Ausgang für die Challenge benutzt werden. Weitere Infos im [Data-README](data/structured/README.md).

(Weitere) verfügbare Daten und Ressourcen könnten sein:

* Öffentliche Meldungen internationaler Organisationen wie World Organisation for Animal Health, World Health Organization oder Food and Agriculture Organization
* Berichte nationaler Veterinär- und Gesundheitsbehörden in Europa
* Nachrichtenquellen und Fachportale zu Tiergesundheit und Landwirtschaft
* Wissenschaftliche Publikationen und Datenbanken
* Historische Daten zu Tierseuchenfällen, betroffenen Regionen und Tierarten
* Geografische Daten zu Ländern, Regionen und Tierbeständen
* Open-Data-Quellen und APIs mit Informationen zu Ausbrüchen und Meldungen
* Manuell erstellte Lageberichte und Risikobeurteilungen als Trainings- oder Vergleichsdaten
* Übersetzungsdienste und Sprachmodelle für mehrsprachige Quellen

## Ziel für den Hackathon

Das Ziel für den Hackathon ist es, einen funktionierenden Prototypen für einen Tierseuchen-Screener zu entwickeln, der internationale Quellen automatisch analysiert, relevante Informationen extrahiert und übersichtlich für die Risikobeurteilung in der Schweiz aufbereitet.

**Weitere Infos**: <br>
- [Fachliche Anforderugen Prototypen](docs/Anforderungen.md)
- [Glossar Tierseuchen für die Challenge](docs/Glossary.md)


## Einschränkungen

Datenschutz und Urheberrecht bei der Nutzung externer Quellen beachten
Nur öffentlich verfügbare oder freigegebene Daten verwenden
Ergebnisse müssen nachvollziehbar und transparent sein
Quellen und Unsicherheiten klar kennzeichnen

## Erwarteter Nutzen

Wenn das Problem gelöst wäre, könnten relevante Tierseuchenmeldungen deutlich schneller erkannt und bewertet werden. Fachpersonen müssten weniger Zeit für die manuelle Suche und Sichtung von Informationen aufwenden und könnten sich stärker auf die eigentliche Analyse und Entscheidungsfindung konzentrieren.

Der Nutzen wäre unter anderem:

- schnellere Erkennung neuer Tierseuchenrisiken
- frühzeitigere Warnungen für die Schweiz
- bessere Übersicht über die Seuchenlage in Europa
- strukturierte und vergleichbare Informationen aus vielen Quellen
- Entlastung von Expertinnen und Experten bei repetitiven Aufgaben
- schnellere und fundiertere Risikoeinschätzungen
- bessere Entscheidungsgrundlagen für Behörden und Fachstellen
- höhere Reaktionsfähigkeit bei neuen Ausbrüchen
- indirekter Schutz von Tiergesundheit, Landwirtschaft und öffentlicher Gesundheit

## Nachhaltigkeit

Nach dem Hackathon können erfolgreiche Ideen und Prototypen in bestehende Arbeiten und Projekte des Bundesamts BLV zur Erneuerung des Radarbulletin-Prozesses einfliessen. Ziel ist es, geeignete Ansätze schrittweise weiterzuentwickeln und in bestehende Abläufe zu integrieren.


# Lösung

[Prototype-Link](https://app.ts-scanner.ch/dashboard/map)


## Backend Pipeline

The backend pipeline is staged so discovery, fetching, parsing, filtering,
rule extraction, LLM enrichment, and final exports can be rerun independently.
Run the full end-to-end pipeline with:

```bash
uv run ts-screener run-all
```

Select sources with repeatable `--source` options:

```bash
uv run ts-screener run-all --source gefluegelnews --source padi_web
```

Individual stages remain available:

```bash
uv run ts-screener discover gefluegelnews
uv run ts-screener fetch gefluegelnews --limit 25 --delay-seconds 1
uv run ts-screener parse gefluegelnews
uv run ts-screener filter-disease gefluegelnews
uv run ts-screener extract-reports gefluegelnews
uv run ts-screener enrich gefluegelnews
uv run ts-screener export-final --source gefluegelnews
```

Raw HTML, raw JSON, and generated JSONL files are local artifacts under
`data/unstructured/<source_id>/` and are ignored by git by default. Parsed
articles keep the original `source_link`, cached `raw_html_path`, and Markdown
`fulltext`; extracted `DiseaseReport` records carry those fields forward for
traceability. Final exports are written as one combined Turtle file at
`lindas/data/rdf/tierseuchen-screener.ttl` and one combined CSV file at
`lindas/data/csv/disease_reports.csv`.

PAFF data is read from the pdfs and analyzed by an llm to filter out relevant information, these data are then displayed in the dashboard when relevant.


## Ontology and LINDAS


## Erweiterungen

- Historische Daten (z.B: Erster Fall in diesem Administration District), Vergleich Vormonat/Vorjahresmonat
- Human in the Loop zur Korrektur der Einschätzung der Wichtigkeit
