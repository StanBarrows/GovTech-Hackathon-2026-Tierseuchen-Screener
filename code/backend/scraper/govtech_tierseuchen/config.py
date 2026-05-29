from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class FileConfig:
    manifest: str
    articles: str
    parse_errors: str
    disease_articles: str
    disease_reports: str


@dataclass(frozen=True)
class ScraperConfig:
    data_dir: str
    rdf_output_dir: str
    log_level: str
    progress_description: str
    commands: list[str]
    files: FileConfig


@dataclass(frozen=True)
class SourceConfig:
    output_dir: str
    timeout_seconds: float
    delay_seconds: float
    limit: int | None
    base_url: str | None = None
    sitemap_path: str | None = None
    article_path_prefix: str | None = None
    articles_api_path: str | None = None
    user_agent: str | None = None
    raw_subdir: str | None = None
    article_serializer: str | None = None
    discovery: dict[str, Any] | None = None


@dataclass(frozen=True)
class DiseaseFilterConfig:
    version: str
    terms: list[str]
    acronym_terms: set[str]
    snippet_radius: int
    max_snippets: int


@dataclass(frozen=True)
class DiseaseReportsConfig:
    extraction_version: str
    confidence_thresholds: dict[str, int]
    european_countries: set[str]
    consequence_terms: dict[str, str]


@dataclass(frozen=True)
class AppConfig:
    project_root: Path
    scraper: ScraperConfig
    sources: dict[str, SourceConfig]
    disease_filter: DiseaseFilterConfig
    disease_reports: DiseaseReportsConfig

    def source_dir(self, data_dir: Path, source: str) -> Path:
        return data_dir / self.sources[source].output_dir

    def output_path(self, data_dir: Path, source: str, file_key: str) -> Path:
        filename = getattr(self.scraper.files, file_key)
        return self.source_dir(data_dir, source) / filename


def load_config(config_path: Path | None = None) -> AppConfig:
    project_root = _find_project_root()
    path = config_path or project_root / "config.yaml"
    with path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}
    return _parse_config(raw, project_root=project_root)


def resolve_config_path(value: str | Path, config: AppConfig) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return config.project_root / path


def _find_project_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").exists():
            return parent
    raise RuntimeError("Could not find project root containing pyproject.toml")


def _parse_config(raw: dict[str, Any], project_root: Path) -> AppConfig:
    scraper = raw["scraper"]
    files = scraper["files"]
    sources = raw["sources"]
    return AppConfig(
        project_root=project_root,
        scraper=ScraperConfig(
            data_dir=str(scraper["data_dir"]),
            rdf_output_dir=str(scraper["rdf_output_dir"]),
            log_level=str(scraper["log_level"]),
            progress_description=str(scraper["progress_description"]),
            commands=list(scraper["commands"]),
            files=FileConfig(
                manifest=str(files["manifest"]),
                articles=str(files["articles"]),
                parse_errors=str(files["parse_errors"]),
                disease_articles=str(files["disease_articles"]),
                disease_reports=str(files["disease_reports"]),
            ),
        ),
        sources={
            source_id: SourceConfig(
                output_dir=str(source["output_dir"]),
                timeout_seconds=float(source["timeout_seconds"]),
                delay_seconds=float(source["delay_seconds"]),
                limit=source["limit"],
                base_url=_optional_str(source.get("base_url")),
                sitemap_path=_optional_str(source.get("sitemap_path")),
                article_path_prefix=_optional_str(source.get("article_path_prefix")),
                articles_api_path=_optional_str(source.get("articles_api_path")),
                user_agent=_optional_str(source.get("user_agent")),
                raw_subdir=_optional_str(source.get("raw_subdir")),
                article_serializer=_optional_str(source.get("article_serializer")),
                discovery=dict(source.get("discovery") or {}),
            )
            for source_id, source in sources.items()
        },
        disease_filter=DiseaseFilterConfig(
            version=str(raw["disease_filter"]["version"]),
            terms=[str(term) for term in raw["disease_filter"]["terms"]],
            acronym_terms={
                str(term) for term in raw["disease_filter"]["acronym_terms"]
            },
            snippet_radius=int(raw["disease_filter"]["snippet_radius"]),
            max_snippets=int(raw["disease_filter"]["max_snippets"]),
        ),
        disease_reports=DiseaseReportsConfig(
            extraction_version=str(raw["disease_reports"]["extraction_version"]),
            confidence_thresholds={
                str(level): int(score)
                for level, score in raw["disease_reports"][
                    "confidence_thresholds"
                ].items()
            },
            european_countries={
                str(country) for country in raw["disease_reports"]["european_countries"]
            },
            consequence_terms={
                str(term): str(normalized)
                for term, normalized in raw["disease_reports"][
                    "consequence_terms"
                ].items()
            },
        ),
    )


def _optional_str(value: object | None) -> str | None:
    return str(value) if value is not None else None
