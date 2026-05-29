import importlib.util
import json
import logging
from types import SimpleNamespace
from dataclasses import fields

from govtech_tierseuchen.config import load_config
from govtech_tierseuchen.enrichment import (
    SEMANTIC_FIELDS,
    build_extraction_prompt,
    enrich_records,
    enrich_source,
)
from govtech_tierseuchen.jsonl import read_jsonl, write_jsonl
from govtech_tierseuchen.cli import main
from govtech_tierseuchen.models import DiseaseReport


SCRAPER_OWNED_FIELDS = {
    "report_id",
    "source_id",
    "source_name",
    "source_document_id",
    "source_document_title",
    "source_link",
    "source_publication_date",
    "source_retrieved_at",
    "fulltext",
    "raw_html_path",
    "content_hash",
    "extraction_method",
    "extraction_version",
    "extraction_status",
    "extraction_confidence",
    "evidence_snippets",
    "rule_relevance_score",
    "rule_matched_terms",
    "rule_disease_type",
    "rule_control_measures",
}


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


def test_semantic_fields_match_disease_report_semantic_fields():
    disease_report_fields = {field.name for field in fields(DiseaseReport)}

    assert SEMANTIC_FIELDS == disease_report_fields - SCRAPER_OWNED_FIELDS


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


def test_build_extraction_prompt_sends_only_relevant_context_and_fulltext():
    candidate = {
        **_candidate_record(),
        "source_link": "https://www.gefluegelnews.de/article/polen",
        "raw_html_path": "raw/secret.html",
        "evidence_snippets": [
            {
                "snippet_id": "snippet:1",
                "text": "H5N1 bei Gefluegel",
                "source_link": "https://www.gefluegelnews.de/article/polen",
                "locator": "p[1]",
                "matched_terms": ["H5N1"],
            }
        ],
    }

    prompt = build_extraction_prompt(candidate)
    context_text = prompt.split("\n", 2)[1]
    context = json.loads(context_text)

    assert context == {
        "source_document_title": "Gefluegelpest in Polen",
        "rule_matched_terms": ["H5N1"],
        "rule_disease_type": "H5N1",
        "rule_control_measures": ["Sperrzonen"],
        "evidence_snippets": [
            {
                "snippet_id": "snippet:1",
                "text": "H5N1 bei Gefluegel",
                "source_link": "https://www.gefluegelnews.de/article/polen",
                "locator": "p[1]",
                "matched_terms": ["H5N1"],
            }
        ],
    }
    assert "Polen meldet H5N1 bei Gefluegel" in prompt
    assert "raw/secret.html" not in prompt
    assert "abc123" not in prompt


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


def test_enrich_source_logs_progress_at_requested_interval(tmp_path, caplog):
    config = load_config()
    source_dir = tmp_path / "gefluegelnews"
    write_jsonl(
        source_dir / "disease_reports.jsonl",
        [_candidate_record(), {**_candidate_record(), "report_id": "second"}],
    )

    with caplog.at_level(logging.INFO, logger="govtech_tierseuchen.enrichment"):
        enrich_source(
            data_dir=tmp_path,
            source="gefluegelnews",
            config=config,
            extractor=lambda record: {"disease_name": "Avian influenza"},
            progress_every=1,
        )

    assert "Enriched 1/2 records" in caplog.text
    assert "Enriched 2/2 records" in caplog.text


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


def test_legacy_interpreter_resolves_relative_prompt_and_output_from_project_root(
    monkeypatch, tmp_path
):
    config = load_config()
    module_path = config.project_root / "code/backend/interpreter/interpreter.py"
    spec = importlib.util.spec_from_file_location("legacy_interpreter", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    seen = {}

    def fake_enrich_source(**kwargs):
        seen.update(kwargs)
        return SimpleNamespace(
            record_count=0,
            output_path=kwargs["output_path"],
            error_count=0,
        )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(module, "enrich_source", fake_enrich_source)

    exit_code = module.main(
        [
            "gefluegelnews",
            "--data-dir",
            str(tmp_path),
            "--prompt",
            "code/backend/interpreter/SystemPromptGN.md",
            "--output",
            "data/unstructured/gefluegelnews/custom.enriched.jsonl",
        ]
    )

    assert exit_code == 0
    assert (
        seen["prompt_path"]
        == config.project_root / "code/backend/interpreter/SystemPromptGN.md"
    )
    assert (
        seen["output_path"]
        == config.project_root / "data/unstructured/gefluegelnews/custom.enriched.jsonl"
    )
