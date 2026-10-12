from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from importlib.resources import files
from time import perf_counter
from typing import Protocol

from openai import OpenAI, OpenAIError, omit
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
NUMBER_VALUES: dict[str, int] = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
}
NUMBER_SCALES: dict[str, int] = {"thousand": 1000, "million": 1_000_000}
NUMBER_WORDS: str = "|".join((*NUMBER_VALUES, "hundred", *NUMBER_SCALES))
QUANTITY_PATTERN: re.Pattern[str] = re.compile(
    rf"\b(?P<number>\d+(?:,\d{{3}})*(?:\.\d+)?|(?:{NUMBER_WORDS})"
    rf"(?:[\s-]+(?:and|{NUMBER_WORDS}))*)\s*"
    r"(?:(?:patient[- ]present|therapy|treatment|therapeutic|psychotherapy|calendar|distinct)\s+)*"
    r"(?P<unit>days?|minutes?|mins?|hours?|hrs?)\b",
    re.IGNORECASE,
)


class Extractor(Protocol):
    def cache_key(self, document: DocumentRecord) -> str: ...

    def extract(self, document: DocumentRecord) -> ExtractionResult: ...


class ExtractionValidationError(ValueError):
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


def normalize_local_time(value: str, service_date: date) -> str:
    match: re.Match[str] | None = re.fullmatch(
        r"(\d{4}-\d{2}-\d{2})T((?:[01]\d|2[0-3]):[0-5]\d)(?::00)?", value
    )
    if match is None:
        return value
    if match.group(1) != service_date.isoformat():
        raise ExtractionValidationError("Interval datetime date must match the service date.")
    return match.group(2)


def normalize_interval(interval: TimeInterval, service_date: date) -> TimeInterval:
    normalized: TimeInterval = TimeInterval(
        start=normalize_local_time(interval.start, service_date),
        end=normalize_local_time(interval.end, service_date),
    )
    validate_interval(normalized)
    return normalized


def parse_quantity(value: str) -> float:
    if value[0].isdigit():
        return float(value.replace(",", ""))
    total: int = 0
    partial: int = 0
    for token in re.split(r"[\s-]+", value.lower()):
        if token == "and":
            continue
        if token == "hundred":
            partial = (partial or 1) * 100
        elif token in NUMBER_SCALES:
            total += (partial or 1) * NUMBER_SCALES[token]
            partial = 0
        else:
            partial += NUMBER_VALUES[token]
    return float(total + partial)


def source_quantities(quotes: list[str]) -> tuple[set[float], set[float]]:
    days: set[float] = set()
    minutes: set[float] = set()
    for quote in quotes:
        for match in QUANTITY_PATTERN.finditer(quote):
            quantity: float = parse_quantity(match.group("number"))
            unit: str = match.group("unit").lower()
            if unit.startswith("day"):
                days.add(quantity)
            else:
                minutes.add(quantity * 60 if unit.startswith(("hour", "hr")) else quantity)
    return days, minutes


def validate_plan_thresholds(plan: PlanClaim) -> None:
    days: set[float]
    minutes: set[float]
    days, minutes = source_quantities(plan.quotes)
    if plan.minimum_days not in days or plan.minimum_minutes not in minutes:
        raise ExtractionValidationError(
            "Plan thresholds must match explicit day and minute/hour quantities in their quotes. "
            "Omit plan claims when numerical participation requirements are not documented."
        )


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
        contact.intervals = [
            normalize_interval(interval, contact.service_date) for interval in contact.intervals
        ]
        contact.breaks = [
            normalize_interval(interval, contact.service_date) for interval in contact.breaks
        ]
        if contact.stated_minutes is not None and contact.stated_minutes < 0:
            raise ExtractionValidationError("Stated contact minutes cannot be negative.")
        if contact.stated_minutes is not None:
            documented_minutes: set[float] = source_quantities(contact.quotes)[1]
            if contact.stated_minutes not in documented_minutes:
                raise ExtractionValidationError(
                    "stated_minutes must match an explicit quoted duration; "
                    "use null for durations inferred from interval clocks."
                )
    for plan in grounded.plans:
        validate_plan_thresholds(plan)
    return grounded


class OpenAIExtractor:
    def __init__(
        self,
        model: str = "gpt-4.1",
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
        usage: ModelUsage | None = None
        instructions: str = self.prompt
        attempt: int = 0
        while True:
            try:
                response: ParsedResponse[DocumentEvidence] = self.client.responses.parse(
                    model=self.model,
                    instructions=instructions,
                    input=document.text,
                    text_format=DocumentEvidence,
                    temperature=self.temperature if self.temperature is not None else omit,
                    max_output_tokens=self.max_output_tokens,
                    store=False,
                )
            except OpenAIError as error:
                if attempt == 0:
                    raise
                raise ExtractionValidationError(
                    f"Validation retry API request failed: {error}",
                    model=self.model,
                    usage=usage,
                    elapsed_seconds=perf_counter() - started,
                ) from error
            if response.usage is not None:
                cost: float | None = None
                if (
                    self.input_rate_per_million is not None
                    and self.output_rate_per_million is not None
                ):
                    cost = (
                        response.usage.input_tokens * self.input_rate_per_million
                        + response.usage.output_tokens * self.output_rate_per_million
                    ) / 1_000_000
                previous_cost: float | None = usage.cost_usd if usage is not None else 0.0
                usage = ModelUsage(
                    input_tokens=(usage.input_tokens if usage is not None else 0)
                    + response.usage.input_tokens,
                    output_tokens=(usage.output_tokens if usage is not None else 0)
                    + response.usage.output_tokens,
                    cost_usd=previous_cost + cost
                    if cost is not None and previous_cost is not None
                    else None,
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
            if response.usage is None or usage is None:
                raise ExtractionValidationError(
                    "Completed extraction did not report token usage.",
                    model=response.model,
                    usage=usage,
                    elapsed_seconds=perf_counter() - started,
                )
            try:
                evidence: DocumentEvidence = attach_sources(document, parsed)
            except ExtractionValidationError as error:
                if attempt == 0:
                    instructions = (
                        f"{self.prompt}\n\nThe previous extraction failed local validation: "
                        f"{error}\n"
                        "Re-extract the entire record. Copy each quote exactly and contiguously "
                        "from the source. Prefer a short exact sentence or table row. Never "
                        "prepend a heading, label, or author to a later sentence; use separate "
                        "quotes for separated passages. Do not rewrite punctuation or wording. "
                        "Omit plans without explicit numeric goals. Use null for inferred "
                        "stated_minutes. Use HH:MM for local "
                        "interval clocks; any ISO datetime date must match the service date. "
                        "Do not emit source locations or invent event identifiers."
                    )
                    attempt += 1
                    continue
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
