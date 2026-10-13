from __future__ import annotations

import argparse
import os
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

from dotenv import load_dotenv
from pydantic import BaseModel, TypeAdapter

from backbone.benchmarking import ReviewQuestion, benchmark, export_submission
from backbone.ingestion import ingest
from backbone.models import ClinicalSnapshot, ModelUsage, PatientHistoryEntry, QueryPlan
from backbone.planning import OpenAIQueryPlanner
from backbone.query import AnswerBundle, answer_question
from backbone.storage import Store, publication_timestamp

__all__ = ["ReviewQuestion", "ReviewAnswer", "main"]


class ReviewAnswer(BaseModel):
    id: str
    answer: AnswerBundle


class QueryExecution(BaseModel):
    snapshot_id: int
    question: str
    operations: list[str]
    elapsed_seconds: float
    model_calls: int = 0
    planning_usage: ModelUsage


class Options(argparse.Namespace):
    command: str
    db: str
    path: str
    model: str
    workers: int
    question: str
    questions: str
    snapshot: int | None
    json: bool
    scenario_budget: int
    output: str
    abstraction: str
    repeats: int
    plans: str | None
    plan: str | None
    save_plan: str | None
    context: str | None
    patient_id: str
    as_of: datetime | None


def read_questions(path: str) -> list[ReviewQuestion]:
    return TypeAdapter(list[ReviewQuestion]).validate_json(Path(path).read_text(encoding="utf-8"))


def read_plans(path: str | None) -> list[QueryPlan] | None:
    if path is None:
        return None
    return TypeAdapter(list[QueryPlan]).validate_json(Path(path).read_bytes())


def parse_publication_time(value: str) -> datetime:
    try:
        parsed: datetime = datetime.fromisoformat(value)
        publication_timestamp(parsed)
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            "Use an ISO publication timestamp with Z or a UTC offset, "
            "for example 2026-10-13T17:26:00-04:00."
        ) from error
    return parsed


def add_revision_options(parser: argparse.ArgumentParser) -> None:
    selector = parser.add_mutually_exclusive_group()
    selector.add_argument("--snapshot", type=int)
    selector.add_argument("--as-of", type=parse_publication_time)


def render_patient_history(patient_id: str, entries: list[PatientHistoryEntry]) -> str:
    if not entries:
        return f"No published history for patient ID {patient_id}."
    lines: list[str] = [
        f"Patient: {patient_id}",
        "Publication time records when this system published the data, not when care occurred.",
        "",
        "| Revision | Published at (UTC) | State |",
        "| --- | --- | --- |",
    ]
    for entry in entries:
        published = entry.published_at.astimezone(UTC).isoformat(timespec="microseconds")
        lines.append(f"| {entry.revision_id} | {published} | {entry.state} |")
    return "\n".join(lines)


def main() -> None:
    load_dotenv(Path(".env"))
    parser = argparse.ArgumentParser(prog="backbone")
    parser.add_argument("--db", default=os.environ.get("BACKBONE_DB", ".backbone/review.sqlite3"))
    commands = parser.add_subparsers(dest="command", required=True)
    ingestion = commands.add_parser("ingest")
    ingestion.add_argument("path")
    for command in ("extract", "process"):
        extraction = commands.add_parser(command)
        extraction.add_argument("path")
        extraction.add_argument("--model", default=os.environ.get("OPENAI_MODEL", "gpt-4.1"))
        extraction.add_argument(
            "--workers", type=int, default=int(os.environ.get("BACKBONE_WORKERS", "4"))
        )
    for command in ("ask", "answer-file", "export", "benchmark"):
        question_parser = commands.add_parser(command)
        question_parser.add_argument("question" if command == "ask" else "questions")
        add_revision_options(question_parser)
        question_parser.add_argument("--scenario-budget", type=int, default=10000)
        question_parser.add_argument(
            "--model",
            default=os.environ.get("OPENAI_QUERY_MODEL", os.environ.get("OPENAI_MODEL", "gpt-4.1")),
        )
        if command == "ask":
            question_parser.add_argument("--json", action="store_true")
            question_parser.add_argument("--plan")
            question_parser.add_argument("--save-plan")
            question_parser.add_argument("--context")
        elif command == "benchmark":
            question_parser.add_argument("--plans")
            question_parser.add_argument("--output", default="artifacts/benchmark.json")
            question_parser.add_argument("--repeats", type=int, default=3)
        else:
            question_parser.add_argument("--plans")
            question_parser.add_argument("--output", default="artifacts")
    commands.add_parser("status")
    commands.add_parser("rebuild")
    history = commands.add_parser("history")
    history.add_argument("patient_id")
    history.add_argument("--json", action="store_true")
    patient_view = commands.add_parser("patient")
    patient_view.add_argument("patient_id")
    add_revision_options(patient_view)
    replay = commands.add_parser("replay")
    replay.add_argument("abstraction")
    replay.add_argument("questions")
    replay.add_argument("--output", default=".backbone/replay")
    replay.add_argument("--scenario-budget", type=int, default=10000)
    replay.add_argument("--plans", required=True)
    options = parser.parse_args(namespace=Options())
    if options.command == "replay":
        snapshot = ClinicalSnapshot.model_validate_json(Path(options.abstraction).read_bytes())
        try:
            result = export_submission(
                snapshot,
                read_questions(options.questions),
                Path(options.output),
                options.scenario_budget,
                plans=read_plans(options.plans),
            )
        except ValueError as error:
            parser.error(str(error))
        print(result.model_dump_json(indent=2))
        return
    store = Store(Path(options.db))
    store.initialize()
    if options.command == "ingest":
        print(ingest(store, Path(options.path)).model_dump_json(indent=2))
    elif options.command in {"extract", "process"}:
        from backbone.extraction import OpenAIExtractor
        from backbone.workflow import extract_documents, process_documents

        workflow = process_documents if options.command == "process" else extract_documents
        report = workflow(
            store, Path(options.path), OpenAIExtractor(options.model), options.workers
        )
        print(report.model_dump_json(indent=2))
        if report.failed_documents:
            raise SystemExit(1)
    elif options.command in {"ask", "answer-file", "export", "benchmark"}:
        try:
            snapshot = (
                store.snapshot_at(options.as_of)
                if options.as_of is not None
                else store.snapshot(options.snapshot)
            )
            if options.command == "ask":
                started = perf_counter()
                saved = (
                    QueryPlan.model_validate_json(Path(options.plan).read_bytes())
                    if options.plan
                    else None
                )
                context = (
                    QueryPlan.model_validate_json(Path(options.context).read_bytes())
                    if options.context
                    else None
                )
                answer = answer_question(
                    options.question,
                    snapshot,
                    options.scenario_budget,
                    plan=saved,
                    planner=OpenAIQueryPlanner(options.model) if saved is None else None,
                    context=context,
                )
                if options.save_plan:
                    target = Path(options.save_plan)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(
                        answer.plan.model_dump_json(indent=2) + "\n", encoding="utf-8"
                    )
                store.record_run(
                    "query",
                    QueryExecution(
                        snapshot_id=snapshot.snapshot_id,
                        question=options.question,
                        operations=[task.operation for task in answer.plan.tasks],
                        model_calls=0 if saved is not None else answer.plan.planner_model_calls,
                        planning_usage=answer.plan.planner_usage if saved is None else ModelUsage(),
                        elapsed_seconds=perf_counter() - started,
                    ).model_dump_json(),
                )
                print(answer.model_dump_json(indent=2) if options.json else answer.text)
            elif options.command == "benchmark":
                benchmark_report = benchmark(
                    snapshot,
                    [entry.question for entry in read_questions(options.questions)],
                    options.repeats,
                    document_count=store.document_count(),
                    scenario_budget=options.scenario_budget,
                    plans=read_plans(options.plans),
                    planner=OpenAIQueryPlanner(options.model) if options.plans is None else None,
                )
                output = Path(options.output)
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(
                    benchmark_report.model_dump_json(indent=2) + "\n", encoding="utf-8"
                )
                store.record_run("benchmark", benchmark_report.model_dump_json())
                print(benchmark_report.model_dump_json(indent=2))
            else:
                output = Path(options.output)
                result = export_submission(
                    snapshot,
                    read_questions(options.questions),
                    output,
                    options.scenario_budget,
                    plans=read_plans(options.plans),
                    planner=OpenAIQueryPlanner(options.model) if options.plans is None else None,
                )
                if options.command == "export":
                    (output / "extractions.jsonl").write_text(
                        "".join(
                            entry.model_dump_json() + "\n"
                            for entry in store.extraction_results(snapshot.snapshot_id)
                        ),
                        encoding="utf-8",
                    )
                    (output / "execution.jsonl").write_text(
                        "".join(
                            entry.model_dump_json() + "\n" for entry in store.execution_records()
                        ),
                        encoding="utf-8",
                    )
                print(f"Saved {result.answer_count} answers to {output}.")
        except ValueError as error:
            parser.error(str(error))
    elif options.command == "history":
        entries = store.patient_history(options.patient_id)
        print(
            TypeAdapter(list[PatientHistoryEntry]).dump_json(entries, indent=2).decode()
            if options.json
            else render_patient_history(options.patient_id, entries)
        )
    elif options.command == "patient":
        try:
            state = store.patient_at(
                options.patient_id,
                as_of=options.as_of,
                revision_id=options.snapshot,
            )
        except ValueError as error:
            parser.error(str(error))
        print(state.model_dump_json(indent=2))
    elif options.command == "rebuild":
        from backbone.workflow import rebuild_saved

        print(f"Published snapshot {rebuild_saved(store)} from saved evidence; model calls: 0.")
    else:
        print(f"Documents: {store.document_count()}; snapshot: {store.latest_revision()}")
