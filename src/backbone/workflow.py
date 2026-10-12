from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from pathlib import Path
from time import perf_counter

from openai import APIError
from pydantic import BaseModel

from backbone.extraction import ExtractionValidationError, Extractor
from backbone.ingestion import ingest
from backbone.models import DocumentRecord, ExtractionResult, IngestionReport
from backbone.reconciliation import RECONCILIATION_VERSION, patient_key, reconcile
from backbone.storage import Store


class ProcessingReport(BaseModel):
    ingestion: IngestionReport
    extracted_documents: int
    cached_documents: int
    failed_documents: dict[str, str]
    input_tokens: int
    output_tokens: int
    usage_incomplete: bool = False
    estimated_cost_usd: float | None
    elapsed_seconds: float
    snapshot_id: int


def extract_documents(
    store: Store, path: Path, extractor: Extractor, workers: int
) -> ProcessingReport:
    started = perf_counter()
    imported = ingest(store, path)
    pending: list[DocumentRecord] = []
    cached = 0
    extracted = 0
    input_tokens = 0
    output_tokens = 0
    costs: list[float | None] = []
    failures: dict[str, str] = {}
    usage_incomplete = False
    for document in store.documents(imported.document_hashes):
        if store.extraction(extractor.cache_key(document)) is None:
            pending.append(document)
        else:
            cached += 1
            store.clear_failure(document.content_hash)
    with ThreadPoolExecutor(max_workers=workers) as executor:
        jobs: dict[Future[ExtractionResult], DocumentRecord] = {
            executor.submit(extractor.extract, document): document for document in pending
        }
        for future in as_completed(jobs):
            document = jobs[future]
            try:
                result = future.result()
            except (APIError, ExtractionValidationError) as error:
                failures[document.document_id] = str(error)
                store.save_failure(document.content_hash, str(error))
                if isinstance(error, ExtractionValidationError) and error.usage is not None:
                    input_tokens += error.usage.input_tokens
                    output_tokens += error.usage.output_tokens
                    costs.append(error.usage.cost_usd)
                else:
                    usage_incomplete = True
                continue
            store.save_extraction(document.content_hash, extractor.cache_key(document), result)
            extracted += 1
            input_tokens += result.usage.input_tokens
            output_tokens += result.usage.output_tokens
            costs.append(result.usage.cost_usd)
    report = ProcessingReport(
        ingestion=imported,
        extracted_documents=extracted,
        cached_documents=cached,
        failed_documents=failures,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        usage_incomplete=usage_incomplete,
        estimated_cost_usd=sum(cost for cost in costs if cost is not None)
        if costs and all(cost is not None for cost in costs)
        else None,
        elapsed_seconds=perf_counter() - started,
        snapshot_id=store.latest_revision(),
    )
    store.record_run("extraction", report.model_dump_json())
    return report


def rebuild_saved(store: Store) -> int:
    base_revision = store.latest_revision()
    patients = reconcile(list(store.active_evidence().values()))
    removed = {patient.patient_id for patient in store.snapshot().patients} - {
        patient.patient_id for patient in patients
    }
    revision = store.publish(
        patients,
        {},
        expected_revision=base_revision,
        removed_patients=removed,
        reconciliation_version=RECONCILIATION_VERSION,
    )
    store.record_run("rebuild", f'{{"snapshot_id": {revision}, "model_calls": 0}}')
    return revision


def process_documents(
    store: Store, path: Path, extractor: Extractor, workers: int
) -> ProcessingReport:
    started = perf_counter()
    base_revision = store.latest_revision()
    report = extract_documents(store, path, extractor, workers)
    if report.failed_documents:
        return report
    selected = store.documents(report.ingestion.document_hashes)
    current_keys = store.active_keys(report.ingestion.document_hashes)
    keys: dict[str, str] = {}
    updates: dict[str, ExtractionResult] = {}
    links: dict[str, set[str]] = {}
    for document in selected:
        key = extractor.cache_key(document)
        if current_keys.get(document.content_hash) == key:
            continue
        result = store.extraction(key)
        assert result is not None
        updates[document.content_hash] = result
        keys[document.content_hash] = key
        links[document.content_hash] = {
            patient_key(patient) for patient in result.evidence.patients
        }
    rebuild = store.reconciliation_version() != RECONCILIATION_VERSION
    if not updates and not rebuild:
        return report
    affected = store.linked_patients(list(updates)) | set().union(*links.values())
    if rebuild:
        evidences = store.active_evidence()
        affected |= {patient.patient_id for patient in store.snapshot().patients}
        affected |= {
            patient_key(patient) for evidence in evidences.values() for patient in evidence.patients
        }
    else:
        evidences = store.evidence_for_patients(affected)
    evidences.update({content_hash: result.evidence for content_hash, result in updates.items()})
    patients = [
        patient for patient in reconcile(list(evidences.values())) if patient.patient_id in affected
    ]
    report.snapshot_id = store.publish(
        patients,
        keys,
        expected_revision=base_revision,
        removed_patients=affected - {patient.patient_id for patient in patients},
        document_patients=links,
        reconciliation_version=RECONCILIATION_VERSION,
    )
    report.elapsed_seconds = perf_counter() - started
    store.record_run("publication", report.model_dump_json())
    return report
