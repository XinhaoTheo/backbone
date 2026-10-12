from __future__ import annotations

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv

from backbone.ingestion import ingest
from backbone.storage import Store


class Options(argparse.Namespace):
    command: str
    db: str
    path: str
    model: str
    workers: int


def main() -> None:
    load_dotenv(Path(".env"))
    parser = argparse.ArgumentParser(prog="backbone")
    parser.add_argument("--db", default=os.environ.get("BACKBONE_DB", ".backbone/review.sqlite3"))
    commands = parser.add_subparsers(dest="command", required=True)
    ingestion = commands.add_parser("ingest")
    ingestion.add_argument("path")
    extraction = commands.add_parser("extract")
    extraction.add_argument("path")
    extraction.add_argument("--model", default=os.environ.get("OPENAI_MODEL", "gpt-4.1-mini"))
    extraction.add_argument("--workers", type=int, default=4)
    commands.add_parser("status")
    options = parser.parse_args(namespace=Options())
    store = Store(Path(options.db))
    store.initialize()
    if options.command == "ingest":
        print(ingest(store, Path(options.path)).model_dump_json(indent=2))
    elif options.command == "extract":
        from backbone.extraction import OpenAIExtractor
        from backbone.workflow import extract_documents

        report = extract_documents(
            store, Path(options.path), OpenAIExtractor(options.model), options.workers
        )
        print(report.model_dump_json(indent=2))
    else:
        print(f"Documents: {len(store.documents())}; snapshot: {store.snapshot().snapshot_id}")
