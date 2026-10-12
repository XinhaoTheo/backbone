from __future__ import annotations

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, TypeAdapter

from backbone.ingestion import ingest
from backbone.query import AnswerBundle, QueryPlanningError, answer_question
from backbone.storage import Store


class ReviewQuestion(BaseModel):
    id: str
    question: str


class ReviewAnswer(BaseModel):
    id: str
    answer: AnswerBundle


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
    for command in ("ask", "answer-file"):
        question_parser = commands.add_parser(command)
        question_parser.add_argument("question" if command == "ask" else "questions")
        question_parser.add_argument("--snapshot", type=int)
        question_parser.add_argument("--scenario-budget", type=int, default=10000)
        if command == "ask":
            question_parser.add_argument("--json", action="store_true")
        else:
            question_parser.add_argument("--output", default="artifacts")
    commands.add_parser("status")
    commands.add_parser("rebuild")
    options = parser.parse_args(namespace=Options())
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
    elif options.command in {"ask", "answer-file"}:
        snapshot = store.snapshot(options.snapshot)
        try:
            if options.command == "ask":
                answer = answer_question(options.question, snapshot, options.scenario_budget)
                print(answer.model_dump_json(indent=2) if options.json else answer.text)
            else:
                questions = TypeAdapter(list[ReviewQuestion]).validate_json(
                    Path(options.questions).read_text(encoding="utf-8")
                )
                answers = [
                    ReviewAnswer(
                        id=question.id,
                        answer=answer_question(
                            question.question, snapshot, options.scenario_budget
                        ),
                    )
                    for question in questions
                ]
                output = Path(options.output)
                output.mkdir(parents=True, exist_ok=True)
                (output / "answers.json").write_text(
                    TypeAdapter(list[ReviewAnswer]).dump_json(answers, indent=2).decode(),
                    encoding="utf-8",
                )
                (output / "answers.md").write_text(
                    "\n\n".join(f"## {answer.id}\n\n{answer.answer.text}" for answer in answers)
                    + "\n",
                    encoding="utf-8",
                )
                print(f"Saved {len(answers)} answers to {output}.")
        except QueryPlanningError as error:
            parser.error(str(error))
    elif options.command == "rebuild":
        from backbone.workflow import rebuild_saved

        print(f"Published snapshot {rebuild_saved(store)} from saved evidence; model calls: 0.")
    else:
        print(f"Documents: {store.document_count()}; snapshot: {store.latest_revision()}")
