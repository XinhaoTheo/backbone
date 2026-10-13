from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from pydantic import TypeAdapter

from backbone.benchmarking import ReviewQuestion
from backbone.extraction import attach_sources
from backbone.ingestion import read_document
from backbone.models import (
    ContactClaim,
    DocumentEvidence,
    ExtractionResult,
    ModelUsage,
    PatientIdentity,
    PlanClaim,
    PlanGrounding,
    QueryPlan,
    QueryTask,
)
from backbone.reconciliation import patient_key

FIXTURE_DIR = Path(__file__).resolve().parent
ORGANIZATION = "Synthetic Review Clinic"
START = date(2027, 3, 1)
SECOND_WEEK = date(2027, 3, 8)
CHANGE = date(2027, 3, 15)
END = date(2027, 3, 28)


@dataclass(frozen=True)
class PlanSpec:
    identifier: str
    start: date
    end: date
    days: int
    minutes: int


@dataclass(frozen=True)
class ContactSpec:
    document_id: str
    encounter_id: str
    day: date
    minutes: int


@dataclass(frozen=True)
class PatientSpec:
    identity: PatientIdentity
    plans: list[PlanSpec]
    contacts: list[ContactSpec]


def write_fixture(
    identity: PatientIdentity,
    identifier: str,
    body: str,
    contacts: list[ContactClaim],
    plans: list[PlanClaim],
) -> ExtractionResult:
    path = FIXTURE_DIR / "documents" / f"{identifier}.txt"
    header = (
        f"Document ID: {identifier}\n"
        "Data kind: SYNTHETIC authored demonstration; not a supplied clinical record.\n"
        f"Organization: {identity.organization}\n"
        f"Patient: {identity.name}; MRN: {identity.patient_id}\n"
        f"Treatment episode: {identity.episode_start} through {identity.episode_end}.\n"
    )
    path.write_text(header + body + "\n", encoding="utf-8")
    evidence = attach_sources(
        read_document(path),
        DocumentEvidence(
            patients=[identity], contacts=contacts, plans=plans, assessments=[], observations=[]
        ),
        require_field_grounding=True,
    )
    return ExtractionResult(
        evidence=evidence,
        model="synthetic-authored-fixture",
        usage=ModelUsage(cost_usd=0.0),
        elapsed_seconds=0.0,
    )


def plan_fixture(identity: PatientIdentity, spec: PlanSpec) -> ExtractionResult:
    unit = "day" if spec.days == 1 else "days"
    days_quote = f"Minimum distinct treatment days: {spec.days} {unit}."
    minutes_quote = f"Minimum patient-contact time: {spec.minutes} minutes."
    start_quote = f"Plan effective start: {spec.start}."
    end_quote = f"Plan effective end: {spec.end}."
    body = "\n".join(
        [
            f"Final treatment plan for {identity.patient_id}.",
            start_quote,
            end_quote,
            days_quote,
            minutes_quote,
            "Requirements apply to each Monday-Sunday calendar week.",
            "Only individual psychotherapy with the patient present counts toward these goals.",
        ]
    )
    return write_fixture(
        identity,
        spec.identifier,
        body,
        [],
        [
            PlanClaim(
                patient_id=identity.patient_id,
                effective_start=spec.start,
                effective_end=spec.end,
                minimum_days=spec.days,
                minimum_minutes=spec.minutes,
                eligible_services=["individual"],
                week_start="Monday",
                patient_present_required=True,
                note="Synthetic documented weekly participation requirements.",
                quotes=[body],
                grounding=PlanGrounding(
                    minimum_days_quote=days_quote,
                    minimum_minutes_quote=minutes_quote,
                    effective_start_quote=start_quote,
                    effective_end_quote=end_quote,
                ),
            )
        ],
    )


def contact_fixture(identity: PatientIdentity, spec: ContactSpec) -> ExtractionResult:
    duration_quote = f"Patient-present individual psychotherapy duration: {spec.minutes} minutes."
    body = "\n".join(
        [
            f"Final patient-contact note for {identity.patient_id}.",
            f"Encounter ID: {spec.encounter_id}.",
            f"Service date: {spec.day}.",
            "Attendance: attended. Patient present: yes.",
            duration_quote,
            "This is an independently signed final note, not a copy or a correction.",
        ]
    )
    return write_fixture(
        identity,
        spec.document_id,
        body,
        [
            ContactClaim(
                patient_id=identity.patient_id,
                service_date=spec.day,
                encounter_id=spec.encounter_id,
                appointment_id=None,
                service_type="individual",
                attendance="attended",
                patient_present=True,
                intervals=[],
                interval_kind="patient_contact",
                breaks=[],
                stated_minutes=spec.minutes,
                stated_minutes_quote=duration_quote,
                record_status="final",
                correction_fields=[],
                is_copy=False,
                note="Synthetic explicitly documented patient-contact duration.",
                quotes=[body],
            )
        ],
        [],
    )


def patient_specs() -> list[PatientSpec]:
    identities = [
        PatientIdentity(
            patient_id=f"SYN-{name.upper()}",
            name=f"{name} Demo",
            organization=ORGANIZATION,
            episode_start=START,
            episode_end=END if name == "Alex" else date(2027, 3, 14),
        )
        for name in ["Casey", "Morgan", "Alex"]
    ]
    return [
        PatientSpec(
            identities[0],
            [PlanSpec("SYN-CASEY-PLAN", START, date(2027, 3, 14), 1, 150)],
            [
                ContactSpec("SYN-CASEY-W1", "SYN-CASEY-E1", START, 120),
                ContactSpec("SYN-CASEY-W2", "SYN-CASEY-E2", SECOND_WEEK, 130),
            ],
        ),
        PatientSpec(
            identities[1],
            [PlanSpec("SYN-MORGAN-PLAN", START, date(2027, 3, 14), 1, 150)],
            [
                ContactSpec("SYN-MORGAN-W1-A", "SYN-MORGAN-E1", START, 130),
                ContactSpec("SYN-MORGAN-W1-B", "SYN-MORGAN-E1", START, 170),
                ContactSpec("SYN-MORGAN-W2-A", "SYN-MORGAN-E2", SECOND_WEEK, 130),
                ContactSpec("SYN-MORGAN-W2-B", "SYN-MORGAN-E2", SECOND_WEEK, 170),
            ],
        ),
        PatientSpec(
            identities[2],
            [
                PlanSpec("SYN-ALEX-PLAN-OLD", START, date(2027, 3, 14), 1, 100),
                PlanSpec("SYN-ALEX-PLAN-NEW", CHANGE, END, 2, 150),
            ],
            [
                ContactSpec("SYN-ALEX-W1", "SYN-ALEX-E1", START, 100),
                ContactSpec("SYN-ALEX-W2", "SYN-ALEX-E2", SECOND_WEEK, 110),
                ContactSpec("SYN-ALEX-W3", "SYN-ALEX-E3", CHANGE, 120),
                ContactSpec("SYN-ALEX-W4-A", "SYN-ALEX-E4", date(2027, 3, 22), 100),
                ContactSpec("SYN-ALEX-W4-B", "SYN-ALEX-E5", date(2027, 3, 23), 60),
            ],
        ),
    ]


def main() -> None:
    (FIXTURE_DIR / "documents").mkdir(parents=True, exist_ok=True)
    patients = patient_specs()
    results = [
        result
        for patient in patients
        for result in [
            *(plan_fixture(patient.identity, plan) for plan in patient.plans),
            *(contact_fixture(patient.identity, contact) for contact in patient.contacts),
        ]
    ]
    (FIXTURE_DIR / "extractions.jsonl").write_text(
        "".join(result.model_dump_json() + "\n" for result in results), encoding="utf-8"
    )
    identifiers = [patient_key(patient.identity) for patient in patients]
    questions = [
        ReviewQuestion(
            id="SYN-01",
            question="How many therapy sessions, treatment days, and minutes did Casey Demo "
            "receive from March 1 through March 14, 2027?",
        ),
        ReviewQuestion(
            id="SYN-02",
            question="Which patients had two consecutive weeks below their documented treatment "
            "requirements from March 1 through March 28, 2027?",
        ),
        ReviewQuestion(
            id="SYN-03",
            question="Compare Alex Demo's sessions, treatment days, total minutes, and weekly "
            "goal attainment before and after the March 15, 2027 treatment plan change, "
            "using March 1 through March 28, 2027.",
        ),
    ]
    tasks = [
        QueryTask(
            operation="durations", patient=identifiers[0], patient_ids=[identifiers[0]],
            start=START, end=date(2027, 3, 14),
            metrics=["sessions", "distinct_days", "minutes"],
        ),
        QueryTask(
            operation="cohort", patient=None, patient_ids=identifiers,
            start=START, end=END, consecutive_weeks=2,
        ),
        QueryTask(
            operation="plan_change", patient=identifiers[2], patient_ids=[identifiers[2]],
            start=START, end=END, change_date=CHANGE,
            metrics=["sessions", "distinct_days", "minutes"],
        ),
    ]
    plans = [
        QueryPlan(question=question.question, snapshot_id=1, tasks=[task])
        for question, task in zip(questions, tasks, strict=True)
    ]
    (FIXTURE_DIR / "questions.json").write_bytes(
        TypeAdapter(list[ReviewQuestion]).dump_json(questions, indent=2)
    )
    (FIXTURE_DIR / "plans.json").write_bytes(
        TypeAdapter(list[QueryPlan]).dump_json(plans, indent=2)
    )


if __name__ == "__main__":
    main()
