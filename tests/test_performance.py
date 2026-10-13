from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import pytest

from backbone.benchmarking import ReviewQuestion
from backbone.models import (
    ContactAlternative,
    DocumentEvidence,
    DocumentRecord,
    Encounter,
    ExtractionResult,
    IngestionReport,
    ModelUsage,
    PatientRecord,
    PlanClaim,
    SourceRef,
    TimeInterval,
)
from backbone.performance import measure_initial_processing, measure_queries
from backbone.planning import (
    IntentResult,
    PatientScope,
    PlanningContext,
    QueryIntent,
    QueryPlanningError,
    TaskIntent,
)
from backbone.storage import Store
from backbone.workflow import ProcessingReport


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


class UnusedExtractor:
    def cache_key(self, document: DocumentRecord) -> str:
        return document.content_hash

    def extract(self, document: DocumentRecord) -> ExtractionResult:
        return ExtractionResult(
            evidence=DocumentEvidence(
                patients=[], contacts=[], plans=[], assessments=[], observations=[]
            ),
            model="test-extractor",
            usage=ModelUsage(),
            elapsed_seconds=0.0,
        )


def patient(patient_id: str = "P1") -> PatientRecord:
    source = SourceRef(
        content_hash=f"SESSION-{patient_id}",
        document_id=f"SESSION-{patient_id}",
        filename="session.txt",
        start_line=3,
        end_line=3,
        quote="Actual patient psychotherapy contact: 09:00-09:40.",
    )
    plan_source = SourceRef(
        content_hash=f"PLAN-{patient_id}",
        document_id=f"PLAN-{patient_id}",
        filename="plan.txt",
        start_line=5,
        end_line=5,
        quote="The weekly goal is one therapy day and 30 minutes.",
    )
    return PatientRecord(
        patient_id=patient_id,
        name="Casey" if patient_id == "P1" else "Jordan",
        organization="Synthetic Clinic",
        episode_start=date(2027, 5, 3),
        episode_end=date(2027, 5, 16),
        encounters=[
            Encounter(
                encounter_id=f"E-{patient_id}",
                patient_id=patient_id,
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
                patient_id=patient_id,
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


def published_store(tmp_path: Path, patients: list[PatientRecord] | None = None) -> Store:
    store = Store(tmp_path / "review.sqlite3")
    store.initialize()
    store.publish(patients if patients is not None else [patient()], {})
    return store


def count_intent(*, elapsed_seconds: float = 0.4) -> IntentResult:
    return IntentResult(
        intent=QueryIntent(
            status="ready",
            message="",
            tasks=[TaskIntent(operation="counts", patients=PatientScope(references=["P1"]))],
        ),
        model="test-planner",
        model_calls=1,
        usage=ModelUsage(input_tokens=100, output_tokens=25, cost_usd=0.002),
        elapsed_seconds=elapsed_seconds,
    )


def test_fresh_query_measures_all_stages_and_replay_has_no_model_calls(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = published_store(tmp_path)
    planner = FakePlanner([count_intent(), count_intent(elapsed_seconds=0.7)])
    ticks: Iterator[float] = iter([0, 1, 2, 5, 7, 8, 10, 11, 12, 14, 18, 21, 22, 25, 29, 30])

    def clock() -> float:
        return next(ticks)

    monkeypatch.setattr("backbone.performance.perf_counter", clock)
    report = measure_queries(
        store,
        [ReviewQuestion(id="Q1", question="Count Casey's therapy sessions.")],
        repeats=2,
        planner=planner,
    )
    first, second = report.queries[0].runs
    assert first.fresh.database_load_seconds == 1
    assert first.fresh.planning_seconds == 3
    assert first.fresh.execution_render_seconds == 2
    assert first.fresh.end_to_end_seconds == 6
    assert second.fresh.end_to_end_seconds == 9
    assert first.replay is not None and second.replay is not None
    assert first.replay.timings.database_load_seconds == 2
    assert first.replay.timings.execution_render_seconds == 1
    assert first.replay.timings.end_to_end_seconds == 3
    assert second.replay.timings.end_to_end_seconds == 7
    for run in (first, second):
        assert run.replay is not None
        assert run.replay.model_calls == 0
        assert run.replay.timings.planning_seconds == 0
        assert run.replay.same_snapshot_as_fresh
        assert run.replay.answer_matches_fresh
        assert run.scope == "individual"
        assert run.answer_status == "established"
        assert run.plan is not None and run.answer is not None
    assert report.queries[0].stable_answers_across_repeats
    assert report.queries[0].fresh_summary.end_to_end.p50_seconds == 7.5
    assert report.queries[0].fresh_summary.end_to_end.p95_seconds == pytest.approx(8.85)
    assert report.queries[0].replay_summary is not None
    assert report.queries[0].replay_summary.end_to_end.p50_seconds == 5
    assert report.fresh_query_runs == 2 and report.replay_runs == 2
    assert len(planner.questions) == report.model_calls == 2
    assert report.planning_usage.input_tokens == 200
    assert report.planning_usage.output_tokens == 50
    assert report.planning_usage.cost_usd == pytest.approx(0.004)
    assert not report.planning_usage_incomplete
    assert report.elapsed_seconds == 30
    assert report.limitations


def test_planning_failures_retain_partial_usage_and_do_not_hide_valid_queries(
    tmp_path: Path,
) -> None:
    store = published_store(tmp_path)
    planner = FakePlanner(
        [
            QueryPlanningError(
                "A patient reference is ambiguous.",
                model_calls=1,
                usage=ModelUsage(input_tokens=800, output_tokens=200, cost_usd=0.01),
            ),
            QueryPlanningError("API timeout.", model_calls=1),
            count_intent(),
        ]
    )
    report = measure_queries(
        store,
        [
            ReviewQuestion(id="Q1", question="Count that patient's sessions."),
            ReviewQuestion(id="Q2", question="Count Casey's sessions."),
            ReviewQuestion(id="Q3", question="Count Casey's therapy sessions."),
        ],
        repeats=1,
        planner=planner,
    )
    failed, timed_out, valid = [query.runs[0] for query in report.queries]
    assert failed.answer_status == timed_out.answer_status == "planning_error"
    assert failed.planner_usage is not None and failed.planner_usage.input_tokens == 800
    assert not failed.planning_usage_incomplete
    assert timed_out.planning_usage_incomplete
    assert failed.replay is None and timed_out.replay is None
    assert failed.fresh.execution_render_seconds == 0
    assert valid.answer_status == "established" and valid.replay is not None
    assert report.planning_usage.input_tokens == 900
    assert report.planning_usage.output_tokens == 225
    assert report.planning_usage.cost_usd is None
    assert report.planning_usage_incomplete
    assert report.model_calls == 3 and report.replay_runs == 1


def test_result_stability_ignores_unused_planning_fields(tmp_path: Path) -> None:
    first = count_intent()
    second = count_intent()
    first.intent.tasks[0].consecutive_weeks = 1
    second.intent.tasks[0].consecutive_weeks = 3
    report = measure_queries(
        published_store(tmp_path),
        [ReviewQuestion(id="Q1", question="Count Casey's therapy sessions.")],
        repeats=2,
        planner=FakePlanner([first, second]),
    )
    query = report.queries[0]
    assert not query.stable_answers_across_repeats
    assert query.stable_results_across_repeats


def test_collection_queries_are_measured_with_their_resolved_tasks(tmp_path: Path) -> None:
    store = published_store(tmp_path, [patient(), patient("P2")])
    intent = IntentResult(
        intent=QueryIntent(
            status="ready",
            message="",
            tasks=[TaskIntent(operation="cohort", patients=PatientScope(kind="all"))],
        ),
        model="test-planner",
        model_calls=1,
        usage=ModelUsage(input_tokens=140, output_tokens=30),
    )
    report = measure_queries(
        store,
        [ReviewQuestion(id="C1", question="Who missed goals for two consecutive weeks?")],
        repeats=1,
        planner=FakePlanner([intent]),
    )
    run = report.queries[0].runs[0]
    assert run.scope == "collection" and run.operations == ["cohort"]
    assert run.patient_count == 2
    assert run.answer is not None and len(run.answer.cohort_results) == 2
    assert run.plan is not None and run.plan.tasks[0].patient_ids == ["P1", "P2"]
    assert run.replay is not None and run.replay.answer_matches_fresh
    assert report.planning_usage.cost_usd is None
    assert not report.planning_usage_incomplete


def test_replay_pins_revision_and_preserves_published_coverage_difference(
    tmp_path: Path,
) -> None:
    store = published_store(tmp_path)
    failed = DocumentRecord(
        content_hash="FAILED",
        document_id="FAILED",
        filename="failed.txt",
        text="A synthetic document failed extraction.",
    )
    store.add_document(failed)
    store.save_failure(failed.content_hash, "Synthetic extraction failure.")
    report = measure_queries(
        store,
        [ReviewQuestion(id="Q1", question="Count Casey's therapy sessions.")],
        repeats=1,
        planner=FakePlanner([count_intent()]),
    )
    run = report.queries[0].runs[0]
    assert run.answer_status == "incomplete_source_processing"
    assert run.answer is not None and run.answer.coverage_status == "failed_source_processing"
    assert run.replay is not None and run.replay.same_snapshot_as_fresh
    assert run.replay.answer_status == "established"
    assert run.replay.answer_matches_fresh is False
    assert not report.planning_usage_incomplete


def test_replay_uses_original_revision_after_publish_during_model_planning(
    tmp_path: Path,
) -> None:
    store = published_store(tmp_path)

    class PublishingPlanner:
        def interpret(self, question: str, context: PlanningContext) -> IntentResult:
            store.publish([patient(), patient("P2")], {})
            return count_intent()

    report = measure_queries(
        store,
        [ReviewQuestion(id="Q1", question="Count Casey's therapy sessions.")],
        repeats=1,
        planner=PublishingPlanner(),
    )
    run = report.queries[0].runs[0]
    assert store.latest_revision() == 2
    assert run.snapshot_id == 1
    assert run.replay is not None and run.replay.snapshot_id == 1
    assert run.replay.same_snapshot_as_fresh and run.replay.answer_matches_fresh
    assert run.replay.answer_status == "established"


def test_single_initial_processing_stopwatch_includes_initialization_and_whole_workflow(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = Store(tmp_path / "initial.sqlite3")
    path = tmp_path / "sources"
    calls: list[tuple[Store, Path, int]] = []
    processing = ProcessingReport(
        ingestion=IngestionReport(
            files_seen=1, new_documents=1, duplicate_documents=0, document_hashes=["T1"]
        ),
        extracted_documents=1,
        cached_documents=0,
        failed_documents={},
        input_tokens=100,
        output_tokens=25,
        estimated_cost_usd=0.002,
        elapsed_seconds=4.5,
        snapshot_id=1,
    )
    ticks: Iterator[float] = iter([1, 3, 8])

    def clock() -> float:
        return next(ticks)

    def process(
        store: Store, path: Path, extractor: UnusedExtractor, workers: int
    ) -> ProcessingReport:
        assert store.path.exists()
        calls.append((store, path, workers))
        return processing

    monkeypatch.setattr("backbone.performance.perf_counter", clock)
    monkeypatch.setattr("backbone.performance.process_documents", process)
    report = measure_initial_processing(store, path, UnusedExtractor(), workers=3)
    assert report.database_initialization_seconds == 2
    assert report.processing_seconds == 5
    assert report.end_to_end_seconds == 7
    assert report.processing == processing and calls == [(store, path, 3)]
    with pytest.raises(ValueError, match="new database path"):
        measure_initial_processing(store, path, UnusedExtractor(), workers=3)


@pytest.mark.parametrize("case", ["repeats", "empty", "duplicate_ids", "budget", "revision"])
def test_invalid_benchmark_contracts_and_missing_revision(tmp_path: Path, case: str) -> None:
    store = published_store(tmp_path)
    planner = FakePlanner([])
    entry = ReviewQuestion(id="Q1", question="Count Casey's sessions.")
    if case == "revision":
        report = measure_queries(store, [entry], repeats=1, planner=planner, snapshot_id=999)
        run = report.queries[0].runs[0]
        assert run.answer_status == "execution_error"
        assert run.snapshot_id is None and run.replay is None
        assert run.reason is not None and "Snapshot 999" in run.reason
        assert report.model_calls == 0 and not planner.questions
        return
    with pytest.raises(ValueError):
        measure_queries(
            store,
            [] if case == "empty" else [entry, entry] if case == "duplicate_ids" else [entry],
            repeats=0 if case == "repeats" else 1,
            planner=planner,
            scenario_budget=0 if case == "budget" else 10_000,
        )
    assert not planner.questions
