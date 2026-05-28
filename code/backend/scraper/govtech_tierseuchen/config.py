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


@dataclass(frozen=True)
class AppConfig:
    project_root: Path
    scraper: ScraperConfig
    sources: dict[str, SourceConfig]

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
            )
            for source_id, source in sources.items()
        },
    )
