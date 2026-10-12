from datetime import date

from backbone.calculation import calculate
from backbone.models import (
    ContactClaim,
    DocumentEvidence,
    PatientIdentity,
    PlanClaim,
    SourceRef,
    TimeInterval,
)
from backbone.reconciliation import delivered_minutes, reconcile


def claim(
    document_id: str, start: str, end: str, *, copy: bool = False, correction: bool = False
) -> ContactClaim:
    return ContactClaim(
        patient_id="P1",
        service_date=date(2026, 1, 19),
        encounter_id="E1",
        appointment_id="A1",
        service_type="group",
        attendance="attended",
        patient_present=True,
        intervals=[TimeInterval(start=start, end=end)],
        interval_kind="patient_presence",
        breaks=[],
        stated_minutes=None,
        record_status="correction" if correction else "final",
        correction_fields=["departure"] if correction else [],
        is_copy=copy,
        note="",
        quotes=[document_id],
        sources=[
            SourceRef(
                content_hash=document_id,
                document_id=document_id,
                filename=document_id,
                start_line=1,
                end_line=1,
                quote=document_id,
            )
        ],
    )


def evidence(contacts: list[ContactClaim]) -> DocumentEvidence:
    return DocumentEvidence(
        patients=[
            PatientIdentity(
                patient_id="P1",
                name="Test Patient",
                organization="Test Clinic",
                episode_start=date(2026, 1, 1),
                episode_end=date(2026, 1, 30),
            )
        ],
        contacts=contacts,
        plans=[],
        assessments=[],
        observations=[],
    )


def test_scoped_correction_survives_later_copy() -> None:
    original = claim("original", "10:00", "11:30")
    update = claim("correction", "10:00", "11:15", correction=True)
    resend = claim("resend", "10:00", "11:30", copy=True)
    activity = claim("activity", "10:00", "11:30")
    activity.interval_kind = "group_activity"
    activity.breaks = [TimeInterval(start="10:45", end="11:00")]
    patient = reconcile([evidence([original, update, resend, activity])])[0]
    assert len(patient.encounters) == 1
    assert patient.encounters[0].alternatives[0].minutes == 60
    assert {source.document_id for source in patient.encounters[0].sources} == {
        "original",
        "correction",
        "resend",
        "activity",
    }


def test_full_contact_conflict_is_not_clinician_time_or_two_visits() -> None:
    first = claim("first", "09:00", "09:50")
    second = claim("second", "09:10", "09:50")
    first.service_type = second.service_type = "individual"
    first.interval_kind = second.interval_kind = "patient_contact"
    patient = reconcile([evidence([first, second])])[0]
    assert len(patient.encounters) == 1
    assert [option.minutes for option in patient.encounters[0].alternatives] == [40, 50]
    assert patient.encounters[0].decisions[-1].status == "conflicting_evidence"


def test_signed_no_show_overrides_unattested_draft() -> None:
    draft = claim("draft", "10:00", "11:30")
    draft.record_status = "draft"
    draft.interval_kind = "scheduled"
    roster = claim("roster", "10:00", "11:30")
    roster.attendance = "no_show"
    roster.patient_present = False
    roster.intervals = []
    patient = reconcile([evidence([draft, roster])])[0]
    assert patient.encounters[0].attendance == "no_show"
    assert patient.encounters[0].alternatives[0].minutes == 0


def test_disconnected_segments_and_overlapping_breaks() -> None:
    intervals = [TimeInterval(start="13:00", end="13:20"), TimeInterval(start="13:30", end="13:55")]
    assert delivered_minutes(intervals, []) == 45
    intervals = [TimeInterval(start="10:15", end="11:15")]
    breaks = [TimeInterval(start="10:45", end="11:00"), TimeInterval(start="10:50", end="11:05")]
    assert delivered_minutes(intervals, breaks) == 40


def test_conflicting_group_activity_breaks_remain_separate_interpretations() -> None:
    presence = claim("attendance", "10:00", "11:30")
    first = claim("activity-a", "10:00", "11:30")
    first.interval_kind = "group_activity"
    first.breaks = [TimeInterval(start="10:30", end="10:45")]
    second = claim("activity-b", "10:00", "11:30")
    second.interval_kind = "group_activity"
    second.breaks = [TimeInterval(start="10:30", end="11:00")]
    encounter = reconcile([evidence([presence, first, second])])[0].encounters[0]
    assert [alternative.minutes for alternative in encounter.alternatives] == [60, 75]
    assert {source.document_id for source in encounter.alternatives[0].sources} == {
        "attendance",
        "activity-b",
    }
    assert encounter.decisions[-1].status == "conflicting_evidence"


def test_anonymous_description_may_duplicate_a_known_encounter() -> None:
    known = claim("known", "10:00", "11:30")
    anonymous = claim("unidentified", "10:00", "11:30")
    anonymous.encounter_id = None
    anonymous.appointment_id = None
    encounters = reconcile([evidence([known, anonymous])])[0].encounters
    assert all(
        any(decision.field == "identity" for decision in encounter.decisions)
        for encounter in encounters
    )


def test_signed_attendance_complements_timed_note_with_unspecified_attendance() -> None:
    clinical = claim("contact-note", "10:00", "10:40")
    clinical.interval_kind = "patient_contact"
    clinical.service_type = "individual"
    clinical.attendance = "unknown"
    roster = claim("attested-roster", "10:00", "10:40")
    roster.service_type = "individual"
    record = reconcile([evidence([clinical, roster])])[0]
    assert record.encounters[0].attendance == "attended"
    record.plans = [PlanClaim(
        patient_id=record.patient_id, effective_start=date(2026, 1, 1), effective_end=None,
        minimum_days=1, minimum_minutes=30, eligible_services=["individual"],
        week_start="Monday", patient_present_required=True,
        note="Patient-present individual therapy.", quotes=["attested-roster"],
        sources=roster.sources,
    )]
    metrics = calculate(record, date(2026, 1, 19), date(2026, 1, 25))
    assert metrics.session_count.exact == 1
    assert metrics.minutes.exact == 40
    assert metrics.weeks[0].decision == "met"
