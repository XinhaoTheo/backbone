from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from pydantic import TypeAdapter

from backbone.benchmarking import ReviewQuestion
from backbone.models import ClinicalSnapshot
from backbone.performance import FullQueryReport
from backbone.query import answer_question
from scripts.validate_demo import CASEY, MORGAN, DemoValidation, validate_demo

DEMO = Path(__file__).resolve().parents[1] / "demo"


@pytest.fixture
def report() -> FullQueryReport:
    return FullQueryReport.model_validate_json(
        (DEMO / "artifacts" / "full-query-benchmark.json").read_bytes()
    )


def validation(report: FullQueryReport) -> DemoValidation:
    questions = TypeAdapter(list[ReviewQuestion]).validate_json(
        (DEMO / "questions.json").read_bytes()
    )
    return validate_demo(report, questions, DEMO / "documents")


def failed_checks(report: FullQueryReport) -> set[str]:
    result = validation(report)
    return {item.name for item in result.checks if not item.passed} | {
        item.name for run in result.results for item in run.checks if not item.passed
    }


def test_demo_validator_checks_every_real_fresh_repeat_and_nested_sources(
    report: FullQueryReport,
) -> None:
    result = validation(report)
    assert result.passed
    assert result.question_count == 3
    assert result.run_count == 3 * report.repeats
    assert result.repeats == report.repeats
    assert {(run.id, run.repeat) for run in result.results} == {
        (identifier, repeat)
        for identifier in ("SYN-01", "SYN-02", "SYN-03")
        for repeat in range(1, report.repeats + 1)
    }
    assert all(run.model_calls > 0 and run.planner_model for run in result.results)
    assert all(
        any(item.name == "answer.source_locations_verbatim" for item in run.checks)
        for run in result.results
    )


def test_demo_validator_accepts_equivalent_compound_counts_and_duration_tasks(
    report: FullQueryReport,
) -> None:
    run = report.queries[0].runs[0]
    assert run.plan is not None
    first = run.plan.tasks[0]
    first.operation = "counts"
    first.metrics = ["sessions", "distinct_days"]
    additional = first.model_copy(deep=True)
    additional.operation = "durations"
    additional.metrics = ["minutes"]
    run.plan.tasks.append(additional)
    snapshot = ClinicalSnapshot.model_validate_json(
        (DEMO / "artifacts" / "abstraction.json").read_bytes()
    )
    run.answer = answer_question(run.plan.question, snapshot, plan=run.plan)
    assert validation(report).passed


def test_demo_validator_rejects_wrong_patient_dates_and_requested_week_count(
    report: FullQueryReport,
) -> None:
    personal = report.queries[0].runs[0]
    cohort = report.queries[1].runs[0]
    comparison = report.queries[2].runs[0]
    assert personal.plan is not None and cohort.plan is not None and comparison.plan is not None
    personal.plan.tasks[0].patient = MORGAN
    personal.plan.tasks[0].start = date(2027, 3, 8)
    cohort.plan.tasks[0].patient_ids.remove(CASEY)
    cohort.plan.tasks[0].consecutive_weeks = 3
    comparison.plan.tasks[0].change_date = date(2027, 3, 16)
    failures = failed_checks(report)
    assert {
        "plan.task_1.patient",
        "plan.task_1.start",
        "plan.selected_patients",
        "plan.task_1.consecutive_weeks",
        "plan.task_1.change_date",
        "answer.executed_fresh_plan",
    } <= failures


def test_demo_validator_rejects_wrong_membership_and_inconsistent_witness(
    report: FullQueryReport,
) -> None:
    run = report.queries[1].runs[0]
    assert run.answer is not None
    morgan = next(result for result in run.answer.cohort_results if result.patient_id == MORGAN)
    morgan.membership = "confirmed"
    morgan.witness[0].minutes = 170
    morgan.witness[0].encounter_ids = ["SYN-MORGAN-E2"]
    failures = failed_checks(report)
    assert {
        f"answer.cohort.{MORGAN}.membership",
        f"answer.cohort.{MORGAN}.witness_minutes",
        f"answer.cohort.{MORGAN}.witness_encounters",
    } <= failures


def test_demo_validator_rejects_wrong_totals_and_plan_goal_decisions(
    report: FullQueryReport,
) -> None:
    personal = report.queries[0].runs[0]
    comparison = report.queries[2].runs[0]
    assert personal.answer is not None and comparison.answer is not None
    personal.answer.metrics[0].minutes.exact = 251
    plan_comparison = comparison.answer.plan_comparison
    assert plan_comparison is not None and plan_comparison.after is not None
    plan_comparison.after.weeks[0].decision = "met"
    goal = plan_comparison.after.weeks[0].goal
    assert goal is not None
    goal.minimum_days = 1
    failures = failed_checks(report)
    assert {
        "answer.metrics_1.minutes.exact",
        "answer.after.weekly_decisions",
        "answer.after.weekly_goals",
        "answer.comparison_metrics_match",
    } <= failures


def test_demo_validator_checks_nested_results_beyond_the_source_catalog(
    report: FullQueryReport,
) -> None:
    run = report.queries[2].runs[0]
    assert run.answer is not None and run.answer.plan_comparison is not None
    after = run.answer.plan_comparison.after
    assert after is not None and after.weeks[0].goal is not None
    after.weeks[0].goal.sources[0].quote = "This passage is absent from the synthetic source."
    assert "answer.source_locations_verbatim" in failed_checks(report)


def test_demo_validator_rejects_line_ranges_that_are_broader_than_the_actual_quote(
    report: FullQueryReport,
) -> None:
    run = report.queries[2].runs[0]
    assert run.answer is not None and run.answer.plan_comparison is not None
    after = run.answer.plan_comparison.after
    assert after is not None and after.weeks[0].goal is not None
    source = after.weeks[0].goal.sources[0]
    source.start_line -= 1
    failures = failed_checks(report)
    assert "answer.source_locations_verbatim" not in failures
    assert "answer.source_locations_exact" in failures


def test_demo_validator_rejects_missing_repeat_unknown_question_and_replay_metadata(
    report: FullQueryReport,
) -> None:
    report.queries[0].runs.pop()
    report.queries[1].runs[0].model_calls = 0
    unknown = report.queries[2].model_copy(deep=True)
    unknown.id = "UNKNOWN"
    report.queries.append(unknown)
    failures = failed_checks(report)
    assert {
        "SYN-01.repeat_numbers",
        "report.question_ids",
        "report.fresh_query_runs",
        "report.model_calls",
        "run.known_question",
        "planner.called_for_fresh_question",
    } <= failures


def test_demo_validator_rejects_missing_fresh_plan_or_answer(report: FullQueryReport) -> None:
    run = report.queries[0].runs[0]
    run.plan = None
    run.answer = None
    run.reason = "Planning failed."
    assert {"planner.plan_available", "execution.answer_available"} <= failed_checks(report)
