from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse

from govtech_tierseuchen.config import load_config
from govtech_tierseuchen.models import (
    DiseaseRelevance,
    DiseaseReport,
    NewsArticle,
)

_CONFIG = load_config().disease_reports
EXTRACTION_VERSION = _CONFIG.extraction_version
CONSEQUENCE_TERMS = _CONFIG.consequence_terms
CONFIDENCE_THRESHOLDS = _CONFIG.confidence_thresholds


def extract_report_rules(
    article: NewsArticle, relevance: DiseaseRelevance
) -> DiseaseReport:
    text = f"{article.title}\n{article.description or ''}\n{article.fulltext}"
    report_id = _report_id(article)
    return DiseaseReport(
        report_id=report_id,
        source_id=article.source_id,
        source_name=article.source_name,
        source_document_id=f"source_document:{report_id}",
        source_document_title=article.title,
        source_link=article.source_link,
        source_publication_date=article.publication_date,
        source_retrieved_at=article.retrieved_at,
        fulltext=article.fulltext,
        raw_html_path=article.raw_html_path,
        content_hash=article.content_hash,
        extraction_method="rules",
        extraction_version=EXTRACTION_VERSION,
        extraction_status="candidate",
        extraction_confidence=_confidence_level(relevance.score),
        evidence_snippets=relevance.evidence_snippets,
        rule_relevance_score=relevance.score,
        rule_matched_terms=relevance.matched_terms,
        rule_disease_type=_first_regex(text, r"\bH[0-9]N[0-9]\b"),
        rule_control_measures=_control_measures(text),
        situation_month=article.publication_date.isoformat()[:7]
        if article.publication_date
        else None,
        raw_relevance_evidence="; ".join(
            snippet.text for snippet in relevance.evidence_snippets
        ),
    )


def _report_id(article: NewsArticle) -> str:
    if article.source_id == "padi_web":
        article_id = Path(article.raw_html_path).stem
        if article_id:
            return f"{article.source_id}:{article_id}"
    slug = urlparse(article.source_link).path.rstrip("/").split("/")[-1]
    return f"{article.source_id}:{slug}"


def _first_regex(text: str, pattern: str) -> str | None:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return match.group(0).upper() if match else None


def _control_measures(text: str) -> list[str]:
    measures = []
    for term, normalized in CONSEQUENCE_TERMS.items():
        if (
            re.search(re.escape(term), text, flags=re.IGNORECASE)
            and normalized not in measures
        ):
            measures.append(normalized)
    return measures


def _confidence_level(score: int) -> str:
    if score >= CONFIDENCE_THRESHOLDS["high"]:
        return "high"
    if score >= CONFIDENCE_THRESHOLDS["medium"]:
        return "medium"
    if score >= CONFIDENCE_THRESHOLDS["low"]:
        return "low"
    return "unknown"
