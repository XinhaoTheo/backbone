from __future__ import annotations

import hashlib
from math import floor
from pathlib import Path
from time import perf_counter
from typing import Literal

from pydantic import BaseModel, Field, TypeAdapter

from backbone.models import ClinicalSnapshot
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
    scope: Literal["in_memory_query_only"] = "in_memory_query_only"
    snapshot_id: int
    patient_count: int
    document_count: int
    abstraction_bytes: int
    repeats: int
    scenario_budget: int
    query_runs: int
    elapsed_seconds: float
    model_calls: Literal[0] = 0
    percentile_method: str = "Linear interpolation between sorted observations."
    queries: list[QueryBenchmark]
    limitations: list[str] = Field(
        default_factory=lambda: [
            "Measures offline planning, calculation, and rendering against a loaded snapshot; "
            "excludes extraction, ingestion, and database loading.",
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
) -> BenchmarkReport:
    if repeats < 1:
        raise ValueError("Benchmark repeats must be positive.")
    if not questions:
        raise ValueError("Benchmark requires at least one question.")
    if document_count < 0:
        raise ValueError("Document count cannot be negative.")
    if scenario_budget < 1:
        raise ValueError("Scenario budget must be positive.")
    results: list[QueryBenchmark] = []
    started = perf_counter()
    for question in questions:
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
                answer = answer_question(question, snapshot, scenario_budget)
            except QueryPlanningError as error:
                status, reason = "planning_error", str(error)
            except ValueError as error:
                status, reason = "execution_error", str(error)
            samples.append(perf_counter() - query_started)
            if answer is not None:
                operation = answer.plan.operation
                patient_id = answer.plan.patient
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
        queries=results,
    )


def replay_questions(
    snapshot: ClinicalSnapshot, questions: list[str], scenario_budget: int = 10_000
) -> list[AnswerBundle]:
    if scenario_budget < 1:
        raise ValueError("Scenario budget must be positive.")
    return [answer_question(question, snapshot, scenario_budget) for question in questions]


def export_submission(
    snapshot: ClinicalSnapshot,
    questions: list[ReviewQuestion],
    output_dir: Path,
    scenario_budget: int = 10_000,
) -> SubmissionExport:
    if not questions:
        raise ValueError("Submission export requires at least one question.")
    if len({question.id for question in questions}) != len(questions):
        raise ValueError("Submission question identifiers must be unique.")
    answers = replay_questions(snapshot, [entry.question for entry in questions], scenario_budget)
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
    abstraction_path.write_bytes(abstraction)
    answers_json_path.write_bytes(answers_json)
    answers_markdown_path.write_text(markdown, encoding="utf-8")
    return SubmissionExport(
        snapshot_id=snapshot.snapshot_id,
        answer_count=len(entries),
        abstraction_bytes=len(abstraction),
        abstraction_path=abstraction_path,
        answers_json_path=answers_json_path,
        answers_markdown_path=answers_markdown_path,
    )
