from __future__ import annotations

import hashlib
import json
import re
from importlib.resources import files
from time import perf_counter
from typing import Protocol

from openai import OpenAI, omit
from openai.types.responses import ParsedResponse

from backbone.models import (
    AssessmentClaim,
    ContactClaim,
    DocumentEvidence,
    DocumentRecord,
    Evidence,
    ExtractionResult,
    ModelUsage,
    Observation,
    PlanClaim,
    SourceRef,
    TimeInterval,
)

EXTRACTION_VERSION: str = "1"


class Extractor(Protocol):
    def cache_key(self, document: DocumentRecord) -> str: ...

    def extract(self, document: DocumentRecord) -> ExtractionResult: ...


class ExtractionValidationError(ValueError):
    """The extracted evidence cannot be grounded in the supplied source."""

    def __init__(
        self,
        message: str,
        *,
        model: str | None = None,
        usage: ModelUsage | None = None,
        elapsed_seconds: float | None = None,
    ) -> None:
        super().__init__(message)
        self.model: str | None = model
        self.usage: ModelUsage | None = usage
        self.elapsed_seconds: float | None = elapsed_seconds


def evidence_claims(evidence: DocumentEvidence) -> list[Evidence]:
    claims: list[Evidence] = []
    claims.extend(evidence.contacts)
    claims.extend(evidence.plans)
    claims.extend(evidence.assessments)
    claims.extend(evidence.observations)
    return claims


def locate_quote(document: DocumentRecord, quote: str) -> list[SourceRef]:
    if not quote.strip():
        raise ExtractionValidationError("Evidence quotes must contain source text.")
    references: list[SourceRef] = []
    offset: int = 0
    while True:
        start: int = document.text.find(quote, offset)
        if start < 0:
            break
        end: int = start + len(quote)
        references.append(
            SourceRef(
                content_hash=document.content_hash,
                document_id=document.document_id,
                filename=document.filename,
                start_line=document.text.count("\n", 0, start) + 1,
                end_line=document.text.count("\n", 0, end - 1) + 1,
                quote=quote,
            )
        )
        offset = end
    if not references:
        raise ExtractionValidationError(
            f"{document.document_id}: quoted evidence is not verbatim: {quote[:120]!r}"
        )
    return references


def validate_interval(interval: TimeInterval) -> None:
    for value in (interval.start, interval.end):
        if re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", value) is None:
            raise ExtractionValidationError(f"Invalid local time: {value!r}; expected HH:MM.")
    if interval.end <= interval.start:
        raise ExtractionValidationError("Contact intervals must end after they start.")


def attach_sources(document: DocumentRecord, evidence: DocumentEvidence) -> DocumentEvidence:
    grounded: DocumentEvidence = evidence.model_copy(deep=True)
    patient_ids: set[str] = {patient.patient_id for patient in grounded.patients}
    for claim in evidence_claims(grounded):
        if not claim.quotes:
            raise ExtractionValidationError("Every evidence claim must include source quotes.")
        if claim.sources:
            raise ExtractionValidationError("Source locations must be attached locally.")
        claim.sources = [
            reference for quote in claim.quotes for reference in locate_quote(document, quote)
        ]
    patient_claims: tuple[ContactClaim | PlanClaim | AssessmentClaim | Observation, ...] = (
        *grounded.contacts,
        *grounded.plans,
        *grounded.assessments,
        *grounded.observations,
    )
    for patient_claim in patient_claims:
        if patient_claim.patient_id not in patient_ids:
            raise ExtractionValidationError("Every claim must identify a listed patient.")
        if patient_claim.patient_id not in document.text:
            raise ExtractionValidationError("Patient identifiers must appear in the source.")
    for contact in grounded.contacts:
        for identifier in (contact.encounter_id, contact.appointment_id):
            if identifier is not None and identifier not in document.text:
                raise ExtractionValidationError("Clinical event identifiers must appear in source.")
        for interval in (*contact.intervals, *contact.breaks):
            validate_interval(interval)
        if contact.stated_minutes is not None and contact.stated_minutes < 0:
            raise ExtractionValidationError("Stated contact minutes cannot be negative.")
    return grounded


class OpenAIExtractor:
    def __init__(
        self,
        model: str = "gpt-4.1-mini",
        *,
        client: OpenAI | None = None,
        input_rate_per_million: float | None = None,
        output_rate_per_million: float | None = None,
        temperature: float | None = 0.0,
        max_output_tokens: int = 12000,
    ) -> None:
        self.model: str = model
        self.client: OpenAI = client if client is not None else OpenAI(timeout=90.0)
        self.input_rate_per_million: float | None = input_rate_per_million
        self.output_rate_per_million: float | None = output_rate_per_million
        self.temperature: float | None = temperature
        self.max_output_tokens: int = max_output_tokens
        self.prompt: str = files("backbone").joinpath("extraction_prompt.txt").read_text("utf-8")

    def cache_key(self, document: DocumentRecord) -> str:
        settings: list[str | float | int | None] = [
            EXTRACTION_VERSION,
            document.content_hash,
            self.model,
            self.temperature,
            self.max_output_tokens,
            self.input_rate_per_million,
            self.output_rate_per_million,
            self.prompt,
            json.dumps(DocumentEvidence.model_json_schema(), sort_keys=True),
        ]
        return hashlib.sha256(json.dumps(settings, ensure_ascii=False).encode("utf-8")).hexdigest()

    def extract(self, document: DocumentRecord) -> ExtractionResult:
        started: float = perf_counter()
        response: ParsedResponse[DocumentEvidence] = self.client.responses.parse(
            model=self.model,
            instructions=self.prompt,
            input=document.text,
            text_format=DocumentEvidence,
            temperature=self.temperature if self.temperature is not None else omit,
            max_output_tokens=self.max_output_tokens,
            store=False,
        )
        usage: ModelUsage | None = None
        cost: float | None = None
        if response.usage is not None:
            if self.input_rate_per_million is not None and self.output_rate_per_million is not None:
                cost = (
                    response.usage.input_tokens * self.input_rate_per_million
                    + response.usage.output_tokens * self.output_rate_per_million
                ) / 1_000_000
            usage = ModelUsage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                cost_usd=cost,
            )
        parsed: DocumentEvidence | None = response.output_parsed
        if response.status != "completed" or parsed is None:
            raise ExtractionValidationError(
                f"{document.document_id}: model response did not contain "
                "completed parsed evidence.",
                model=response.model,
                usage=usage,
                elapsed_seconds=perf_counter() - started,
            )
        if usage is None:
            raise ExtractionValidationError(
                "Completed extraction did not report token usage.",
                model=response.model,
                elapsed_seconds=perf_counter() - started,
            )
        try:
            evidence: DocumentEvidence = attach_sources(document, parsed)
        except ExtractionValidationError as error:
            raise ExtractionValidationError(
                str(error),
                model=response.model,
                usage=usage,
                elapsed_seconds=perf_counter() - started,
            ) from error
        return ExtractionResult(
            evidence=evidence,
            model=response.model,
            usage=usage,
            elapsed_seconds=perf_counter() - started,
        )
