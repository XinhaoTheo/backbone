import os
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest
from pydantic import TypeAdapter

from backbone.benchmarking import BenchmarkReport
from backbone.cli import ReviewAnswer, ReviewQuestion
from backbone.ingestion import read_document
from backbone.models import (
    AssessmentClaim,
    ClinicalSnapshot,
    ContactAlternative,
    ContactClaim,
    DocumentEvidence,
    DocumentRecord,
    Encounter,
    ExtractionResult,
    ModelUsage,
    PatientIdentity,
    PatientRecord,
    PlanClaim,
    QueryOperation,
    QueryPlan,
    QueryTask,
    SourceRef,
)
from backbone.query import AnswerBundle
from backbone.storage import Store


def source_document(
    directory: Path, identifier: str, quote: str
) -> tuple[DocumentRecord, SourceRef]:
    path = directory / f"{identifier}.txt"
    path.write_text(f"Document ID: {identifier}\n{quote}\n", encoding="utf-8")
    document = read_document(path)
    return document, SourceRef(
        content_hash=document.content_hash, document_id=document.document_id,
        filename=document.filename, start_line=2, end_line=2, quote=quote,
    )


def publish_patient(store: Store, directory: Path, minutes: int) -> int:
    plan_document, plan_source = source_document(
        directory, "PLAN", "Ellis (TEST-1), episode February 1-7, 2027: at least one "
        "patient-present individual psychotherapy day and 30 minutes each Monday-Sunday week, "
        "effective February 1, 2027."
    )
    contact_document, contact_source = source_document(
        directory, f"CONTACT-{minutes}",
        f"Ellis (TEST-1) attended {minutes} minutes of patient-present individual psychotherapy "
        "on February 1, 2027, encounter CONTACT-1."
        + (" This corrects the earlier contact duration." if minutes != 40 else ""),
    )
    assessment_document, assessment_source = source_document(
        directory, "MEASURE", "Ellis (TEST-1) completed PHQ-9 FORM-1 on February 1, 2027; "
        "score 12, item 9 zero."
    )
    for document in [plan_document, contact_document, assessment_document]:
        store.add_document(document)
    patient = PatientRecord(
        patient_id="TEST-1", name="Ellis", organization="Test clinic",
        episode_start=date(2027, 2, 1), episode_end=date(2027, 2, 7),
        encounters=[Encounter(
            encounter_id="CONTACT-1", patient_id="TEST-1", service_date=date(2027, 2, 1),
            service_type="individual", attendance="attended", patient_present=True,
            alternatives=[ContactAlternative(
                minutes=minutes, intervals=[], sources=[contact_source],
            )], decisions=[], sources=[contact_source],
        )],
        plans=[PlanClaim(
            patient_id="TEST-1", effective_start=date(2027, 2, 1), effective_end=None,
            minimum_days=1, minimum_minutes=30, eligible_services=["individual"],
            week_start="Monday", patient_present_required=True,
            note="Documented patient-present therapy goal.",
            quotes=[plan_source.quote], sources=[plan_source],
        )],
        assessments=[AssessmentClaim(
            patient_id="TEST-1", completed_date=date(2027, 2, 1), instrument="PHQ-9", score=12,
            form_id="FORM-1", item_nine=0, is_copy=False,
            quotes=[assessment_source.quote], sources=[assessment_source],
        )], observations=[],
    )
    identity = PatientIdentity(
        patient_id=patient.patient_id, name=patient.name, organization=patient.organization,
        episode_start=patient.episode_start, episode_end=patient.episode_end,
    )
    evidences = [
        (plan_document, DocumentEvidence(
            patients=[identity], contacts=[], plans=patient.plans, assessments=[], observations=[],
        )),
        (contact_document, DocumentEvidence(
            patients=[identity], contacts=[ContactClaim(
                patient_id=patient.patient_id, service_date=date(2027, 2, 1),
                encounter_id="CONTACT-1", appointment_id=None, service_type="individual",
                attendance="attended", patient_present=True, intervals=[],
                interval_kind="patient_contact", breaks=[], stated_minutes=minutes,
                record_status="correction" if minutes != 40 else "final",
                correction_fields=["duration"] if minutes != 40 else [],
                is_copy=False, note="Full patient contact duration.",
                quotes=[contact_source.quote], sources=[contact_source],
            )], plans=[], assessments=[], observations=[],
        )),
        (assessment_document, DocumentEvidence(
            patients=[identity], contacts=[], plans=[],
            assessments=patient.assessments, observations=[],
        )),
    ]
    active_keys: dict[str, str] = {}
    for document, evidence in evidences:
        cache_key = f"offline-test:{document.content_hash}"
        store.save_extraction(document.content_hash, cache_key, ExtractionResult(
            evidence=evidence, model="offline-test-fixture", usage=ModelUsage(), elapsed_seconds=0,
        ))
        active_keys[document.content_hash] = cache_key
    return store.publish([patient], active_keys)


def cli(
    directory: Path, database: Path, arguments: list[str]
) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["OPENAI_API_KEY"] = ""
    return subprocess.run(
        [sys.executable, "-m", "backbone", "--db", str(database), *arguments],
        cwd=directory, env=environment, capture_output=True, text=True, check=False, timeout=20,
    )


def write_questions(directory: Path, questions: list[ReviewQuestion]) -> Path:
    adapter: TypeAdapter[list[ReviewQuestion]] = TypeAdapter(list[ReviewQuestion])
    path = directory / "questions.json"
    path.write_bytes(adapter.dump_json(questions))
    return path


def query_plan(question: str, snapshot_id: int, operation: QueryOperation) -> QueryPlan:
    return QueryPlan(
        question=question, snapshot_id=snapshot_id,
        tasks=[QueryTask(
            operation=operation, patient="TEST-1", patient_ids=["TEST-1"],
            start=date(2027, 2, 1), end=date(2027, 2, 7),
        )],
    )


def write_plan(directory: Path, plan: QueryPlan) -> Path:
    path = directory / "plan.json"
    path.write_text(plan.model_dump_json(), encoding="utf-8")
    return path


def write_plans(directory: Path, plans: list[QueryPlan]) -> Path:
    adapter: TypeAdapter[list[QueryPlan]] = TypeAdapter(list[QueryPlan])
    path = directory / "plans.json"
    path.write_bytes(adapter.dump_json(plans))
    return path


def test_ask_after_restart_uses_selected_persisted_snapshot(tmp_path: Path) -> None:
    database = tmp_path / "review.sqlite3"
    store = Store(database)
    store.initialize()
    first = publish_patient(store, tmp_path, 40)
    second = publish_patient(store, tmp_path, 50)
    question = "How many therapy minutes did Ellis receive?"
    plan_path = write_plan(tmp_path, query_plan(question, first, "durations"))
    historical = cli(tmp_path, database, [
        "ask", question, "--snapshot", str(first), "--json", "--plan", str(plan_path),
    ])
    assert historical.returncode == 0, historical.stderr
    previous = AnswerBundle.model_validate_json(historical.stdout)
    assert previous.snapshot_id == first
    assert previous.metrics[0].minutes.exact == 40
    assert previous.metrics[0].session_count.exact == 1
    assert any(source.document_id == "CONTACT-40" for source in previous.sources)

    write_plan(tmp_path, query_plan(question, second, "durations"))
    current = cli(tmp_path, database, ["ask", question, "--json", "--plan", str(plan_path)])
    assert current.returncode == 0, current.stderr
    latest = AnswerBundle.model_validate_json(current.stdout)
    assert latest.snapshot_id == second
    assert latest.metrics[0].minutes.exact == 50
    assert any(source.document_id == "CONTACT-50" for source in latest.sources)


def test_answer_file_preserves_ids_and_snapshot_for_metrics_and_symptoms(tmp_path: Path) -> None:
    database = tmp_path / "review.sqlite3"
    store = Store(database)
    store.initialize()
    first = publish_patient(store, tmp_path, 40)
    publish_patient(store, tmp_path, 50)
    questions = [
        ReviewQuestion(
            id="custom-duration", question="How many therapy minutes did Ellis receive?",
        ),
        ReviewQuestion(
            id="custom-symptoms", question="Summarize Ellis's symptom course during the episode.",
        ),
    ]
    question_adapter: TypeAdapter[list[ReviewQuestion]] = TypeAdapter(list[ReviewQuestion])
    question_path = tmp_path / "questions.json"
    question_path.write_bytes(question_adapter.dump_json(questions))
    plans_path = write_plans(tmp_path, [
        query_plan(questions[0].question, first, "durations"),
        query_plan(questions[1].question, first, "symptoms"),
    ])
    output = tmp_path / "answers"
    completed = cli(tmp_path, database, [
        "answer-file", str(question_path), "--snapshot", str(first), "--output", str(output),
        "--plans", str(plans_path),
    ])
    assert completed.returncode == 0, completed.stderr
    answer_adapter: TypeAdapter[list[ReviewAnswer]] = TypeAdapter(list[ReviewAnswer])
    answers = answer_adapter.validate_json((output / "answers.json").read_bytes())
    assert [answer.id for answer in answers] == ["custom-duration", "custom-symptoms"]
    assert all(answer.answer.snapshot_id == first for answer in answers)
    assert answers[0].answer.metrics[0].minutes.exact == 40
    assert [(item.completed_date, item.score) for item in answers[1].answer.assessments] == [
        (date(2027, 2, 1), 12),
    ]
    assert any(source.document_id == "MEASURE" for source in answers[1].answer.sources)
    markdown = (output / "answers.md").read_text(encoding="utf-8")
    assert "## custom-duration" in markdown and "## custom-symptoms" in markdown


def test_missing_query_api_key_exits_nonzero_with_actionable_error(tmp_path: Path) -> None:
    database = tmp_path / "review.sqlite3"
    store = Store(database)
    store.initialize()
    publish_patient(store, tmp_path, 40)
    completed = cli(tmp_path, database, [
        "ask", "How many therapy minutes did Ellis receive?", "--json",
    ])
    assert completed.returncode != 0
    assert "Configure OPENAI_API_KEY" in completed.stderr
    assert "Traceback" not in completed.stderr
    assert not completed.stdout


def test_saved_plan_from_wrong_snapshot_is_rejected(tmp_path: Path) -> None:
    database = tmp_path / "review.sqlite3"
    store = Store(database)
    store.initialize()
    first = publish_patient(store, tmp_path, 40)
    publish_patient(store, tmp_path, 50)
    question = "How many therapy minutes did Ellis receive?"
    plan_path = write_plan(tmp_path, query_plan(question, first, "durations"))
    completed = cli(tmp_path, database, ["ask", question, "--plan", str(plan_path), "--json"])
    assert completed.returncode != 0
    assert "must match this question and snapshot" in completed.stderr
    assert "Traceback" not in completed.stderr
    assert not completed.stdout


def test_export_and_replay_preserve_snapshot_without_api_or_database(tmp_path: Path) -> None:
    database = tmp_path / "review.sqlite3"
    store = Store(database)
    store.initialize()
    first = publish_patient(store, tmp_path, 40)
    question_path = write_questions(tmp_path, [ReviewQuestion(
        id="offline-duration", question="How many therapy minutes did Ellis receive?",
    )])
    plans_path = write_plans(tmp_path, [
        query_plan("How many therapy minutes did Ellis receive?", first, "durations"),
    ])
    exported = tmp_path / "exported"
    completed = cli(tmp_path, database, [
        "export", str(question_path), "--output", str(exported), "--plans", str(plans_path),
    ])
    assert completed.returncode == 0, completed.stderr
    assert {path.name for path in exported.iterdir()} >= {
        "abstraction.json", "answers.json", "answers.md", "extractions.jsonl", "execution.jsonl",
        "plans.json",
    }
    saved = ClinicalSnapshot.model_validate_json((exported / "abstraction.json").read_bytes())
    assert saved.snapshot_id == first
    publish_patient(store, tmp_path, 50)

    nonexistent_database = tmp_path / "unused" / "review.sqlite3"
    replayed = tmp_path / "replayed"
    completed = cli(tmp_path, nonexistent_database, [
        "replay", str(exported / "abstraction.json"), str(question_path),
        "--output", str(replayed), "--plans", str(exported / "plans.json"),
    ])
    assert completed.returncode == 0, completed.stderr
    assert not nonexistent_database.exists()
    assert not nonexistent_database.parent.exists()
    adapter: TypeAdapter[list[ReviewAnswer]] = TypeAdapter(list[ReviewAnswer])
    original_answers = adapter.validate_json((exported / "answers.json").read_bytes())
    replayed_answers = adapter.validate_json((replayed / "answers.json").read_bytes())
    assert [answer.model_dump() for answer in replayed_answers] == [
        answer.model_dump() for answer in original_answers
    ]
    assert replayed_answers[0].id == "offline-duration"
    assert replayed_answers[0].answer.snapshot_id == first
    assert replayed_answers[0].answer.metrics[0].minutes.exact == 40


def test_benchmark_covers_cohort_queries_with_zero_model_calls(tmp_path: Path) -> None:
    database = tmp_path / "review.sqlite3"
    store = Store(database)
    store.initialize()
    revision = publish_patient(store, tmp_path, 40)
    questions = [
        ReviewQuestion(id="duration", question="How many therapy minutes did Ellis receive?"),
        ReviewQuestion(
            id="cohort",
            question="Which patients had two consecutive weeks below their treatment requirements?",
        ),
    ]
    question_path = write_questions(tmp_path, questions)
    plans_path = write_plans(tmp_path, [
        query_plan(questions[0].question, revision, "durations"),
        query_plan(questions[1].question, revision, "cohort"),
    ])
    output = tmp_path / "benchmark.json"
    completed = cli(tmp_path, database, [
        "benchmark", str(question_path), "--repeats", "3", "--output", str(output),
        "--plans", str(plans_path),
    ])
    assert completed.returncode == 0, completed.stderr
    report = BenchmarkReport.model_validate_json(output.read_bytes())
    printed = BenchmarkReport.model_validate_json(completed.stdout)
    assert printed.model_dump() == report.model_dump()
    assert report.snapshot_id == revision
    assert report.scope == "in_memory_execution_only"
    assert report.model_calls == 0
    assert report.repeats == 3 and report.query_runs == 6
    assert report.patient_count == 1 and report.document_count == 3
    assert [query.operation for query in report.queries] == ["durations", "cohort"]
    assert all(query.answer_status == "established" for query in report.queries)
    assert all(query.stable_across_repeats for query in report.queries)
    assert all(len(query.latency_seconds) == 3 for query in report.queries)
    assert all(sample >= 0 for query in report.queries for sample in query.latency_seconds)


@pytest.mark.parametrize("command", ["answer-file", "export", "benchmark", "replay"])
def test_malformed_saved_plans_exit_cleanly_before_api_or_export(
    tmp_path: Path, command: str
) -> None:
    database = tmp_path / "review.sqlite3"
    store = Store(database)
    store.initialize()
    publish_patient(store, tmp_path, 40)
    question_path = write_questions(tmp_path, [ReviewQuestion(
        id="duration", question="How many therapy minutes did Ellis receive?",
    )])
    plans_path = tmp_path / "plans.json"
    plans_path.write_text('[{"question":', encoding="utf-8")
    output = tmp_path / "output"
    arguments = [command, str(question_path), "--plans", str(plans_path), "--output", str(output)]
    if command == "replay":
        abstraction = tmp_path / "abstraction.json"
        abstraction.write_text(store.snapshot().model_dump_json(), encoding="utf-8")
        arguments.insert(1, str(abstraction))
    completed = cli(tmp_path, database, arguments)
    assert completed.returncode == 2
    assert "Invalid JSON" in completed.stderr
    assert "Traceback" not in completed.stderr
    assert "Configure OPENAI_API_KEY" not in completed.stderr
    assert not completed.stdout
    assert not output.exists()
    assert store.execution_records() == []


@pytest.mark.parametrize("command", ["answer-file", "export", "benchmark", "replay"])
def test_saved_plan_count_must_match_questions_before_api_or_export(
    tmp_path: Path, command: str
) -> None:
    database = tmp_path / "review.sqlite3"
    store = Store(database)
    store.initialize()
    revision = publish_patient(store, tmp_path, 40)
    questions = [
        ReviewQuestion(id="duration", question="How many therapy minutes did Ellis receive?"),
        ReviewQuestion(id="symptoms", question="Summarize Ellis's symptoms."),
    ]
    question_path = write_questions(tmp_path, questions)
    plans_path = write_plans(tmp_path, [query_plan(questions[0].question, revision, "durations")])
    output = tmp_path / "output"
    arguments = [command, str(question_path), "--plans", str(plans_path), "--output", str(output)]
    if command == "replay":
        abstraction = tmp_path / "abstraction.json"
        abstraction.write_text(store.snapshot().model_dump_json(), encoding="utf-8")
        arguments.insert(1, str(abstraction))
    completed = cli(tmp_path, database, arguments)
    assert completed.returncode == 2
    assert "Provide one saved plan per" in completed.stderr
    assert "Traceback" not in completed.stderr
    assert "Configure OPENAI_API_KEY" not in completed.stderr
    assert not completed.stdout
    assert not output.exists()
    assert store.execution_records() == []
