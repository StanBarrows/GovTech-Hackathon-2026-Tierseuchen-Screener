"""Auto-generated from SystemPromptGN.md — do not edit by hand."""

from dataclasses import dataclass, asdict


@dataclass
class ExtractionSchema:
    disease_name: str | None = None  # primary disease named in the report
    disease_type: str | None = (
        None  # broader category the disease belongs to as stated or
    )
    country_or_territory: str | None = (
        None  # country or territory where the outbreak is
    )
    is_in_europe: bool | None = (
        None  # true if the report places the disease in at least
    )
    administrative_division_level_1: str | None = (
        None  # first-level administrative area
    )
    administrative_division_level_2: str | None = (
        None  # second-level administrative area
    )
    administrative_division_level_3: str | None = (
        None  # third-level administrative area
    )
    relevance_level: str | None = None  # how relevant the report is for veterinary /
    relevance_rationale: str | None = (
        None  # one-sentence justification grounded in the text
    )
    severity_level: str | None = None  # severity of the outbreak
    severity_rationale: str | None = None  # one-sentence justification
    reach_level: str | None = None  # geographic reach
    reach_rationale: str | None = None  # one-sentence justification
    has_consequences: bool | None = None  # true if the report describes at least one
    consequences: str | None = None  # a single concise text describing the described
    control_measures: list[str] | None = None  # measures already taken to control the
    prevention_measures: list[dict] | None = None  # measures recommended to prevent
    species: str | None = None  # animal species or "humans" affected
    cases: int | None = None  # animals/humans showing clinical signs
    dead: int | None = None  # animals/humans that died from the disease
    killed: int | None = None  # animals culled by authorities to control the outbreak
    slaughtered: int | None = None  # animals sent to commercial slaughter due to the
    vaccinated: int | None = None  # animals/humans vaccinated in response
    confirmation_date: str | None = None  # date the outbreak was officially confirmed
    result_date: str | None = None  # date of the diagnostic test result
    status: str | None = None  # outbreak status as stated in the text (e

    @classmethod
    def empty(cls) -> dict:
        """Return all schema fields as a dict with None values."""
        return asdict(cls())
