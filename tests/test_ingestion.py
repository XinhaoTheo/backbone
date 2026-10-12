from pathlib import Path

from backbone.ingestion import ingest
from backbone.storage import Store


def test_duplicate_import_and_restart(tmp_path: Path) -> None:
    source = tmp_path / "input"
    source.mkdir()
    (source / "note.txt").write_text("Document ID: T1\nActual contact.\n", encoding="utf-8")
    (source / "copy.txt").write_text("Document ID: T1\nActual contact.\n", encoding="utf-8")
    store = Store(tmp_path / "review.sqlite3")
    store.initialize()
    first = ingest(store, source)
    assert first.new_documents == 1
    assert first.duplicate_documents == 1
    restarted = Store(store.path)
    second = ingest(restarted, source)
    assert second.new_documents == 0
    assert len(restarted.documents()) == 1
    assert restarted.documents()[0].text == "Document ID: T1\nActual contact.\n"
