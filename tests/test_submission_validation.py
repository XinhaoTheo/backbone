from __future__ import annotations

from datetime import date
from pathlib import Path

from pydantic import TypeAdapter

from backbone.benchmarking import ReviewQuestion, SubmissionAnswer
from backbone.models import ClinicalSnapshot, ModelUsage, QueryOperation, QueryPlan, QueryTask
from backbone.performance import (
    FreshQueryRun,
    FullQueryReport,
    QueryPerformance,
    QueryTimings,
    summarize_timings,
)
from backbone.query import answer_question
from scripts.validate_submission import (
    PATIENT_ID,
    REVIEW_END,
    REVIEW_START,
    SELECTED_DATES,
    LegacyLiveRun,
    ValidationRun,
    live_records,
    validate_submission,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def questions() -> list[ReviewQuestion]:
    return TypeAdapter(list[ReviewQuestion]).validate_json(
        (PROJECT_ROOT / "questions.json").read_bytes()
    )


def fixture_runs() -> list[ValidationRun]:
    snapshot = ClinicalSnapshot.model_validate_json(
        (PROJECT_ROOT / "artifacts" / "abstraction.json").read_bytes()
    )
    operations: dict[str, QueryOperation] = {
        "DEV-01": "counts",
        "DEV-02": "durations",
        "DEV-03": "weekly",
        "DEV-04": "day",
        "DEV-05": "symptoms",
    }
    runs: list[ValidationRun] = []
    for question in questions():
        dates = SELECTED_DATES if question.id == "DEV-04" else []
        usage = ModelUsage(input_tokens=100, output_tokens=25, cost_usd=0.002)
        plan = QueryPlan(
            question=question.question,
            snapshot_id=snapshot.snapshot_id,
            tasks=[
                QueryTask(
                    operation=operations[question.id],
                    patient=PATIENT_ID,
                    patient_ids=[PATIENT_ID],
                    start=min(dates) if dates else REVIEW_START,
                    end=max(dates) if dates else REVIEW_END,
                    selected_dates=dates,
                )
            ],
            planner_model="checker-test-fixture",
            planner_usage=usage,
            planner_elapsed_seconds=0.2,
            planner_model_calls=1,
        )
        runs.append(
            ValidationRun(
                id=question.id,
                question=question.question,
                repeat=1,
                timings=QueryTimings(
                    database_load_seconds=0.1,
                    planning_seconds=0.2,
                    execution_render_seconds=0.05,
                    end_to_end_seconds=0.35,
                ),
                plan=plan,
                answer=answer_question(question.question, snapshot, plan=plan),
                error=None,
                usage=usage,
                model_calls=1,
            )
        )
    return runs


def failed_check_names(runs: list[ValidationRun]) -> set[str]:
    report = validate_submission(runs, questions(), PROJECT_ROOT / "documents")
    return {item.name for result in report.results for item in result.checks if not item.passed} | {
        item.name for item in report.checks if not item.passed
    }


def test_reference_checker_accepts_gold_results_and_checks_source_grounding() -> None:
    report = validate_submission(fixture_runs(), questions(), PROJECT_ROOT / "documents")
    assert report.passed and report.run_count == report.observed_question_count == 5
    assert report.input_run_count == 5 and not report.excluded_question_ids
    for result in report.results:
        assert result.passed
        assert result.planner_model == "checker-test-fixture"
        assert any(item.name == "answer.source_locations_verbatim" for item in result.checks)


def test_checker_rejects_wrong_planner_scope_even_if_answer_numbers_are_correct() -> None:
    runs = fixture_runs()
    counts, _, _, dates, symptoms = runs
    assert counts.plan is not None and dates.plan is not None and symptoms.plan is not None
    counts.plan = counts.plan.model_copy(deep=True)
    counts.plan.tasks[0].patient_ids = ["UNKNOWN"]
    dates.plan = dates.plan.model_copy(deep=True)
    dates.plan.tasks[0].selected_dates = [date(2026, 1, 19)]
    symptoms.plan = symptoms.plan.model_copy(deep=True)
    symptoms.plan.tasks[0].start = date(2026, 1, 19)
    failures = failed_check_names(runs)
    assert "plan.task_1.patient_ids" in failures
    assert "plan.requested_dates" in failures
    assert "plan.task_1.start" in failures
    assert "answer.executed_fresh_plan" in failures


def test_checker_rejects_lost_duration_alternative_wrong_day_and_symptom_dates() -> None:
    runs = fixture_runs()
    _, durations, _, days, symptoms = runs
    assert durations.answer is not None and days.answer is not None and symptoms.answer is not None
    durations.answer.metrics[0].minutes.values = [595]
    days.answer.metrics[0].minutes.exact = 105
    symptoms.answer.assessments[-1].completed_date = date(2026, 1, 19)
    failures = failed_check_names(runs)
    assert "answer.metrics_1.minutes.values" in failures
    assert "answer.metrics_1.minutes" in failures
    assert "answer.assessment_dates" in failures


def test_checker_rejects_replay_metadata_missing_questions_and_invalid_source_quotes() -> None:
    runs = fixture_runs()
    counts = runs[0]
    counts.model_calls = 0
    assert counts.answer is not None
    counts.answer.sources[0].quote = "A quotation absent from the supplied document."
    failures = failed_check_names(runs[:-1])
    assert "planner.called_for_fresh_question" in failures
    assert "runs.cover_all_questions" in failures
    assert "answer.source_locations_verbatim" in failures


def test_loader_reads_legacy_live_shape_without_replacing_plan_or_answer(tmp_path: Path) -> None:
    runs = fixture_runs()
    legacy = [
        LegacyLiveRun(
            id=run.id,
            question=run.question,
            database_seconds=run.timings.database_load_seconds,
            planning_seconds=run.timings.planning_seconds,
            execution_seconds=run.timings.execution_render_seconds,
            end_to_end_seconds=run.timings.end_to_end_seconds,
            plan=run.plan,
            answer=SubmissionAnswer(id=run.id, answer=run.answer)
            if run.answer is not None
            else None,
            error=run.error,
            usage=run.usage,
            model_calls=run.model_calls,
        )
        for run in runs
    ]
    path = tmp_path / "live.json"
    path.write_bytes(TypeAdapter(list[LegacyLiveRun]).dump_json(legacy))
    restored = live_records(path)
    assert restored == runs


def test_full_report_loader_checks_every_fresh_repeat_and_reports_excluded_queries(
    tmp_path: Path,
) -> None:
    runs = fixture_runs()
    measurements: list[QueryPerformance] = []
    for run in runs:
        assert run.plan is not None
        repeats = [
            FreshQueryRun(
                repeat=repeat,
                snapshot_id=run.plan.snapshot_id,
                patient_count=1,
                scope="individual",
                operations=[task.operation for task in run.plan.tasks],
                answer_status="established",
                reason=None,
                fresh=run.timings,
                model_calls=run.model_calls,
                planner_model=run.plan.planner_model,
                planner_usage=run.usage,
                planning_usage_incomplete=False,
                plan=run.plan,
                answer=run.answer,
                replay=None,
            )
            for repeat in (1, 2)
        ]
        measurements.append(
            QueryPerformance(
                id=run.id,
                question=run.question,
                scopes=["individual"],
                runs=repeats,
                fresh_summary=summarize_timings([run.timings, run.timings]),
                replay_summary=None,
                stable_answers_across_repeats=True,
            )
        )
    report = FullQueryReport(
        repeats=2,
        scenario_budget=10000,
        question_count=5,
        fresh_query_runs=10,
        replay_runs=0,
        snapshot_ids=[runs[0].plan.snapshot_id] if runs[0].plan is not None else [],
        model_calls=10,
        planning_usage=ModelUsage(input_tokens=1000, output_tokens=250, cost_usd=0.02),
        planning_usage_incomplete=False,
        elapsed_seconds=3.5,
        queries=measurements,
    )
    path = tmp_path / "benchmark.json"
    path.write_text(report.model_dump_json(), encoding="utf-8")
    restored = live_records(path)
    assert len(restored) == 10
    restored[-1].answer = None
    restored[-1].error = "A failed fresh run must be checked."
    extra = runs[0].model_copy(deep=True)
    extra.id = "COHORT-01"
    result = validate_submission(restored + [extra], questions(), PROJECT_ROOT / "documents")
    assert not result.passed
    assert result.run_count == 10 and result.input_run_count == 11
    assert result.excluded_question_ids == ["COHORT-01"] and result.excluded_run_count == 1
    assert result.results[-1].repeat == 2 and not result.results[-1].passed
