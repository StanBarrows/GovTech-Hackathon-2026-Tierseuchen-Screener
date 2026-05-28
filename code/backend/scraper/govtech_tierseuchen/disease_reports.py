from __future__ import annotations

import re
from urllib.parse import urlparse

from govtech_tierseuchen.models import (
    DiseaseRelevance,
    DiseaseReport,
    NewsArticle,
    PreventionMeasure,
)

EXTRACTION_VERSION = "rules-v1"
EUROPEAN_COUNTRIES = {
    "Albanien",
    "Andorra",
    "Belgien",
    "Bosnien",
    "Bulgarien",
    "Dänemark",
    "Deutschland",
    "Estland",
    "Finnland",
    "Frankreich",
    "Griechenland",
    "Irland",
    "Island",
    "Italien",
    "Kroatien",
    "Lettland",
    "Liechtenstein",
    "Litauen",
    "Luxemburg",
    "Malta",
    "Moldau",
    "Niederlande",
    "Norwegen",
    "Österreich",
    "Polen",
    "Portugal",
    "Rumänien",
    "Schweden",
    "Schweiz",
    "Serbien",
    "Slowakei",
    "Slowenien",
    "Spanien",
    "Tschechien",
    "Ukraine",
    "Ungarn",
    "Vereinigtes Königreich",
}

CONSEQUENCE_TERMS = {
    "Sperrzone": "Sperrzonen",
    "Sperrzonen": "Sperrzonen",
    "keulen": "Keulung",
    "gekeult": "Keulung",
    "Keulung": "Keulung",
    "Stallpflicht": "Stallpflicht",
    "Impfung": "Impfung",
    "Monitoring": "Monitoring",
    "Biosicherheit": "Biosicherheit",
    "Handel": "Handel",
    "Export": "Export",
}


def extract_report_rules(
    article: NewsArticle, relevance: DiseaseRelevance
) -> DiseaseReport:
    text = f"{article.title}\n{article.description or ''}\n{article.fulltext}"
    country = _first_match(text, sorted(EUROPEAN_COUNTRIES))
    disease_name = _disease_name(text)
    disease_type = _first_regex(text, r"\bH[0-9]N[0-9]\b")
    control_measures = _control_measures(text)
    consequences = _consequence_sentence(article.fulltext)
    report_id = f"{article.source_id}:{urlparse(article.source_link).path.rstrip('/').split('/')[-1]}"
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
        situation_key=_situation_key(disease_name, country, article.publication_date),
        situation_month=article.publication_date.isoformat()[:7]
        if article.publication_date
        else None,
        country_or_territory=country,
        country_concept_id=f"country-{_slug(country)}" if country else None,
        disease_name=disease_name,
        disease_concept_id=_slug(disease_name) if disease_name else None,
        disease_type=disease_type,
        disease_type_concept_id=_slug(disease_type) if disease_type else None,
        control_measures=control_measures,
        relevance_level="high" if relevance.score >= 3 else "medium",
        raw_relevance_evidence="; ".join(
            snippet.text for snippet in relevance.evidence_snippets
        ),
        is_in_europe=country in EUROPEAN_COUNTRIES if country else None,
        has_consequences=bool(consequences) if consequences is not None else None,
        consequences=consequences,
        prevention_measures=_prevention_measures(text),
    )


def _first_match(text: str, terms: list[str]) -> str | None:
    for term in terms:
        if re.search(rf"\b{re.escape(term)}\b", text, flags=re.IGNORECASE):
            return term
    return None


def _first_regex(text: str, pattern: str) -> str | None:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return match.group(0).upper() if match else None


def _disease_name(text: str) -> str | None:
    if re.search(
        r"Vogelgrippe|Geflügelpest|Gefluegelpest|HPAI|Aviäre Influenza",
        text,
        flags=re.IGNORECASE,
    ):
        return "HPAI"
    if re.search(r"Newcastle", text, flags=re.IGNORECASE):
        return "Newcastle Disease"
    if re.search(r"Afrikanische Schweinepest|\bASP\b", text, flags=re.IGNORECASE):
        return "ASP"
    if re.search(r"Lumpy Skin Disease|\bLSD\b", text, flags=re.IGNORECASE):
        return "LSD"
    return None


def _control_measures(text: str) -> list[str]:
    measures = []
    for term, normalized in CONSEQUENCE_TERMS.items():
        if (
            re.search(re.escape(term), text, flags=re.IGNORECASE)
            and normalized not in measures
        ):
            measures.append(normalized)
    return measures


def _prevention_measures(text: str) -> list[PreventionMeasure]:
    measures = []
    for term, normalized in CONSEQUENCE_TERMS.items():
        match = re.search(re.escape(term), text, flags=re.IGNORECASE)
        if match:
            sentence = _sentence_containing(text, match.start()) or match.group(0)
            measures.append(
                PreventionMeasure(
                    text=sentence,
                    prevention_type=normalized,
                    raw_evidence=match.group(0),
                )
            )
    return measures


def _consequence_sentence(text: str) -> str | None:
    sentences = re.split(r"(?<=[.!?])\s+", text.replace("\n", " "))
    for sentence in sentences:
        if any(
            re.search(re.escape(term), sentence, flags=re.IGNORECASE)
            for term in CONSEQUENCE_TERMS
        ):
            return sentence.strip()
    return None


def _sentence_containing(text: str, index: int) -> str | None:
    sentences = re.split(r"(?<=[.!?])\s+", text.replace("\n", " "))
    cursor = 0
    for sentence in sentences:
        end = cursor + len(sentence)
        if cursor <= index <= end:
            return sentence.strip()
        cursor = end + 1
    return None


def _confidence_level(score: int) -> str:
    if score >= 4:
        return "high"
    if score >= 2:
        return "medium"
    if score >= 1:
        return "low"
    return "unknown"


def _situation_key(
    disease_name: str | None, country: str | None, publication_date: object
) -> str | None:
    if not disease_name or not country or not publication_date:
        return None
    return f"{_slug(disease_name)}|{_slug(country)}|{publication_date.isoformat()[:7]}"


def _slug(value: str | None) -> str:
    if not value:
        return "unknown"
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return re.sub(r"-+", "-", value).strip("-") or "unknown"
