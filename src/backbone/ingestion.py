from __future__ import annotations

import hashlib
import re
from pathlib import Path

from backbone.models import DocumentRecord, IngestionReport
from backbone.storage import Store


def read_document(path: Path) -> DocumentRecord:
    content = path.read_bytes()
    text = content.decode("utf-8")
    match = re.search(r"^Document ID:\s*(\S+)", text, re.MULTILINE)
    return DocumentRecord(
        content_hash=hashlib.sha256(content).hexdigest(),
        document_id=match.group(1) if match else path.name,
        filename=path.name,
        text=text,
    )


def ingest(store: Store, path: Path) -> IngestionReport:
    paths = [path] if path.is_file() else sorted(path.rglob("*.txt"))
    added = 0
    hashes: list[str] = []
    for file_path in paths:
        document = read_document(file_path)
        added += int(store.add_document(document))
        hashes.append(document.content_hash)
    return IngestionReport(
        files_seen=len(paths),
        new_documents=added,
        duplicate_documents=len(paths) - added,
        document_hashes=hashes,
    )
