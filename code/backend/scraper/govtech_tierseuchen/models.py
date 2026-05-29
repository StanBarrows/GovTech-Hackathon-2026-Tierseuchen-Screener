from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass(frozen=True)
class DiscoveredArticle:
    source_id: str
    source_name: str
    source_link: str
    discovered_at: datetime
    last_modified: datetime | None = None


@dataclass(frozen=True)
class FetchedArticle:
    source_id: str
    source_name: str
    source_link: str
    fetched_at: datetime
    status_code: int
    raw_html_path: str
    content_hash: str
    canonical_url: str | None = None


@dataclass(frozen=True)
class NewsArticle:
    source_id: str
    source_name: str
    source_link: str
    canonical_url: str
    title: str
    description: str | None
    keywords: list[str]
    publication_date: date | None
    retrieved_at: datetime
    category: str | None
    author: str | None
    image_url: str | None
    image_credit: str | None
    source_attribution: str | None
    partner_content: bool | None
    fulltext: str
    raw_html_path: str
    content_hash: str


@dataclass(frozen=True)
class EvidenceSnippet:
    snippet_id: str
    text: str
    source_link: str
    locator: str | None = None
    matched_terms: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DiseaseRelevance:
    article_source_link: str
    is_relevant: bool
    score: int
    matched_terms: list[str]
    evidence_snippets: list[EvidenceSnippet]
    filter_version: str


@dataclass(frozen=True)
class PreventionMeasure:
    text: str
    prevention_type: str | None = None
    raw_evidence: str | None = None


@dataclass(frozen=True)
class ResearchReference:
    title: str | None = None
    url: str | None = None
    citation_text: str | None = None
    link_type: str | None = None
    raw_evidence: str | None = None


@dataclass(frozen=True)
class DiseaseReport:
    report_id: str
    source_id: str
    source_name: str
    source_document_id: str
    source_document_title: str
    source_link: str
    source_publication_date: date | None
    source_retrieved_at: datetime
    fulltext: str
    raw_html_path: str
    content_hash: str
    extraction_method: str
    extraction_version: str
    extraction_status: str
    extraction_confidence: str
    evidence_snippets: list[EvidenceSnippet]
    rule_relevance_score: int | None = None
    rule_matched_terms: list[str] = field(default_factory=list)
    rule_disease_type: str | None = None
    rule_control_measures: list[str] = field(default_factory=list)
    situation_key: str | None = None
    situation_month: str | None = None
    country_or_territory: str | None = None
    country_concept_id: str | None = None
    administrative_division_level_1: str | None = None
    administrative_division_level_2: str | None = None
    administrative_division_level_3: str | None = None
    location: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    approximate_location: bool | None = None
    disease_name: str | None = None
    disease_concept_id: str | None = None
    disease_type: str | None = None
    disease_type_concept_id: str | None = None
    species: str | None = None
    production_type: str | None = None
    wildlife_type: str | None = None
    epidemiological_unit: str | None = None
    susceptible: int | None = None
    cases: int | None = None
    dead: int | None = None
    killed: int | None = None
    slaughtered: int | None = None
    vaccinated: int | None = None
    suspicion_start_date: date | None = None
    confirmation_date: date | None = None
    end_date: date | None = None
    status: str | None = None
    clinical_signs: bool | None = None
    diagnostic_tests: bool | None = None
    necropsy: bool | None = None
    test_name: str | None = None
    result_date: date | None = None
    result_type: str | None = None
    control_measures: list[str] = field(default_factory=list)
    relevance_level: str | None = None
    relevance_rationale: str | None = None
    raw_relevance_evidence: str | None = None
    severity_level: str | None = None
    severity_rationale: str | None = None
    raw_severity_evidence: str | None = None
    reach_level: str | None = None
    reach_rationale: str | None = None
    is_in_europe: bool | None = None
    has_consequences: bool | None = None
    consequences: str | None = None
    prevention_measures: list[PreventionMeasure] = field(default_factory=list)
    research_references: list[ResearchReference] = field(default_factory=list)


@dataclass(frozen=True)
class FetchError:
    source_link: str
    error_type: str
    message: str
    occurred_at: datetime


@dataclass(frozen=True)
class ParseError:
    source_link: str
    raw_html_path: str
    error_type: str
    message: str
    occurred_at: datetime


def news_article_from_dict(row: dict) -> NewsArticle:
    publication_date = (
        date.fromisoformat(row["publication_date"])
        if row.get("publication_date")
        else None
    )
    retrieved_at = datetime.fromisoformat(row["retrieved_at"])
    return NewsArticle(
        source_id=row["source_id"],
        source_name=row["source_name"],
        source_link=row["source_link"],
        canonical_url=row["canonical_url"],
        title=row["title"],
        description=row.get("description"),
        keywords=list(row.get("keywords") or []),
        publication_date=publication_date,
        retrieved_at=retrieved_at,
        category=row.get("category"),
        author=row.get("author"),
        image_url=row.get("image_url"),
        image_credit=row.get("image_credit"),
        source_attribution=row.get("source_attribution"),
        partner_content=row.get("partner_content"),
        fulltext=row["fulltext"],
        raw_html_path=row["raw_html_path"],
        content_hash=row["content_hash"],
    )
