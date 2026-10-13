from contextlib import closing
from datetime import UTC, date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from backbone.models import DocumentRecord, PatientRecord
from backbone.storage import Store, publication_timestamp


def patient(patient_id: str, name: str) -> PatientRecord:
    return PatientRecord(
        patient_id=patient_id,
        name=name,
        organization="Clinic",
        episode_start=date(2026, 1, 1),
        episode_end=date(2026, 1, 30),
        encounters=[],
        plans=[],
        assessments=[],
        observations=[],
    )


@pytest.fixture
def store(tmp_path: Path) -> Store:
    result = Store(tmp_path / "history.sqlite3")
    result.initialize()
    return result


def publish_at(
    store: Store,
    published_at: datetime,
    patients: list[PatientRecord],
    removed_patients: set[str] | None = None,
) -> int:
    revision_id = store.publish(patients, {}, removed_patients=removed_patients)
    with closing(store.connect()) as connection, connection:
        connection.execute(
            "UPDATE revisions SET created_at = ? WHERE id = ?",
            (publication_timestamp(published_at), revision_id),
        )
    return revision_id


def test_history_lists_only_patient_updates_and_publication_times(store: Store) -> None:
    first_time = datetime(2026, 10, 10, 16, 20, tzinfo=UTC)
    second_time = first_time + timedelta(days=1)
    third_time = first_time + timedelta(days=2)
    first = publish_at(store, first_time, [patient("clinic::P1", "Original")])
    publish_at(store, second_time, [patient("clinic::P2", "Other")])
    third = publish_at(store, third_time, [patient("clinic::P1", "Updated")])

    history = store.patient_history("clinic::P1")

    assert [entry.revision_id for entry in history] == [third, first]
    assert [entry.published_at for entry in history] == [third_time, first_time]
    assert [entry.state for entry in history] == ["updated", "updated"]
    assert store.patient_history("P1") == []
    assert store.patient_history("clinic::unknown") == []


def test_patient_state_carries_forward_unchanged_patient_revision(store: Store) -> None:
    first_time = datetime(2026, 10, 10, tzinfo=UTC)
    second_time = first_time + timedelta(days=1)
    first = publish_at(store, first_time, [patient("clinic::P1", "Original")])
    second = publish_at(store, second_time, [patient("clinic::P2", "Other")])

    state = store.patient_at("clinic::P1", revision_id=second)

    assert state.snapshot_id == second
    assert state.snapshot_published_at == second_time
    assert state.patient_revision_id == first
    assert state.patient_published_at == first_time
    assert state.state == "present"
    assert state.patient == patient("clinic::P1", "Original")
    assert store.patient_at("clinic::P1") == state


def test_publication_time_query_is_inclusive_and_resolves_latest_tie(store: Store) -> None:
    first_time = datetime(2026, 10, 10, 16, 20, 0, 123456, tzinfo=UTC)
    first = publish_at(store, first_time, [patient("clinic::P1", "Original")])
    later_time = first_time + timedelta(hours=1)
    publish_at(store, later_time, [patient("clinic::P1", "First update")])
    latest = publish_at(store, later_time, [patient("clinic::P1", "Second update")])

    at_first = store.revision_at(first_time)
    assert at_first is not None
    assert at_first.revision_id == first
    assert at_first.published_at == first_time
    assert store.patient_at("clinic::P1", as_of=later_time - timedelta(microseconds=1)).patient == (
        patient("clinic::P1", "Original")
    )
    at_tie = store.revision_at(later_time)
    assert at_tie is not None
    assert at_tie.revision_id == latest
    assert store.patient_at("clinic::P1", as_of=later_time).patient == (
        patient("clinic::P1", "Second update")
    )


def test_existing_whole_second_publication_timestamp_matches_exact_cutoff(store: Store) -> None:
    published_at = datetime(2026, 10, 10, 16, 20, tzinfo=UTC)
    revision_id = publish_at(store, published_at, [patient("clinic::P1", "Original")])
    with closing(store.connect()) as connection, connection:
        connection.execute(
            "UPDATE revisions SET created_at = ? WHERE id = ?",
            (published_at.isoformat(), revision_id),
        )

    selected = store.revision_at(published_at)

    assert selected is not None
    assert selected.revision_id == revision_id
    assert store.patient_at("clinic::P1", as_of=published_at).state == "present"
    assert store.revision_at(published_at - timedelta(microseconds=1)) is None


def test_timezone_offsets_select_the_same_publication(store: Store) -> None:
    published_at = datetime(2026, 10, 10, 16, 20, tzinfo=UTC)
    publish_at(store, published_at, [patient("clinic::P1", "Original")])
    eastern = published_at.astimezone(timezone(timedelta(hours=-4)))
    eastern_utc = store.patient_at("clinic::P1", as_of=published_at)

    assert store.revision_at(eastern) == store.revision_at(published_at)
    assert store.patient_at("clinic::P1", as_of=eastern) == eastern_utc
    assert store.snapshot_at(eastern) == store.snapshot_at(published_at)
    assert publication_timestamp(eastern) == "2026-10-10T16:20:00.000000+00:00"


def test_before_first_publication_and_unknown_patient_are_not_recorded(store: Store) -> None:
    published_at = datetime(2026, 10, 10, tzinfo=UTC)
    revision_id = publish_at(store, published_at, [patient("clinic::P1", "Original")])
    before = published_at - timedelta(microseconds=1)

    assert store.revision_at(before) is None
    assert store.snapshot_at(before).snapshot_id == 0
    assert store.snapshot_at(before).patients == []
    state = store.patient_at("clinic::P1", as_of=before)
    assert state.snapshot_id == 0
    assert state.snapshot_published_at is None
    assert state.patient_revision_id is None
    assert state.patient_published_at is None
    assert state.state == "not_recorded"
    assert state.patient is None
    unknown = store.patient_at("clinic::unknown", revision_id=revision_id)
    assert unknown.snapshot_id == revision_id
    assert unknown.snapshot_published_at == published_at
    assert unknown.patient_revision_id is None
    assert unknown.patient_published_at is None
    assert unknown.state == "not_recorded"
    assert unknown.patient is None


def test_empty_database_has_no_patient_history_or_publication(store: Store) -> None:
    as_of = datetime(2026, 10, 10, tzinfo=UTC)

    assert store.patient_history("clinic::P1") == []
    assert store.revision_at(as_of) is None
    assert store.snapshot_at(as_of).snapshot_id == 0
    assert store.patient_at("clinic::P1").state == "not_recorded"
    assert store.patient_at("clinic::P1", revision_id=0).snapshot_id == 0


def test_removals_remain_absent_until_patient_is_reintroduced(store: Store) -> None:
    first_time = datetime(2026, 10, 10, tzinfo=UTC)
    first = publish_at(store, first_time, [patient("clinic::P1", "Original")])
    removed_time = first_time + timedelta(days=1)
    removed = publish_at(store, removed_time, [], {"clinic::P1"})
    other_time = first_time + timedelta(days=2)
    other = publish_at(store, other_time, [patient("clinic::P2", "Other")])
    restored_time = first_time + timedelta(days=3)
    restored = publish_at(store, restored_time, [patient("clinic::P1", "Restored")])

    assert store.patient_at("clinic::P1", revision_id=first).state == "present"
    state = store.patient_at("clinic::P1", revision_id=other)
    assert state.snapshot_id == other
    assert state.patient_revision_id == removed
    assert state.patient_published_at == removed_time
    assert state.state == "removed"
    assert state.patient is None
    assert store.patient_at("clinic::P1", as_of=other_time) == state
    assert all(item.patient_id != "clinic::P1" for item in store.snapshot_at(other_time).patients)
    history = store.patient_history("clinic::P1")
    assert [entry.revision_id for entry in history] == [restored, removed, first]
    assert [entry.state for entry in history] == ["updated", "removed", "updated"]
    assert store.patient_at("clinic::P1").patient == patient("clinic::P1", "Restored")


def test_as_of_snapshot_uses_published_coverage_instead_of_current_failures(store: Store) -> None:
    published_at = datetime(2026, 10, 10, tzinfo=UTC)
    revision_id = publish_at(store, published_at, [patient("clinic::P1", "Original")])
    document = DocumentRecord(
        content_hash="new-hash",
        document_id="D1",
        filename="new.txt",
        text="Document ID: D1\nNew evidence.",
    )
    store.add_document(document)
    store.save_failure(document.content_hash, "Extraction failed.")

    assert store.snapshot().failed_documents == ["D1"]
    historical = store.snapshot_at(published_at + timedelta(days=1))
    assert historical.snapshot_id == revision_id
    assert historical.failed_documents == []
    assert historical.pending_documents == []
    assert store.snapshot_at(published_at - timedelta(days=1)).pending_documents == []


def test_time_lookup_and_patient_history_survive_restart(store: Store) -> None:
    published_at = datetime(2026, 10, 10, tzinfo=UTC)
    publish_at(store, published_at, [patient("clinic::P1", "Original")])
    restarted = Store(store.path)
    restarted.initialize()

    assert restarted.patient_history("clinic::P1") == store.patient_history("clinic::P1")
    assert restarted.patient_at("clinic::P1", as_of=published_at) == store.patient_at("clinic::P1")
    assert restarted.snapshot_at(published_at) == store.snapshot_at(published_at)


@pytest.mark.parametrize("revision_id", [-1, 1, 50])
def test_patient_at_rejects_nonexistent_explicit_revision(store: Store, revision_id: int) -> None:
    with pytest.raises(ValueError, match=f"Snapshot {revision_id} does not exist"):
        store.patient_at("clinic::P1", revision_id=revision_id)


def test_patient_at_rejects_two_cutoffs(store: Store) -> None:
    with pytest.raises(ValueError, match="not both"):
        store.patient_at("clinic::P1", as_of=datetime(2026, 10, 10, tzinfo=UTC), revision_id=0)


def test_naive_publication_times_are_rejected(store: Store) -> None:
    naive = datetime(2026, 10, 10)
    with pytest.raises(ValueError, match="timezone offset"):
        publication_timestamp(naive)
    with pytest.raises(ValueError, match="timezone offset"):
        store.revision_at(naive)
    with pytest.raises(ValueError, match="timezone offset"):
        store.snapshot_at(naive)
    with pytest.raises(ValueError, match="timezone offset"):
        store.patient_at("clinic::P1", as_of=naive)


def test_publication_time_lookup_has_a_timestamp_and_revision_index(store: Store) -> None:
    with closing(store.connect()) as connection:
        columns = connection.execute("PRAGMA index_info(revision_publication)").fetchall()
        plan = connection.execute(
            "EXPLAIN QUERY PLAN SELECT id, created_at FROM revisions WHERE created_at <= ? "
            "ORDER BY created_at DESC, id DESC LIMIT 1",
            ("2026-10-10T00:00:00.000000+00:00",),
        ).fetchall()

    assert [str(row["name"]) for row in columns] == ["created_at", "id"]
    assert any("revision_publication" in str(row["detail"]) for row in plan)
