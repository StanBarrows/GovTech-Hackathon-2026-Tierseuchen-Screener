from __future__ import annotations

import hashlib
import re

from govtech_tierseuchen.config import load_config
from govtech_tierseuchen.models import DiseaseRelevance, EvidenceSnippet, NewsArticle

_CONFIG = load_config().disease_filter
FILTER_VERSION = _CONFIG.version
DISEASE_TERMS = _CONFIG.terms
ACRONYM_TERMS = _CONFIG.acronym_terms
SNIPPET_RADIUS = _CONFIG.snippet_radius
MAX_SNIPPETS = _CONFIG.max_snippets


def assess_disease_relevance(article: NewsArticle) -> DiseaseRelevance:
    haystack = "\n".join(
        part
        for part in [
            article.title,
            article.description or "",
            " ".join(article.keywords),
            article.category or "",
            article.fulltext,
        ]
        if part
    )
    matched_terms = []
    snippets = []
    for term in DISEASE_TERMS:
        if _term_matches(haystack, term):
            matched_terms.append(term)
            snippet = _snippet_for_term(
                article.source_link, haystack, term, radius=SNIPPET_RADIUS
            )
            if snippet and all(existing.text != snippet.text for existing in snippets):
                snippets.append(snippet)
    score = len(matched_terms)
    return DiseaseRelevance(
        article_source_link=article.source_link,
        is_relevant=score > 0,
        score=score,
        matched_terms=matched_terms,
        evidence_snippets=snippets[:MAX_SNIPPETS],
        filter_version=FILTER_VERSION,
    )


def _term_pattern(term: str) -> str:
    escaped = re.escape(term)
    if term in ACRONYM_TERMS:
        return rf"(?<!\w){escaped}(?!\w)"
    return escaped


def _term_matches(text: str, term: str) -> bool:
    return re.search(_term_pattern(term), text, flags=re.IGNORECASE) is not None


def _snippet_for_term(
    source_link: str, text: str, term: str, radius: int = 90
) -> EvidenceSnippet | None:
    match = re.search(_term_pattern(term), text, flags=re.IGNORECASE)
    if match is None:
        return None
    start = max(0, match.start() - radius)
    end = min(len(text), match.end() + radius)
    snippet_text = re.sub(r"\s+", " ", text[start:end]).strip()
    snippet_hash = hashlib.sha1(
        f"{source_link}|{term}|{start}".encode("utf-8")
    ).hexdigest()[:12]
    return EvidenceSnippet(
        snippet_id=f"snippet:{snippet_hash}",
        text=snippet_text,
        source_link=source_link,
        locator=f"char[{start}:{end}]",
        matched_terms=[term],
    )
