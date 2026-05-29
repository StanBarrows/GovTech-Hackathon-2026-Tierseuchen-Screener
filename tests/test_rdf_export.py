from datetime import date, datetime, timezone

from rdflib import Graph, Literal, Namespace, RDF, XSD

from govtech_tierseuchen.cli import main
from govtech_tierseuchen.enrichment import enrich_records
from govtech_tierseuchen.jsonl import write_jsonl
from govtech_tierseuchen.models import DiseaseReport, EvidenceSnippet, PreventionMeasure
from govtech_tierseuchen.rdf_export import (
    disease_report_from_dict,
    export_disease_reports_to_rdf,
)

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


def test_cli_export_final_writes_combined_rdf_and_no_qa_ttl(tmp_path):
    data_dir = tmp_path / "data" / "unstructured"
    rdf_output = tmp_path / "lindas" / "data" / "rdf" / "tierseuchen-screener.ttl"
    csv_output = tmp_path / "lindas" / "data" / "csv" / "disease_reports.csv"
    frontend_csv_output = csv_output.with_name("disease_reports_mock_data_.csv")
    write_jsonl(
        data_dir / "gefluegelnews" / "disease_reports.enriched.jsonl",
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
            "export-final",
            "--source",
            "gefluegelnews",
            "--data-dir",
            str(data_dir),
            "--rdf-output",
            str(rdf_output),
            "--csv-output",
            str(csv_output),
        ]
    )

    assert exit_code == 0
    assert rdf_output.exists()
    assert csv_output.exists()
    assert frontend_csv_output.exists()
    assert not (rdf_output.parent / "gefluegelnews" / "gefluegelnews.qa.ttl").exists()


def test_enriched_record_with_null_collection_fields_exports_to_rdf(tmp_path):
    candidate = {
        "report_id": "gefluegelnews:polen",
        "source_id": "gefluegelnews",
        "source_name": "Gefluegelnews",
        "source_document_id": "source_document:gefluegelnews:polen",
        "source_document_title": "Gefluegelpest in Polen",
        "source_link": "https://www.gefluegelnews.de/article/polen",
        "source_publication_date": "2026-05-20",
        "source_retrieved_at": "2026-05-28T12:00:00+00:00",
        "fulltext": "Ein Ausbruch in Polen hat Sperrzonen zur Folge.",
        "raw_html_path": "raw.html",
        "content_hash": "abc123",
        "extraction_method": "rules",
        "extraction_version": "rules-v1",
        "extraction_status": "candidate",
        "extraction_confidence": "medium",
        "evidence_snippets": [],
        "rule_relevance_score": 4,
        "rule_matched_terms": ["H5N1"],
        "rule_disease_type": "H5N1",
        "rule_control_measures": ["Sperrzonen"],
        "prevention_measures": [],
        "research_references": [],
    }
    enriched = enrich_records(
        [candidate],
        extractor=lambda _record: {
            "disease_name": "Avian influenza",
            "relevance_level": "high",
            "relevance_rationale": "H5N1 outbreak in poultry.",
            "prevention_measures": None,
            "research_references": None,
        },
    )
    report = disease_report_from_dict(enriched[0])
    output_path = tmp_path / "enriched.ttl"

    export_disease_reports_to_rdf([report], output_path)

    graph = Graph()
    graph.parse(output_path)

    candidate_uri = TSD["candidate_gefluegelnews_polen"]
    relevance = TSD["relevance_gefluegelnews_polen"]
    assert (candidate_uri, TS.hasRelevanceAssessment, relevance) in graph
    assert (relevance, TS.hasRelevanceLevel, TSS["relevance-high"]) in graph
