from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field
from pydantic.json_schema import SkipJsonSchema

ServiceType = Literal[
    "individual", "group", "family", "medication", "collateral", "coordination", "other"
]
Attendance = Literal["attended", "no_show", "cancelled", "unknown"]
RecordStatus = Literal["final", "draft", "administrative", "correction"]


class SourceRef(BaseModel):
    content_hash: str
    document_id: str
    filename: str
    start_line: int
    end_line: int
    quote: str


class DocumentRecord(BaseModel):
    content_hash: str
    document_id: str
    filename: str
    text: str


class Evidence(BaseModel):
    quotes: list[str]
    sources: SkipJsonSchema[list[SourceRef]] = Field(default_factory=list)


class PatientIdentity(BaseModel):
    patient_id: str
    name: str
    organization: str
    episode_start: date | None
    episode_end: date | None


class TimeInterval(BaseModel):
    start: str
    end: str


class ContactClaim(Evidence):
    patient_id: str
    service_date: date
    encounter_id: str | None
    appointment_id: str | None
    service_type: ServiceType
    attendance: Attendance
    patient_present: bool | None
    intervals: list[TimeInterval]
    interval_kind: Literal["patient_contact", "patient_presence", "scheduled", "group_activity"]
    breaks: list[TimeInterval]
    stated_minutes: int | None
    record_status: RecordStatus
    correction_fields: list[Literal["arrival", "departure", "attendance", "duration", "intervals"]]
    is_copy: bool
    note: str


class PlanClaim(Evidence):
    patient_id: str
    effective_start: date
    effective_end: date | None
    minimum_days: int
    minimum_minutes: int
    eligible_services: list[ServiceType]
    week_start: Literal["Monday"]
    patient_present_required: bool
    note: str


class AssessmentClaim(Evidence):
    patient_id: str
    completed_date: date
    instrument: str
    score: float
    form_id: str | None
    item_nine: float | None
    is_copy: bool
    score_alternatives: SkipJsonSchema[list[float]] = Field(default_factory=list)
    item_nine_alternatives: SkipJsonSchema[list[float]] = Field(default_factory=list)


class Observation(Evidence):
    patient_id: str
    observed_date: date
    kind: Literal[
        "patient_report", "clinician_observation", "collateral_report", "reason_for_contact"
    ]
    text: str


class DocumentEvidence(BaseModel):
    patients: list[PatientIdentity]
    contacts: list[ContactClaim]
    plans: list[PlanClaim]
    assessments: list[AssessmentClaim]
    observations: list[Observation]


class Decision(BaseModel):
    field: str
    status: Literal["established", "conflicting_evidence", "missing_evidence"]
    reason: str
    sources: list[SourceRef]


class ContactAlternative(BaseModel):
    minutes: int | None
    intervals: list[TimeInterval]
    sources: list[SourceRef]
    choices: dict[str, str] = Field(default_factory=dict)
    service_date: date | None = None
    service_type: ServiceType | None = None
    attendance: Attendance | None = None
    patient_present: bool | None = None


class Encounter(BaseModel):
    encounter_id: str
    patient_id: str
    service_date: date
    service_type: ServiceType
    attendance: Attendance
    patient_present: bool | None
    alternatives: list[ContactAlternative]
    decisions: list[Decision]
    sources: list[SourceRef]


class PatientRecord(BaseModel):
    patient_id: str
    name: str
    organization: str
    episode_start: date | None
    episode_end: date | None
    encounters: list[Encounter]
    plans: list[PlanClaim]
    assessments: list[AssessmentClaim]
    observations: list[Observation]


class ClinicalSnapshot(BaseModel):
    snapshot_id: int
    patients: list[PatientRecord]
    failed_documents: list[str] = Field(default_factory=list)


class ModelUsage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float | None = None


class ExtractionResult(BaseModel):
    evidence: DocumentEvidence
    model: str
    usage: ModelUsage
    elapsed_seconds: float


class IngestionReport(BaseModel):
    files_seen: int
    new_documents: int
    duplicate_documents: int
    document_hashes: list[str]


class QueryPlan(BaseModel):
    operation: Literal[
        "counts", "durations", "weekly", "day", "timeline", "symptoms", "cohort", "plan_change"
    ]
    patient: str | None
    start: date | None
    end: date | None
    change_date: date | None = None
    selected_dates: list[date] = Field(default_factory=list)
