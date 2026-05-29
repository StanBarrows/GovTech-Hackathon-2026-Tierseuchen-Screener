"""Auto-generated from SystemPromptPAFF.md — do not edit by hand."""
from dataclasses import dataclass, asdict


@dataclass
class ExtractionSchema:
    Relevanz: dict | None = None  # how relevant the report is to monitored
    Severity: dict | None = None  # how severe the outbreak is
    Reichweite: dict | None = None  # geographic / administrative reach of the
    Prävention: dict | None = None  # preventive / response measures mentioned in the

    @classmethod
    def empty(cls) -> dict:
        """Return all schema fields as a dict with None values."""
        return asdict(cls())
