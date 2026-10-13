from __future__ import annotations

from pathlib import Path
from time import perf_counter
from typing import Literal

from pydantic import BaseModel, Field

from backbone.benchmarking import AnswerStatus, ReviewQuestion, classify_answer, percentile
from backbone.extraction import Extractor
from backbone.models import ModelUsage, QueryOperation, QueryPlan
from backbone.planning import QueryPlanner, QueryPlanningError, plan_question
from backbone.query import AnswerBundle, answer_question
from backbone.storage import Store
from backbone.workflow import ProcessingReport, process_documents

QueryScope = Literal["individual", "collection", "unresolved"]


class TokenRates(BaseModel):
    input_usd_per_million: float | None
    output_usd_per_million: float | None
    basis: str = (
        "Standard uncached token estimate; excludes billing adjustments and cache discounts."
    )


class QueryTimings(BaseModel):
    database_load_seconds: float
    planning_seconds: float
    execution_render_seconds: float
    end_to_end_seconds: float


class StagePercentiles(BaseModel):
    sample_count: int
    p50_seconds: float
    p95_seconds: float


class TimingSummary(BaseModel):
    database_load: StagePercentiles
    planning: StagePercentiles
    execution_render: StagePercentiles
    end_to_end: StagePercentiles


class ReplayMeasurement(BaseModel):
    snapshot_id: int | None
    timings: QueryTimings
    answer_status: AnswerStatus
    reason: str | None
    model_calls: Literal[0] = 0
    same_snapshot_as_fresh: bool
    answer_matches_fresh: bool | None


class FreshQueryRun(BaseModel):
    repeat: int
    snapshot_id: int | None
    patient_count: int
    scope: QueryScope
    operations: list[QueryOperation]
    answer_status: AnswerStatus
    reason: str | None
    fresh: QueryTimings
    model_calls: int
    planner_model: str | None
    planner_usage: ModelUsage | None
    planning_usage_incomplete: bool
    plan: QueryPlan | None
    answer: AnswerBundle | None
    replay: ReplayMeasurement | None


class QueryPerformance(BaseModel):
    id: str
    question: str
    scopes: list[QueryScope]
    runs: list[FreshQueryRun]
    fresh_summary: TimingSummary
    replay_summary: TimingSummary | None
    stable_answers_across_repeats: bool | None
    stable_results_across_repeats: bool | None = None


class FullQueryReport(BaseModel):
    measurement_kind: Literal["measured"] = "measured"
    scope: Literal["database_planning_execution_and_saved_plan_replay"] = (
        "database_planning_execution_and_saved_plan_replay"
    )
    repeats: int
    scenario_budget: int
    question_count: int
    fresh_query_runs: int
    replay_runs: int
    snapshot_ids: list[int]
    model_calls: int
    planning_usage: ModelUsage
    planning_usage_incomplete: bool
    elapsed_seconds: float
    requested_model: str | None = None
    token_rates: TokenRates | None = None
    queries: list[QueryPerformance]
    percentile_method: str = "Linear interpolation between sorted observations."
    limitations: list[str] = Field(
        default_factory=lambda: [
            "Fresh runs include SQLite snapshot loading, planning context construction, model "
            "planning, plan validation, calculation, and rendering. Planner construction, "
            "database initialization, report serialization, and output file writes are excluded.",
            "Every fresh repeat calls the planner. Replay reloads the database and executes the "
            "same saved plan without model calls; saved-plan file reading is excluded.",
            "Database loading uses new SQLite connections but does not clear operating-system "
            "file caches. Samples do not represent guaranteed cold-disk latency.",
            "Replay pins the fresh run's revision. A latest read includes current failed/pending "
            "coverage, which can differ from that revision's published coverage. Snapshot IDs "
            "and answer comparisons expose differences rather than replacing coverage.",
            "Reported costs are estimates from configured token rates, not billing records. "
            "Unknown usage or prices leave the total cost unresolved.",
            "Percentiles describe these observations; few repeats do not establish tail latency "
            "or performance at larger patient or document counts.",
            "Exact answer stability includes generated task fields. Result stability compares "
            "the answer content after removing its plan and task instructions.",
        ]
    )


class InitialProcessingReport(BaseModel):
    measurement_kind: Literal["measured"] = "measured"
    scope: Literal["single_initialization_ingestion_extraction_reconciliation_publication"] = (
        "single_initialization_ingestion_extraction_reconciliation_publication"
    )
    database_initialization_seconds: float
    processing_seconds: float
    end_to_end_seconds: float
    processing: ProcessingReport
    requested_model: str | None = None
    token_rates: TokenRates | None = None
    limitations: list[str] = Field(
        default_factory=lambda: [
            "Measured in one invocation against a new database. The total includes database "
            "initialization, ingestion, extraction, reconciliation, and publication; extractor "
            "construction and report output are excluded.",
            "Extraction failures are retained in the processing report; a failed run does not "
            "claim successful publication.",
        ]
    )


def summarize_timings(samples: list[QueryTimings]) -> TimingSummary:
    def stage(values: list[float]) -> StagePercentiles:
        return StagePercentiles(
            sample_count=len(values),
            p50_seconds=percentile(values, 0.5),
            p95_seconds=percentile(values, 0.95),
        )

    return TimingSummary(
        database_load=stage([sample.database_load_seconds for sample in samples]),
        planning=stage([sample.planning_seconds for sample in samples]),
        execution_render=stage([sample.execution_render_seconds for sample in samples]),
        end_to_end=stage([sample.end_to_end_seconds for sample in samples]),
    )


def query_scope(plan: QueryPlan | None) -> QueryScope:
    if plan is None:
        return "unresolved"
    identifiers = {identifier for task in plan.tasks for identifier in task.patient_ids}
    return (
        "collection"
        if len(identifiers) > 1 or any(task.operation == "cohort" for task in plan.tasks)
        else "individual"
    )


def answer_payload(answer: AnswerBundle) -> str:
    return answer.model_dump_json(
        exclude={
            "plan": {
                "planner_model",
                "planner_usage",
                "planner_elapsed_seconds",
                "planner_model_calls",
            }
        }
    )


def result_payload(answer: AnswerBundle) -> str:
    return answer.model_dump_json(exclude={"plan": True, "task_answers": {"__all__": {"task"}}})


def measure_replay(
    store: Store,
    question: str,
    plan: QueryPlan,
    fresh_answer: AnswerBundle | None,
    snapshot_id: int,
    scenario_budget: int,
) -> ReplayMeasurement:
    started = perf_counter()
    try:
        snapshot = store.snapshot(snapshot_id)
    except ValueError as error:
        finished = perf_counter()
        return ReplayMeasurement(
            snapshot_id=None,
            timings=QueryTimings(
                database_load_seconds=finished - started,
                planning_seconds=0.0,
                execution_render_seconds=0.0,
                end_to_end_seconds=finished - started,
            ),
            answer_status="execution_error",
            reason=f"Database snapshot loading failed: {error}",
            same_snapshot_as_fresh=False,
            answer_matches_fresh=None,
        )
    loaded = perf_counter()
    answer: AnswerBundle | None = None
    status: AnswerStatus
    reason: str | None
    try:
        answer = answer_question(question, snapshot, scenario_budget, plan=plan)
    except QueryPlanningError as error:
        status, reason = "planning_error", str(error)
    except ValueError as error:
        status, reason = "execution_error", str(error)
    else:
        status, reason = classify_answer(answer), "; ".join(answer.uncertainty) or None
    finished = perf_counter()
    return ReplayMeasurement(
        snapshot_id=snapshot.snapshot_id,
        timings=QueryTimings(
            database_load_seconds=loaded - started,
            planning_seconds=0.0,
            execution_render_seconds=finished - loaded,
            end_to_end_seconds=finished - started,
        ),
        answer_status=status,
        reason=reason,
        same_snapshot_as_fresh=snapshot.snapshot_id == plan.snapshot_id,
        answer_matches_fresh=(
            answer_payload(answer) == answer_payload(fresh_answer)
            if answer is not None and fresh_answer is not None
            else None
        ),
    )


def measure_fresh_query(
    store: Store,
    question: str,
    repeat: int,
    planner: QueryPlanner,
    snapshot_id: int | None,
    scenario_budget: int,
) -> FreshQueryRun:
    started = perf_counter()
    try:
        snapshot = store.snapshot(snapshot_id)
    except ValueError as error:
        finished = perf_counter()
        return FreshQueryRun(
            repeat=repeat,
            snapshot_id=None,
            patient_count=0,
            scope="unresolved",
            operations=[],
            answer_status="execution_error",
            reason=f"Database snapshot loading failed: {error}",
            fresh=QueryTimings(
                database_load_seconds=finished - started,
                planning_seconds=0.0,
                execution_render_seconds=0.0,
                end_to_end_seconds=finished - started,
            ),
            model_calls=0,
            planner_model=None,
            planner_usage=None,
            planning_usage_incomplete=False,
            plan=None,
            answer=None,
            replay=None,
        )
    loaded = perf_counter()
    try:
        plan = plan_question(question, snapshot, planner=planner)
    except QueryPlanningError as error:
        finished = perf_counter()
        return FreshQueryRun(
            repeat=repeat,
            snapshot_id=snapshot.snapshot_id,
            patient_count=len(snapshot.patients),
            scope="unresolved",
            operations=[],
            answer_status="planning_error",
            reason=str(error),
            fresh=QueryTimings(
                database_load_seconds=loaded - started,
                planning_seconds=finished - loaded,
                execution_render_seconds=0.0,
                end_to_end_seconds=finished - started,
            ),
            model_calls=error.model_calls,
            planner_model=None,
            planner_usage=error.usage,
            planning_usage_incomplete=error.model_calls > 0 and error.usage is None,
            plan=None,
            answer=None,
            replay=None,
        )
    planned = perf_counter()
    answer: AnswerBundle | None = None
    status: AnswerStatus
    reason: str | None
    try:
        answer = answer_question(question, snapshot, scenario_budget, plan=plan)
    except QueryPlanningError as error:
        status, reason = "planning_error", str(error)
    except ValueError as error:
        status, reason = "execution_error", str(error)
    else:
        status, reason = classify_answer(answer), "; ".join(answer.uncertainty) or None
    finished = perf_counter()
    return FreshQueryRun(
        repeat=repeat,
        snapshot_id=snapshot.snapshot_id,
        patient_count=len(snapshot.patients),
        scope=query_scope(plan),
        operations=list(dict.fromkeys(task.operation for task in plan.tasks)),
        answer_status=status,
        reason=reason,
        fresh=QueryTimings(
            database_load_seconds=loaded - started,
            planning_seconds=planned - loaded,
            execution_render_seconds=finished - planned,
            end_to_end_seconds=finished - started,
        ),
        model_calls=plan.planner_model_calls,
        planner_model=plan.planner_model,
        planner_usage=plan.planner_usage,
        planning_usage_incomplete=False,
        plan=plan,
        answer=answer,
        replay=measure_replay(store, question, plan, answer, snapshot.snapshot_id, scenario_budget),
    )


def measure_queries(
    store: Store,
    questions: list[ReviewQuestion],
    repeats: int = 3,
    *,
    planner: QueryPlanner,
    snapshot_id: int | None = None,
    scenario_budget: int = 10_000,
) -> FullQueryReport:
    if repeats < 1:
        raise ValueError("Benchmark repeats must be positive.")
    if not questions:
        raise ValueError("Benchmark requires at least one question.")
    if len({question.id for question in questions}) != len(questions):
        raise ValueError("Benchmark question identifiers must be unique.")
    if scenario_budget < 1:
        raise ValueError("Scenario budget must be positive.")
    started = perf_counter()
    measurements: list[QueryPerformance] = []
    all_runs: list[FreshQueryRun] = []
    for question in questions:
        runs = [
            measure_fresh_query(
                store, question.question, repeat, planner, snapshot_id, scenario_budget
            )
            for repeat in range(1, repeats + 1)
        ]
        all_runs.extend(runs)
        replay_samples = [run.replay.timings for run in runs if run.replay is not None]
        answers = [answer_payload(run.answer) for run in runs if run.answer is not None]
        results = [result_payload(run.answer) for run in runs if run.answer is not None]
        measurements.append(
            QueryPerformance(
                id=question.id,
                question=question.question,
                scopes=sorted({run.scope for run in runs}),
                runs=runs,
                fresh_summary=summarize_timings([run.fresh for run in runs]),
                replay_summary=summarize_timings(replay_samples) if replay_samples else None,
                stable_answers_across_repeats=(
                    len(set(answers)) == 1 if len(answers) == len(runs) else None
                ),
                stable_results_across_repeats=(
                    len(set(results)) == 1 if len(results) == len(runs) else None
                ),
            )
        )
    model_calls = sum(run.model_calls for run in all_runs)
    usage_incomplete = any(run.planning_usage_incomplete for run in all_runs)
    costs = [
        run.planner_usage.cost_usd
        for run in all_runs
        if run.model_calls and run.planner_usage is not None
    ]
    known_cost = not usage_incomplete and all(cost is not None for cost in costs)
    return FullQueryReport(
        repeats=repeats,
        scenario_budget=scenario_budget,
        question_count=len(questions),
        fresh_query_runs=len(all_runs),
        replay_runs=sum(run.replay is not None for run in all_runs),
        snapshot_ids=sorted({run.snapshot_id for run in all_runs if run.snapshot_id is not None}),
        model_calls=model_calls,
        planning_usage=ModelUsage(
            input_tokens=sum(
                run.planner_usage.input_tokens for run in all_runs if run.planner_usage is not None
            ),
            output_tokens=sum(
                run.planner_usage.output_tokens for run in all_runs if run.planner_usage is not None
            ),
            cost_usd=sum(cost for cost in costs if cost is not None) if known_cost else None,
        ),
        planning_usage_incomplete=usage_incomplete,
        elapsed_seconds=perf_counter() - started,
        queries=measurements,
    )


def measure_initial_processing(
    store: Store, path: Path, extractor: Extractor, workers: int
) -> InitialProcessingReport:
    if store.path.exists():
        raise ValueError("Initial processing measurement requires a new database path.")
    started = perf_counter()
    store.initialize()
    initialized = perf_counter()
    processing = process_documents(store, path, extractor, workers)
    finished = perf_counter()
    return InitialProcessingReport(
        database_initialization_seconds=initialized - started,
        processing_seconds=finished - initialized,
        end_to_end_seconds=finished - started,
        processing=processing,
    )
