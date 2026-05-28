from dataclasses import dataclass
from datetime import date, datetime, timezone

from govtech_tierseuchen.disease_filter import assess_disease_relevance
from govtech_tierseuchen.disease_reports import extract_report_rules
from govtech_tierseuchen.jsonl import read_jsonl, write_jsonl
from govtech_tierseuchen.models import (
    DiseaseReport,
    EvidenceSnippet,
    NewsArticle,
    PreventionMeasure,
    news_article_from_dict,
)


def test_news_article_keeps_source_link_and_markdown_fulltext():
    article = NewsArticle(
        source_id="gefluegelnews",
        source_name="Gefluegelnews",
        source_link="https://www.gefluegelnews.de/article/example",
        canonical_url="https://www.gefluegelnews.de/article/example",
        title="Gefluegelpest: Beispiel",
        description="Kurztext",
        keywords=["Gefluegelpest", "H5N1"],
        publication_date=date(2026, 5, 20),
        retrieved_at=datetime(2026, 5, 28, 12, 0, tzinfo=timezone.utc),
        category="Biosicherheit",
        author="Gefluegelnews",
        image_url="https://www.gefluegelnews.de/storage/example.jpg",
        image_credit="Redaktion",
        source_attribution="Ministerium",
        partner_content=False,
        fulltext="# Gefluegelpest: Beispiel\n\nEin Ausbruch wurde gemeldet.",
        raw_html_path="data/unstructured/gefluegelnews/raw_html/example.html",
        content_hash="abc123",
    )

    assert article.source_link == "https://www.gefluegelnews.de/article/example"
    assert article.fulltext.startswith("# Gefluegelpest")
    assert article.keywords == ["Gefluegelpest", "H5N1"]


def test_disease_report_has_extended_screening_fields():
    report = DiseaseReport(
        report_id="gefluegelnews:example",
        source_id="gefluegelnews",
        source_name="Gefluegelnews",
        source_document_id="source_document:gefluegelnews:example",
        source_document_title="Gefluegelpest: Beispiel",
        source_link="https://www.gefluegelnews.de/article/example",
        source_publication_date=date(2026, 5, 20),
        source_retrieved_at=datetime(2026, 5, 28, 12, 0, tzinfo=timezone.utc),
        fulltext="Ein Ausbruch in Polen hat Sperrzonen zur Folge.",
        raw_html_path="data/unstructured/gefluegelnews/raw_html/example.html",
        content_hash="abc123",
        extraction_method="rules",
        extraction_version="rules-v1",
        extraction_status="candidate",
        extraction_confidence="medium",
        evidence_snippets=[
            EvidenceSnippet(
                snippet_id="snippet:example:1",
                text="Ausbruch in Polen",
                source_link="https://www.gefluegelnews.de/article/example",
                locator="p[1]",
                matched_terms=["Ausbruch", "Polen"],
            )
        ],
        situation_key="hpai|polen|2026-05",
        situation_month="2026-05",
        country_or_territory="Polen",
        country_concept_id="country-polen",
        disease_name="HPAI",
        disease_concept_id="hpai",
        is_in_europe=True,
        has_consequences=True,
        consequences="Sperrzonen wurden eingerichtet.",
        prevention_measures=[
            PreventionMeasure(
                text="Sperrzonen wurden eingerichtet.",
                prevention_type="restriction-zone",
                raw_evidence="Sperrzonen wurden eingerichtet.",
            )
        ],
    )

    assert report.source_link.endswith("/example")
    assert report.source_document_title == "Gefluegelpest: Beispiel"
    assert report.is_in_europe is True
    assert report.has_consequences is True
    assert report.consequences == "Sperrzonen wurden eingerichtet."
    assert report.evidence_snippets[0].locator == "p[1]"


@dataclass(frozen=True)
class _ExampleRecord:
    name: str
    published: date
    retrieved_at: datetime
    tags: list[str]


def test_jsonl_round_trip_preserves_dates(tmp_path):
    path = tmp_path / "records.jsonl"
    records = [
        _ExampleRecord(
            name="one",
            published=date(2026, 5, 28),
            retrieved_at=datetime(2026, 5, 28, 12, 0, tzinfo=timezone.utc),
            tags=["HPAI"],
        )
    ]

    write_jsonl(path, records)

    assert read_jsonl(path) == [
        {
            "name": "one",
            "published": "2026-05-28",
            "retrieved_at": "2026-05-28T12:00:00+00:00",
            "tags": ["HPAI"],
        }
    ]


def test_assess_disease_relevance_returns_matches_and_snippets():
    article = NewsArticle(
        source_id="gefluegelnews",
        source_name="Gefluegelnews",
        source_link="https://www.gefluegelnews.de/article/polen",
        canonical_url="https://www.gefluegelnews.de/article/polen",
        title="Polen wird zum Vogelgrippe-Hotspot Europas",
        description="H5N1-Ausbrüche treffen Geflügelbetriebe.",
        keywords=["Vogelgrippe", "H5N1"],
        publication_date=date(2026, 5, 26),
        retrieved_at=datetime(2026, 5, 28, 12, 0, tzinfo=timezone.utc),
        category="Biosicherheit",
        author="Gefluegelnews",
        image_url=None,
        image_credit=None,
        source_attribution=None,
        partner_content=False,
        fulltext="Polen bleibt Europas Hotspot der Vogelgrippe. Bereits 140 H5N1-Ausbrüche trafen Geflügelbetriebe.",
        raw_html_path="raw.html",
        content_hash="abc123",
    )

    relevance = assess_disease_relevance(article)

    assert relevance.is_relevant is True
    assert relevance.score >= 3
    assert "Vogelgrippe" in relevance.matched_terms
    assert "H5N1" in relevance.matched_terms
    assert any(
        "Hotspot der Vogelgrippe" in snippet.text
        for snippet in relevance.evidence_snippets
    )
    assert relevance.evidence_snippets[0].source_link == article.source_link


def test_assess_disease_relevance_does_not_match_acronym_inside_word():
    article = NewsArticle(
        source_id="gefluegelnews",
        source_name="Gefluegelnews",
        source_link="https://www.gefluegelnews.de/article/haltung",
        canonical_url="https://www.gefluegelnews.de/article/haltung",
        title="Aspekte der Haltung",
        description="Aspekte der Fütterung und Haltung.",
        keywords=[],
        publication_date=date(2026, 5, 26),
        retrieved_at=datetime(2026, 5, 28, 12, 0, tzinfo=timezone.utc),
        category=None,
        author="Gefluegelnews",
        image_url=None,
        image_credit=None,
        source_attribution=None,
        partner_content=False,
        fulltext="Aspekte der Haltung wurden beschrieben.",
        raw_html_path="raw.html",
        content_hash="abc123",
    )

    relevance = assess_disease_relevance(article)

    assert relevance.is_relevant is False
    assert "ASP" not in relevance.matched_terms


def test_extract_report_rules_populates_europe_and_consequences():
    article = NewsArticle(
        source_id="gefluegelnews",
        source_name="Gefluegelnews",
        source_link="https://www.gefluegelnews.de/article/polen",
        canonical_url="https://www.gefluegelnews.de/article/polen",
        title="Polen wird zum Vogelgrippe-Hotspot Europas",
        description="Polen bleibt Europas Hotspot der Vogelgrippe.",
        keywords=["Vogelgrippe", "H5N1"],
        publication_date=date(2026, 5, 26),
        retrieved_at=datetime(2026, 5, 28, 12, 0, tzinfo=timezone.utc),
        category="Biosicherheit",
        author="Gefluegelnews",
        image_url=None,
        image_credit=None,
        source_attribution="Behördenmeldung",
        partner_content=False,
        fulltext=(
            "Polen bleibt Europas Hotspot der Vogelgrippe. "
            "Bereits 140 H5N1-Ausbrüche trafen 2026 Geflügelbetriebe. "
            "Sperrzonen wurden eingerichtet und Betriebe mussten Tiere keulen."
        ),
        raw_html_path="raw.html",
        content_hash="abc123",
    )
    relevance = assess_disease_relevance(article)

    report = extract_report_rules(article, relevance)

    assert report.report_id == "gefluegelnews:polen"
    assert report.source_document_title == article.title
    assert report.source_link == article.source_link
    assert report.fulltext == article.fulltext
    assert report.situation_key == "hpai|polen|2026-05"
    assert report.situation_month == "2026-05"
    assert report.disease_name == "HPAI"
    assert report.disease_type == "H5N1"
    assert report.country_or_territory == "Polen"
    assert report.is_in_europe is True
    assert report.has_consequences is True
    assert "Sperrzonen" in report.consequences
    assert any(
        measure.prevention_type == "Keulung" for measure in report.prevention_measures
    )


def test_extract_report_rules_slug_normalizes_accented_country_names():
    article = NewsArticle(
        source_id="gefluegelnews",
        source_name="Gefluegelnews",
        source_link="https://www.gefluegelnews.de/article/oesterreich",
        canonical_url="https://www.gefluegelnews.de/article/oesterreich",
        title="HPAI in Österreich",
        description="Österreich meldet Vogelgrippe.",
        keywords=["Vogelgrippe", "H5N1"],
        publication_date=date(2026, 5, 26),
        retrieved_at=datetime(2026, 5, 28, 12, 0, tzinfo=timezone.utc),
        category="Biosicherheit",
        author="Gefluegelnews",
        image_url=None,
        image_credit=None,
        source_attribution=None,
        partner_content=False,
        fulltext="Österreich meldet einen H5N1-Ausbruch.",
        raw_html_path="raw.html",
        content_hash="abc123",
    )
    relevance = assess_disease_relevance(article)

    report = extract_report_rules(article, relevance)

    assert report.country_or_territory == "Österreich"
    assert report.country_concept_id == "country-osterreich"
    assert report.situation_key == "hpai|osterreich|2026-05"


def test_news_article_from_dict_restores_dates():
    article = news_article_from_dict(
        {
            "source_id": "gefluegelnews",
            "source_name": "Gefluegelnews",
            "source_link": "https://example.test/article",
            "canonical_url": "https://example.test/article",
            "title": "Vogelgrippe",
            "description": None,
            "keywords": ["H5N1"],
            "publication_date": "2026-05-26",
            "retrieved_at": "2026-05-28T12:00:00+00:00",
            "category": "Biosicherheit",
            "author": None,
            "image_url": None,
            "image_credit": None,
            "source_attribution": None,
            "partner_content": False,
            "fulltext": "Vogelgrippe in Polen.",
            "raw_html_path": "raw.html",
            "content_hash": "abc",
        }
    )

    assert article.publication_date == date(2026, 5, 26)
    assert article.retrieved_at == datetime(2026, 5, 28, 12, 0, tzinfo=timezone.utc)
