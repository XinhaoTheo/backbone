from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from pydantic import BaseModel, TypeAdapter

from backbone.benchmarking import ReviewQuestion, SubmissionAnswer
from backbone.ingestion import read_document
from backbone.models import DocumentRecord, ModelUsage, QueryPlan
from backbone.performance import FullQueryReport, QueryTimings
from backbone.query import AnswerBundle

PATIENT_ID = "harbor grove behavioral health::HG-M042"
REVIEW_START = date(2026, 1, 5)
REVIEW_END = date(2026, 1, 30)
SELECTED_DATES = [date(2026, 1, 19), date(2026, 1, 21)]
EXPECTED_OPERATIONS: dict[str, set[str]] = {
    "DEV-01": {"counts", "timeline"},
    "DEV-02": {"durations", "weekly"},
    "DEV-03": {"weekly"},
    "DEV-04": {"day", "timeline"},
    "DEV-05": {"symptoms"},
}
REQUIRED_OPERATIONS: dict[str, str] = {
    "DEV-01": "counts",
    "DEV-02": "durations",
    "DEV-03": "weekly",
    "DEV-05": "symptoms",
}


class LegacyLiveRun(BaseModel):
    id: str
    question: str
    database_seconds: float
    planning_seconds: float
    execution_seconds: float
    end_to_end_seconds: float
    plan: QueryPlan | None
    answer: SubmissionAnswer | None
    error: str | None
    usage: ModelUsage | None
    model_calls: int


class ValidationRun(BaseModel):
    id: str
    question: str
    repeat: int
    timings: QueryTimings
    plan: QueryPlan | None
    answer: AnswerBundle | None
    error: str | None
    usage: ModelUsage | None
    model_calls: int


class ValidationCheck(BaseModel):
    name: str
    passed: bool
    expected: str
    observed: str


class QuestionValidation(BaseModel):
    id: str
    repeat: int
    passed: bool
    planner_model: str | None
    model_calls: int
    usage: ModelUsage | None
    timings: QueryTimings
    checks: list[ValidationCheck]


class SubmissionValidation(BaseModel):
    scope: str = "Live planning and execution of the five supplied development questions."
    gold_reference: str = "tests/test_reference_records.py"
    passed: bool
    expected_question_count: int
    observed_question_count: int
    input_run_count: int
    run_count: int
    excluded_question_ids: list[str]
    excluded_run_count: int
    checks: list[ValidationCheck]
    results: list[QuestionValidation]


class Options(argparse.Namespace):
    input: str
    questions: str
    sources: str
    output: str


def check(name: str, expected: str, observed: str) -> ValidationCheck:
    return ValidationCheck(
        name=name, passed=expected == observed, expected=expected, observed=observed
    )


def live_records(path: Path) -> list[ValidationRun]:
    payload = path.read_text(encoding="utf-8")
    if payload.lstrip().startswith("["):
        runs = TypeAdapter(list[LegacyLiveRun]).validate_json(payload)
        return [
            ValidationRun(
                id=run.id,
                question=run.question,
                repeat=1,
                timings=QueryTimings(
                    database_load_seconds=run.database_seconds,
                    planning_seconds=run.planning_seconds,
                    execution_render_seconds=run.execution_seconds,
                    end_to_end_seconds=run.end_to_end_seconds,
                ),
                plan=run.plan,
                answer=run.answer.answer if run.answer is not None else None,
                error=run.error,
                usage=run.usage,
                model_calls=run.model_calls,
            )
            for run in runs
        ]
    report = FullQueryReport.model_validate_json(payload)
    return [
        ValidationRun(
            id=question.id,
            question=question.question,
            repeat=run.repeat,
            timings=run.fresh,
            plan=run.plan,
            answer=run.answer,
            error=run.reason if run.answer is None else None,
            usage=run.planner_usage,
            model_calls=run.model_calls,
        )
        for question in report.queries
        for run in question.runs
    ]


def plan_checks(run: ValidationRun, question: ReviewQuestion) -> list[ValidationCheck]:
    checks = [
        check("question.original_text", question.question, run.question),
        check("run.error", "None", str(run.error)),
        check("planner.called_for_fresh_question", "True", str(run.model_calls > 0)),
        check("planner.plan_available", "True", str(run.plan is not None)),
        check("execution.answer_available", "True", str(run.answer is not None)),
    ]
    plan = run.plan
    if plan is None:
        return checks
    checks.extend(
        [
            check("plan.original_question", question.question, plan.question),
            check("planner.model_recorded", "True", str(bool(plan.planner_model))),
            check("planner.calls_recorded", str(run.model_calls), str(plan.planner_model_calls)),
            check("planner.usage_recorded", str(run.usage), str(plan.planner_usage)),
        ]
    )
    operations = {task.operation for task in plan.tasks}
    allowed = EXPECTED_OPERATIONS[run.id]
    checks.append(check("plan.supported_tasks", "True", str(operations <= allowed)))
    required = REQUIRED_OPERATIONS.get(run.id)
    if required is not None:
        checks.append(
            check(
                "plan.required_task",
                required,
                required if required in operations else ",".join(sorted(operations)),
            )
        )
    for index, task in enumerate(plan.tasks, start=1):
        prefix = f"plan.task_{index}"
        checks.extend(
            [
                check(f"{prefix}.patient", PATIENT_ID, str(task.patient)),
                check(f"{prefix}.patient_ids", PATIENT_ID, ",".join(task.patient_ids)),
                check(f"{prefix}.change_date", "None", str(task.change_date)),
            ]
        )
        if run.id == "DEV-04":
            dates = task.selected_dates or ([task.start] if task.start == task.end else [])
            checks.extend(
                [
                    check(f"{prefix}.explicit_dates", "True", str(bool(dates))),
                    check(
                        f"{prefix}.dates_in_requested_set",
                        "True",
                        str(set(dates) <= set(SELECTED_DATES)),
                    ),
                    check(
                        f"{prefix}.start",
                        str(min(dates, default=SELECTED_DATES[0])),
                        str(task.start),
                    ),
                    check(
                        f"{prefix}.end", str(max(dates, default=SELECTED_DATES[-1])), str(task.end)
                    ),
                ]
            )
        else:
            checks.extend(
                [
                    check(f"{prefix}.start", str(REVIEW_START), str(task.start)),
                    check(f"{prefix}.end", str(REVIEW_END), str(task.end)),
                    check(f"{prefix}.selected_dates", "[]", str(task.selected_dates)),
                ]
            )
    if run.id == "DEV-04":
        dates = sorted(
            {
                value
                for task in plan.tasks
                for value in (
                    task.selected_dates or ([task.start] if task.start == task.end else [])
                )
            }
        )
        checks.append(check("plan.requested_dates", str(SELECTED_DATES), str(dates)))
    if run.answer is not None:
        checks.extend(
            [
                check("answer.original_question", question.question, run.answer.question),
                check("answer.snapshot_id", str(plan.snapshot_id), str(run.answer.snapshot_id)),
                check(
                    "answer.executed_fresh_plan",
                    plan.model_dump_json(),
                    run.answer.plan.model_dump_json(),
                ),
                check("answer.coverage", "available_records", run.answer.coverage_status),
                check("answer.text_available", "True", str(bool(run.answer.text))),
                check("answer.sources_available", "True", str(bool(run.answer.sources))),
            ]
        )
    return checks


def metric_checks(run: ValidationRun) -> list[ValidationCheck]:
    answer = run.answer
    if answer is None or run.id == "DEV-05":
        return []
    checks = [check("answer.metrics_available", "True", str(bool(answer.metrics)))]
    for index, metrics in enumerate(answer.metrics, start=1):
        prefix = f"answer.metrics_{index}"
        checks.append(check(f"{prefix}.patient_id", PATIENT_ID, metrics.patient_id))
        if run.id == "DEV-04":
            expected: dict[date, tuple[int, int]] = {
                SELECTED_DATES[0]: (2, 90),
                SELECTED_DATES[1]: (1, 45),
            }
            counts = expected.get(metrics.start)
            checks.append(check(f"{prefix}.requested_date", "True", str(counts is not None)))
            checks.append(check(f"{prefix}.end", str(metrics.start), str(metrics.end)))
            if counts is not None:
                checks.extend(
                    [
                        check(
                            f"{prefix}.sessions", str(counts[0]), str(metrics.session_count.exact)
                        ),
                        check(f"{prefix}.minutes", str(counts[1]), str(metrics.minutes.exact)),
                    ]
                )
            continue
        checks.extend(
            [
                check(f"{prefix}.start", str(REVIEW_START), str(metrics.start)),
                check(f"{prefix}.end", str(REVIEW_END), str(metrics.end)),
            ]
        )
        if run.id == "DEV-01":
            checks.extend(
                [
                    check(f"{prefix}.sessions", "12", str(metrics.session_count.exact)),
                    check(f"{prefix}.distinct_days", "11", str(metrics.distinct_days.exact)),
                ]
            )
            for service, count in {"individual": 5, "group": 5, "family": 2}.items():
                value = metrics.session_counts.get(service)
                checks.append(
                    check(
                        f"{prefix}.{service}_sessions",
                        str(count),
                        str(value.exact) if value is not None else "missing",
                    )
                )
        if run.id == "DEV-02":
            checks.extend(
                [
                    check(f"{prefix}.minutes.values", "[585, 595]", str(metrics.minutes.values)),
                    check(f"{prefix}.minutes.exact", "None", str(metrics.minutes.exact)),
                    check(f"{prefix}.minutes.lower_bound", "585", str(metrics.minutes.lower_bound)),
                    check(f"{prefix}.minutes.upper_bound", "595", str(metrics.minutes.upper_bound)),
                    check(
                        f"{prefix}.weekly_minutes",
                        "[[140], [120], [180], [145, 155]]",
                        str([week.minutes.values for week in metrics.weeks]),
                    ),
                ]
            )
        if run.id == "DEV-03":
            checks.extend(
                [
                    check(
                        f"{prefix}.weekly_days",
                        "[3, 2, 3, 3]",
                        str([week.distinct_days.exact for week in metrics.weeks]),
                    ),
                    check(
                        f"{prefix}.weekly_decisions",
                        "['not_met', 'not_met', 'met', 'indeterminate']",
                        str([week.decision for week in metrics.weeks]),
                    ),
                    check(
                        f"{prefix}.weekly_goals",
                        "[(3, 150), (3, 150), (3, 150), (3, 150)]",
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
            )
    if run.id == "DEV-04":
        checks.append(
            check(
                "answer.requested_dates",
                str(SELECTED_DATES),
                str(sorted({metrics.start for metrics in answer.metrics})),
            )
        )
    return checks


def symptom_checks(run: ValidationRun) -> list[ValidationCheck]:
    answer = run.answer
    if run.id != "DEV-05" or answer is None:
        return []
    return [
        check(
            "answer.assessment_dates",
            "[datetime.date(2026, 1, 5), datetime.date(2026, 1, 16), datetime.date(2026, 1, 30)]",
            str([assessment.completed_date for assessment in answer.assessments]),
        ),
        check(
            "answer.assessment_scores",
            "[18.0, 14.0, 10.0]",
            str([assessment.score for assessment in answer.assessments]),
        ),
        check(
            "answer.january_19_reason_for_contact",
            "True",
            str(
                any(
                    observation.observed_date == SELECTED_DATES[0]
                    and observation.kind == "reason_for_contact"
                    for observation in answer.observations
                )
            ),
        ),
    ]


def source_checks(
    answer: AnswerBundle, documents: dict[str, DocumentRecord]
) -> list[ValidationCheck]:
    invalid: list[str] = []
    for source in answer.sources:
        document = documents.get(source.filename)
        if document is None:
            invalid.append(f"{source.filename}: source file not found")
            continue
        lines = document.text.splitlines(keepends=True)
        valid = (
            source.content_hash == document.content_hash
            and source.document_id == document.document_id
            and 1 <= source.start_line <= source.end_line <= len(lines)
            and source.quote in "".join(lines[source.start_line - 1 : source.end_line])
        )
        if not valid:
            invalid.append(f"{source.document_id}:{source.start_line}-{source.end_line}")
    return [check("answer.source_locations_verbatim", "[]", str(invalid))]


def validate_submission(
    runs: list[ValidationRun], questions: list[ReviewQuestion], source_directory: Path
) -> SubmissionValidation:
    expected = {question.id: question for question in questions}
    selected = [run for run in runs if run.id in expected]
    observed = {run.id for run in selected}
    excluded = {run.id for run in runs if run.id not in expected}
    batch_checks = [
        check(
            "questions.match_reference_set", str(sorted(EXPECTED_OPERATIONS)), str(sorted(expected))
        ),
        check("runs.cover_all_questions", str(sorted(expected)), str(sorted(observed))),
        check(
            "runs.unique_question_repeat_pairs",
            "True",
            str(len({(run.id, run.repeat) for run in selected}) == len(selected)),
        ),
    ]
    documents = {path.name: read_document(path) for path in source_directory.glob("*.txt")}
    results: list[QuestionValidation] = []
    for run in selected:
        question = expected.get(run.id)
        checks = [
            check(
                "run.known_question",
                "True",
                str(question is not None and run.id in EXPECTED_OPERATIONS),
            )
        ]
        if question is not None and run.id in EXPECTED_OPERATIONS:
            checks.extend(plan_checks(run, question))
            checks.extend(metric_checks(run))
            checks.extend(symptom_checks(run))
            if run.answer is not None:
                checks.extend(source_checks(run.answer, documents))
        results.append(
            QuestionValidation(
                id=run.id,
                repeat=run.repeat,
                passed=all(item.passed for item in checks),
                planner_model=run.plan.planner_model if run.plan is not None else None,
                model_calls=run.model_calls,
                usage=run.usage,
                timings=run.timings,
                checks=checks,
            )
        )
    return SubmissionValidation(
        passed=all(item.passed for item in batch_checks)
        and all(result.passed for result in results),
        expected_question_count=len(expected),
        observed_question_count=len(observed),
        input_run_count=len(runs),
        run_count=len(selected),
        excluded_question_ids=sorted(excluded),
        excluded_run_count=len(runs) - len(selected),
        checks=batch_checks,
        results=results,
    )


def main() -> None:
    parser = argparse.ArgumentParser(prog="validate-submission")
    parser.add_argument("input")
    parser.add_argument("--questions", default="questions.json")
    parser.add_argument("--sources", default="documents")
    parser.add_argument("--output", default="artifacts/planner_validation.json")
    options = parser.parse_args(namespace=Options())
    questions = TypeAdapter(list[ReviewQuestion]).validate_json(
        Path(options.questions).read_bytes()
    )
    report = validate_submission(
        live_records(Path(options.input)), questions, Path(options.sources)
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
        f"Validated {report.run_count} fresh runs "
        f"covering {report.observed_question_count} questions."
    )
    if report.excluded_run_count:
        print(
            f"Excluded {report.excluded_run_count} runs outside the reference question set: "
            + ", ".join(report.excluded_question_ids)
        )


if __name__ == "__main__":
    main()
