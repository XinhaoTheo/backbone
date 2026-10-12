from __future__ import annotations

import argparse
import os
from pathlib import Path
from time import perf_counter

from dotenv import load_dotenv
from pydantic import BaseModel, TypeAdapter

from backbone.benchmarking import ReviewQuestion, benchmark, export_submission
from backbone.ingestion import ingest
from backbone.models import ClinicalSnapshot
from backbone.query import AnswerBundle, QueryPlanningError, answer_question
from backbone.storage import Store

__all__ = ["ReviewQuestion", "ReviewAnswer", "main"]


class ReviewAnswer(BaseModel):
    id: str
    answer: AnswerBundle


class QueryExecution(BaseModel):
    snapshot_id: int
    question: str
    operation: str
    elapsed_seconds: float
    model_calls: int = 0


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


def read_questions(path: str) -> list[ReviewQuestion]:
    return TypeAdapter(list[ReviewQuestion]).validate_json(Path(path).read_text(encoding="utf-8"))


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
        question_parser.add_argument("--snapshot", type=int)
        question_parser.add_argument("--scenario-budget", type=int, default=10000)
        if command == "ask":
            question_parser.add_argument("--json", action="store_true")
        elif command == "benchmark":
            question_parser.add_argument("--output", default="artifacts/benchmark.json")
            question_parser.add_argument("--repeats", type=int, default=3)
        else:
            question_parser.add_argument("--output", default="artifacts")
    commands.add_parser("status")
    commands.add_parser("rebuild")
    replay = commands.add_parser("replay")
    replay.add_argument("abstraction")
    replay.add_argument("questions")
    replay.add_argument("--output", default=".backbone/replay")
    replay.add_argument("--scenario-budget", type=int, default=10000)
    options = parser.parse_args(namespace=Options())
    if options.command == "replay":
        snapshot = ClinicalSnapshot.model_validate_json(Path(options.abstraction).read_bytes())
        try:
            result = export_submission(
                snapshot,
                read_questions(options.questions),
                Path(options.output),
                options.scenario_budget,
            )
        except QueryPlanningError as error:
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
        snapshot = store.snapshot(options.snapshot)
        try:
            if options.command == "ask":
                started = perf_counter()
                answer = answer_question(options.question, snapshot, options.scenario_budget)
                store.record_run(
                    "query",
                    QueryExecution(
                        snapshot_id=snapshot.snapshot_id,
                        question=options.question,
                        operation=answer.plan.operation,
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
                    snapshot, read_questions(options.questions), output, options.scenario_budget
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
        except QueryPlanningError as error:
            parser.error(str(error))
    elif options.command == "rebuild":
        from backbone.workflow import rebuild_saved

        print(f"Published snapshot {rebuild_saved(store)} from saved evidence; model calls: 0.")
    else:
        print(f"Documents: {store.document_count()}; snapshot: {store.latest_revision()}")
