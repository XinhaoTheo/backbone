from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from backbone.models import (
    ClinicalSnapshot,
    DocumentEvidence,
    DocumentRecord,
    ExtractionResult,
    PatientRecord,
)


@dataclass
class Store:
    path: Path

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self.connect()) as connection, connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS documents (
                    content_hash TEXT PRIMARY KEY, document_id TEXT NOT NULL,
                    filename TEXT NOT NULL, text TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS aliases (
                    content_hash TEXT NOT NULL REFERENCES documents,
                    filename TEXT NOT NULL, PRIMARY KEY (content_hash, filename)
                );
                CREATE TABLE IF NOT EXISTS extractions (
                    cache_key TEXT PRIMARY KEY, content_hash TEXT NOT NULL REFERENCES documents,
                    result TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS active_extractions (
                    content_hash TEXT PRIMARY KEY REFERENCES documents,
                    cache_key TEXT NOT NULL REFERENCES extractions
                );
                CREATE TABLE IF NOT EXISTS failures (
                    content_hash TEXT PRIMARY KEY REFERENCES documents, error TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS revisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS patient_versions (
                    patient_id TEXT NOT NULL, revision_id INTEGER NOT NULL REFERENCES revisions,
                    payload TEXT NOT NULL, PRIMARY KEY (patient_id, revision_id)
                );
                CREATE INDEX IF NOT EXISTS patient_revision
                    ON patient_versions (revision_id, patient_id);
                CREATE TABLE IF NOT EXISTS runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL,
                    kind TEXT NOT NULL, payload TEXT NOT NULL
                );
            """)

    def add_document(self, document: DocumentRecord) -> bool:
        with closing(self.connect()) as connection, connection:
            cursor = connection.execute(
                "INSERT OR IGNORE INTO documents VALUES (?, ?, ?, ?)",
                (document.content_hash, document.document_id, document.filename, document.text),
            )
            connection.execute(
                "INSERT OR IGNORE INTO aliases VALUES (?, ?)",
                (document.content_hash, document.filename),
            )
            return cursor.rowcount == 1

    def documents(self) -> list[DocumentRecord]:
        with closing(self.connect()) as connection:
            rows = connection.execute("SELECT * FROM documents ORDER BY filename").fetchall()
            return [
                DocumentRecord(
                    content_hash=str(row["content_hash"]),
                    document_id=str(row["document_id"]),
                    filename=str(row["filename"]),
                    text=str(row["text"]),
                )
                for row in rows
            ]

    def extraction(self, cache_key: str) -> ExtractionResult | None:
        with closing(self.connect()) as connection:
            row = connection.execute(
                "SELECT result FROM extractions WHERE cache_key = ?", (cache_key,)
            ).fetchone()
            return None if row is None else ExtractionResult.model_validate_json(str(row["result"]))

    def save_extraction(self, content_hash: str, cache_key: str, result: ExtractionResult) -> None:
        with closing(self.connect()) as connection, connection:
            connection.execute(
                "INSERT OR REPLACE INTO extractions VALUES (?, ?, ?)",
                (cache_key, content_hash, result.model_dump_json()),
            )

    def save_failure(self, content_hash: str, error: str) -> None:
        with closing(self.connect()) as connection, connection:
            connection.execute(
                "INSERT OR REPLACE INTO failures VALUES (?, ?)", (content_hash, error)
            )

    def active_evidence(self) -> dict[str, DocumentEvidence]:
        with closing(self.connect()) as connection:
            rows = connection.execute("""
                SELECT a.content_hash, e.result FROM active_extractions a
                JOIN extractions e USING (cache_key) ORDER BY a.content_hash
            """).fetchall()
            return {
                str(row["content_hash"]): ExtractionResult.model_validate_json(
                    str(row["result"])
                ).evidence
                for row in rows
            }

    def publish(self, patients: list[PatientRecord], active_keys: dict[str, str]) -> int:
        with closing(self.connect()) as connection, connection:
            cursor = connection.execute(
                "INSERT INTO revisions (created_at) VALUES (?)", (datetime.now(UTC).isoformat(),)
            )
            revision_id = cast(int, cursor.lastrowid)
            for patient in patients:
                connection.execute(
                    "INSERT INTO patient_versions VALUES (?, ?, ?)",
                    (patient.patient_id, revision_id, patient.model_dump_json()),
                )
            for content_hash, cache_key in active_keys.items():
                connection.execute(
                    "INSERT OR REPLACE INTO active_extractions VALUES (?, ?)",
                    (content_hash, cache_key),
                )
                connection.execute("DELETE FROM failures WHERE content_hash = ?", (content_hash,))
            return revision_id

    def snapshot(self, revision_id: int | None = None) -> ClinicalSnapshot:
        with closing(self.connect()) as connection, connection:
            connection.execute("BEGIN")
            row = connection.execute("SELECT COALESCE(MAX(id), 0) AS id FROM revisions").fetchone()
            selected_id = int(row["id"]) if revision_id is None else revision_id
            rows = connection.execute(
                """
                SELECT p.payload FROM patient_versions p
                JOIN (SELECT patient_id, MAX(revision_id) AS revision_id FROM patient_versions
                      WHERE revision_id <= ? GROUP BY patient_id) latest
                USING (patient_id, revision_id) ORDER BY p.patient_id
            """,
                (selected_id,),
            ).fetchall()
            failures = connection.execute(
                "SELECT content_hash FROM failures ORDER BY content_hash"
            ).fetchall()
            return ClinicalSnapshot(
                snapshot_id=selected_id,
                patients=[PatientRecord.model_validate_json(str(item["payload"])) for item in rows],
                failed_documents=[str(item["content_hash"]) for item in failures],
            )

    def record_run(self, kind: str, payload: str) -> None:
        with closing(self.connect()) as connection, connection:
            connection.execute(
                "INSERT INTO runs (created_at, kind, payload) VALUES (?, ?, ?)",
                (datetime.now(UTC).isoformat(), kind, payload),
            )

    def run_records(self) -> list[str]:
        with closing(self.connect()) as connection:
            return [
                str(row["payload"])
                for row in connection.execute("SELECT payload FROM runs ORDER BY id")
            ]
