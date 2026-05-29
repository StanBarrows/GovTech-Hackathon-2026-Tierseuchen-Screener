from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

CSV_COLUMNS = [
    "report_id",
    "source_id",
    "source_name",
    "source_document_title",
    "source_link",
    "source_publication_date",
    "source_retrieved_at",
    "disease_name",
    "disease_type",
    "country_or_territory",
    "is_in_europe",
    "species",
    "cases",
    "dead",
    "killed",
    "slaughtered",
    "vaccinated",
    "confirmation_date",
    "status",
    "relevance_level",
    "relevance_rationale",
    "severity_level",
    "severity_rationale",
    "reach_level",
    "reach_rationale",
    "has_consequences",
    "consequences",
    "control_measures",
    "prevention_measures",
    "research_references",
]

FRONTEND_REPORT_COLUMNS = [
    "id",
    "source",
    "title",
    "url",
    "teaser",
    "body",
    "report_date",
    "admin_level_1",
    "admin_level_2",
    "admin_level_3",
    "relevance_score",
    "relevance_score_string",
    "distance_km",
    "created_at",
    "updated_at",
]


@dataclass(frozen=True)
class CsvExportResult:
    output_path: Path
    record_count: int


def export_records_to_csv(
    records: Iterable[dict[str, Any]], output_path: Path
) -> CsvExportResult:
    rows = list(records)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {column: _format_cell(row.get(column)) for column in CSV_COLUMNS}
            )
    return CsvExportResult(output_path=output_path, record_count=len(rows))


def frontend_reports_mock_data_path(output_path: Path) -> Path:
    return output_path.with_name(f"{output_path.stem}_mock_data_{output_path.suffix}")


def export_records_to_frontend_reports_csv(
    records: Iterable[dict[str, Any]], output_path: Path
) -> CsvExportResult:
    rows = list(records)
    mock_data_path = frontend_reports_mock_data_path(output_path)
    mock_data_path.parent.mkdir(parents=True, exist_ok=True)
    with mock_data_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FRONTEND_REPORT_COLUMNS)
        writer.writeheader()
        for index, row in enumerate(rows, start=1):
            writer.writerow(_frontend_report_row(index, row))
    return CsvExportResult(output_path=mock_data_path, record_count=len(rows))


def _frontend_report_row(index: int, row: dict[str, Any]) -> dict[str, str]:
    timestamp = row.get("source_retrieved_at")
    return {
        "id": str(index),
        "source": _format_cell(row.get("source_id")),
        "title": _format_cell(row.get("source_document_title")),
        "url": _format_cell(row.get("source_link")),
        "teaser": _format_cell(row.get("relevance_rationale")),
        "body": _format_cell(row.get("fulltext")),
        "report_date": _format_cell(
            row.get("source_publication_date") or row.get("confirmation_date")
        ),
        "admin_level_1": _format_cell(row.get("administrative_division_level_1")),
        "admin_level_2": _format_cell(row.get("administrative_division_level_2")),
        "admin_level_3": _format_cell(row.get("administrative_division_level_3")),
        "relevance_score": _format_cell(row.get("rule_relevance_score")),
        "relevance_score_string": _format_cell(row.get("relevance_level")),
        "distance_km": "",
        "created_at": _format_cell(timestamp),
        "updated_at": _format_cell(timestamp),
    }


def _format_cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list | dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)
