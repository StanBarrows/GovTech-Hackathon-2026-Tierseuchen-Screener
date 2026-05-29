import csv
import json

from govtech_tierseuchen.csv_export import (
    frontend_reports_mock_data_path,
    export_records_to_csv,
    export_records_to_frontend_reports_csv,
)


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
            "administrative_division_level_1": "Wielkopolskie",
            "administrative_division_level_2": "Poznan",
            "administrative_division_level_3": "Example district",
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
    assert rows[0]["administrative_division_level_1"] == "Wielkopolskie"
    assert rows[0]["administrative_division_level_2"] == "Poznan"
    assert rows[0]["administrative_division_level_3"] == "Example district"
    assert json.loads(rows[0]["control_measures"]) == ["surveillance zone"]
    assert json.loads(rows[0]["prevention_measures"]) == [
        {"prevention_type": "biosecurity", "text": "enhanced biosecurity"}
    ]


def test_frontend_reports_export_uses_reports_schema_and_mock_data_suffix(tmp_path):
    output_path = tmp_path / "lindas" / "data" / "csv" / "disease_reports.csv"
    records = [
        {
            "source_id": "gefluegelnews",
            "source_document_title": "Gefluegelpest in Polen",
            "source_link": "https://www.gefluegelnews.de/article/polen",
            "source_publication_date": "2026-05-20",
            "source_retrieved_at": "2026-05-28T12:00:00+00:00",
            "fulltext": "Ein Ausbruch in Polen.",
            "administrative_division_level_1": "Wielkopolskie",
            "administrative_division_level_2": "Poznan",
            "administrative_division_level_3": "Example district",
            "rule_relevance_score": 4,
            "relevance_level": "high",
        }
    ]

    result = export_records_to_frontend_reports_csv(records, output_path)

    assert result.output_path == output_path.with_name("disease_reports_mock_data_.csv")
    with result.output_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert rows == [
        {
            "id": "1",
            "source": "gefluegelnews",
            "title": "Gefluegelpest in Polen",
            "url": "https://www.gefluegelnews.de/article/polen",
            "teaser": "",
            "body": "Ein Ausbruch in Polen.",
            "report_date": "2026-05-20",
            "admin_level_1": "Wielkopolskie",
            "admin_level_2": "Poznan",
            "admin_level_3": "Example district",
            "relevance_score": "4",
            "relevance_score_string": "high",
            "distance_km": "",
            "created_at": "2026-05-28T12:00:00+00:00",
            "updated_at": "2026-05-28T12:00:00+00:00",
        }
    ]


def test_frontend_reports_mock_data_path_keeps_extension(tmp_path):
    output_path = tmp_path / "disease_reports.csv"

    assert frontend_reports_mock_data_path(output_path) == (
        tmp_path / "disease_reports_mock_data_.csv"
    )
