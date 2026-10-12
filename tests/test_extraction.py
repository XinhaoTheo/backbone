from __future__ import annotations

import json
from datetime import date

import httpx2
import pytest
from openai import OpenAI
from pydantic import BaseModel

from backbone.extraction import (
    ExtractionValidationError,
    OpenAIExtractor,
    attach_sources,
    locate_quote,
    source_quantities,
)
from backbone.models import (
    ContactClaim,
    DocumentEvidence,
    DocumentRecord,
    ExtractionResult,
    PatientIdentity,
    PlanClaim,
    SourceRef,
    TimeInterval,
)


@pytest.fixture
def document() -> DocumentRecord:
    return DocumentRecord(
        content_hash="source-hash",
        document_id="TEST-D001",
        filename="visit.txt",
        text=(
            "Document ID: TEST-D001\n"
            "Test clinic | Avery Jordan | MRN TEST-P001\n"
            "Individual psychotherapy | Encounter TEST-E001 | Service date 2030-02-04\n"
            "Actual patient contact: 09:00–09:30, 30 minutes.\n"
            "Record status: Final, signed.\n"
        ),
    )


@pytest.fixture
def evidence(document: DocumentRecord) -> DocumentEvidence:
    return DocumentEvidence(
        patients=[
            PatientIdentity(
                patient_id="TEST-P001",
                name="Avery Jordan",
                organization="Test clinic",
                episode_start=None,
                episode_end=None,
            )
        ],
        contacts=[
            ContactClaim(
                patient_id="TEST-P001",
                service_date=date(2030, 2, 4),
                encounter_id="TEST-E001",
                appointment_id=None,
                service_type="individual",
                attendance="attended",
                patient_present=True,
                intervals=[TimeInterval(start="09:00", end="09:30")],
                interval_kind="patient_contact",
                breaks=[],
                stated_minutes=30,
                record_status="final",
                correction_fields=[],
                is_copy=False,
                note="Actual patient contact is documented.",
                quotes=[document.text.splitlines()[2], document.text.splitlines()[3]],
            )
        ],
        plans=[],
        assessments=[],
        observations=[],
    )


def test_quote_locations_cover_multiline_and_repeated_passages() -> None:
    document: DocumentRecord = DocumentRecord(
        content_hash="hash",
        document_id="TEST-D002",
        filename="repeated.txt",
        text="Header\nFirst line\nSecond line\nOther\nFirst line\nSecond line\n",
    )
    references: list[SourceRef] = locate_quote(document, "First line\nSecond line\n")
    locations: list[tuple[int, int]] = [
        (reference.start_line, reference.end_line) for reference in references
    ]
    assert locations == [(2, 3), (5, 6)]
    assert all(reference.content_hash == "hash" for reference in references)


def test_sources_are_attached_without_mutating_parsed_evidence(
    document: DocumentRecord, evidence: DocumentEvidence
) -> None:
    grounded: DocumentEvidence = attach_sources(document, evidence)
    assert evidence.contacts[0].sources == []
    assert [(source.start_line, source.end_line) for source in grounded.contacts[0].sources] == [
        (3, 3),
        (4, 4),
    ]


def test_quote_validation_rejects_punctuation_normalization(
    document: DocumentRecord, evidence: DocumentEvidence
) -> None:
    evidence.contacts[0].quotes = ["Actual patient contact: 09:00-09:30, 30 minutes."]
    with pytest.raises(ExtractionValidationError, match="not verbatim"):
        attach_sources(document, evidence)


def test_claim_without_quotes_is_rejected(
    document: DocumentRecord, evidence: DocumentEvidence
) -> None:
    evidence.contacts[0].quotes = []
    with pytest.raises(ExtractionValidationError, match="include source quotes"):
        attach_sources(document, evidence)


def test_model_cannot_supply_unverified_source_locations(
    document: DocumentRecord, evidence: DocumentEvidence
) -> None:
    evidence.contacts[0].sources = [
        SourceRef(
            content_hash="made-up-hash",
            document_id="made-up-document",
            filename="made-up.txt",
            start_line=100,
            end_line=100,
            quote=evidence.contacts[0].quotes[0],
        )
    ]
    with pytest.raises(ExtractionValidationError, match="attached locally"):
        attach_sources(document, evidence)


def test_undocumented_event_identity_is_rejected(
    document: DocumentRecord, evidence: DocumentEvidence
) -> None:
    evidence.contacts[0].encounter_id = "INVENTED-EVENT"
    with pytest.raises(ExtractionValidationError, match="identifiers must appear"):
        attach_sources(document, evidence)


@pytest.mark.parametrize("start,end", [("09:70", "10:30"), ("10:30", "09:30")])
def test_invalid_contact_intervals_are_rejected(
    document: DocumentRecord, evidence: DocumentEvidence, start: str, end: str
) -> None:
    evidence.contacts[0].intervals = [TimeInterval(start=start, end=end)]
    with pytest.raises(ExtractionValidationError):
        attach_sources(document, evidence)


def test_service_date_datetimes_are_normalized_without_changing_source_quotes(
    document: DocumentRecord, evidence: DocumentEvidence
) -> None:
    evidence.contacts[0].intervals = [
        TimeInterval(start="2030-02-04T09:00", end="2030-02-04T09:30:00")
    ]
    grounded: DocumentEvidence = attach_sources(document, evidence)
    assert grounded.contacts[0].intervals == [TimeInterval(start="09:00", end="09:30")]
    assert grounded.contacts[0].sources[1].quote == document.text.splitlines()[3]
    assert evidence.contacts[0].intervals[0].start == "2030-02-04T09:00"


def test_datetime_on_another_date_is_rejected(
    document: DocumentRecord, evidence: DocumentEvidence
) -> None:
    evidence.contacts[0].intervals = [
        TimeInterval(start="2030-02-05T09:00", end="2030-02-05T09:30")
    ]
    with pytest.raises(ExtractionValidationError, match="must match the service date"):
        attach_sources(document, evidence)


def participation_plan(quote: str, days: int, minutes: int) -> PlanClaim:
    return PlanClaim(
        patient_id="TEST-P001",
        effective_start=date(2030, 2, 4),
        effective_end=None,
        minimum_days=days,
        minimum_minutes=minutes,
        eligible_services=["individual", "group"],
        week_start="Monday",
        patient_present_required=True,
        note="Documented weekly participation goal.",
        quotes=[quote],
    )


@pytest.mark.parametrize(
    "quote",
    [
        "Each week requires at least 3 therapy days and at least 150 minutes of therapy.",
        "Each week requires three therapy days and one hundred and fifty minutes of therapy.",
        "Each week requires three therapy days and one hundred\nand fifty minutes of therapy.",
        "Each week requires three distinct therapy days and 2.5 hours of therapy.",
        "Each week requires three therapy days and 150 mins of therapy.",
        "Each week requires three therapy days and 2.5 hr of therapy.",
    ],
)
def test_plan_thresholds_require_matching_quantities_and_units(
    document: DocumentRecord, evidence: DocumentEvidence, quote: str
) -> None:
    document.text += quote + "\n"
    evidence.plans = [participation_plan(quote, 3, 150)]
    grounded: DocumentEvidence = attach_sources(document, evidence)
    assert grounded.plans[0].minimum_days == 3
    assert grounded.plans[0].minimum_minutes == 150


def test_generic_plan_cannot_become_zero_participation_requirements(
    document: DocumentRecord, evidence: DocumentEvidence
) -> None:
    quote: str = "Continue scheduled treatment; participation goals will be documented separately."
    document.text += quote + "\n"
    evidence.plans = [participation_plan(quote, 0, 0)]
    with pytest.raises(ExtractionValidationError, match="Omit plan claims"):
        attach_sources(document, evidence)


def test_plan_thresholds_cannot_use_another_number_from_the_record(
    document: DocumentRecord, evidence: DocumentEvidence
) -> None:
    quote: str = "At least three therapy days and one hundred fifty minutes each week."
    document.text += quote + "\n"
    evidence.plans = [participation_plan(quote, 3, 180)]
    with pytest.raises(ExtractionValidationError, match="Plan thresholds must match"):
        attach_sources(document, evidence)


def test_computed_clock_difference_cannot_be_a_stated_duration(
    document: DocumentRecord, evidence: DocumentEvidence
) -> None:
    evidence.contacts[0].quotes[-1] = "Actual patient contact: 09:00–09:30"
    with pytest.raises(ExtractionValidationError, match="explicit quoted duration"):
        attach_sources(document, evidence)


@pytest.mark.parametrize(
    "quote,minutes",
    [("30 min", 30.0), ("30mins", 30.0), ("1 hr", 60.0), ("1.5hrs", 90.0)],
)
def test_conventional_duration_abbreviations_preserve_units(quote: str, minutes: float) -> None:
    assert source_quantities([quote]) == (set(), {minutes})


class FormatRequest(BaseModel):
    type: str
    name: str
    strict: bool


class TextRequest(BaseModel):
    format: FormatRequest


class ExtractionRequest(BaseModel):
    model: str
    instructions: str
    input: str
    temperature: float | None = None
    max_output_tokens: int
    store: bool
    text: TextRequest


def mock_client(
    evidence: DocumentEvidence,
    *,
    refuse: bool = False,
    subsequent_evidence: DocumentEvidence | None = None,
) -> tuple[OpenAI, list[ExtractionRequest]]:
    requests: list[ExtractionRequest] = []

    def respond(request: httpx2.Request) -> httpx2.Response:
        requests.append(ExtractionRequest.model_validate_json(request.content))
        emitted: DocumentEvidence = (
            subsequent_evidence
            if len(requests) > 1 and subsequent_evidence is not None
            else evidence
        )
        excluded: dict[str, dict[str, set[str]]] = {
            category: {"__all__": {"sources"}}
            for category in ("contacts", "plans", "assessments", "observations")
        }
        content: dict[str, object] = (
            {"type": "refusal", "refusal": "Unable to process this record."}
            if refuse
            else {
                "type": "output_text",
                "text": emitted.model_dump_json(exclude=excluded),
                "annotations": [],
            }
        )
        payload: dict[str, object] = {
            "id": "resp_test",
            "object": "response",
            "created_at": 0,
            "model": "test-model-snapshot",
            "status": "completed",
            "output": [
                {
                    "id": "msg_test",
                    "type": "message",
                    "role": "assistant",
                    "status": "completed",
                    "content": [content],
                }
            ],
            "usage": {
                "input_tokens": 100,
                "output_tokens": 50,
                "total_tokens": 150,
                "input_tokens_details": {"cached_tokens": 0, "cache_write_tokens": 0},
                "output_tokens_details": {"reasoning_tokens": 0},
            },
        }
        return httpx2.Response(200, json=payload)

    client: OpenAI = OpenAI(
        api_key="test-key",
        http_client=httpx2.Client(transport=httpx2.MockTransport(respond)),
        max_retries=0,
    )
    return client, requests


def test_sdk_structured_parsing_records_usage_and_local_provenance(
    document: DocumentRecord, evidence: DocumentEvidence
) -> None:
    client: OpenAI
    requests: list[ExtractionRequest]
    client, requests = mock_client(evidence)
    with client:
        extractor: OpenAIExtractor = OpenAIExtractor(
            model="test-model",
            client=client,
            input_rate_per_million=2.0,
            output_rate_per_million=8.0,
        )
        result: ExtractionResult = extractor.extract(document)
    assert requests[0].model == "test-model"
    assert requests[0].input == document.text
    assert requests[0].text.format.type == "json_schema"
    assert requests[0].text.format.name == "DocumentEvidence"
    assert requests[0].text.format.strict
    assert requests[0].temperature == 0.0
    assert not requests[0].store
    assert result.model == "test-model-snapshot"
    assert result.usage.input_tokens == 100
    assert result.usage.output_tokens == 50
    assert result.usage.cost_usd == pytest.approx(0.0006)
    assert result.evidence.contacts[0].sources[1].start_line == 4
    assert result.elapsed_seconds >= 0


def test_cost_is_unavailable_without_configured_rates_and_temperature_can_be_omitted(
    document: DocumentRecord, evidence: DocumentEvidence
) -> None:
    client: OpenAI
    requests: list[ExtractionRequest]
    client, requests = mock_client(evidence)
    with client:
        extractor: OpenAIExtractor = OpenAIExtractor(client=client, temperature=None)
        result: ExtractionResult = extractor.extract(document)
    assert result.usage.cost_usd is None
    assert "temperature" not in requests[0].model_fields_set


def test_refused_response_fails_without_caching_empty_evidence(
    document: DocumentRecord, evidence: DocumentEvidence
) -> None:
    client: OpenAI
    requests: list[ExtractionRequest]
    client, requests = mock_client(evidence, refuse=True)
    with client, pytest.raises(
        ExtractionValidationError, match="completed parsed evidence"
    ) as failure:
        OpenAIExtractor(client=client).extract(document)
    assert failure.value.usage is not None
    assert failure.value.usage.input_tokens == 100


def test_invalid_completed_output_retains_spent_token_usage(
    document: DocumentRecord, evidence: DocumentEvidence
) -> None:
    evidence.contacts[0].quotes = ["An invented quotation."]
    client: OpenAI
    requests: list[ExtractionRequest]
    client, requests = mock_client(evidence)
    with client, pytest.raises(ExtractionValidationError, match="not verbatim") as failure:
        OpenAIExtractor(
            client=client, input_rate_per_million=2.0, output_rate_per_million=8.0
        ).extract(document)
    assert failure.value.model == "test-model-snapshot"
    assert failure.value.elapsed_seconds is not None
    assert failure.value.elapsed_seconds >= 0
    assert failure.value.usage is not None
    assert failure.value.usage.input_tokens == 200
    assert failure.value.usage.output_tokens == 100
    assert failure.value.usage.cost_usd == pytest.approx(0.0012)
    assert len(requests) == 2


def test_quote_validation_retry_recovers_and_counts_both_model_calls(
    document: DocumentRecord, evidence: DocumentEvidence
) -> None:
    invalid: DocumentEvidence = evidence.model_copy(deep=True)
    invalid.contacts[0].quotes = ["Actual patient contact: 09:00-09:30, 30 minutes."]
    client: OpenAI
    requests: list[ExtractionRequest]
    client, requests = mock_client(invalid, subsequent_evidence=evidence)
    with client:
        result: ExtractionResult = OpenAIExtractor(
            client=client, input_rate_per_million=2.0, output_rate_per_million=8.0
        ).extract(document)
    assert len(requests) == 2
    assert "not verbatim" in requests[1].instructions
    assert requests[1].input == document.text
    assert result.evidence.contacts[0].sources[1].quote == document.text.splitlines()[3]
    assert result.usage.input_tokens == 200
    assert result.usage.output_tokens == 100
    assert result.usage.cost_usd == pytest.approx(0.0012)


def test_local_provenance_is_absent_from_extraction_schema() -> None:
    schema: str = json.dumps(DocumentEvidence.model_json_schema())
    assert '"sources"' not in schema
    assert '"SourceRef"' not in schema


def test_cache_key_changes_when_model_prompt_or_generation_settings_change(
    document: DocumentRecord, evidence: DocumentEvidence
) -> None:
    client: OpenAI
    requests: list[ExtractionRequest]
    client, requests = mock_client(evidence)
    with client:
        extractor: OpenAIExtractor = OpenAIExtractor(client=client)
        original_key: str = extractor.cache_key(document)
        assert original_key == extractor.cache_key(document)
        other_model: OpenAIExtractor = OpenAIExtractor(client=client, model="other-model")
        other_model_key: str = other_model.cache_key(document)
        assert original_key != other_model_key
        assert original_key != OpenAIExtractor(client=client, temperature=0.5).cache_key(document)
        extractor.prompt += "\nAdditional extraction instruction."
        assert original_key != extractor.cache_key(document)
    assert requests == []
