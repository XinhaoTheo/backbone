from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import pytest

from backbone.extraction import ExtractionValidationError
from backbone.models import (
    ContactClaim,
    DocumentEvidence,
    DocumentRecord,
    ExtractionResult,
    ModelUsage,
    PatientIdentity,
    TimeInterval,
)
from backbone.storage import RevisionConflict, Store
from backbone.workflow import process_documents


@dataclass
class FixtureExtractor:
    evidences: dict[str, DocumentEvidence]
    version: str = "1"
    failures: set[str] = field(default_factory=set)
    calls: list[str] = field(default_factory=list)

    def cache_key(self, document: DocumentRecord) -> str:
        return f"{self.version}:{document.content_hash}"

    def extract(self, document: DocumentRecord) -> ExtractionResult:
        self.calls.append(document.document_id)
        if document.document_id in self.failures:
            raise ExtractionValidationError("Fixture extraction failed.")
        return ExtractionResult(
            evidence=self.evidences[document.document_id],
            model="fixture",
            usage=ModelUsage(input_tokens=1, output_tokens=1),
            elapsed_seconds=0.0,
        )


@dataclass
class TrackedStore(Store):
    rebuilt: list[set[str]] = field(default_factory=list)

    def evidence_for_patients(self, patient_ids: set[str]) -> dict[str, DocumentEvidence]:
        self.rebuilt.append(patient_ids.copy())
        return super().evidence_for_patients(patient_ids)


def evidence(patient_id: str, end: str, *, correction: bool = False) -> DocumentEvidence:
    return DocumentEvidence(
        patients=[
            PatientIdentity(
                patient_id=patient_id,
                name=patient_id,
                organization="Clinic",
                episode_start=date(2026, 1, 1),
                episode_end=date(2026, 1, 31),
            )
        ],
        contacts=[
            ContactClaim(
                patient_id=patient_id,
                service_date=date(2026, 1, 5),
                encounter_id="E1",
                appointment_id=None,
                service_type="individual",
                attendance="attended",
                patient_present=True,
                intervals=[TimeInterval(start="09:00", end=end)],
                interval_kind="patient_contact",
                breaks=[],
                stated_minutes=None,
                record_status="correction" if correction else "final",
                correction_fields=["intervals"] if correction else [],
                is_copy=False,
                note="",
                quotes=["Contact"],
                sources=[],
            )
        ],
        plans=[],
        assessments=[],
        observations=[],
    )


def source(directory: Path, document_id: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{document_id}.txt"
    path.write_text(f"Document ID: {document_id}\nContact\n", encoding="utf-8")
    return path


def test_duplicate_restart_and_patient_local_update(tmp_path: Path) -> None:
    store = TrackedStore(tmp_path / "review.sqlite3")
    store.initialize()
    first_path = source(tmp_path / "initial", "D1")
    extractor = FixtureExtractor({"D1": evidence("P1", "09:50"), "D2": evidence("P2", "09:30")})
    first = process_documents(store, first_path, extractor, workers=1)
    old_payload = store.snapshot().patients[0].model_dump_json()
    restarted = TrackedStore(store.path)
    duplicate = process_documents(restarted, first_path, extractor, workers=1)
    assert duplicate.snapshot_id == first.snapshot_id
    assert duplicate.cached_documents == 1
    second_path = source(tmp_path / "update", "D2")
    process_documents(restarted, second_path, extractor, workers=1)
    assert restarted.rebuilt == [{"clinic::P2"}]
    assert restarted.snapshot().patients[0].model_dump_json() == old_payload
    assert extractor.calls == ["D1", "D2"]


def test_correction_changes_current_snapshot_and_preserves_history(tmp_path: Path) -> None:
    store = Store(tmp_path / "review.sqlite3")
    store.initialize()
    extractor = FixtureExtractor(
        {"D1": evidence("P1", "09:50"), "D2": evidence("P1", "09:40", correction=True)}
    )
    first = process_documents(store, source(tmp_path / "old", "D1"), extractor, 1)
    process_documents(store, source(tmp_path / "new", "D2"), extractor, 1)
    assert store.snapshot().patients[0].encounters[0].alternatives[0].minutes == 40
    assert store.snapshot(first.snapshot_id).patients[0].encounters[0].alternatives[0].minutes == 50
    assert len(store.extraction_results(first.snapshot_id)) == 1
    assert len(store.extraction_results()) == 2


def test_failed_batch_preserves_revision_and_retry_reuses_valid_results(tmp_path: Path) -> None:
    store = Store(tmp_path / "review.sqlite3")
    store.initialize()
    extractor = FixtureExtractor(
        {
            "D1": evidence("P1", "09:50"),
            "D2": evidence("P2", "09:30"),
            "D3": evidence("P3", "09:20"),
        }
    )
    first = process_documents(store, source(tmp_path / "old", "D1"), extractor, 1)
    source(tmp_path / "batch", "D2")
    source(tmp_path / "batch", "D3")
    extractor.failures = {"D3"}
    failed = process_documents(store, tmp_path / "batch", extractor, 1)
    assert failed.snapshot_id == first.snapshot_id
    assert len(store.snapshot().patients) == 1
    assert store.snapshot().failed_documents == ["D3"]
    assert store.snapshot(first.snapshot_id).failed_documents == []
    extractor.failures.clear()
    retried = process_documents(store, tmp_path / "batch", extractor, 1)
    assert retried.cached_documents == 1
    assert extractor.calls.count("D2") == 1
    assert len(store.snapshot().patients) == 3
    assert store.snapshot().failed_documents == []


def test_changed_extraction_relinks_patient_without_mutating_history(tmp_path: Path) -> None:
    store = Store(tmp_path / "review.sqlite3")
    store.initialize()
    path = source(tmp_path / "records", "D1")
    extractor = FixtureExtractor({"D1": evidence("P1", "09:50")})
    first = process_documents(store, path, extractor, 1)
    extractor.version = "2"
    extractor.evidences["D1"] = evidence("P2", "09:40")
    process_documents(store, path, extractor, 1)
    assert [patient.patient_id for patient in store.snapshot().patients] == ["clinic::P2"]
    assert store.snapshot(first.snapshot_id).patients[0].patient_id == "clinic::P1"
    assert store.extraction_results(first.snapshot_id)[0].evidence.patients[0].patient_id == "P1"


def test_stale_writer_cannot_publish_over_newer_revision(tmp_path: Path) -> None:
    store = Store(tmp_path / "review.sqlite3")
    store.initialize()
    revision = store.publish([], {}, expected_revision=0)
    with pytest.raises(RevisionConflict, match="snapshot changed"):
        store.publish([], {}, expected_revision=0)
    assert store.latest_revision() == revision


def test_cache_payload_is_immutable_for_historical_replay(tmp_path: Path) -> None:
    store = Store(tmp_path / "review.sqlite3")
    store.initialize()
    extractor = FixtureExtractor({"D1": evidence("P1", "09:50")})
    process_documents(store, source(tmp_path / "records", "D1"), extractor, 1)
    document = store.documents()[0]
    extractor.evidences["D1"] = evidence("P1", "09:40")
    store.save_extraction(
        document.content_hash, extractor.cache_key(document), extractor.extract(document)
    )
    assert store.extraction_results()[0].evidence.contacts[0].intervals[0].end == "09:50"


def test_partial_retry_retains_pending_coverage_in_fixed_snapshot(tmp_path: Path) -> None:
    store = Store(tmp_path / "review.sqlite3")
    store.initialize()
    extractor = FixtureExtractor(
        {"D1": evidence("P1", "09:50"), "D2": evidence("P2", "09:30")}, failures={"D2"}
    )
    source(tmp_path / "batch", "D1")
    second = source(tmp_path / "batch", "D2")
    process_documents(store, tmp_path / "batch", extractor, 1)
    extractor.failures.clear()
    retried = process_documents(store, second, extractor, 1)
    assert store.snapshot().pending_documents == ["D1"]
    assert store.snapshot(retried.snapshot_id).pending_documents == ["D1"]
    process_documents(store, tmp_path / "batch", extractor, 1)
    assert store.snapshot().pending_documents == []
    assert store.snapshot(retried.snapshot_id).pending_documents == ["D1"]


def test_changed_reconciliation_version_rebuilds_without_model_calls(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = Store(tmp_path / "review.sqlite3")
    store.initialize()
    extractor = FixtureExtractor({"D1": evidence("P1", "09:50")})
    path = source(tmp_path / "records", "D1")
    first = process_documents(store, path, extractor, 1)
    monkeypatch.setattr("backbone.workflow.RECONCILIATION_VERSION", "2")
    updated = process_documents(store, path, extractor, 1)
    assert updated.snapshot_id > first.snapshot_id
    assert updated.cached_documents == 1
    assert extractor.calls == ["D1"]
    assert store.snapshot().reconciliation_version == "2"
    assert store.snapshot(first.snapshot_id).reconciliation_version == "1"
