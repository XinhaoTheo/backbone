from __future__ import annotations

import argparse
from datetime import date, timedelta
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, TypeAdapter

from backbone.benchmarking import ReviewQuestion
from backbone.calculation import IntegerResult, PatientMetrics
from backbone.extraction import locate_quote
from backbone.ingestion import read_document
from backbone.models import DocumentRecord, SourceRef
from backbone.performance import FreshQueryRun, FullQueryReport
from backbone.query import AnswerData, unique_sources
from scripts.validate_submission import QuestionValidation, ValidationCheck, check, source_checks

START = date(2027, 3, 1)
FIRST_END = date(2027, 3, 14)
CHANGE = date(2027, 3, 15)
END = date(2027, 3, 28)
CASEY = "synthetic review clinic::SYN-CASEY"
MORGAN = "synthetic review clinic::SYN-MORGAN"
ALEX = "synthetic review clinic::SYN-ALEX"
PATIENTS = {CASEY, MORGAN, ALEX}
OPERATIONS: dict[str, set[str]] = {
    "SYN-01": {"counts", "durations"},
    "SYN-02": {"cohort"},
    "SYN-03": {"plan_change"},
}


class DemoValidation(BaseModel):
    scope: Literal["synthetic_live_planning_and_execution"] = (
        "synthetic_live_planning_and_execution"
    )
    gold_reference: str = "demo/create_fixtures.py and tests/test_demo.py"
    passed: bool
    question_count: int
    run_count: int
    repeats: int
    checks: list[ValidationCheck]
    results: list[QuestionValidation]


class Options(argparse.Namespace):
    input: str
    questions: str
    sources: str
    output: str


def exact_integer_checks(
    prefix: str, result: IntegerResult, expected: int
) -> list[ValidationCheck]:
    return [
        check(f"{prefix}.exact", str(expected), str(result.exact)),
        check(f"{prefix}.values", str([expected]), str(result.values)),
        check(f"{prefix}.lower_bound", str(expected), str(result.lower_bound)),
        check(f"{prefix}.upper_bound", str(expected), str(result.upper_bound)),
        check(f"{prefix}.status", "established", result.status),
    ]


def metric_checks(
    prefix: str,
    metrics: PatientMetrics,
    patient_id: str,
    start: date,
    end: date,
    totals: tuple[int, int, int],
    weekly_minutes: list[int],
    weekly_days: list[int],
    decisions: list[str],
    goal: tuple[int, int],
) -> list[ValidationCheck]:
    checks = [
        check(f"{prefix}.patient_id", patient_id, metrics.patient_id),
        check(f"{prefix}.start", str(start), str(metrics.start)),
        check(f"{prefix}.end", str(end), str(metrics.end)),
        check(f"{prefix}.analysis_status", "complete", metrics.analysis_status),
        check(
            f"{prefix}.week_starts",
            str([start, start + timedelta(days=7)]),
            str([week.week_start for week in metrics.weeks]),
        ),
        check(
            f"{prefix}.weekly_minutes",
            str(weekly_minutes),
            str([week.minutes.exact for week in metrics.weeks]),
        ),
        check(
            f"{prefix}.weekly_days",
            str(weekly_days),
            str([week.distinct_days.exact for week in metrics.weeks]),
        ),
        check(
            f"{prefix}.weekly_decisions",
            str(decisions),
            str([week.decision for week in metrics.weeks]),
        ),
        check(
            f"{prefix}.weekly_goals",
            str([goal, goal]),
            str(
                [
                    (week.goal.minimum_days, week.goal.minimum_minutes)
                    if week.goal is not None
                    else None
                    for week in metrics.weeks
                ]
            ),
        ),
    ]
    for name, result, expected in [
        ("sessions", metrics.session_count, totals[0]),
        ("distinct_days", metrics.distinct_days, totals[1]),
        ("minutes", metrics.minutes, totals[2]),
    ]:
        checks.extend(exact_integer_checks(f"{prefix}.{name}", result, expected))
    return checks


def plan_checks(
    identifier: str, question: ReviewQuestion, run: FreshQueryRun
) -> list[ValidationCheck]:
    checks = [
        check("planner.called_for_fresh_question", "True", str(run.model_calls > 0)),
        check("planner.plan_available", "True", str(run.plan is not None)),
        check("execution.answer_available", "True", str(run.answer is not None)),
        check("execution.patient_count", "3", str(run.patient_count)),
    ]
    plan = run.plan
    if plan is None:
        return checks
    checks.extend(
        [
            check("plan.original_question", question.question, plan.question),
            check("plan.snapshot_id", str(run.snapshot_id), str(plan.snapshot_id)),
            check("planner.model_recorded", "True", str(bool(plan.planner_model))),
            check("planner.model_matches_run", str(run.planner_model), str(plan.planner_model)),
            check("planner.calls_recorded", str(run.model_calls), str(plan.planner_model_calls)),
            check("planner.usage_available", "True", str(run.planner_usage is not None)),
            check("planner.usage_recorded", str(run.planner_usage), str(plan.planner_usage)),
            check(
                "plan.supported_tasks",
                "True",
                str({task.operation for task in plan.tasks} <= OPERATIONS[identifier]),
            ),
        ]
    )
    if identifier in {"SYN-01", "SYN-03"}:
        metrics = {metric for task in plan.tasks for metric in task.metrics}
        checks.append(
            check(
                "plan.requested_metrics",
                "True",
                str({"sessions", "distinct_days", "minutes"} <= metrics),
            )
        )
    selected = {patient_id for task in plan.tasks for patient_id in task.patient_ids}
    expected_patients = (
        PATIENTS if identifier == "SYN-02" else {CASEY if identifier == "SYN-01" else ALEX}
    )
    checks.append(
        check("plan.selected_patients", str(sorted(expected_patients)), str(sorted(selected)))
    )
    for index, task in enumerate(plan.tasks, start=1):
        prefix = f"plan.task_{index}"
        checks.extend(
            [
                check(f"{prefix}.start", str(START), str(task.start)),
                check(
                    f"{prefix}.end",
                    str(FIRST_END if identifier == "SYN-01" else END),
                    str(task.end),
                ),
                check(f"{prefix}.selected_dates", "[]", str(task.selected_dates)),
                check(
                    f"{prefix}.change_date",
                    str(CHANGE if identifier == "SYN-03" else None),
                    str(task.change_date),
                ),
            ]
        )
        if identifier == "SYN-02":
            checks.extend(
                [
                    check(f"{prefix}.consecutive_weeks", "2", str(task.consecutive_weeks)),
                    check(
                        f"{prefix}.cohort_patient_member",
                        "True",
                        str(task.patient is None or task.patient in task.patient_ids),
                    ),
                ]
            )
        else:
            patient_id = CASEY if identifier == "SYN-01" else ALEX
            checks.extend(
                [
                    check(f"{prefix}.patient", patient_id, str(task.patient)),
                    check(f"{prefix}.patient_ids", str([patient_id]), str(task.patient_ids)),
                ]
            )
    if run.answer is not None:
        answer = run.answer
        checks.extend(
            [
                check("answer.original_question", question.question, answer.question),
                check("answer.snapshot_id", str(plan.snapshot_id), str(answer.snapshot_id)),
                check(
                    "answer.executed_fresh_plan",
                    plan.model_dump_json(),
                    answer.plan.model_dump_json(),
                ),
                check("answer.coverage", "available_records", answer.coverage_status),
                check("answer.text_available", "True", str(bool(answer.text))),
                check("answer.sources_available", "True", str(bool(answer.sources))),
                check("answer.task_count", str(len(plan.tasks)), str(len(answer.task_answers))),
            ]
        )
        for index, (task, task_answer) in enumerate(zip(plan.tasks, answer.task_answers), start=1):
            checks.append(
                check(
                    f"answer.task_{index}.executed_task",
                    task.model_dump_json(),
                    task_answer.task.model_dump_json(),
                )
            )
    return checks


def cohort_checks(answer: AnswerData, patient_ids: set[str]) -> list[ValidationCheck]:
    expected_membership = {CASEY: "confirmed", MORGAN: "possible", ALEX: "excluded"}
    checks = [
        check(
            "answer.cohort.patient_ids",
            str(sorted(patient_ids)),
            str(sorted(entry.patient_id for entry in answer.cohort_results)),
        ),
    ]
    for result in answer.cohort_results:
        prefix = f"answer.cohort.{result.patient_id}"
        checks.append(
            check(
                f"{prefix}.membership",
                expected_membership.get(result.patient_id, "unknown"),
                result.membership,
            )
        )
        if result.patient_id == ALEX:
            checks.append(check(f"{prefix}.witness", "[]", str(result.witness)))
        elif result.patient_id in {CASEY, MORGAN}:
            minutes = [120, 130] if result.patient_id == CASEY else [130, 130]
            encounter_ids = [
                [f"SYN-{'CASEY' if result.patient_id == CASEY else 'MORGAN'}-E{number}"]
                for number in (1, 2)
            ]
            checks.extend(
                [
                    check(
                        f"{prefix}.witness_weeks",
                        str([START, date(2027, 3, 8)]),
                        str([week.week_start for week in result.witness]),
                    ),
                    check(
                        f"{prefix}.witness_minutes",
                        str(minutes),
                        str([week.minutes for week in result.witness]),
                    ),
                    check(
                        f"{prefix}.witness_days",
                        "[1, 1]",
                        str([week.distinct_days for week in result.witness]),
                    ),
                    check(
                        f"{prefix}.witness_decisions",
                        "['not_met', 'not_met']",
                        str([week.decision for week in result.witness]),
                    ),
                    check(
                        f"{prefix}.witness_encounters",
                        str(encounter_ids),
                        str([week.encounter_ids for week in result.witness]),
                    ),
                ]
            )
            if result.patient_id == MORGAN:
                checks.append(
                    check(f"{prefix}.consistent_choices", "True", str(bool(result.choices)))
                )
    return checks


def answer_checks(
    identifier: str, answer: AnswerData, *, patient_ids: set[str] | None = None
) -> list[ValidationCheck]:
    if identifier == "SYN-02":
        return cohort_checks(answer, PATIENTS if patient_ids is None else patient_ids)
    if identifier == "SYN-01":
        checks = [check("answer.metrics_available", "True", str(bool(answer.metrics)))]
        for index, metrics in enumerate(answer.metrics, start=1):
            checks.extend(
                metric_checks(
                    f"answer.metrics_{index}",
                    metrics,
                    CASEY,
                    START,
                    FIRST_END,
                    (2, 2, 250),
                    [120, 130],
                    [1, 1],
                    ["not_met", "not_met"],
                    (1, 150),
                )
            )
        return checks
    comparison = answer.plan_comparison
    checks = [check("answer.plan_comparison_available", "True", str(comparison is not None))]
    if comparison is None:
        return checks
    checks.extend(
        [
            check("answer.plan_comparison.patient_id", ALEX, comparison.patient_id),
            check("answer.plan_comparison.change_date", str(CHANGE), str(comparison.change_date)),
            check(
                "answer.plan_comparison.before_available",
                "True",
                str(comparison.before is not None),
            ),
            check(
                "answer.plan_comparison.after_available", "True", str(comparison.after is not None)
            ),
        ]
    )
    if comparison.before is not None:
        checks.extend(
            metric_checks(
                "answer.before",
                comparison.before,
                ALEX,
                START,
                FIRST_END,
                (2, 2, 210),
                [100, 110],
                [1, 1],
                ["met", "met"],
                (1, 100),
            )
        )
    if comparison.after is not None:
        checks.extend(
            metric_checks(
                "answer.after",
                comparison.after,
                ALEX,
                CHANGE,
                END,
                (3, 3, 280),
                [120, 160],
                [1, 2],
                ["not_met", "met"],
                (2, 150),
            )
        )
    expected_metrics = [
        entry for entry in [comparison.before, comparison.after] if entry is not None
    ]
    checks.append(
        check(
            "answer.comparison_metrics_match",
            str([entry.model_dump_json() for entry in expected_metrics]),
            str([entry.model_dump_json() for entry in answer.metrics]),
        )
    )
    return checks


def metric_sources(metrics: PatientMetrics) -> list[SourceRef]:
    sources = list(metrics.constraint_sources)
    for contribution in [*metrics.contributions, *metrics.exclusions]:
        sources.extend(contribution.sources)
        for interpretation in contribution.interpretations:
            sources.extend(interpretation.sources)
    for week in metrics.weeks:
        sources.extend(week.sources)
        if week.goal is not None:
            sources.extend(week.goal.sources)
    return sources


def answer_sources(answer: AnswerData) -> list[SourceRef]:
    sources = list(answer.sources)
    metrics = list(answer.metrics)
    if answer.plan_comparison is not None:
        metrics.extend(
            entry
            for entry in [answer.plan_comparison.before, answer.plan_comparison.after]
            if entry is not None
        )
    for entry in metrics:
        sources.extend(metric_sources(entry))
    for result in answer.cohort_results:
        sources.extend(result.sources)
    for claim in [*answer.assessments, *answer.observations]:
        sources.extend(claim.sources)
    for need in answer.evidence_needs:
        sources.extend(need.sources)
    return sources


def exact_source_checks(
    references: list[SourceRef], documents: dict[str, DocumentRecord]
) -> list[ValidationCheck]:
    invalid: list[str] = []
    for source in references:
        document = documents.get(source.filename)
        if (
            document is None
            or not source.quote.strip()
            or source.quote not in document.text
            or source not in locate_quote(document, source.quote)
        ):
            invalid.append(f"{source.document_id}:{source.start_line}-{source.end_line}")
    return [check("answer.source_locations_exact", "[]", str(invalid))]


def validate_demo(
    report: FullQueryReport, questions: list[ReviewQuestion], source_directory: Path
) -> DemoValidation:
    expected = {question.id: question for question in questions}
    observed = [question.id for question in report.queries]
    runs = [run for question in report.queries for run in question.runs]
    checks = [
        check("questions.reference_ids", str(sorted(OPERATIONS)), str(sorted(expected))),
        check("questions.unique_ids", str(len(questions)), str(len(expected))),
        check("report.question_ids", str(sorted(expected)), str(sorted(observed))),
        check("report.question_count", str(len(expected)), str(report.question_count)),
        check("report.fresh_query_runs", str(len(runs)), str(report.fresh_query_runs)),
        check(
            "report.model_calls", str(sum(run.model_calls for run in runs)), str(report.model_calls)
        ),
        check("report.positive_repeats", "True", str(report.repeats > 0)),
    ]
    documents = {path.name: read_document(path) for path in source_directory.glob("*.txt")}
    results: list[QuestionValidation] = []
    for measurement in report.queries:
        question = expected.get(measurement.id)
        checks.append(
            check(
                f"{measurement.id}.repeat_numbers",
                str(list(range(1, report.repeats + 1))),
                str(sorted(run.repeat for run in measurement.runs)),
            )
        )
        for run in measurement.runs:
            run_checks = [
                check(
                    "run.known_question",
                    "True",
                    str(question is not None and measurement.id in OPERATIONS),
                )
            ]
            if question is not None and measurement.id in OPERATIONS:
                run_checks.append(
                    check("question.original_text", question.question, measurement.question)
                )
                run_checks.extend(plan_checks(measurement.id, question, run))
                if run.answer is not None:
                    run_checks.extend(answer_checks(measurement.id, run.answer))
                    for index, task_answer in enumerate(run.answer.task_answers, start=1):
                        task_checks = answer_checks(
                            measurement.id,
                            task_answer,
                            patient_ids=set(task_answer.task.patient_ids),
                        )
                        for task_check in task_checks:
                            task_check.name = f"task_{index}.{task_check.name}"
                        run_checks.extend(task_checks)
                    sourced = run.answer.model_copy()
                    references = answer_sources(run.answer)
                    for task_answer in run.answer.task_answers:
                        references.extend(answer_sources(task_answer))
                    sourced.sources = unique_sources(references)
                    run_checks.extend(source_checks(sourced, documents))
                    run_checks.extend(exact_source_checks(sourced.sources, documents))
            results.append(
                QuestionValidation(
                    id=measurement.id,
                    repeat=run.repeat,
                    passed=all(item.passed for item in run_checks),
                    planner_model=run.plan.planner_model if run.plan is not None else None,
                    model_calls=run.model_calls,
                    usage=run.planner_usage,
                    timings=run.fresh,
                    checks=run_checks,
                )
            )
    return DemoValidation(
        passed=all(item.passed for item in checks) and all(result.passed for result in results),
        question_count=len(expected),
        run_count=len(runs),
        repeats=report.repeats,
        checks=checks,
        results=results,
    )


def main() -> None:
    parser = argparse.ArgumentParser(prog="validate-demo")
    parser.add_argument("input")
    parser.add_argument("--questions", default="demo/questions.json")
    parser.add_argument("--sources", default="demo/documents")
    parser.add_argument("--output", default="demo/artifacts/planner-validation.json")
    options = parser.parse_args(namespace=Options())
    report = validate_demo(
        FullQueryReport.model_validate_json(Path(options.input).read_bytes()),
        TypeAdapter(list[ReviewQuestion]).validate_json(Path(options.questions).read_bytes()),
        Path(options.sources),
    )
    output = Path(options.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")
    failed = [item.name for item in report.checks if not item.passed]
    failed.extend(
        f"{result.id} repeat {result.repeat}: {item.name}"
        for result in report.results
        for item in result.checks
        if not item.passed
    )
    if failed:
        parser.exit(1, "Validation failed:\n" + "\n".join(failed) + "\n")
    print(
        f"Validated {report.run_count} fresh synthetic runs "
        f"covering {report.question_count} questions."
    )


if __name__ == "__main__":
    main()
