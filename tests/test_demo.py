from __future__ import annotations

from datetime import date
from pathlib import Path
from shutil import copyfile

import pytest
from pydantic import TypeAdapter

from backbone.benchmarking import SubmissionAnswer, replay_questions
from backbone.calculation import calculate
from backbone.demo import DemoReport, SyntheticFixtureExtractor, build_demo
from backbone.extraction import ExtractionValidationError, evidence_claims
from backbone.ingestion import read_document
from backbone.models import ClinicalSnapshot, ExtractionResult, QueryPlan
from backbone.storage import Store
from backbone.workflow import process_documents

FIXTURES = Path(__file__).resolve().parents[1] / "demo"
START = date(2027, 3, 1)
END = date(2027, 3, 28)
CASEY = "synthetic review clinic::SYN-CASEY"
MORGAN = "synthetic review clinic::SYN-MORGAN"
ALEX = "synthetic review clinic::SYN-ALEX"


def demo_answers(directory: Path) -> dict[str, SubmissionAnswer]:
    answers = TypeAdapter(list[SubmissionAnswer]).validate_json(
        (directory / "answers.json").read_bytes()
    )
    return {answer.id: answer for answer in answers}


def test_demo_runs_source_pipeline_and_exports_isolated_snapshot(tmp_path: Path) -> None:
    report = build_demo(tmp_path, FIXTURES)
    assert report.data_kind == "synthetic"
    assert report.extraction_kind == "authored_fixture"
    assert report.planning_kind == "authored_saved_plans"
    assert report.model_calls == 0
    assert report.patient_count == 3
    assert report.document_count == 15
    assert report.processing.extracted_documents == 15
    assert report.processing.failed_documents == {}
    assert report.processing.snapshot_id == 1
    assert {
        "review.sqlite3", "documents", "abstraction.json", "answers.json", "answers.md",
        "plans.json", "questions.json", "extractions.jsonl", "execution.jsonl", "demo-report.json",
    } <= {path.name for path in tmp_path.iterdir()}
    snapshot = ClinicalSnapshot.model_validate_json((tmp_path / "abstraction.json").read_bytes())
    assert snapshot.model_dump() == Store(report.database_path).snapshot().model_dump()
    assert {patient.patient_id for patient in snapshot.patients} == {CASEY, MORGAN, ALEX}
    assert snapshot.unprocessed_documents == []
    saved_report = DemoReport.model_validate_json((tmp_path / "demo-report.json").read_bytes())
    assert saved_report.model_dump() == report.model_dump()


def test_demo_collection_query_has_confirmed_possible_and_excluded_witnesses(
    tmp_path: Path,
) -> None:
    report = build_demo(tmp_path, FIXTURES)
    answers = demo_answers(tmp_path)
    personal = answers["SYN-01"].answer.metrics[0]
    assert personal.patient_id == CASEY
    assert personal.session_count.exact == 2
    assert personal.distinct_days.exact == 2
    assert personal.minutes.exact == 250
    assert [week.decision for week in personal.weeks] == ["not_met", "not_met"]
    cohort = {entry.patient_id: entry for entry in answers["SYN-02"].answer.cohort_results}
    assert {identifier: entry.membership for identifier, entry in cohort.items()} == {
        CASEY: "confirmed", MORGAN: "possible", ALEX: "excluded",
    }
    assert [week.minutes for week in cohort[CASEY].witness] == [120, 130]
    assert [week.minutes for week in cohort[MORGAN].witness] == [130, 130]
    assert cohort[MORGAN].choices
    assert all(week.decision == "not_met" for week in cohort[MORGAN].witness)
    assert cohort[ALEX].witness == []
    snapshot = Store(report.database_path).snapshot()
    morgan = next(patient for patient in snapshot.patients if patient.patient_id == MORGAN)
    metrics = calculate(morgan, START, date(2027, 3, 14))
    assert metrics.session_count.exact == 2
    assert metrics.minutes.values == [260, 300, 340]
    assert metrics.scenario_count == 4
    assert [week.minutes.values for week in metrics.weeks] == [[130, 170], [130, 170]]


def test_demo_plan_change_uses_documented_boundary_and_separate_goals(tmp_path: Path) -> None:
    build_demo(tmp_path, FIXTURES)
    answer = demo_answers(tmp_path)["SYN-03"].answer
    comparison = answer.plan_comparison
    assert comparison is not None
    assert comparison.change_date == date(2027, 3, 15)
    before, after = comparison.before, comparison.after
    assert before is not None and after is not None
    assert (before.start, before.end) == (START, date(2027, 3, 14))
    assert (after.start, after.end) == (date(2027, 3, 15), END)
    assert (
        before.session_count.exact, before.distinct_days.exact, before.minutes.exact
    ) == (2, 2, 210)
    assert (
        after.session_count.exact, after.distinct_days.exact, after.minutes.exact
    ) == (3, 3, 280)
    assert [week.decision for week in before.weeks] == ["met", "met"]
    assert [week.decision for week in after.weeks] == ["not_met", "met"]
    for week in before.weeks:
        assert week.goal is not None
        assert (week.goal.minimum_days, week.goal.minimum_minutes) == (1, 100)
    for week in after.weeks:
        assert week.goal is not None
        assert (week.goal.minimum_days, week.goal.minimum_minutes) == (2, 150)
    assert {"SYN-ALEX-PLAN-OLD", "SYN-ALEX-PLAN-NEW"} <= {
        source.document_id for source in answer.sources
    }


def test_demo_extraction_and_answer_sources_are_verbatim_and_located(tmp_path: Path) -> None:
    build_demo(tmp_path, FIXTURES)
    extractions = [
        ExtractionResult.model_validate_json(line)
        for line in (tmp_path / "extractions.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    sources = [
        source
        for extraction in extractions
        for claim in evidence_claims(extraction.evidence)
        for source in claim.sources
    ]
    sources.extend(
        source for entry in demo_answers(tmp_path).values() for source in entry.answer.sources
    )
    assert len(extractions) == 15
    assert all(result.model == "synthetic-authored-fixture" for result in extractions)
    assert all(
        result.usage.input_tokens == result.usage.output_tokens == 0 for result in extractions
    )
    assert sources
    for source in sources:
        document = read_document(tmp_path / "documents" / source.filename)
        assert "SYNTHETIC" in document.text
        assert source.content_hash == document.content_hash
        assert source.document_id == document.document_id
        lines = document.text.splitlines(keepends=True)
        assert 1 <= source.start_line <= source.end_line <= len(lines)
        assert source.quote in "".join(lines[source.start_line - 1 : source.end_line])


def test_demo_rerun_and_duplicate_file_do_not_add_contacts_or_revisions(tmp_path: Path) -> None:
    first = build_demo(tmp_path, FIXTURES)
    original_abstraction = (tmp_path / "abstraction.json").read_bytes()
    original_answers = (tmp_path / "answers.json").read_bytes()
    second = build_demo(tmp_path, FIXTURES)
    assert second.processing.extracted_documents == 0
    assert second.processing.cached_documents == 15
    assert second.processing.snapshot_id == first.processing.snapshot_id
    assert (tmp_path / "abstraction.json").read_bytes() == original_abstraction
    assert (tmp_path / "answers.json").read_bytes() == original_answers
    documents = tmp_path / "documents"
    copyfile(documents / "SYN-MORGAN-W1-A.txt", documents / "duplicate.txt")
    store = Store(first.database_path)
    report = process_documents(
        store, documents, SyntheticFixtureExtractor(FIXTURES / "extractions.jsonl"), workers=1
    )
    assert report.ingestion.files_seen == 16
    assert report.ingestion.new_documents == 0
    assert report.extracted_documents == 0
    assert report.snapshot_id == first.processing.snapshot_id
    assert len(store.documents()) == 15
    assert store.snapshot().model_dump_json(indent=2).encode("utf-8") == original_abstraction


def test_demo_saved_plans_replay_identical_answers_without_database(tmp_path: Path) -> None:
    build_demo(tmp_path, FIXTURES)
    snapshot = ClinicalSnapshot.model_validate_json((tmp_path / "abstraction.json").read_bytes())
    plans = TypeAdapter(list[QueryPlan]).validate_json((tmp_path / "plans.json").read_bytes())
    original = list(demo_answers(tmp_path).values())
    replayed = replay_questions(
        snapshot, [entry.answer.question for entry in original], plans=plans
    )
    assert [entry.model_dump() for entry in replayed] == [
        entry.answer.model_dump() for entry in original
    ]
    assert all(plan.planner_model_calls == 0 for plan in plans)


def test_demo_fixture_revalidates_patient_duration_against_source() -> None:
    extractor = SyntheticFixtureExtractor(FIXTURES / "extractions.jsonl")
    document = read_document(FIXTURES / "documents" / "SYN-CASEY-W1.txt")
    extractor.results[document.content_hash].evidence.contacts[0].stated_minutes = 121
    with pytest.raises(ExtractionValidationError, match="explicit quoted duration"):
        extractor.extract(document)


def test_demo_refuses_to_mix_with_other_database_records(tmp_path: Path) -> None:
    store = Store(tmp_path / "review.sqlite3")
    store.initialize()
    source = tmp_path / "unrelated.txt"
    source.write_text("Document ID: UNRELATED\nAn unrelated record.\n", encoding="utf-8")
    store.add_document(read_document(source))
    with pytest.raises(ValueError, match="separate output directory"):
        build_demo(tmp_path, FIXTURES)
    assert len(store.documents()) == 1
