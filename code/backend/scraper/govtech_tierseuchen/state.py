from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable

from govtech_tierseuchen.jsonl import to_jsonable

STATE_FILENAME = "pipeline_state.sqlite"


def pipeline_state_path(data_dir: Path) -> Path:
    return data_dir / STATE_FILENAME


def stable_fingerprint(value: Any) -> str:
    payload = json.dumps(
        to_jsonable(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class PipelineState:
    def __init__(self, path: Path) -> None:
        self.path = path

    @classmethod
    def from_data_dir(cls, data_dir: Path) -> PipelineState:
        return cls(pipeline_state_path(data_dir))

    def is_current(
        self, *, source: str, stage: str, record_key: str, fingerprint: str
    ) -> bool:
        return (
            self.fingerprint_for(source=source, stage=stage, record_key=record_key)
            == fingerprint
        )

    def fingerprint_for(
        self, *, source: str, stage: str, record_key: str
    ) -> str | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT fingerprint
                FROM processed_records
                WHERE source = ? AND stage = ? AND record_key = ?
                """,
                (source, stage, record_key),
            ).fetchone()
        return row[0] if row is not None else None

    def mark_current(
        self, *, source: str, stage: str, record_key: str, fingerprint: str
    ) -> None:
        self.mark_many(
            source=source,
            stage=stage,
            records=[(record_key, fingerprint)],
        )

    def mark_many(
        self,
        *,
        source: str,
        stage: str,
        records: Iterable[tuple[str, str]],
    ) -> None:
        now = datetime.now(UTC).isoformat()
        rows = [
            (source, stage, record_key, fingerprint, now)
            for record_key, fingerprint in records
        ]
        if not rows:
            return
        with self._connect() as connection:
            connection.executemany(
                """
                INSERT INTO processed_records (
                    source,
                    stage,
                    record_key,
                    fingerprint,
                    processed_at
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(source, stage, record_key)
                DO UPDATE SET
                    fingerprint = excluded.fingerprint,
                    processed_at = excluded.processed_at
                """,
                rows,
            )

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=30)
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS processed_records (
                source TEXT NOT NULL,
                stage TEXT NOT NULL,
                record_key TEXT NOT NULL,
                fingerprint TEXT NOT NULL,
                processed_at TEXT NOT NULL,
                PRIMARY KEY (source, stage, record_key)
            )
            """
        )
        return connection
