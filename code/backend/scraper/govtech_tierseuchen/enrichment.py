from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
from urllib import request

from govtech_tierseuchen.config import AppConfig, resolve_config_path
from govtech_tierseuchen.jsonl import read_jsonl, write_jsonl

Extractor = Callable[[dict[str, Any]], dict[str, Any]]

SEMANTIC_FIELDS = {
    "situation_key",
    "situation_month",
    "country_or_territory",
    "country_concept_id",
    "administrative_division_level_1",
    "administrative_division_level_2",
    "administrative_division_level_3",
    "location",
    "latitude",
    "longitude",
    "approximate_location",
    "disease_name",
    "disease_concept_id",
    "disease_type",
    "disease_type_concept_id",
    "species",
    "production_type",
    "wildlife_type",
    "epidemiological_unit",
    "susceptible",
    "cases",
    "dead",
    "killed",
    "slaughtered",
    "vaccinated",
    "suspicion_start_date",
    "confirmation_date",
    "end_date",
    "status",
    "clinical_signs",
    "diagnostic_tests",
    "necropsy",
    "test_name",
    "result_date",
    "result_type",
    "control_measures",
    "relevance_level",
    "relevance_rationale",
    "raw_relevance_evidence",
    "severity_level",
    "severity_rationale",
    "raw_severity_evidence",
    "reach_level",
    "reach_rationale",
    "is_in_europe",
    "has_consequences",
    "consequences",
    "prevention_measures",
    "research_references",
}


@dataclass(frozen=True)
class EnrichmentResult:
    input_path: Path
    output_path: Path
    record_count: int
    error_count: int


def enrich_source(
    data_dir: Path,
    source: str,
    config: AppConfig,
    *,
    extractor: Extractor | None = None,
    prompt_path: Path | None = None,
    output_path: Path | None = None,
    progress_every: int | None = None,
) -> EnrichmentResult:
    input_path = config.output_path(data_dir, source, "disease_reports")
    resolved_output_path = output_path or config.output_path(
        data_dir, source, "enriched_disease_reports"
    )
    resolved_extractor = extractor or build_live_extractor(
        source=source,
        config=config,
        prompt_path=prompt_path,
    )
    records = read_jsonl(input_path)
    enriched = enrich_records(records, extractor=resolved_extractor)
    write_jsonl(resolved_output_path, enriched)
    return EnrichmentResult(
        input_path=input_path,
        output_path=resolved_output_path,
        record_count=len(enriched),
        error_count=sum(1 for record in enriched if record.get("_error")),
    )


def enrich_records(
    records: list[dict[str, Any]], *, extractor: Extractor
) -> list[dict[str, Any]]:
    enriched = []
    for record in records:
        try:
            labels = extractor(record)
            if not isinstance(labels, dict):
                raise TypeError("extractor must return a JSON object")
            enriched.append(merge_semantic_fields(record, labels))
        except Exception as exc:
            enriched.append(
                {
                    **record,
                    "_error": f"extraction: {type(exc).__name__}: {exc}",
                }
            )
    return enriched


def merge_semantic_fields(
    record: dict[str, Any], labels: dict[str, Any]
) -> dict[str, Any]:
    merged = dict(record)
    for key, value in labels.items():
        if key in SEMANTIC_FIELDS:
            merged[key] = value
    return merged


def build_live_extractor(
    *,
    source: str,
    config: AppConfig,
    prompt_path: Path | None = None,
) -> Extractor:
    resolved_prompt_path = prompt_path or resolve_config_path(
        config.interpreter.prompts[source], config
    )
    system_prompt = resolved_prompt_path.read_text(encoding="utf-8")
    base_url = _required_env(config.interpreter.base_url_env)
    api_key = _required_env(config.interpreter.api_key_env)

    def extract(record: dict[str, Any]) -> dict[str, Any]:
        return extract_with_openai_compatible_chat(
            record=record,
            system_prompt=system_prompt,
            base_url=base_url,
            api_key=api_key,
            model=config.interpreter.model,
            timeout_seconds=config.interpreter.timeout_seconds,
        )

    return extract


def extract_with_openai_compatible_chat(
    *,
    record: dict[str, Any],
    system_prompt: str,
    base_url: str,
    api_key: str,
    model: str,
    timeout_seconds: float,
) -> dict[str, Any]:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": build_extraction_prompt(record)},
        ],
        "temperature": 0,
    }
    body = json.dumps(payload).encode("utf-8")
    chat_request = request.Request(
        f"{base_url.rstrip('/')}/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "GovTech-Tierseuchen-Screener/0.1",
        },
        method="POST",
    )
    with request.urlopen(chat_request, timeout=timeout_seconds) as response:
        response_payload = json.loads(response.read().decode("utf-8"))
    content = response_payload["choices"][0]["message"]["content"]
    return parse_model_json(content)


def build_extraction_prompt(record: dict[str, Any]) -> str:
    context = {
        "source_document_title": record.get("source_document_title"),
        "rule_matched_terms": record.get("rule_matched_terms") or [],
        "rule_disease_type": record.get("rule_disease_type"),
        "rule_control_measures": record.get("rule_control_measures") or [],
        "evidence_snippets": record.get("evidence_snippets") or [],
    }
    return (
        "# Candidate context\n"
        f"{json.dumps(context, ensure_ascii=False, sort_keys=True)}\n\n"
        '# Text to parse\n"""\n'
        f"{str(record.get('fulltext') or '').strip()}\n"
        '"""'
    )


def parse_model_json(raw: str) -> dict[str, Any]:
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.lstrip().startswith("json"):
            text = text.lstrip()[4:]
    parsed = json.loads(text.strip())
    if not isinstance(parsed, dict):
        raise TypeError("model response must be a JSON object")
    return parsed


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value
