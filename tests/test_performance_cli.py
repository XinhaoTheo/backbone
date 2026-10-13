from __future__ import annotations

from contextlib import closing
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from pydantic import TypeAdapter

from backbone.benchmarking import ReviewQuestion
from backbone.cli import Options, main
from backbone.demo import DemoReport
from backbone.extraction import ExtractionValidationError
from backbone.models import (
    ClinicalSnapshot,
    ContactAlternative,
    DocumentRecord,
    Encounter,
    ExtractionResult,
    ModelUsage,
    PatientRecord,
    PlanClaim,
)
from backbone.performance import FullQueryReport, InitialProcessingReport, measure_queries
from backbone.planning import (
    IntentResult,
    PatientScope,
    PlanningContext,
    QueryIntent,
    QueryPlanner,
    QueryPlanningError,
    TaskIntent,
)
from backbone.storage import Store


@dataclass
class OfflinePlanner:
    fail: bool = False
    contexts: list[PlanningContext] = field(default_factory=list)

    def interpret(self, question: str, context: PlanningContext) -> IntentResult:
        self.contexts.append(context)
        if self.fail:
            raise QueryPlanningError(
                "Synthetic planning failure.",
                model_calls=1,
                usage=ModelUsage(input_tokens=90, output_tokens=12, cost_usd=0.001),
            )
        return IntentResult(
            intent=QueryIntent(
                status="ready",
                message="",
                tasks=[
                    TaskIntent(
                        operation="durations",
                        patients=PatientScope(references=["P1"]),
                        metrics=["minutes"],
                    )
                ],
            ),
            model="offline-test-planner",
            model_calls=1,
            usage=ModelUsage(input_tokens=80, output_tokens=15, cost_usd=0.001),
        )


@dataclass
class OfflineFailureExtractor:
    calls: int = 0

    def cache_key(self, document: DocumentRecord) -> str:
        return "offline-cli-test:" + document.content_hash

    def extract(self, document: DocumentRecord) -> ExtractionResult:
        self.calls += 1
        raise ExtractionValidationError("Synthetic extraction failure.")


def clinical_patient(minutes: int) -> PatientRecord:
    return PatientRecord(
        patient_id="P1",
        name="Synthetic Casey",
        organization="Synthetic Clinic",
        episode_start=date(2026, 1, 5),
        episode_end=date(2026, 1, 11),
        encounters=[
            Encounter(
                encounter_id="E1",
                patient_id="P1",
                service_date=date(2026, 1, 5),
                service_type="individual",
                attendance="attended",
                patient_present=True,
                alternatives=[ContactAlternative(minutes=minutes, intervals=[], sources=[])],
                decisions=[],
                sources=[],
            )
        ],
        plans=[
            PlanClaim(
                patient_id="P1",
                effective_start=date(2026, 1, 5),
                effective_end=None,
                minimum_days=1,
                minimum_minutes=10,
                eligible_services=["individual"],
                week_start="Monday",
                patient_present_required=True,
                note="Synthetic weekly goal.",
                quotes=[],
            )
        ],
        assessments=[],
        observations=[],
    )


def published_database(directory: Path) -> Store:
    store = Store(directory / "review.sqlite3")
    store.initialize()
    first = store.publish([clinical_patient(40)], {})
    second = store.publish([clinical_patient(50)], {})
    with closing(store.connect()) as connection, connection:
        connection.executemany(
            "UPDATE revisions SET created_at = ? WHERE id = ?",
            [
                (datetime(2026, 10, day, 12, tzinfo=UTC).isoformat(), revision)
                for day, revision in [(1, first), (2, second)]
            ],
        )
    return store


def question_file(directory: Path) -> Path:
    path = directory / "questions.json"
    adapter: TypeAdapter[list[ReviewQuestion]] = TypeAdapter(list[ReviewQuestion])
    path.write_bytes(
        adapter.dump_json(
            [
                ReviewQuestion(
                    id="Q1", question="How many therapy minutes did Synthetic Casey receive?"
                )
            ]
        )
    )
    return path


def patch_planner(monkeypatch: pytest.MonkeyPatch, planner: OfflinePlanner) -> None:
    def create_planner(options: Options) -> OfflinePlanner:
        return planner

    monkeypatch.setattr("backbone.cli.query_planner", create_planner)


def patch_extractor(monkeypatch: pytest.MonkeyPatch, extractor: OfflineFailureExtractor) -> None:
    def create_extractor(
        model: str,
        *,
        input_rate_per_million: float | None = None,
        output_rate_per_million: float | None = None,
    ) -> OfflineFailureExtractor:
        return extractor

    monkeypatch.setattr("backbone.extraction.OpenAIExtractor", create_extractor)


@pytest.mark.parametrize(
    "selector",
    [
        ["--snapshot", "1"],
        ["--as-of", "2026-10-01T18:00:00Z"],
    ],
)
def test_live_benchmark_receives_store_and_measures_selected_history(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    selector: list[str],
) -> None:
    store = published_database(tmp_path)
    questions = question_file(tmp_path)
    output = tmp_path / "benchmarks" / "live.json"
    planner = OfflinePlanner()
    patch_planner(monkeypatch, planner)
    monkeypatch.chdir(tmp_path)
    loads: list[int | None] = []
    original_snapshot = Store.snapshot
    measured_stores: list[Store] = []

    def snapshot(database: Store, revision_id: int | None = None) -> ClinicalSnapshot:
        loads.append(revision_id)
        return original_snapshot(database, revision_id)

    def measured(
        database: Store,
        requested: list[ReviewQuestion],
        repeats: int = 3,
        *,
        planner: QueryPlanner,
        snapshot_id: int | None = None,
        scenario_budget: int = 10_000,
    ) -> FullQueryReport:
        assert isinstance(database, Store)
        assert database.path == store.path
        assert not loads
        measured_stores.append(database)
        return measure_queries(
            database,
            requested,
            repeats,
            planner=planner,
            snapshot_id=snapshot_id,
            scenario_budget=scenario_budget,
        )

    monkeypatch.setattr(Store, "snapshot", snapshot)
    monkeypatch.setattr("backbone.performance.measure_queries", measured)
    monkeypatch.setattr(
        "sys.argv",
        [
            "backbone",
            "--db",
            str(store.path),
            "benchmark-live",
            str(questions),
            "--repeats",
            "1",
            "--output",
            str(output),
            *selector,
        ],
    )
    main()
    report = FullQueryReport.model_validate_json(output.read_bytes())
    run = report.queries[0].runs[0]
    assert len(measured_stores) == 1
    assert loads == [1, 1]
    assert [context.snapshot_id for context in planner.contexts] == [1]
    assert run.snapshot_id == 1 and run.answer is not None
    assert run.answer.metrics[0].minutes.exact == 40
    assert run.replay is not None and run.replay.answer_matches_fresh
    assert run.fresh.database_load_seconds > 0
    assert run.fresh.planning_seconds > 0
    assert run.fresh.execution_render_seconds > 0
    assert report.model_calls == 1 and report.replay_runs == 1
    assert store.execution_records()[-1].kind == "benchmark-live"


def test_live_planning_failure_retains_report_and_log_before_nonzero_exit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = published_database(tmp_path)
    questions = question_file(tmp_path)
    output = tmp_path / "failure.json"
    patch_planner(monkeypatch, OfflinePlanner(fail=True))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "sys.argv",
        [
            "backbone",
            "--db",
            str(store.path),
            "benchmark-live",
            str(questions),
            "--repeats",
            "1",
            "--output",
            str(output),
        ],
    )
    with pytest.raises(SystemExit) as raised:
        main()
    assert raised.value.code == 1
    report = FullQueryReport.model_validate_json(output.read_bytes())
    run = report.queries[0].runs[0]
    assert run.answer_status == "planning_error"
    assert run.reason == "Synthetic planning failure."
    assert run.planner_usage is not None and run.planner_usage.input_tokens == 90
    assert run.answer is None and run.replay is None
    assert report.fresh_query_runs == 1 and report.replay_runs == 0
    assert store.execution_records()[-1].kind == "benchmark-live"


def test_live_snapshot_failure_retains_report_without_calling_planner(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = published_database(tmp_path)
    questions = question_file(tmp_path)
    output = tmp_path / "missing-revision.json"
    planner = OfflinePlanner()
    patch_planner(monkeypatch, planner)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "sys.argv",
        [
            "backbone",
            "--db",
            str(store.path),
            "benchmark-live",
            str(questions),
            "--snapshot",
            "999",
            "--repeats",
            "1",
            "--output",
            str(output),
        ],
    )
    with pytest.raises(SystemExit) as raised:
        main()
    assert raised.value.code == 1
    report = FullQueryReport.model_validate_json(output.read_bytes())
    run = report.queries[0].runs[0]
    assert run.answer_status == "execution_error"
    assert run.reason is not None and "snapshot loading failed" in run.reason
    assert run.snapshot_id is None
    assert run.fresh.database_load_seconds > 0
    assert run.fresh.planning_seconds == 0
    assert not planner.contexts
    assert report.model_calls == 0 and report.replay_runs == 0


def test_initial_benchmark_refuses_existing_database_without_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    store = published_database(tmp_path)
    before = store.path.read_bytes()
    output = tmp_path / "initial.json"
    extractor = OfflineFailureExtractor()
    patch_extractor(monkeypatch, extractor)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "sys.argv",
        [
            "backbone",
            "--db",
            str(store.path),
            "benchmark-process",
            str(tmp_path / "missing"),
            "--output",
            str(output),
        ],
    )
    with pytest.raises(SystemExit) as raised:
        main()
    assert raised.value.code == 2
    assert "requires a new database path" in capsys.readouterr().err
    assert store.path.read_bytes() == before
    assert store.latest_revision() == 2
    assert extractor.calls == 0
    assert not output.exists()


def test_initial_processing_failure_preserves_measurement_before_nonzero_exit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database = tmp_path / "new.sqlite3"
    document = tmp_path / "synthetic.txt"
    document.write_text("Document ID: SYN-FAILED\nSynthetic failed record.\n", encoding="utf-8")
    output = tmp_path / "measurements" / "initial.json"
    extractor = OfflineFailureExtractor()
    patch_extractor(monkeypatch, extractor)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "sys.argv",
        [
            "backbone",
            "--db",
            str(database),
            "benchmark-process",
            str(document),
            "--workers",
            "1",
            "--output",
            str(output),
        ],
    )
    with pytest.raises(SystemExit) as raised:
        main()
    assert raised.value.code == 1
    report = InitialProcessingReport.model_validate_json(output.read_bytes())
    assert report.processing.failed_documents == {"SYN-FAILED": "Synthetic extraction failure."}
    assert report.processing.extracted_documents == 0
    assert report.processing.snapshot_id == 0
    assert report.database_initialization_seconds > 0
    assert report.processing_seconds > 0
    assert report.end_to_end_seconds >= report.processing_seconds
    assert extractor.calls == 1
    assert Store(database).snapshot().failed_documents == ["SYN-FAILED"]


def test_demo_uses_separate_output_without_touching_default_database(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = published_database(tmp_path)
    before = store.path.read_bytes()
    fixtures = Path(__file__).resolve().parents[1] / "demo"
    output = tmp_path / "synthetic-demo"
    monkeypatch.setenv("BACKBONE_DB", str(store.path))
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "sys.argv",
        [
            "backbone",
            "demo",
            "--fixtures",
            str(fixtures),
            "--output",
            str(output),
        ],
    )
    main()
    report = DemoReport.model_validate_json((output / "demo-report.json").read_bytes())
    assert report.data_kind == "synthetic"
    assert report.model_calls == 0 and report.patient_count >= 3
    assert report.database_path == output / "review.sqlite3"
    assert (output / "abstraction.json").exists()
    assert (output / "answers.json").exists()
    assert store.path.read_bytes() == before
    assert store.snapshot().patients[0].encounters[0].alternatives[0].minutes == 50
