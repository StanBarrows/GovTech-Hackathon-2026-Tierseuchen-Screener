from govtech_tierseuchen.config import load_config
from govtech_tierseuchen.enrichment import enrich_records, enrich_source
from govtech_tierseuchen.jsonl import read_jsonl, write_jsonl
from govtech_tierseuchen.cli import main


def _candidate_record():
    return {
        "report_id": "gefluegelnews:polen",
        "source_id": "gefluegelnews",
        "source_name": "Gefluegelnews",
        "source_document_id": "source_document:gefluegelnews:polen",
        "source_document_title": "Gefluegelpest in Polen",
        "source_link": "https://www.gefluegelnews.de/article/polen",
        "source_publication_date": "2026-05-20",
        "source_retrieved_at": "2026-05-28T12:00:00+00:00",
        "fulltext": "Polen meldet H5N1 bei Gefluegel. Sperrzonen wurden eingerichtet.",
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


def test_enrich_records_preserves_scraper_fields_and_drops_unexpected_keys():
    candidate = _candidate_record()

    def fake_extract(record):
        assert record["report_id"] == candidate["report_id"]
        return {
            "disease_name": "Avian influenza",
            "country_or_territory": "Poland",
            "is_in_europe": True,
            "relevance_level": "high",
            "report_id": "model-tried-to-overwrite",
            "llm_disease_name": "parallel-field",
        }

    enriched = enrich_records([candidate], extractor=fake_extract)

    assert enriched == [
        {
            **candidate,
            "disease_name": "Avian influenza",
            "country_or_territory": "Poland",
            "is_in_europe": True,
            "relevance_level": "high",
        }
    ]
    assert enriched[0]["report_id"] == "gefluegelnews:polen"
    assert "llm_disease_name" not in enriched[0]


def test_enrich_records_preserves_record_error_and_continues():
    first = _candidate_record()
    second = {**_candidate_record(), "report_id": "gefluegelnews:second"}

    def fake_extract(record):
        if record["report_id"] == "gefluegelnews:polen":
            raise ValueError("bad model json")
        return {"disease_name": "Avian influenza"}

    enriched = enrich_records([first, second], extractor=fake_extract)

    assert enriched[0]["report_id"] == "gefluegelnews:polen"
    assert enriched[0]["_error"] == "extraction: ValueError: bad model json"
    assert enriched[1]["disease_name"] == "Avian influenza"


def test_enrich_source_writes_enriched_jsonl_with_fake_extractor(tmp_path):
    config = load_config()
    source_dir = tmp_path / "gefluegelnews"
    write_jsonl(source_dir / "disease_reports.jsonl", [_candidate_record()])

    result = enrich_source(
        data_dir=tmp_path,
        source="gefluegelnews",
        config=config,
        extractor=lambda record: {"disease_name": "Avian influenza"},
    )

    rows = read_jsonl(source_dir / "disease_reports.enriched.jsonl")
    assert result.input_path == source_dir / "disease_reports.jsonl"
    assert result.output_path == source_dir / "disease_reports.enriched.jsonl"
    assert result.record_count == 1
    assert rows[0]["disease_name"] == "Avian influenza"


def test_enrich_command_returns_nonzero_when_llm_env_is_missing(
    monkeypatch, tmp_path, capsys
):
    monkeypatch.delenv("TS_SCREENER_LLM_BASE_URL", raising=False)
    monkeypatch.delenv("TS_SCREENER_LLM_API_KEY", raising=False)

    exit_code = main(["enrich", "gefluegelnews", "--data-dir", str(tmp_path)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Missing required environment variable:" in captured.out
    assert "TS_SCREENER_LLM_BASE_URL" in captured.out
