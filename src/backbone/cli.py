from __future__ import annotations

import argparse
from pathlib import Path

from backbone.ingestion import ingest
from backbone.storage import Store


class Options(argparse.Namespace):
    command: str
    db: str
    path: str


def main() -> None:
    parser = argparse.ArgumentParser(prog="backbone")
    parser.add_argument("--db", default=".backbone/review.sqlite3")
    commands = parser.add_subparsers(dest="command", required=True)
    ingestion = commands.add_parser("ingest")
    ingestion.add_argument("path")
    commands.add_parser("status")
    options = parser.parse_args(namespace=Options())
    store = Store(Path(options.db))
    store.initialize()
    if options.command == "ingest":
        print(ingest(store, Path(options.path)).model_dump_json(indent=2))
    else:
        print(f"Documents: {len(store.documents())}; snapshot: {store.snapshot().snapshot_id}")
