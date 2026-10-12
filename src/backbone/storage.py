from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from pydantic import JsonValue, TypeAdapter

from backbone.models import (
    ClinicalSnapshot,
    DocumentEvidence,
    DocumentRecord,
    ExecutionRecord,
    ExtractionResult,
    NonContactRecord,
    PatientRecord,
    SourceCoverage,
    SourceRef,
)


class RevisionConflict(RuntimeError):
    pass


def fetch_rows(cursor: sqlite3.Cursor) -> list[sqlite3.Row]:
    return cast(list[sqlite3.Row], cursor.fetchall())


def fetch_row(cursor: sqlite3.Cursor) -> sqlite3.Row | None:
    return cast(sqlite3.Row | None, cursor.fetchone())


@dataclass
class Store:
    path: Path

    def connect(self) -> sqlite3.Connection:
        connection: sqlite3.Connection = sqlite3.connect(self.path)
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
                CREATE INDEX IF NOT EXISTS extraction_document ON extractions (content_hash);
                CREATE TABLE IF NOT EXISTS patient_documents (
                    patient_id TEXT NOT NULL, content_hash TEXT NOT NULL REFERENCES documents,
                    PRIMARY KEY (patient_id, content_hash)
                );
                CREATE INDEX IF NOT EXISTS document_patient
                    ON patient_documents (content_hash, patient_id);
                CREATE TABLE IF NOT EXISTS revision_extractions (
                    revision_id INTEGER NOT NULL REFERENCES revisions,
                    content_hash TEXT NOT NULL REFERENCES documents,
                    cache_key TEXT NOT NULL REFERENCES extractions,
                    PRIMARY KEY (revision_id, content_hash)
                );
                CREATE TABLE IF NOT EXISTS revision_coverage (
                    revision_id INTEGER PRIMARY KEY REFERENCES revisions,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS revision_algorithms (
                    revision_id INTEGER PRIMARY KEY REFERENCES revisions,
                    reconciliation_version TEXT NOT NULL
                );
            """)

    def add_document(self, document: DocumentRecord) -> bool:
        with closing(self.connect()) as connection, connection:
            cursor: sqlite3.Cursor = connection.execute(
                "INSERT OR IGNORE INTO documents VALUES (?, ?, ?, ?)",
                (document.content_hash, document.document_id, document.filename, document.text),
            )
            connection.execute(
                "INSERT OR IGNORE INTO aliases VALUES (?, ?)",
                (document.content_hash, document.filename),
            )
            return cursor.rowcount == 1

    def documents(self, hashes: list[str] | None = None) -> list[DocumentRecord]:
        with closing(self.connect()) as connection:
            rows: list[sqlite3.Row]
            if hashes is None:
                rows = fetch_rows(connection.execute("SELECT * FROM documents ORDER BY filename"))
            else:
                rows = fetch_rows(
                    connection.execute(
                        "SELECT * FROM documents WHERE content_hash IN "
                        f"({','.join('?' for item in hashes)}) ORDER BY filename",
                        hashes,
                    )
                )
            return [
                DocumentRecord(
                    content_hash=str(row["content_hash"]),
                    document_id=str(row["document_id"]),
                    filename=str(row["filename"]),
                    text=str(row["text"]),
                )
                for row in rows
            ]

    def document_count(self) -> int:
        with closing(self.connect()) as connection:
            row: sqlite3.Row = cast(
                sqlite3.Row, fetch_row(connection.execute("SELECT COUNT(*) FROM documents"))
            )
            return int(row[0])

    def latest_revision(self) -> int:
        with closing(self.connect()) as connection:
            row: sqlite3.Row = cast(
                sqlite3.Row,
                fetch_row(connection.execute("SELECT COALESCE(MAX(id), 0) FROM revisions")),
            )
            return int(row[0])

    def reconciliation_version(self) -> str | None:
        with closing(self.connect()) as connection:
            row: sqlite3.Row | None = fetch_row(
                connection.execute(
                    "SELECT reconciliation_version FROM revision_algorithms "
                    "ORDER BY revision_id DESC LIMIT 1"
                )
            )
            return None if row is None else str(row["reconciliation_version"])

    def extraction(self, cache_key: str) -> ExtractionResult | None:
        with closing(self.connect()) as connection:
            row: sqlite3.Row | None = fetch_row(
                connection.execute(
                    "SELECT result FROM extractions WHERE cache_key = ?", (cache_key,)
                )
            )
            return None if row is None else ExtractionResult.model_validate_json(str(row["result"]))

    def save_extraction(self, content_hash: str, cache_key: str, result: ExtractionResult) -> None:
        with closing(self.connect()) as connection, connection:
            connection.execute(
                "INSERT OR IGNORE INTO extractions VALUES (?, ?, ?)",
                (cache_key, content_hash, result.model_dump_json()),
            )
            connection.execute("DELETE FROM failures WHERE content_hash = ?", (content_hash,))

    def clear_failure(self, content_hash: str) -> None:
        with closing(self.connect()) as connection, connection:
            connection.execute("DELETE FROM failures WHERE content_hash = ?", (content_hash,))

    def save_failure(self, content_hash: str, error: str) -> None:
        with closing(self.connect()) as connection, connection:
            connection.execute(
                "INSERT OR REPLACE INTO failures VALUES (?, ?)", (content_hash, error)
            )

    def active_evidence(self) -> dict[str, DocumentEvidence]:
        with closing(self.connect()) as connection:
            rows: list[sqlite3.Row] = fetch_rows(
                connection.execute("""
                SELECT a.content_hash, e.result FROM active_extractions a
                JOIN extractions e USING (cache_key) ORDER BY a.content_hash
            """)
            )
            return {
                str(row["content_hash"]): ExtractionResult.model_validate_json(
                    str(row["result"])
                ).evidence
                for row in rows
            }

    def active_keys(self, hashes: list[str]) -> dict[str, str]:
        with closing(self.connect()) as connection:
            return {
                str(row["content_hash"]): str(row["cache_key"])
                for row in cast(
                    Iterable[sqlite3.Row],
                    connection.execute(
                        "SELECT * FROM active_extractions WHERE content_hash IN "
                        f"({','.join('?' for item in hashes)})",
                        hashes,
                    ),
                )
            }

    def linked_patients(self, hashes: list[str]) -> set[str]:
        with closing(self.connect()) as connection:
            return {
                str(row["patient_id"])
                for row in cast(
                    Iterable[sqlite3.Row],
                    connection.execute(
                        "SELECT DISTINCT patient_id FROM patient_documents WHERE content_hash IN "
                        f"({','.join('?' for item in hashes)})",
                        hashes,
                    ),
                )
            }

    def evidence_for_patients(self, patient_ids: set[str]) -> dict[str, DocumentEvidence]:
        with closing(self.connect()) as connection:
            rows: list[sqlite3.Row] = fetch_rows(
                connection.execute(
                    "SELECT DISTINCT a.content_hash, e.result FROM patient_documents p "
                    "JOIN active_extractions a USING (content_hash) "
                    "JOIN extractions e USING (cache_key) WHERE p.patient_id IN "
                    f"({','.join('?' for item in patient_ids)})",
                    sorted(patient_ids),
                )
            )
            return {
                str(row["content_hash"]): ExtractionResult.model_validate_json(
                    str(row["result"])
                ).evidence
                for row in rows
            }

    def extraction_results(self, revision_id: int | None = None) -> list[ExtractionResult]:
        with closing(self.connect()) as connection:
            selected: int = self.latest_revision() if revision_id is None else revision_id
            rows: list[sqlite3.Row] = fetch_rows(
                connection.execute(
                    "SELECT e.result FROM revision_extractions r "
                    "JOIN (SELECT content_hash, MAX(revision_id) AS revision_id "
                    "FROM revision_extractions WHERE revision_id <= ? "
                    "GROUP BY content_hash) latest "
                    "USING (content_hash, revision_id) JOIN extractions e USING (cache_key) "
                    "ORDER BY r.content_hash",
                    (selected,),
                )
            )
            return [ExtractionResult.model_validate_json(str(row["result"])) for row in rows]

    def coverage(self, connection: sqlite3.Connection) -> SourceCoverage:
        failed: list[sqlite3.Row] = fetch_rows(
            connection.execute(
                "SELECT d.document_id FROM failures f JOIN documents d USING (content_hash) "
                "ORDER BY d.document_id"
            )
        )
        pending: list[sqlite3.Row] = fetch_rows(
            connection.execute(
                "SELECT d.document_id FROM documents d LEFT JOIN active_extractions a "
                "USING (content_hash) WHERE a.content_hash IS NULL ORDER BY d.document_id"
            )
        )
        return SourceCoverage(
            failed_documents=[str(row["document_id"]) for row in failed],
            pending_documents=[str(row["document_id"]) for row in pending],
        )

    def non_contact_records(
        self, connection: sqlite3.Connection, revision_id: int
    ) -> list[NonContactRecord]:
        rows = fetch_rows(
            connection.execute(
                "SELECT d.*, e.result FROM revision_extractions r "
                "JOIN (SELECT content_hash, MAX(revision_id) AS revision_id "
                "FROM revision_extractions "
                "WHERE revision_id <= ? GROUP BY content_hash) latest "
                "USING (content_hash, revision_id) JOIN extractions e USING (cache_key) "
                "JOIN documents d USING (content_hash) ORDER BY d.document_id",
                (revision_id,),
            )
        )
        records: list[NonContactRecord] = []
        for row in rows:
            evidence = ExtractionResult.model_validate_json(str(row["result"])).evidence
            contact_ids = {claim.patient_id for claim in evidence.contacts}
            patients = [
                patient for patient in evidence.patients if patient.patient_id not in contact_ids
            ]
            if not patients:
                continue
            text = str(row["text"])
            quote = text.rstrip("\n")
            patient_ids = {patient.patient_id for patient in patients}
            records.append(
                NonContactRecord(
                    patient_ids=[
                        f"{patient.organization.strip().casefold()}::{patient.patient_id}"
                        for patient in patients
                    ],
                    assessment_claims=sum(
                        claim.patient_id in patient_ids
                        for claim in evidence.assessments
                    ),
                    observation_claims=sum(
                        claim.patient_id in patient_ids
                        for claim in evidence.observations
                    ),
                    source=SourceRef(
                        content_hash=str(row["content_hash"]),
                        document_id=str(row["document_id"]),
                        filename=str(row["filename"]),
                        start_line=1,
                        end_line=quote.count("\n") + 1,
                        quote=quote,
                    ),
                )
            )
        return records

    def publish(
        self,
        patients: list[PatientRecord],
        active_keys: dict[str, str],
        *,
        expected_revision: int | None = None,
        removed_patients: set[str] | None = None,
        document_patients: dict[str, set[str]] | None = None,
        reconciliation_version: str = "1",
    ) -> int:
        with closing(self.connect()) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            current_row: sqlite3.Row = cast(
                sqlite3.Row,
                fetch_row(connection.execute("SELECT COALESCE(MAX(id), 0) FROM revisions")),
            )
            current: int = int(current_row[0])
            if expected_revision is not None and current != expected_revision:
                raise RevisionConflict(
                    "The snapshot changed during processing; retry using cached evidence."
                )
            cursor: sqlite3.Cursor = connection.execute(
                "INSERT INTO revisions (created_at) VALUES (?)", (datetime.now(UTC).isoformat(),)
            )
            revision_id: int = cast(int, cursor.lastrowid)
            for patient in patients:
                connection.execute(
                    "INSERT INTO patient_versions VALUES (?, ?, ?)",
                    (patient.patient_id, revision_id, patient.model_dump_json()),
                )
            for patient_id in removed_patients or set():
                connection.execute(
                    "INSERT INTO patient_versions VALUES (?, ?, 'null')",
                    (patient_id, revision_id),
                )
            for content_hash, cache_key in active_keys.items():
                connection.execute(
                    "INSERT OR REPLACE INTO active_extractions VALUES (?, ?)",
                    (content_hash, cache_key),
                )
                connection.execute(
                    "INSERT INTO revision_extractions VALUES (?, ?, ?)",
                    (revision_id, content_hash, cache_key),
                )
                connection.execute("DELETE FROM failures WHERE content_hash = ?", (content_hash,))
            for content_hash, patient_ids in (document_patients or {}).items():
                connection.execute(
                    "DELETE FROM patient_documents WHERE content_hash = ?", (content_hash,)
                )
                connection.executemany(
                    "INSERT INTO patient_documents VALUES (?, ?)",
                    [(patient_id, content_hash) for patient_id in sorted(patient_ids)],
                )
            connection.execute(
                "INSERT INTO revision_coverage VALUES (?, ?)",
                (revision_id, self.coverage(connection).model_dump_json()),
            )
            connection.execute(
                "INSERT INTO revision_algorithms VALUES (?, ?)",
                (revision_id, reconciliation_version),
            )
            return revision_id

    def snapshot(self, revision_id: int | None = None) -> ClinicalSnapshot:
        with closing(self.connect()) as connection, connection:
            connection.execute("BEGIN")
            row: sqlite3.Row = cast(
                sqlite3.Row,
                fetch_row(connection.execute("SELECT COALESCE(MAX(id), 0) AS id FROM revisions")),
            )
            selected_id: int = int(row["id"]) if revision_id is None else revision_id
            if (
                selected_id != 0
                and fetch_row(
                    connection.execute("SELECT id FROM revisions WHERE id = ?", (selected_id,))
                )
                is None
            ):
                raise ValueError(f"Snapshot {selected_id} does not exist.")
            rows: list[sqlite3.Row] = fetch_rows(
                connection.execute(
                    """
                SELECT p.payload FROM patient_versions p
                JOIN (SELECT patient_id, MAX(revision_id) AS revision_id FROM patient_versions
                      WHERE revision_id <= ? GROUP BY patient_id) latest
                USING (patient_id, revision_id) ORDER BY p.patient_id
            """,
                    (selected_id,),
                )
            )
            coverage: SourceCoverage
            if revision_id is None:
                coverage = self.coverage(connection)
            else:
                coverage_row: sqlite3.Row | None = fetch_row(
                    connection.execute(
                        "SELECT payload FROM revision_coverage WHERE revision_id = ?",
                        (selected_id,),
                    )
                )
                coverage = (
                    SourceCoverage()
                    if coverage_row is None
                    else SourceCoverage.model_validate_json(str(coverage_row["payload"]))
                )
            algorithm_row: sqlite3.Row | None = fetch_row(
                connection.execute(
                    "SELECT reconciliation_version FROM revision_algorithms WHERE revision_id = ?",
                    (selected_id,),
                )
            )
            return ClinicalSnapshot(
                snapshot_id=selected_id,
                patients=[
                    PatientRecord.model_validate_json(str(item["payload"]))
                    for item in rows
                    if str(item["payload"]) != "null"
                ],
                failed_documents=coverage.failed_documents,
                pending_documents=coverage.pending_documents,
                reconciliation_version="unversioned"
                if algorithm_row is None
                else str(algorithm_row[0]),
                non_contact_records=self.non_contact_records(connection, selected_id),
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
                for row in cast(
                    Iterable[sqlite3.Row],
                    connection.execute("SELECT payload FROM runs ORDER BY id"),
                )
            ]

    def execution_records(self) -> list[ExecutionRecord]:
        with closing(self.connect()) as connection:
            return [
                ExecutionRecord(
                    created_at=str(row["created_at"]),
                    kind=str(row["kind"]),
                    payload=TypeAdapter(JsonValue).validate_json(str(row["payload"])),
                )
                for row in fetch_rows(connection.execute("SELECT * FROM runs ORDER BY id"))
            ]
