import os
import subprocess
import sys
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from pydantic import TypeAdapter

from backbone.benchmarking import BenchmarkReport, ReviewQuestion
from backbone.cli import ReviewAnswer
from backbone.models import (
    ClinicalSnapshot,
    ContactAlternative,
    DocumentRecord,
    Encounter,
    HistoricalPatientState,
    PatientHistoryEntry,
    PatientRecord,
    PlanClaim,
    QueryPlan,
    QueryTask,
)
from backbone.query import AnswerBundle
from backbone.storage import Store


@dataclass
class HistoryDatabase:
    store: Store
    first: int
    second: int
    third: int
    fourth: int


def history_patient(patient_id: str, name: str, minutes: int) -> PatientRecord:
    return PatientRecord(
        patient_id=patient_id,
        name=name,
        organization="Test clinic",
        episode_start=date(2027, 2, 1),
        episode_end=date(2027, 2, 7),
        encounters=[Encounter(
            encounter_id=f"{patient_id}-CONTACT",
            patient_id=patient_id,
            service_date=date(2027, 2, 1),
            service_type="individual",
            attendance="attended",
            patient_present=True,
            alternatives=[ContactAlternative(minutes=minutes, intervals=[], sources=[])],
            decisions=[],
            sources=[],
        )],
        plans=[PlanClaim(
            patient_id=patient_id,
            effective_start=date(2027, 2, 1),
            effective_end=None,
            minimum_days=1,
            minimum_minutes=30,
            eligible_services=["individual"],
            week_start="Monday",
            patient_present_required=True,
            note="Weekly patient-present treatment goal.",
            quotes=[],
        )],
        assessments=[],
        observations=[],
    )


@pytest.fixture
def history_database(tmp_path: Path) -> HistoryDatabase:
    store = Store(tmp_path / "review.sqlite3")
    store.initialize()
    first = store.publish([history_patient("P1", "Ellis", 40)], {})
    second = store.publish([history_patient("P2", "Alex", 60)], {})
    third = store.publish([history_patient("P1", "Ellis", 50)], {})
    fourth = store.publish([], {}, removed_patients={"P1"})
    with closing(store.connect()) as connection, connection:
        connection.executemany(
            "UPDATE revisions SET created_at = ? WHERE id = ?",
            [
                (datetime(2027, 2, day, 12, tzinfo=UTC).isoformat(), revision)
                for day, revision in enumerate([first, second, third, fourth], start=1)
            ],
        )
    return HistoryDatabase(store, first, second, third, fourth)


def history_cli(
    directory: Path, database: Path, arguments: list[str]
) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["OPENAI_API_KEY"] = ""
    return subprocess.run(
        [sys.executable, "-m", "backbone", "--db", str(database), *arguments],
        cwd=directory,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )


def history_plan(question: str, snapshot_id: int) -> QueryPlan:
    return QueryPlan(
        question=question,
        snapshot_id=snapshot_id,
        tasks=[QueryTask(
            operation="durations",
            patient="P1",
            patient_ids=["P1"],
            start=date(2027, 2, 1),
            end=date(2027, 2, 7),
        )],
    )


def test_history_lists_only_patient_updates_and_removal_latest_first(
    tmp_path: Path, history_database: HistoryDatabase
) -> None:
    completed = history_cli(
        tmp_path, history_database.store.path, ["history", "P1", "--json"]
    )
    assert completed.returncode == 0, completed.stderr
    entries = TypeAdapter(list[PatientHistoryEntry]).validate_json(completed.stdout)
    assert [(entry.revision_id, entry.state) for entry in entries] == [
        (history_database.fourth, "removed"),
        (history_database.third, "updated"),
        (history_database.first, "updated"),
    ]
    assert [entry.published_at for entry in entries] == [
        datetime(2027, 2, day, 12, tzinfo=UTC) for day in (4, 3, 1)
    ]


def test_history_human_output_identifies_publication_time_and_removal(
    tmp_path: Path, history_database: HistoryDatabase
) -> None:
    completed = history_cli(tmp_path, history_database.store.path, ["history", "P1"])
    assert completed.returncode == 0, completed.stderr
    assert "Revision" in completed.stdout
    assert "Published at (UTC)" in completed.stdout
    assert "State" in completed.stdout
    assert "2027-02-04" in completed.stdout
    assert "removed" in completed.stdout
    assert "updated" in completed.stdout


def test_unknown_patient_has_empty_history_in_text_and_json(
    tmp_path: Path, history_database: HistoryDatabase
) -> None:
    text_result = history_cli(tmp_path, history_database.store.path, ["history", "UNKNOWN"])
    assert text_result.returncode == 0, text_result.stderr
    assert "No published history" in text_result.stdout
    json_result = history_cli(
        tmp_path, history_database.store.path, ["history", "UNKNOWN", "--json"]
    )
    assert json_result.returncode == 0, json_result.stderr
    assert TypeAdapter(list[PatientHistoryEntry]).validate_json(json_result.stdout) == []


def test_latest_patient_distinguishes_snapshot_from_carried_forward_patient_revision(
    tmp_path: Path, history_database: HistoryDatabase
) -> None:
    completed = history_cli(tmp_path, history_database.store.path, ["patient", "P2"])
    assert completed.returncode == 0, completed.stderr
    state = HistoricalPatientState.model_validate_json(completed.stdout)
    assert state.patient_id == "P2"
    assert state.snapshot_id == history_database.fourth
    assert state.snapshot_published_at == datetime(2027, 2, 4, 12, tzinfo=UTC)
    assert state.patient_revision_id == history_database.second
    assert state.patient_published_at == datetime(2027, 2, 2, 12, tzinfo=UTC)
    assert state.state == "present"
    assert state.patient is not None
    assert state.patient.name == "Alex"
    assert state.patient.encounters[0].alternatives[0].minutes == 60


def test_patient_snapshot_reads_last_update_at_or_before_selected_global_revision(
    tmp_path: Path, history_database: HistoryDatabase
) -> None:
    completed = history_cli(tmp_path, history_database.store.path, [
        "patient", "P1", "--snapshot", str(history_database.second),
    ])
    assert completed.returncode == 0, completed.stderr
    state = HistoricalPatientState.model_validate_json(completed.stdout)
    assert state.snapshot_id == history_database.second
    assert state.patient_revision_id == history_database.first
    assert state.snapshot_published_at == datetime(2027, 2, 2, 12, tzinfo=UTC)
    assert state.patient_published_at == datetime(2027, 2, 1, 12, tzinfo=UTC)
    assert state.patient is not None
    assert state.patient.encounters[0].alternatives[0].minutes == 40


def test_patient_as_of_normalizes_offset_and_includes_publication_at_cutoff(
    tmp_path: Path, history_database: HistoryDatabase
) -> None:
    completed = history_cli(tmp_path, history_database.store.path, [
        "patient", "P1", "--as-of", "2027-02-03T07:00:00-05:00",
    ])
    assert completed.returncode == 0, completed.stderr
    state = HistoricalPatientState.model_validate_json(completed.stdout)
    assert state.snapshot_id == history_database.third
    assert state.patient_revision_id == history_database.third
    assert state.patient is not None
    assert state.patient.encounters[0].alternatives[0].minutes == 50


def test_patient_distinguishes_removed_from_not_recorded(
    tmp_path: Path, history_database: HistoryDatabase
) -> None:
    removed_result = history_cli(tmp_path, history_database.store.path, ["patient", "P1"])
    assert removed_result.returncode == 0, removed_result.stderr
    removed = HistoricalPatientState.model_validate_json(removed_result.stdout)
    assert removed.state == "removed"
    assert removed.patient is None
    assert removed.patient_revision_id == history_database.fourth
    not_recorded_result = history_cli(tmp_path, history_database.store.path, [
        "patient", "P2", "--snapshot", str(history_database.first),
    ])
    assert not_recorded_result.returncode == 0, not_recorded_result.stderr
    not_recorded = HistoricalPatientState.model_validate_json(not_recorded_result.stdout)
    assert not_recorded.state == "not_recorded"
    assert not_recorded.patient is None
    assert not_recorded.patient_revision_id is None
    assert not_recorded.patient_published_at is None


def test_patient_as_of_before_first_publication_returns_empty_historical_state(
    tmp_path: Path, history_database: HistoryDatabase
) -> None:
    completed = history_cli(tmp_path, history_database.store.path, [
        "patient", "P1", "--as-of", "2027-02-01T11:59:59Z",
    ])
    assert completed.returncode == 0, completed.stderr
    state = HistoricalPatientState.model_validate_json(completed.stdout)
    assert state.snapshot_id == 0
    assert state.snapshot_published_at is None
    assert state.state == "not_recorded"
    assert state.patient is None


def test_as_of_ask_uses_published_coverage_and_saved_plan_without_api(
    tmp_path: Path, history_database: HistoryDatabase
) -> None:
    question = "How many therapy minutes did Ellis receive?"
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(
        history_plan(question, history_database.second).model_dump_json(), encoding="utf-8"
    )
    history_database.store.add_document(DocumentRecord(
        content_hash="late-failed-document",
        document_id="LATE-FAILURE",
        filename="late.txt",
        text="Document ID: LATE-FAILURE\nLater unprocessed evidence.",
    ))
    history_database.store.save_failure("late-failed-document", "Unavailable extraction")
    completed = history_cli(tmp_path, history_database.store.path, [
        "ask", question, "--as-of", "2027-02-02T13:00:00Z",
        "--plan", str(plan_path), "--json",
    ])
    assert completed.returncode == 0, completed.stderr
    answer = AnswerBundle.model_validate_json(completed.stdout)
    assert answer.snapshot_id == history_database.second
    assert answer.metrics[0].minutes.exact == 40
    assert answer.coverage_status == "available_records"
    assert "LATE-FAILURE" not in answer.text
    assert "Configure OPENAI_API_KEY" not in completed.stderr


@pytest.mark.parametrize("command", ["answer-file", "export", "benchmark"])
def test_as_of_batch_commands_select_the_historical_snapshot_offline(
    tmp_path: Path, history_database: HistoryDatabase, command: str
) -> None:
    question = "How many therapy minutes did Ellis receive?"
    questions_path = tmp_path / "questions.json"
    questions_path.write_bytes(TypeAdapter(list[ReviewQuestion]).dump_json([
        ReviewQuestion(id="historical-duration", question=question),
    ]))
    plans_path = tmp_path / "plans.json"
    plans_path.write_bytes(TypeAdapter(list[QueryPlan]).dump_json([
        history_plan(question, history_database.second),
    ]))
    output = tmp_path / ("benchmark.json" if command == "benchmark" else "answers")
    completed = history_cli(tmp_path, history_database.store.path, [
        command, str(questions_path), "--as-of", "2027-02-02T13:00:00Z",
        "--plans", str(plans_path), "--output", str(output),
    ])
    assert completed.returncode == 0, completed.stderr
    assert "Configure OPENAI_API_KEY" not in completed.stderr
    if command == "benchmark":
        report = BenchmarkReport.model_validate_json(output.read_bytes())
        assert report.snapshot_id == history_database.second
        assert report.model_calls == 0
    else:
        answers = TypeAdapter(list[ReviewAnswer]).validate_json(
            (output / "answers.json").read_bytes()
        )
        assert answers[0].answer.snapshot_id == history_database.second
        assert answers[0].answer.metrics[0].minutes.exact == 40
        if command == "export":
            snapshot = ClinicalSnapshot.model_validate_json(
                (output / "abstraction.json").read_bytes()
            )
            assert snapshot.snapshot_id == history_database.second


@pytest.mark.parametrize("command", ["patient", "ask", "answer-file", "export", "benchmark"])
@pytest.mark.parametrize("timestamp", ["2027-02-02T12:00:00", "not-a-timestamp"])
def test_invalid_as_of_exits_cleanly_before_api_or_file_reads(
    tmp_path: Path, command: str, timestamp: str
) -> None:
    subject = "P1" if command == "patient" else "unused-question-or-file"
    completed = history_cli(tmp_path, tmp_path / "review.sqlite3", [
        command, subject, "--as-of", timestamp,
    ])
    assert completed.returncode == 2
    assert "--as-of" in completed.stderr
    assert "ISO" in completed.stderr or "timezone" in completed.stderr
    assert "Traceback" not in completed.stderr
    assert "Configure OPENAI_API_KEY" not in completed.stderr
    assert not completed.stdout


@pytest.mark.parametrize("command", ["patient", "ask", "answer-file", "export", "benchmark"])
def test_snapshot_and_as_of_are_mutually_exclusive(tmp_path: Path, command: str) -> None:
    subject = "P1" if command == "patient" else "unused-question-or-file"
    completed = history_cli(tmp_path, tmp_path / "review.sqlite3", [
        command, subject, "--snapshot", "1", "--as-of", "2027-02-02T12:00:00Z",
    ])
    assert completed.returncode == 2
    assert "--snapshot" in completed.stderr and "--as-of" in completed.stderr
    assert "not allowed" in completed.stderr
    assert "Traceback" not in completed.stderr
    assert "Configure OPENAI_API_KEY" not in completed.stderr
    assert not completed.stdout
