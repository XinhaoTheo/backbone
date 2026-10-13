from __future__ import annotations

import hashlib
from pathlib import Path
from shutil import copyfile
from typing import Literal

from pydantic import BaseModel, TypeAdapter

from backbone.benchmarking import ReviewQuestion, SubmissionExport, export_submission
from backbone.extraction import ExtractionValidationError, attach_sources, evidence_claims
from backbone.models import DocumentRecord, ExtractionResult, QueryPlan
from backbone.storage import Store
from backbone.workflow import ProcessingReport, process_documents


class DemoReport(BaseModel):
    data_kind: Literal["synthetic"] = "synthetic"
    extraction_kind: Literal["authored_fixture"] = "authored_fixture"
    planning_kind: Literal["authored_saved_plans"] = "authored_saved_plans"
    model_calls: int = 0
    database_path: Path
    patient_count: int
    document_count: int
    processing: ProcessingReport
    export: SubmissionExport


class SyntheticFixtureExtractor:
    def __init__(self, fixture_path: Path) -> None:
        self.results: dict[str, ExtractionResult] = {}
        for line in fixture_path.read_text(encoding="utf-8").splitlines():
            result = ExtractionResult.model_validate_json(line)
            hashes = {
                source.content_hash
                for claim in evidence_claims(result.evidence)
                for source in claim.sources
            }
            if len(hashes) != 1:
                raise ExtractionValidationError(
                    "Each synthetic extraction fixture must identify exactly one document."
                )
            content_hash = next(iter(hashes))
            if content_hash in self.results:
                raise ExtractionValidationError(
                    "Synthetic extraction document hashes must be unique."
                )
            self.results[content_hash] = result

    def cache_key(self, document: DocumentRecord) -> str:
        fixture_hash = hashlib.sha256(
            self.results[document.content_hash].model_dump_json().encode("utf-8")
        ).hexdigest()
        return f"synthetic-demo-v1:{document.content_hash}:{fixture_hash}"

    def extract(self, document: DocumentRecord) -> ExtractionResult:
        result = self.results[document.content_hash].model_copy(deep=True)
        for claim in evidence_claims(result.evidence):
            claim.sources = []
        result.evidence = attach_sources(document, result.evidence, require_field_grounding=True)
        return result


def build_demo(output_dir: Path, fixture_dir: Path = Path("demo")) -> DemoReport:
    questions = TypeAdapter(list[ReviewQuestion]).validate_json(
        (fixture_dir / "questions.json").read_bytes()
    )
    plans = TypeAdapter(list[QueryPlan]).validate_json((fixture_dir / "plans.json").read_bytes())
    extractor = SyntheticFixtureExtractor(fixture_dir / "extractions.jsonl")
    document_dir = output_dir / "documents"
    document_dir.mkdir(parents=True, exist_ok=True)
    for path in sorted((fixture_dir / "documents").glob("*.txt")):
        copyfile(path, document_dir / path.name)
    database_path = output_dir / "review.sqlite3"
    store = Store(database_path)
    store.initialize()
    if any(document.content_hash not in extractor.results for document in store.documents()):
        raise ValueError(
            "Use a separate output directory; this database contains non-demo records."
        )
    processing = process_documents(store, document_dir, extractor, workers=1)
    if processing.failed_documents:
        raise ExtractionValidationError("Synthetic demo fixture processing failed.")
    snapshot = store.snapshot()
    for plan in plans:
        plan.snapshot_id = snapshot.snapshot_id
    export = export_submission(snapshot, questions, output_dir, plans=plans)
    (output_dir / "questions.json").write_bytes(
        TypeAdapter(list[ReviewQuestion]).dump_json(questions, indent=2)
    )
    (output_dir / "extractions.jsonl").write_text(
        "".join(result.model_dump_json() + "\n" for result in store.extraction_results()),
        encoding="utf-8",
    )
    (output_dir / "execution.jsonl").write_text(
        "".join(record.model_dump_json() + "\n" for record in store.execution_records()),
        encoding="utf-8",
    )
    report = DemoReport(
        database_path=database_path,
        patient_count=len(snapshot.patients),
        document_count=len(store.documents()),
        processing=processing,
        export=export,
    )
    (output_dir / "demo-report.json").write_text(
        report.model_dump_json(indent=2) + "\n", encoding="utf-8"
    )
    return report
