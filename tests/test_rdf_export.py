from datetime import date, datetime, timezone

from rdflib import Graph, Literal, Namespace, RDF, XSD

from govtech_tierseuchen.cli import main
from govtech_tierseuchen.jsonl import write_jsonl
from govtech_tierseuchen.models import DiseaseReport, EvidenceSnippet, PreventionMeasure
from govtech_tierseuchen.rdf_export import export_disease_reports_to_rdf

TS = Namespace("https://data.tierseuchen-screener.example.org/ontology/adis#")
TSD = Namespace("https://data.tierseuchen-screener.example.org/data/")
TSS = Namespace("https://data.tierseuchen-screener.example.org/skos/")


def test_export_disease_reports_writes_news_candidate_evidence_and_situation(tmp_path):
    output_path = tmp_path / "gefluegelnews.ttl"
    report = DiseaseReport(
        report_id="gefluegelnews:polen",
        source_id="gefluegelnews",
        source_name="Gefluegelnews",
        source_document_id="source_document:gefluegelnews:polen",
        source_document_title="Gefluegelpest in Polen",
        source_link="https://www.gefluegelnews.de/article/polen",
        source_publication_date=date(2026, 5, 20),
        source_retrieved_at=datetime(2026, 5, 28, 12, 0, tzinfo=timezone.utc),
        fulltext="Ein Ausbruch in Polen hat Sperrzonen zur Folge.",
        raw_html_path="raw.html",
        content_hash="abc123",
        extraction_method="rules",
        extraction_version="rules-v1",
        extraction_status="candidate",
        extraction_confidence="medium",
        evidence_snippets=[
            EvidenceSnippet(
                snippet_id="snippet:polen:1",
                text="Ausbruch in Polen",
                source_link="https://www.gefluegelnews.de/article/polen",
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
        consequences="Sperrzonen wurden eingerichtet.",
        prevention_measures=[
            PreventionMeasure(
                text="Sperrzonen wurden eingerichtet.",
                prevention_type="restriction-zone",
                raw_evidence="Sperrzonen wurden eingerichtet.",
            )
        ],
    )

    result = export_disease_reports_to_rdf([report], output_path)

    assert result.report_count == 1
    assert result.triple_count > 0
    assert output_path.exists()

    graph = Graph()
    graph.parse(output_path)

    news = TSD["news_gefluegelnews_polen"]
    candidate = TSD["candidate_gefluegelnews_polen"]
    snippet = TSD["snippet_polen_1"]
    situation = TSD["situation_hpai_polen_2026_05"]
    consequence = TSD["consequence_gefluegelnews_polen_1"]
    prevention = TSD["prevention_gefluegelnews_polen_1"]

    assert (news, RDF.type, TS.NewsReport) in graph
    assert (news, TS.sourceDocumentTitle, Literal("Gefluegelpest in Polen")) in graph
    assert (
        news,
        TS.sourcePublishedDate,
        Literal("2026-05-20", datatype=XSD.date),
    ) in graph
    assert (news, TS.sourceContentHash, Literal("abc123")) in graph

    assert (candidate, RDF.type, TS.ExtractionCandidate) in graph
    assert (candidate, TS.extractedFromSource, news) in graph
    assert (candidate, TS.hasEvidenceSnippet, snippet) in graph
    assert (candidate, TS.hasExtractionStatus, TSS["status-candidate"]) in graph
    assert (candidate, TS.hasExtractionConfidence, TSS["confidence-medium"]) in graph
    assert (candidate, TS.candidateDescribesSituation, situation) in graph

    assert (snippet, RDF.type, TS.EvidenceSnippet) in graph
    assert (snippet, TS.snippetText, Literal("Ausbruch in Polen")) in graph
    assert (snippet, TS.sourceTextLocator, Literal("p[1]")) in graph

    assert (situation, RDF.type, TS.OutbreakSituation) in graph
    assert (situation, TS.hasSituationKey, Literal("hpai|polen|2026-05")) in graph
    assert (situation, TS.situationDisease, TSS["hpai"]) in graph
    assert (situation, TS.situationCountry, TSD["country_polen"]) in graph

    assert (candidate, TS.hasConsequence, consequence) in graph
    assert (consequence, RDF.type, TS.Consequence) in graph
    assert (
        consequence,
        TS.consequenceText,
        Literal("Sperrzonen wurden eingerichtet."),
    ) in graph
    assert (candidate, TS.hasPreventionMeasure, prevention) in graph


def test_export_disease_reports_skips_incomplete_situations(tmp_path):
    output_path = tmp_path / "gefluegelnews.ttl"
    report = DiseaseReport(
        report_id="gefluegelnews:without-situation",
        source_id="gefluegelnews",
        source_name="Gefluegelnews",
        source_document_id="source_document:gefluegelnews:without-situation",
        source_document_title="Vogelgrippe ohne Ortsangabe",
        source_link="https://www.gefluegelnews.de/article/without-situation",
        source_publication_date=None,
        source_retrieved_at=datetime(2026, 5, 28, 12, 0, tzinfo=timezone.utc),
        fulltext="Vogelgrippe wurde erwähnt.",
        raw_html_path="raw.html",
        content_hash="def456",
        extraction_method="rules",
        extraction_version="rules-v1",
        extraction_status="candidate",
        extraction_confidence="low",
        evidence_snippets=[],
        disease_name="HPAI",
        disease_concept_id="hpai",
    )

    export_disease_reports_to_rdf([report], output_path)

    graph = Graph()
    graph.parse(output_path)

    candidate = TSD["candidate_gefluegelnews_without_situation"]
    assert (candidate, RDF.type, TS.ExtractionCandidate) in graph
    assert not list(graph.objects(candidate, TS.candidateDescribesSituation))


def test_cli_export_rdf_writes_to_lindas_style_source_directory(tmp_path):
    data_dir = tmp_path / "data" / "unstructured"
    rdf_dir = tmp_path / "lindas" / "data" / "rdf"
    write_jsonl(
        data_dir / "gefluegelnews" / "disease_reports.jsonl",
        [
            {
                "report_id": "gefluegelnews:polen",
                "source_id": "gefluegelnews",
                "source_name": "Gefluegelnews",
                "source_document_id": "source_document:gefluegelnews:polen",
                "source_document_title": "Gefluegelpest in Polen",
                "source_link": "https://www.gefluegelnews.de/article/polen",
                "source_publication_date": "2026-05-20",
                "source_retrieved_at": "2026-05-28T12:00:00+00:00",
                "fulltext": "Ein Ausbruch in Polen.",
                "raw_html_path": "raw.html",
                "content_hash": "abc123",
                "extraction_method": "rules",
                "extraction_version": "rules-v1",
                "extraction_status": "candidate",
                "extraction_confidence": "medium",
                "evidence_snippets": [],
                "prevention_measures": [],
                "research_references": [],
            }
        ],
    )

    exit_code = main(
        [
            "export-rdf",
            "gefluegelnews",
            "--data-dir",
            str(data_dir),
            "--rdf-dir",
            str(rdf_dir),
        ]
    )

    assert exit_code == 0
    output_path = rdf_dir / "gefluegelnews" / "gefluegelnews.qa.ttl"
    assert output_path.exists()
