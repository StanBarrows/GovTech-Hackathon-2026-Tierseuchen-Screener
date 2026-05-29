import csv
import json

from govtech_tierseuchen.csv_export import export_records_to_csv


def test_export_records_to_csv_writes_combined_file(tmp_path):
    output_path = tmp_path / "lindas" / "data" / "csv" / "disease_reports.csv"
    records = [
        {
            "report_id": "gefluegelnews:polen",
            "source_id": "gefluegelnews",
            "source_name": "Gefluegelnews",
            "source_document_title": "Gefluegelpest in Polen",
            "source_link": "https://www.gefluegelnews.de/article/polen",
            "source_publication_date": "2026-05-20",
            "disease_name": "Avian influenza",
            "country_or_territory": "Poland",
            "is_in_europe": True,
            "relevance_level": "high",
            "control_measures": ["surveillance zone"],
            "prevention_measures": [
                {"text": "enhanced biosecurity", "prevention_type": "biosecurity"}
            ],
        },
        {
            "report_id": "padi_web:uk",
            "source_id": "padi_web",
            "source_name": "PADI-web",
            "source_document_title": "Avian influenza in the UK",
            "source_link": "https://example.test/uk",
            "source_publication_date": "2026-05-21",
            "disease_name": "Avian influenza",
            "country_or_territory": "United Kingdom",
            "is_in_europe": True,
            "relevance_level": "medium",
            "control_measures": [],
            "prevention_measures": [],
        },
    ]

    result = export_records_to_csv(records, output_path)

    with output_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert result.output_path == output_path
    assert result.record_count == 2
    assert rows[0]["report_id"] == "gefluegelnews:polen"
    assert rows[1]["source_id"] == "padi_web"
    assert rows[0]["is_in_europe"] == "true"
    assert json.loads(rows[0]["control_measures"]) == ["surveillance zone"]
    assert json.loads(rows[0]["prevention_measures"]) == [
        {"prevention_type": "biosecurity", "text": "enhanced biosecurity"}
    ]
