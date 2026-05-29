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


def _format_cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list | dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)
