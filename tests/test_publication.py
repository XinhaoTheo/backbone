from datetime import date
from pathlib import Path

from backbone.models import PatientRecord
from backbone.storage import Store


def patient(name: str) -> PatientRecord:
    return PatientRecord(
        patient_id="clinic::P1",
        name=name,
        organization="Clinic",
        episode_start=date(2026, 1, 1),
        episode_end=date(2026, 1, 30),
        encounters=[],
        plans=[],
        assessments=[],
        observations=[],
    )


def test_published_patient_versions_survive_restart(tmp_path: Path) -> None:
    store = Store(tmp_path / "review.sqlite3")
    store.initialize()
    first = store.publish([patient("Original")], {})
    second = store.publish([patient("Updated")], {})
    restarted = Store(store.path)
    assert restarted.snapshot(first).patients[0].name == "Original"
    assert restarted.snapshot().patients[0].name == "Updated"
    assert restarted.snapshot().snapshot_id == second
