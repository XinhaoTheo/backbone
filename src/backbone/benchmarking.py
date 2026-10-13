from __future__ import annotations

import hashlib
from math import floor
from pathlib import Path
from time import perf_counter
from typing import Literal

from pydantic import BaseModel, Field, TypeAdapter

from backbone.models import ClinicalSnapshot, QueryPlan
from backbone.planning import QueryPlanner, plan_question
from backbone.query import AnswerBundle, QueryPlanningError, answer_question

AnswerStatus = Literal[
    "established",
    "evidence_uncertainty",
    "analysis_incomplete",
    "incomplete_source_processing",
    "planning_error",
    "execution_error",
]


class ReviewQuestion(BaseModel):
    id: str = Field(min_length=1)
    question: str = Field(min_length=1)


class QueryBenchmark(BaseModel):
    question: str
    operation: str | None
    patient_id: str | None
    answer_status: AnswerStatus
    reason: str | None
    latency_seconds: list[float]
    p50_seconds: float
    p95_seconds: float
    stable_across_repeats: bool


class BenchmarkReport(BaseModel):
    measurement_kind: Literal["measured"] = "measured"
    scope: Literal["in_memory_execution_only"] = "in_memory_execution_only"
    snapshot_id: int
    patient_count: int
    document_count: int
    abstraction_bytes: int
    repeats: int
    scenario_budget: int
    query_runs: int
    elapsed_seconds: float
    model_calls: int = 0
    planning_seconds: float = 0.0
    planning_input_tokens: int = 0
    planning_output_tokens: int = 0
    planning_usage_incomplete: bool = False
    percentile_method: str = "Linear interpolation between sorted observations."
    queries: list[QueryBenchmark]
    limitations: list[str] = Field(
        default_factory=lambda: [
            "Query samples measure calculation and rendering with saved plans; model planning "
            "is reported separately. Extraction, ingestion, and database loading are excluded.",
            "Percentiles describe these samples; few repeats do not establish tail latency "
            "or performance at a larger document count.",
        ]
    )


class SubmissionAnswer(BaseModel):
    id: str
    answer: AnswerBundle


class SubmissionExport(BaseModel):
    snapshot_id: int
    answer_count: int
    abstraction_bytes: int
    abstraction_path: Path
    answers_json_path: Path
    answers_markdown_path: Path
    plans_path: Path


def percentile(samples: list[float], probability: float) -> float:
    ordered = sorted(samples)
    position = (len(ordered) - 1) * probability
    lower = floor(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def classify_answer(answer: AnswerBundle) -> AnswerStatus:
    if answer.coverage_status == "failed_source_processing":
        return "incomplete_source_processing"
    if any(result.analysis_status == "analysis_incomplete" for result in answer.metrics):
        return "analysis_incomplete"
    if any(result.membership == "analysis_incomplete" for result in answer.cohort_results):
        return "analysis_incomplete"
    return "evidence_uncertainty" if answer.uncertainty else "established"


def benchmark(
    snapshot: ClinicalSnapshot,
    questions: list[str],
    repeats: int = 3,
    *,
    document_count: int,
    scenario_budget: int = 10_000,
    plans: list[QueryPlan] | None = None,
    planner: QueryPlanner | None = None,
) -> BenchmarkReport:
    if repeats < 1:
        raise ValueError("Benchmark repeats must be positive.")
    if not questions:
        raise ValueError("Benchmark requires at least one question.")
    if document_count < 0:
        raise ValueError("Document count cannot be negative.")
    if scenario_budget < 1:
        raise ValueError("Scenario budget must be positive.")
    if plans is not None and len(plans) != len(questions):
        raise ValueError("Provide one saved plan per benchmark question.")
    results: list[QueryBenchmark] = []
    started = perf_counter()
    model_calls = 0
    planning_seconds = 0.0
    input_tokens = 0
    output_tokens = 0
    usage_incomplete = False
    for index, question in enumerate(questions):
        resolved: QueryPlan | None = None
        planning_error: str | None = None
        try:
            resolved = (
                plans[index]
                if plans is not None
                else plan_question(question, snapshot, planner=planner)
            )
        except QueryPlanningError as error:
            planning_error = str(error)
            model_calls += error.model_calls
            planning_seconds += error.elapsed_seconds
            if error.usage is not None:
                input_tokens += error.usage.input_tokens
                output_tokens += error.usage.output_tokens
            elif error.model_calls:
                usage_incomplete = True
        if plans is None and resolved is not None:
            model_calls += resolved.planner_model_calls
            planning_seconds += resolved.planner_elapsed_seconds
            input_tokens += resolved.planner_usage.input_tokens
            output_tokens += resolved.planner_usage.output_tokens
        samples: list[float] = []
        fingerprints: list[str] = []
        operation: str | None = None
        patient_id: str | None = None
        status: AnswerStatus = "execution_error"
        reason: str | None = None
        for _ in range(repeats):
            query_started = perf_counter()
            answer: AnswerBundle | None = None
            try:
                if resolved is None:
                    raise QueryPlanningError(str(planning_error))
                answer = answer_question(question, snapshot, scenario_budget, plan=resolved)
            except QueryPlanningError as error:
                status, reason = "planning_error", str(error)
            except ValueError as error:
                status, reason = "execution_error", str(error)
            samples.append(perf_counter() - query_started)
            if answer is not None:
                operation = ",".join(dict.fromkeys(task.operation for task in answer.plan.tasks))
                identifiers = {
                    identifier for task in answer.plan.tasks for identifier in task.patient_ids
                }
                patient_id = next(iter(identifiers)) if len(identifiers) == 1 else None
                status = classify_answer(answer)
                reason = "; ".join(answer.uncertainty) or None
                payload = answer.model_dump_json()
            else:
                payload = f"{status}:{reason}"
            fingerprints.append(hashlib.sha256(payload.encode("utf-8")).hexdigest())
        results.append(
            QueryBenchmark(
                question=question,
                operation=operation,
                patient_id=patient_id,
                answer_status=status,
                reason=reason,
                latency_seconds=samples,
                p50_seconds=percentile(samples, 0.5),
                p95_seconds=percentile(samples, 0.95),
                stable_across_repeats=len(set(fingerprints)) == 1,
            )
        )
    elapsed = perf_counter() - started
    return BenchmarkReport(
        snapshot_id=snapshot.snapshot_id,
        patient_count=len(snapshot.patients),
        document_count=document_count,
        abstraction_bytes=len(snapshot.model_dump_json().encode("utf-8")),
        repeats=repeats,
        scenario_budget=scenario_budget,
        query_runs=len(questions) * repeats,
        elapsed_seconds=elapsed,
        model_calls=model_calls,
        planning_seconds=planning_seconds,
        planning_input_tokens=input_tokens,
        planning_output_tokens=output_tokens,
        planning_usage_incomplete=usage_incomplete,
        queries=results,
    )


def replay_questions(
    snapshot: ClinicalSnapshot,
    questions: list[str],
    scenario_budget: int = 10_000,
    *,
    plans: list[QueryPlan],
) -> list[AnswerBundle]:
    if scenario_budget < 1:
        raise ValueError("Scenario budget must be positive.")
    if len(plans) != len(questions):
        raise ValueError("Provide one saved plan per replay question.")
    return [
        answer_question(question, snapshot, scenario_budget, plan=plan)
        for question, plan in zip(questions, plans, strict=True)
    ]


def export_submission(
    snapshot: ClinicalSnapshot,
    questions: list[ReviewQuestion],
    output_dir: Path,
    scenario_budget: int = 10_000,
    *,
    plans: list[QueryPlan] | None = None,
    planner: QueryPlanner | None = None,
) -> SubmissionExport:
    if not questions:
        raise ValueError("Submission export requires at least one question.")
    if len({question.id for question in questions}) != len(questions):
        raise ValueError("Submission question identifiers must be unique.")
    resolved = (
        plans
        if plans is not None
        else [plan_question(entry.question, snapshot, planner=planner) for entry in questions]
    )
    answers = replay_questions(
        snapshot, [entry.question for entry in questions], scenario_budget, plans=resolved
    )
    entries = [
        SubmissionAnswer(id=question.id, answer=answer)
        for question, answer in zip(questions, answers, strict=True)
    ]
    abstraction = snapshot.model_dump_json(indent=2).encode("utf-8")
    answers_json = TypeAdapter(list[SubmissionAnswer]).dump_json(entries, indent=2)
    markdown = "\n\n".join(f"## {entry.id}\n\n{entry.answer.text}" for entry in entries) + "\n"
    output_dir.mkdir(parents=True, exist_ok=True)
    abstraction_path = output_dir / "abstraction.json"
    answers_json_path = output_dir / "answers.json"
    answers_markdown_path = output_dir / "answers.md"
    plans_path = output_dir / "plans.json"
    abstraction_path.write_bytes(abstraction)
    answers_json_path.write_bytes(answers_json)
    answers_markdown_path.write_text(markdown, encoding="utf-8")
    plans_path.write_bytes(TypeAdapter(list[QueryPlan]).dump_json(resolved, indent=2))
    return SubmissionExport(
        snapshot_id=snapshot.snapshot_id,
        answer_count=len(entries),
        abstraction_bytes=len(abstraction),
        abstraction_path=abstraction_path,
        answers_json_path=answers_json_path,
        answers_markdown_path=answers_markdown_path,
        plans_path=plans_path,
    )
