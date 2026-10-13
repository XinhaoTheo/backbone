from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import pytest
from pydantic import TypeAdapter

from backbone.benchmarking import (
    ReviewQuestion,
    SubmissionAnswer,
    benchmark,
    export_submission,
    replay_questions,
)
from backbone.models import (
    ClinicalSnapshot,
    ContactAlternative,
    Encounter,
    ModelUsage,
    PatientRecord,
    PlanClaim,
    QueryOperation,
    QueryPlan,
    QueryTask,
    SourceRef,
    TimeInterval,
)
from backbone.planning import (
    IntentResult,
    PlanningContext,
    QueryIntent,
    QueryPlanningError,
    TaskIntent,
)


@dataclass
class FakePlanner:
    results: list[IntentResult | QueryPlanningError]
    questions: list[str] = field(default_factory=list)

    def interpret(self, question: str, context: PlanningContext) -> IntentResult:
        result = self.results[len(self.questions)]
        self.questions.append(question)
        if isinstance(result, QueryPlanningError):
            raise result
        return result


def saved_plan(question: str, operation: QueryOperation) -> QueryPlan:
    return QueryPlan(
        question=question,
        snapshot_id=12,
        tasks=[
            QueryTask(
                operation=operation,
                patient="P1",
                patient_ids=["P1"],
                start=date(2027, 5, 3),
                end=date(2027, 5, 9),
            )
        ],
    )


def count_intent() -> IntentResult:
    return IntentResult(
        intent=QueryIntent(status="ready", message="", tasks=[TaskIntent(operation="counts")]),
        model="test-planner",
        model_calls=1,
    )


def unsupported_intent() -> IntentResult:
    return IntentResult(
        intent=QueryIntent(status="unsupported", message="Unsupported clinical advice.", tasks=[]),
        model="test-planner",
        model_calls=1,
    )


def snapshot() -> ClinicalSnapshot:
    source = SourceRef(
        content_hash="SESSION",
        document_id="SESSION",
        filename="session.txt",
        start_line=3,
        end_line=3,
        quote="Actual patient psychotherapy contact: 09:00-09:40.",
    )
    plan_source = SourceRef(
        content_hash="PLAN",
        document_id="PLAN",
        filename="plan.txt",
        start_line=5,
        end_line=5,
        quote="The weekly goal is one therapy day and 30 minutes.",
    )
    patient = PatientRecord(
        patient_id="P1",
        name="Casey",
        organization="Test Clinic",
        episode_start=date(2027, 5, 3),
        episode_end=date(2027, 5, 9),
        encounters=[
            Encounter(
                encounter_id="E1",
                patient_id="P1",
                service_date=date(2027, 5, 4),
                service_type="individual",
                attendance="attended",
                patient_present=True,
                alternatives=[
                    ContactAlternative(
                        minutes=40,
                        intervals=[TimeInterval(start="09:00", end="09:40")],
                        sources=[source],
                    )
                ],
                decisions=[],
                sources=[source],
            )
        ],
        plans=[
            PlanClaim(
                patient_id="P1",
                effective_start=date(2027, 5, 3),
                effective_end=None,
                minimum_days=1,
                minimum_minutes=30,
                eligible_services=["individual"],
                week_start="Monday",
                patient_present_required=True,
                note="Patient-present therapy.",
                quotes=[plan_source.quote],
                sources=[plan_source],
            )
        ],
        assessments=[],
        observations=[],
    )
    return ClinicalSnapshot(snapshot_id=12, patients=[patient])


def test_benchmark_reports_measured_samples_and_interpolated_percentiles(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ticks: Iterator[float] = iter([0.0, 1.0, 1.001, 2.0, 2.002, 3.0, 3.010, 4.0])

    def clock() -> float:
        return next(ticks)

    monkeypatch.setattr("backbone.benchmarking.perf_counter", clock)
    report = benchmark(
        snapshot(),
        ["How many therapy minutes did Casey receive?"],
        document_count=2,
        plans=[saved_plan("How many therapy minutes did Casey receive?", "durations")],
    )
    result = report.queries[0]
    assert result.latency_seconds == pytest.approx([0.001, 0.002, 0.010])
    assert result.p50_seconds == pytest.approx(0.002)
    assert result.p95_seconds == pytest.approx(0.0092)
    assert result.answer_status == "established"
    assert result.operation == "durations"
    assert result.stable_across_repeats
    assert report.elapsed_seconds == 4.0
    assert report.document_count == 2 and report.patient_count == 1
    assert report.snapshot_id == 12 and report.scenario_budget == 10_000
    assert report.query_runs == 3 and report.model_calls == 0
    assert report.measurement_kind == "measured"
    assert report.scope == "in_memory_execution_only"
    assert report.planning_seconds == 0
    assert report.planning_input_tokens == 0
    assert report.planning_output_tokens == 0
    assert report.abstraction_bytes == len(snapshot().model_dump_json().encode("utf-8"))
    assert report.limitations


def test_unsupported_question_is_measured_without_hiding_valid_query_results() -> None:
    planner = FakePlanner([unsupported_intent(), count_intent()])
    report = benchmark(
        snapshot(),
        ["Recommend medication for Casey.", "Count Casey's therapy sessions."],
        repeats=1,
        document_count=2,
        planner=planner,
    )
    assert report.queries[0].answer_status == "planning_error"
    assert report.queries[0].reason is not None
    assert report.queries[0].operation is None
    assert report.queries[1].answer_status == "established"
    assert report.query_runs == 2
    assert report.model_calls == 2
    assert len(planner.questions) == 2


def test_benchmark_plans_once_and_measures_only_repeated_execution() -> None:
    result = count_intent()
    result.usage = ModelUsage(input_tokens=140, output_tokens=35)
    result.elapsed_seconds = 0.4
    planner = FakePlanner([result])
    report = benchmark(
        snapshot(),
        ["Count Casey's therapy sessions."],
        repeats=3,
        document_count=2,
        planner=planner,
    )
    assert planner.questions == ["Count Casey's therapy sessions."]
    assert report.model_calls == 1
    assert report.query_runs == 3
    assert report.planning_input_tokens == 140
    assert report.planning_output_tokens == 35
    assert report.planning_seconds == pytest.approx(0.4)
    assert report.queries[0].stable_across_repeats


def test_benchmark_retains_usage_when_model_returns_unsupported_intent() -> None:
    failed = unsupported_intent()
    failed.usage = ModelUsage(input_tokens=140, output_tokens=35)
    failed.elapsed_seconds = 0.4
    planner = FakePlanner([failed])
    report = benchmark(
        snapshot(),
        ["Recommend medication for Casey."],
        repeats=2,
        document_count=2,
        planner=planner,
    )
    assert report.model_calls == 1
    assert report.planning_input_tokens == 140
    assert report.planning_output_tokens == 35
    assert report.planning_seconds == pytest.approx(0.4)
    assert not report.planning_usage_incomplete
    assert report.queries[0].answer_status == "planning_error"
    assert len(planner.questions) == 1


def test_benchmark_reports_unknown_usage_after_planning_api_failure() -> None:
    planner = FakePlanner(
        [
            QueryPlanningError(
                "Query planning API request failed.", model_calls=1, elapsed_seconds=0.2
            )
        ]
    )
    report = benchmark(
        snapshot(),
        ["Count Casey's therapy sessions."],
        repeats=2,
        document_count=2,
        planner=planner,
    )
    assert report.model_calls == 1
    assert report.planning_usage_incomplete
    assert report.planning_input_tokens == 0
    assert report.planning_output_tokens == 0
    assert report.planning_seconds == pytest.approx(0.2)
    assert report.queries[0].answer_status == "planning_error"


def test_benchmark_distinguishes_source_failure_from_analysis_budget_exhaustion() -> None:
    incomplete_source = snapshot().model_copy(update={"failed_documents": ["unprocessed.txt"]})
    source_report = benchmark(
        incomplete_source,
        ["Count Casey's therapy sessions."],
        repeats=1,
        document_count=3,
        plans=[saved_plan("Count Casey's therapy sessions.", "counts")],
    )
    assert source_report.queries[0].answer_status == "incomplete_source_processing"
    limited = snapshot()
    alternative = (
        limited.patients[0].encounters[0].alternatives[0].model_copy(update={"minutes": 50})
    )
    limited.patients[0].encounters[0].alternatives.append(alternative)
    budget_report = benchmark(
        limited,
        ["How many therapy minutes did Casey receive?"],
        repeats=1,
        document_count=2,
        scenario_budget=1,
        plans=[saved_plan("How many therapy minutes did Casey receive?", "durations")],
    )
    assert budget_report.queries[0].answer_status == "analysis_incomplete"
    assert "scenario_budget_exceeded" in (budget_report.queries[0].reason or "")


def test_replay_is_reproducible_after_snapshot_round_trip() -> None:
    original = snapshot()
    restored = ClinicalSnapshot.model_validate_json(original.model_dump_json())
    questions = ["Count Casey's therapy sessions.", "Did Casey meet the weekly therapy goal?"]
    plans = [saved_plan(questions[0], "counts"), saved_plan(questions[1], "weekly")]
    restored_plans = [QueryPlan.model_validate_json(plan.model_dump_json()) for plan in plans]
    before = replay_questions(original, questions, plans=plans)
    after = replay_questions(restored, questions, plans=restored_plans)
    assert [answer.model_dump_json() for answer in before] == [
        answer.model_dump_json() for answer in after
    ]
    assert before[0].metrics[0].session_count.exact == 1
    assert before[1].metrics[0].weeks[0].decision == "met"


def test_export_preserves_question_ids_snapshot_and_precise_evidence(tmp_path: Path) -> None:
    output = tmp_path / "submission"
    questions = [
        ReviewQuestion(id="COUNT", question="Count Casey's therapy sessions."),
        ReviewQuestion(id="MINUTES", question="How many therapy minutes did Casey receive?"),
    ]
    plans = [
        saved_plan(questions[0].question, "counts"),
        saved_plan(questions[1].question, "durations"),
    ]
    exported = export_submission(snapshot(), questions, output, plans=plans)
    saved_snapshot = ClinicalSnapshot.model_validate_json(exported.abstraction_path.read_bytes())
    answers = TypeAdapter(list[SubmissionAnswer]).validate_json(
        exported.answers_json_path.read_bytes()
    )
    saved_plans = TypeAdapter(list[QueryPlan]).validate_json(exported.plans_path.read_bytes())
    assert saved_snapshot.snapshot_id == 12
    assert [entry.id for entry in answers] == ["COUNT", "MINUTES"]
    assert answers[1].answer.metrics[0].minutes.exact == 40
    assert all(entry.answer.snapshot_id == saved_snapshot.snapshot_id for entry in answers)
    assert exported.answer_count == 2
    assert [plan.model_dump() for plan in saved_plans] == [plan.model_dump() for plan in plans]
    assert exported.abstraction_bytes == len(exported.abstraction_path.read_bytes())
    markdown = exported.answers_markdown_path.read_text("utf-8")
    assert "# COUNT" in markdown and "# MINUTES" in markdown
    assert "session.txt, lines 3-3" in markdown
    assert "Actual patient psychotherapy contact: 09:00-09:40." in markdown


def test_failed_replay_does_not_write_partial_submission(tmp_path: Path) -> None:
    output = tmp_path / "submission"
    with pytest.raises(ValueError, match="Unsupported"):
        export_submission(
            snapshot(),
            [
                ReviewQuestion(id="VALID", question="Count Casey's therapy sessions."),
                ReviewQuestion(id="INVALID", question="Recommend medication for Casey."),
            ],
            output,
            planner=FakePlanner([count_intent(), unsupported_intent()]),
        )
    assert not output.exists()


def test_invalid_benchmark_configuration_and_duplicate_export_ids_are_rejected(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="repeats"):
        benchmark(
            snapshot(),
            ["Count Casey's sessions."],
            repeats=0,
            document_count=2,
            plans=[saved_plan("Count Casey's sessions.", "counts")],
        )
    with pytest.raises(ValueError, match="at least one"):
        benchmark(snapshot(), [], document_count=2)
    with pytest.raises(ValueError, match="negative"):
        benchmark(
            snapshot(),
            ["Count Casey's sessions."],
            document_count=-1,
            plans=[saved_plan("Count Casey's sessions.", "counts")],
        )
    with pytest.raises(ValueError, match="Scenario budget"):
        replay_questions(
            snapshot(),
            ["Count Casey's sessions."],
            scenario_budget=0,
            plans=[saved_plan("Count Casey's sessions.", "counts")],
        )
    with pytest.raises(ValueError, match="unique"):
        export_submission(
            snapshot(),
            [
                ReviewQuestion(id="SAME", question="Count Casey's sessions."),
                ReviewQuestion(id="SAME", question="How many therapy minutes did Casey receive?"),
            ],
            tmp_path / "submission",
            plans=[],
        )
