from dataclasses import dataclass
from pathlib import Path

from backbone.models import DocumentEvidence, DocumentRecord, ExtractionResult, ModelUsage
from backbone.storage import Store
from backbone.workflow import extract_documents


@dataclass
class FakeExtractor:
    calls: int = 0

    def cache_key(self, document: DocumentRecord) -> str:
        return f"test:{document.content_hash}"

    def extract(self, document: DocumentRecord) -> ExtractionResult:
        self.calls += 1
        return ExtractionResult(
            evidence=DocumentEvidence(
                patients=[], contacts=[], plans=[], assessments=[], observations=[]
            ),
            model="test",
            usage=ModelUsage(input_tokens=2, output_tokens=3, cost_usd=0.01),
            elapsed_seconds=0.0,
        )


def test_persisted_extraction_cache_avoids_new_model_calls(tmp_path: Path) -> None:
    source = tmp_path / "administrative.txt"
    source.write_text("Document ID: A1\nNo clinical information.\n", encoding="utf-8")
    store = Store(tmp_path / "review.sqlite3")
    store.initialize()
    extractor = FakeExtractor()
    first = extract_documents(store, source, extractor, workers=1)
    assert first.extracted_documents == 1
    assert first.input_tokens == 2
    assert first.estimated_cost_usd == 0.01
    restarted = Store(store.path)
    second = extract_documents(restarted, source, extractor, workers=1)
    assert second.cached_documents == 1
    assert second.extracted_documents == 0
    assert second.input_tokens == 0
    assert extractor.calls == 1
