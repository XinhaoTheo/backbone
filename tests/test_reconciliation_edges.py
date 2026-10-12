from datetime import date
from typing import Literal

from backbone.calculation import calculate
from backbone.models import (
    AssessmentClaim,
    ContactClaim,
    DocumentEvidence,
    Observation,
    PatientIdentity,
    PatientRecord,
    PlanClaim,
    RecordStatus,
    ServiceType,
    SourceRef,
    TimeInterval,
)
from backbone.reconciliation import reconcile

IntervalKind = Literal["patient_contact", "patient_presence", "scheduled", "group_activity"]
CorrectionField = Literal["arrival", "departure", "attendance", "duration", "intervals"]


def reference(identifier: str, quote: str) -> SourceRef:
    return SourceRef(
        content_hash=identifier,
        document_id=identifier,
        filename=f"{identifier}.txt",
        start_line=3,
        end_line=3,
        quote=quote,
    )


def contact(
    identifier: str,
    start: str = "10:00",
    end: str = "11:30",
    *,
    kind: IntervalKind = "patient_presence",
    status: RecordStatus = "final",
    service_type: ServiceType = "group",
    service_date: date = date(2026, 1, 19),
    is_copy: bool = False,
    encounter_id: str | None = "E1",
    appointment_id: str | None = "A1",
    correction_fields: list[CorrectionField] | None = None,
) -> ContactClaim:
    source = reference(identifier, f"{identifier}: {kind} from {start} to {end}.")
    return ContactClaim(
        patient_id="P1",
        service_date=service_date,
        encounter_id=encounter_id,
        appointment_id=appointment_id,
        service_type=service_type,
        attendance="attended",
        patient_present=True,
        intervals=[TimeInterval(start=start, end=end)],
        interval_kind=kind,
        breaks=[],
        stated_minutes=None,
        record_status=status,
        correction_fields=correction_fields or [],
        is_copy=is_copy,
        note="Actual patient evidence.",
        quotes=[source.quote],
        sources=[source],
    )


def activity() -> ContactClaim:
    claim = contact("ACTIVITY", kind="group_activity")
    claim.breaks = [TimeInterval(start="10:45", end="11:00")]
    return claim


def patient_for(
    contacts: list[ContactClaim],
    *,
    assessments: list[AssessmentClaim] | None = None,
    observations: list[Observation] | None = None,
) -> PatientRecord:
    plan_source = reference(
        "PLAN", "The weekly goal is one day and 30 patient-present therapy minutes."
    )
    plan = PlanClaim(
        patient_id="P1",
        effective_start=date(2026, 1, 1),
        effective_end=None,
        minimum_days=1,
        minimum_minutes=30,
        eligible_services=["individual", "group", "family"],
        week_start="Monday",
        patient_present_required=True,
        note="Count patient-present psychotherapy.",
        quotes=[plan_source.quote],
        sources=[plan_source],
    )
    evidence = DocumentEvidence(
        patients=[
            PatientIdentity(
                patient_id="P1",
                name="Test Patient",
                organization="Test Clinic",
                episode_start=date(2026, 1, 1),
                episode_end=date(2026, 1, 31),
            )
        ],
        contacts=contacts,
        plans=[plan],
        assessments=assessments or [],
        observations=observations or [],
    )
    return reconcile([evidence])[0]


def test_administrative_actual_roster_complements_final_activity() -> None:
    patient = patient_for([activity(), contact("ROSTER", status="administrative")])
    assert len(patient.encounters) == 1
    alternative = patient.encounters[0].alternatives[0]
    assert alternative.minutes == 75
    assert {source.document_id for source in alternative.sources} == {"ACTIVITY", "ROSTER"}


def test_copy_only_actual_roster_preserves_unique_attendance_evidence() -> None:
    patient = patient_for([activity(), contact("ROSTER_COPY", is_copy=True)])
    assert [option.minutes for option in patient.encounters[0].alternatives] == [75]
    assert {source.document_id for source in patient.encounters[0].alternatives[0].sources} == {
        "ACTIVITY",
        "ROSTER_COPY",
    }


def test_presence_outside_group_activity_does_not_increase_therapy_minutes() -> None:
    patient = patient_for([activity(), contact("ROSTER", "09:50", "11:40")])
    assert [option.minutes for option in patient.encounters[0].alternatives] == [75]
    assert patient.encounters[0].alternatives[0].intervals == [
        TimeInterval(start="10:00", end="11:30")
    ]


def test_same_form_score_and_item_nine_conflicts_remain_one_assessment() -> None:
    original_source = reference("FORM", "Form F1: PHQ-9 score 10, item nine 0.")
    copy_source = reference("FORM_COPY", "Form F1: PHQ-9 score 12, item nine 1.")
    original = AssessmentClaim(
        patient_id="P1",
        completed_date=date(2026, 1, 16),
        instrument="PHQ-9",
        score=10,
        form_id="F1",
        item_nine=0,
        is_copy=False,
        quotes=[original_source.quote],
        sources=[original_source],
    )
    copied = original.model_copy(
        update={
            "score": 12.0,
            "item_nine": 1.0,
            "is_copy": True,
            "quotes": [copy_source.quote],
            "sources": [copy_source],
        }
    )
    patient = patient_for([], assessments=[original, copied])
    assert len(patient.assessments) == 1
    assessment = patient.assessments[0]
    assert assessment.score_alternatives == [10.0, 12.0]
    assert assessment.item_nine_alternatives == [0.0, 1.0]
    assert {source.document_id for source in assessment.sources} == {"FORM", "FORM_COPY"}
    assert original.score_alternatives == []


def test_conflicting_service_dates_keep_one_encounter_and_two_date_interpretations() -> None:
    first = contact("FIRST", "10:00", "10:40", kind="patient_contact", service_type="individual")
    second = contact(
        "SECOND",
        "10:00",
        "10:40",
        kind="patient_contact",
        service_type="individual",
        service_date=date(2026, 1, 20),
    )
    patient = patient_for([first, second])
    assert len(patient.encounters) == 1
    assert {option.service_date for option in patient.encounters[0].alternatives} == {
        date(2026, 1, 19),
        date(2026, 1, 20),
    }
    assert any(
        decision.field == "service_date" and decision.status == "conflicting_evidence"
        for decision in patient.encounters[0].decisions
    )
    metrics = calculate(patient, date(2026, 1, 19), date(2026, 1, 19))
    assert metrics.session_count.values == [0, 1]
    assert metrics.minutes.values == [0, 40]


def test_ineligible_anchor_service_does_not_erase_eligible_interpretation() -> None:
    collateral = contact(
        "COLLATERAL", "10:00", "10:40", kind="patient_contact", service_type="collateral"
    )
    individual = contact(
        "INDIVIDUAL", "10:00", "10:40", kind="patient_contact", service_type="individual"
    )
    patient = patient_for([collateral, individual])
    assert {option.service_type for option in patient.encounters[0].alternatives} == {
        "collateral",
        "individual",
    }
    metrics = calculate(patient, date(2026, 1, 19), date(2026, 1, 19))
    assert metrics.session_count.exact is None
    assert metrics.session_count.values == [0, 1]
    assert metrics.minutes.values == [0, 40]


def test_attendance_departure_correction_does_not_rewrite_contact_assertion() -> None:
    presence = contact("ROSTER", service_type="individual")
    full_contact = contact("CONTACT", kind="patient_contact", service_type="individual")
    correction = contact(
        "CORRECTION",
        "10:00",
        "11:15",
        status="correction",
        service_type="individual",
        correction_fields=["departure"],
    )
    patient = patient_for([presence, full_contact, correction])
    assert {option.minutes for option in patient.encounters[0].alternatives} == {75, 90}
    full = next(option for option in patient.encounters[0].alternatives if option.minutes == 90)
    assert {source.document_id for source in full.sources} == {"CONTACT"}


def test_coupled_arrival_departure_corrections_do_not_create_hybrid_intervals() -> None:
    original = contact("ROSTER", "09:00", "11:30")
    first = contact(
        "CORRECTION_A",
        "10:00",
        "11:00",
        status="correction",
        correction_fields=["arrival", "departure"],
    )
    second = contact(
        "CORRECTION_B",
        "10:15",
        "11:45",
        status="correction",
        correction_fields=["arrival", "departure"],
    )
    patient = patient_for([original, first, second])
    alternatives = patient.encounters[0].alternatives
    assert {option.minutes for option in alternatives} == {60, 90}
    assert {(option.intervals[0].start, option.intervals[0].end) for option in alternatives} == {
        ("10:00", "11:00"),
        ("10:15", "11:45"),
    }
    for option in alternatives:
        assert (
            len(
                {source.document_id for source in option.sources} & {"CORRECTION_A", "CORRECTION_B"}
            )
            == 1
        )


def test_identical_observations_merge_all_source_references() -> None:
    first_source = reference("NOTE_A", "The patient reported uneven sleep.")
    second_source = reference("NOTE_B", "The patient reported uneven sleep.")
    first = Observation(
        patient_id="P1",
        observed_date=date(2026, 1, 19),
        kind="patient_report",
        text="The patient reported uneven sleep.",
        quotes=[first_source.quote],
        sources=[first_source],
    )
    second = first.model_copy(update={"sources": [second_source]})
    patient = patient_for([], observations=[first, second])
    assert len(patient.observations) == 1
    assert {source.document_id for source in patient.observations[0].sources} == {
        "NOTE_A",
        "NOTE_B",
    }


def test_anonymous_same_day_descriptions_do_not_establish_two_contacts() -> None:
    first = contact(
        "NOTE_A",
        "10:00",
        "10:40",
        kind="patient_contact",
        service_type="individual",
        encounter_id=None,
        appointment_id=None,
    )
    second = contact(
        "NOTE_B",
        "10:00",
        "10:40",
        kind="patient_contact",
        service_type="individual",
        encounter_id=None,
        appointment_id=None,
    )
    patient = patient_for([first, second])
    assert all(
        any(
            decision.field == "identity" and decision.status == "missing_evidence"
            for decision in encounter.decisions
        )
        for encounter in patient.encounters
    )
    metrics = calculate(patient, date(2026, 1, 19), date(2026, 1, 19))
    assert metrics.analysis_status == "analysis_incomplete"
    assert metrics.reason == "unresolved_encounter_identity"
    assert metrics.session_count.exact is None
    assert metrics.minutes.exact is None
