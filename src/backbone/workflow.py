from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from pathlib import Path
from time import perf_counter

from openai import APIError
from pydantic import BaseModel

from backbone.extraction import ExtractionValidationError, Extractor
from backbone.ingestion import ingest
from backbone.models import DocumentRecord, ExtractionResult, IngestionReport
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
    selected_hashes = set(imported.document_hashes)
    for document in store.documents():
        if document.content_hash not in selected_hashes:
            continue
        if store.extraction(extractor.cache_key(document)) is None:
            pending.append(document)
        else:
            cached += 1
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
        snapshot_id=store.snapshot().snapshot_id,
    )
    store.record_run("extraction", report.model_dump_json())
    return report
