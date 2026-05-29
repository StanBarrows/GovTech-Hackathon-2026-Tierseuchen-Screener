from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

from rdflib import Graph, Literal, Namespace, RDF, SKOS, XSD

from govtech_tierseuchen.models import (
    DiseaseReport,
    EvidenceSnippet,
    PreventionMeasure,
    ResearchReference,
)

TS = Namespace("https://data.tierseuchen-screener.example.org/ontology/adis#")
TSD = Namespace("https://data.tierseuchen-screener.example.org/data/")
TSS = Namespace("https://data.tierseuchen-screener.example.org/skos/")


@dataclass(frozen=True)
class RdfExportResult:
    output_path: Path
    report_count: int
    triple_count: int


def export_disease_reports_to_rdf(
    reports: Iterable[DiseaseReport], output_path: Path
) -> RdfExportResult:
    graph = Graph()
    _bind_namespaces(graph)

    report_count = 0
    for report in reports:
        report_count += 1
        _add_report(graph, report)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(destination=output_path, format="turtle")
    return RdfExportResult(
        output_path=output_path,
        report_count=report_count,
        triple_count=len(graph),
    )


def disease_report_from_dict(row: dict[str, Any]) -> DiseaseReport:
    return DiseaseReport(
        report_id=row["report_id"],
        source_id=row["source_id"],
        source_name=row["source_name"],
        source_document_id=row["source_document_id"],
        source_document_title=row["source_document_title"],
        source_link=row["source_link"],
        source_publication_date=_parse_date(row.get("source_publication_date")),
        source_retrieved_at=_parse_datetime(row["source_retrieved_at"]),
        fulltext=row["fulltext"],
        raw_html_path=row["raw_html_path"],
        content_hash=row["content_hash"],
        extraction_method=row["extraction_method"],
        extraction_version=row["extraction_version"],
        extraction_status=row["extraction_status"],
        extraction_confidence=row["extraction_confidence"],
        evidence_snippets=[
            EvidenceSnippet(
                snippet_id=snippet["snippet_id"],
                text=snippet["text"],
                source_link=snippet["source_link"],
                locator=snippet.get("locator"),
                matched_terms=list(snippet.get("matched_terms") or []),
            )
            for snippet in row.get("evidence_snippets", [])
        ],
        rule_relevance_score=row.get("rule_relevance_score"),
        rule_matched_terms=list(row.get("rule_matched_terms") or []),
        rule_disease_type=row.get("rule_disease_type"),
        rule_control_measures=list(row.get("rule_control_measures") or []),
        situation_key=row.get("situation_key"),
        situation_month=row.get("situation_month"),
        country_or_territory=row.get("country_or_territory"),
        country_concept_id=row.get("country_concept_id"),
        administrative_division_level_1=row.get("administrative_division_level_1"),
        administrative_division_level_2=row.get("administrative_division_level_2"),
        administrative_division_level_3=row.get("administrative_division_level_3"),
        location=row.get("location"),
        latitude=row.get("latitude"),
        longitude=row.get("longitude"),
        approximate_location=row.get("approximate_location"),
        disease_name=row.get("disease_name"),
        disease_concept_id=row.get("disease_concept_id"),
        disease_type=row.get("disease_type"),
        disease_type_concept_id=row.get("disease_type_concept_id"),
        species=row.get("species"),
        production_type=row.get("production_type"),
        wildlife_type=row.get("wildlife_type"),
        epidemiological_unit=row.get("epidemiological_unit"),
        susceptible=row.get("susceptible"),
        cases=row.get("cases"),
        dead=row.get("dead"),
        killed=row.get("killed"),
        slaughtered=row.get("slaughtered"),
        vaccinated=row.get("vaccinated"),
        suspicion_start_date=_parse_date(row.get("suspicion_start_date")),
        confirmation_date=_parse_date(row.get("confirmation_date")),
        end_date=_parse_date(row.get("end_date")),
        status=row.get("status"),
        clinical_signs=row.get("clinical_signs"),
        diagnostic_tests=row.get("diagnostic_tests"),
        necropsy=row.get("necropsy"),
        test_name=row.get("test_name"),
        result_date=_parse_date(row.get("result_date")),
        result_type=row.get("result_type"),
        control_measures=list(row.get("control_measures") or []),
        relevance_level=row.get("relevance_level"),
        relevance_rationale=row.get("relevance_rationale"),
        raw_relevance_evidence=row.get("raw_relevance_evidence"),
        severity_level=row.get("severity_level"),
        severity_rationale=row.get("severity_rationale"),
        raw_severity_evidence=row.get("raw_severity_evidence"),
        reach_level=row.get("reach_level"),
        reach_rationale=row.get("reach_rationale"),
        is_in_europe=row.get("is_in_europe"),
        has_consequences=row.get("has_consequences"),
        consequences=row.get("consequences"),
        prevention_measures=[
            PreventionMeasure(
                text=measure["text"],
                prevention_type=measure.get("prevention_type"),
                raw_evidence=measure.get("raw_evidence"),
            )
            for measure in row.get("prevention_measures", [])
        ],
        research_references=[
            ResearchReference(
                title=reference.get("title"),
                url=reference.get("url"),
                citation_text=reference.get("citation_text"),
                link_type=reference.get("link_type"),
                raw_evidence=reference.get("raw_evidence"),
            )
            for reference in row.get("research_references", [])
        ],
    )


def _bind_namespaces(graph: Graph) -> None:
    graph.bind("ts", TS)
    graph.bind("tsd", TSD)
    graph.bind("tss", TSS)
    graph.bind("skos", SKOS)
    graph.bind("xsd", XSD)


def _add_report(graph: Graph, report: DiseaseReport) -> None:
    report_slug = _slug(report.report_id)
    news = TSD[f"news_{report_slug}"]
    candidate = TSD[f"candidate_{report_slug}"]

    graph.add((news, RDF.type, TS.NewsReport))
    graph.add((news, RDF.type, TS.SourceDocument))
    _add_literal(graph, news, TS.referenceId, report.source_document_id)
    _add_literal(graph, news, TS.sourceDocumentTitle, report.source_document_title)
    _add_literal(graph, news, TS.sourceURL, report.source_link, datatype=XSD.anyURI)
    _add_literal(
        graph,
        news,
        TS.sourcePublishedDate,
        report.source_publication_date,
        datatype=XSD.date,
    )
    _add_literal(
        graph,
        news,
        TS.sourceRetrievedAt,
        report.source_retrieved_at,
        datatype=XSD.dateTime,
    )
    _add_literal(graph, news, TS.sourcePublisher, report.source_name)
    _add_literal(graph, news, TS.sourceFullText, report.fulltext)
    _add_literal(graph, news, TS.sourceContentHash, report.content_hash)

    graph.add((candidate, RDF.type, TS.ExtractionCandidate))
    graph.add((candidate, TS.extractedFromSource, news))
    _add_literal(graph, candidate, TS.referenceId, report.report_id)
    _add_literal(graph, candidate, TS.extractionMethod, report.extraction_method)
    _add_literal(graph, candidate, TS.extractionVersion, report.extraction_version)
    _add_concept_link(
        graph,
        candidate,
        TS.hasExtractionStatus,
        "status",
        report.extraction_status,
    )
    _add_concept_link(
        graph,
        candidate,
        TS.hasExtractionConfidence,
        "confidence",
        report.extraction_confidence,
    )

    situation = _add_situation(graph, report)
    if situation is not None:
        graph.add((candidate, TS.candidateDescribesSituation, situation))

    for index, snippet in enumerate(report.evidence_snippets, start=1):
        snippet_uri = TSD[_snippet_id(snippet, index)]
        graph.add((snippet_uri, RDF.type, TS.EvidenceSnippet))
        graph.add((candidate, TS.hasEvidenceSnippet, snippet_uri))
        _add_literal(graph, snippet_uri, TS.snippetText, snippet.text)
        _add_literal(graph, snippet_uri, TS.sourceTextLocator, snippet.locator)
        for term in snippet.matched_terms:
            _add_literal(graph, snippet_uri, TS.rawMatchedTerm, term)

    _add_assessments(graph, candidate, report, report_slug)
    _add_consequences(graph, candidate, report, report_slug)
    _add_prevention_measures(graph, candidate, report, report_slug)
    _add_research_references(graph, candidate, report, report_slug)


def _add_situation(graph: Graph, report: DiseaseReport):
    if not (
        report.situation_key
        and report.situation_month
        and report.disease_concept_id
        and report.country_concept_id
    ):
        return None

    situation = TSD[f"situation_{_slug(report.situation_key)}"]
    country = TSD[_country_id(report.country_concept_id)]
    disease = TSS[report.disease_concept_id]

    graph.add((situation, RDF.type, TS.OutbreakSituation))
    graph.add((country, RDF.type, TS.Location))
    graph.add((disease, RDF.type, SKOS.Concept))
    graph.add((disease, RDF.type, TS.Disease))
    graph.add((situation, TS.situationDisease, disease))
    graph.add((situation, TS.situationCountry, country))
    _add_literal(graph, situation, TS.hasSituationKey, report.situation_key)
    _add_literal(
        graph,
        situation,
        TS.situationMonth,
        report.situation_month,
        datatype=XSD.gYearMonth,
    )
    _add_literal(graph, country, TS.locationLabel, report.country_or_territory)
    _add_literal(graph, disease, SKOS.prefLabel, report.disease_name)
    return situation


def _add_assessments(
    graph: Graph, candidate, report: DiseaseReport, report_slug: str
) -> None:
    if (
        report.relevance_level
        or report.raw_relevance_evidence
        or report.relevance_rationale
    ):
        relevance = TSD[f"relevance_{report_slug}"]
        graph.add((relevance, RDF.type, TS.RelevanceAssessment))
        graph.add((candidate, TS.hasRelevanceAssessment, relevance))
        _add_concept_link(
            graph, relevance, TS.hasRelevanceLevel, "relevance", report.relevance_level
        )
        _add_literal(
            graph, relevance, TS.rawRelevanceEvidence, report.raw_relevance_evidence
        )
        _add_literal(
            graph, relevance, TS.relevanceRationale, report.relevance_rationale
        )

    if (
        report.severity_level
        or report.raw_severity_evidence
        or report.severity_rationale
    ):
        severity = TSD[f"severity_{report_slug}"]
        graph.add((severity, RDF.type, TS.SeverityAssessment))
        graph.add((candidate, TS.hasSeverityAssessment, severity))
        _add_concept_link(
            graph, severity, TS.hasSeverityLevel, "severity", report.severity_level
        )
        _add_literal(
            graph, severity, TS.rawSeverityEvidence, report.raw_severity_evidence
        )
        _add_literal(graph, severity, TS.severityRationale, report.severity_rationale)

    if report.reach_level or report.reach_rationale:
        reach = TSD[f"reach_{report_slug}"]
        graph.add((reach, RDF.type, TS.ReachAssessment))
        graph.add((candidate, TS.hasReachAssessment, reach))
        _add_concept_link(graph, reach, TS.hasReachLevel, "reach", report.reach_level)
        _add_literal(graph, reach, TS.reachRationale, report.reach_rationale)


def _add_consequences(
    graph: Graph, candidate, report: DiseaseReport, report_slug: str
) -> None:
    if not report.consequences:
        return
    consequence = TSD[f"consequence_{report_slug}_1"]
    graph.add((consequence, RDF.type, TS.Consequence))
    graph.add((candidate, TS.hasConsequence, consequence))
    _add_literal(graph, consequence, TS.consequenceText, report.consequences)
    _add_literal(graph, consequence, TS.rawConsequenceEvidence, report.consequences)


def _add_prevention_measures(
    graph: Graph, candidate, report: DiseaseReport, report_slug: str
) -> None:
    for index, measure in enumerate(report.prevention_measures, start=1):
        prevention = TSD[f"prevention_{report_slug}_{index}"]
        graph.add((prevention, RDF.type, TS.PreventionMeasure))
        graph.add((candidate, TS.hasPreventionMeasure, prevention))
        _add_literal(graph, prevention, TS.preventionMeasureText, measure.text)
        _add_literal(graph, prevention, TS.rawPreventionEvidence, measure.raw_evidence)
        _add_concept_link(
            graph,
            prevention,
            TS.hasPreventionType,
            "prevention",
            measure.prevention_type,
        )


def _add_research_references(
    graph: Graph, candidate, report: DiseaseReport, report_slug: str
) -> None:
    for index, reference in enumerate(report.research_references, start=1):
        research = TSD[f"research_{report_slug}_{index}"]
        graph.add((research, RDF.type, TS.ResearchReference))
        graph.add((candidate, TS.hasResearchReference, research))
        _add_literal(graph, research, TS.researchTitle, reference.title)
        _add_literal(
            graph, research, TS.researchURL, reference.url, datatype=XSD.anyURI
        )
        _add_literal(graph, research, TS.researchCitationText, reference.citation_text)
        _add_literal(graph, research, TS.rawResearchEvidence, reference.raw_evidence)
        _add_concept_link(
            graph,
            research,
            TS.hasResearchLinkType,
            "research",
            reference.link_type,
        )


def _add_concept_link(
    graph: Graph, subject, predicate, prefix: str, value: str | None
) -> None:
    if not value:
        return
    graph.add((subject, predicate, TSS[f"{prefix}-{_slug(value)}"]))


def _add_literal(
    graph: Graph,
    subject,
    predicate,
    value: object | None,
    *,
    datatype=None,
) -> None:
    if value is None or value == "":
        return
    if isinstance(value, datetime):
        graph.add((subject, predicate, Literal(value.isoformat(), datatype=datatype)))
        return
    if isinstance(value, date):
        graph.add((subject, predicate, Literal(value.isoformat(), datatype=datatype)))
        return
    graph.add((subject, predicate, Literal(value, datatype=datatype)))


def _snippet_id(snippet: EvidenceSnippet, fallback_index: int) -> str:
    if snippet.snippet_id:
        return f"snippet_{_strip_kind(snippet.snippet_id, 'snippet')}"
    return f"snippet_{fallback_index}"


def _country_id(country_concept_id: str) -> str:
    return country_concept_id.replace("country-", "country_", 1)


def _strip_kind(value: str, kind: str) -> str:
    if value.startswith(f"{kind}:"):
        value = value[len(kind) + 1 :]
    return _slug(value)


def _slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_value = ascii_value.strip().lower()
    ascii_value = re.sub(r"[^a-z0-9]+", "_", ascii_value)
    return re.sub(r"_+", "_", ascii_value).strip("_") or "unknown"


def _parse_date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)
