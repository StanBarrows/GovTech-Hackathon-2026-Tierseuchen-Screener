from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
from urllib import request

from govtech_tierseuchen.config import AppConfig, resolve_config_path
from govtech_tierseuchen.jsonl import read_jsonl, write_jsonl
from govtech_tierseuchen.state import PipelineState, stable_fingerprint

Extractor = Callable[[dict[str, Any]], dict[str, Any]]
LOGGER = logging.getLogger(__name__)

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
    force: bool = False,
) -> EnrichmentResult:
    input_path = config.output_path(data_dir, source, "disease_reports")
    resolved_output_path = output_path or config.output_path(
        data_dir, source, "enriched_disease_reports"
    )
    records = read_jsonl(input_path)
    if not records and extractor is None:
        build_live_extractor(source=source, config=config, prompt_path=prompt_path)
    existing_records = {
        _record_key(record): record
        for record in read_jsonl(resolved_output_path)
        if _record_key(record)
    }
    prompt_hash = _prompt_fingerprint(
        source=source, config=config, prompt_path=prompt_path
    )
    state = PipelineState.from_data_dir(data_dir)
    resolved_progress_every = (
        progress_every
        if progress_every is not None
        else config.interpreter.progress_every
    )
    pending_records = []
    reused_records: dict[str, dict[str, Any]] = {}
    fingerprints: dict[str, str] = {}
    for record in records:
        record_key = _record_key(record)
        fingerprint = _enrich_fingerprint(record, config, prompt_hash)
        fingerprints[record_key] = fingerprint
        existing = existing_records.get(record_key)
        stored_fingerprint = (
            state.fingerprint_for(source=source, stage="enrich", record_key=record_key)
            if record_key
            else None
        )
        if (
            record_key
            and existing is not None
            and not existing.get("_error")
            and not force
            and (
                stored_fingerprint == fingerprint
                or (
                    stored_fingerprint is None
                    and existing.get("content_hash") == record.get("content_hash")
                )
            )
        ):
            reused_records[record_key] = existing
        else:
            pending_records.append(record)

    pending_enriched: dict[str, dict[str, Any]] = {}
    if pending_records:
        resolved_extractor = extractor or build_live_extractor(
            source=source,
            config=config,
            prompt_path=prompt_path,
        )
        pending_enriched = {
            _record_key(record): record
            for record in enrich_records(
                pending_records,
                extractor=resolved_extractor,
                progress_every=resolved_progress_every,
            )
        }

    enriched = []
    state_updates = []
    for record in records:
        record_key = _record_key(record)
        enriched_record = reused_records.get(record_key) or pending_enriched[record_key]
        enriched.append(enriched_record)
        if record_key and not enriched_record.get("_error"):
            state_updates.append((record_key, fingerprints[record_key]))

    state.mark_many(
        source=source,
        stage="enrich",
        records=state_updates,
    )
    write_jsonl(resolved_output_path, enriched)
    return EnrichmentResult(
        input_path=input_path,
        output_path=resolved_output_path,
        record_count=len(enriched),
        error_count=sum(1 for record in enriched if record.get("_error")),
    )


def _record_key(record: dict[str, Any]) -> str:
    return str(record.get("report_id") or "")


def _prompt_fingerprint(
    *, source: str, config: AppConfig, prompt_path: Path | None
) -> str:
    resolved_prompt_path = prompt_path or resolve_config_path(
        config.interpreter.prompts[source], config
    )
    if not resolved_prompt_path.exists():
        return stable_fingerprint(
            {
                "model": config.interpreter.model,
                "prompt_path": str(resolved_prompt_path),
                "prompt_missing": True,
            }
        )
    return stable_fingerprint(
        {
            "model": config.interpreter.model,
            "prompt_path": str(resolved_prompt_path),
            "prompt": resolved_prompt_path.read_text(encoding="utf-8"),
        }
    )


def _enrich_fingerprint(
    record: dict[str, Any], config: AppConfig, prompt_fingerprint: str
) -> str:
    return stable_fingerprint(
        {
            "record": record,
            "model": config.interpreter.model,
            "prompt": prompt_fingerprint,
        }
    )


def enrich_records(
    records: list[dict[str, Any]],
    *,
    extractor: Extractor,
    progress_every: int | None = None,
) -> list[dict[str, Any]]:
    enriched = []
    total = len(records)
    for index, record in enumerate(records, start=1):
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
        if _should_log_progress(index, total, progress_every):
            LOGGER.info("Enriched %s/%s records", index, total)
    return enriched


def _should_log_progress(index: int, total: int, progress_every: int | None) -> bool:
    if progress_every is None or progress_every <= 0 or total == 0:
        return False
    return index % progress_every == 0 or index == total


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
