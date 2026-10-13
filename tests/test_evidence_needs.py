from datetime import date

from backbone.models import (
    AssessmentClaim,
    ClinicalSnapshot,
    ContactAlternative,
    Decision,
    Encounter,
    Observation,
    PatientRecord,
    PlanClaim,
    QueryMetric,
    QueryOperation,
    QueryPlan,
    QueryTask,
    SourceRef,
)
from backbone.query import AnswerBundle, answer_question


def source(identifier: str, quote: str) -> SourceRef:
    return SourceRef(
        content_hash=identifier,
        document_id=identifier,
        filename=f"{identifier}.txt",
        start_line=7,
        end_line=7,
        quote=quote,
    )


def synthetic_patient() -> PatientRecord:
    plan_source = source("PLAN", "Weekly goal: one day and 45 patient-present therapy minutes.")
    duration_sources = [
        source("D40", "E115 on January 26: actual patient contact was 40 minutes."),
        source("D50", "E115 on January 26: actual patient contact was 50 minutes."),
    ]
    return PatientRecord(
        patient_id="P1",
        name="Synthetic Casey",
        organization="Synthetic clinic",
        episode_start=date(2026, 1, 19),
        episode_end=date(2026, 2, 1),
        encounters=[
            Encounter(
                encounter_id="E115",
                patient_id="P1",
                service_date=date(2026, 1, 26),
                service_type="individual",
                attendance="attended",
                patient_present=True,
                alternatives=[
                    ContactAlternative(
                        minutes=minutes,
                        intervals=[],
                        sources=[reference],
                        choices={"duration:E115": str(minutes)},
                    )
                    for minutes, reference in zip([40, 50], duration_sources, strict=True)
                ],
                decisions=[
                    Decision(
                        field="duration",
                        status="conflicting_evidence",
                        reason="Two final patient-contact records disagree.",
                        sources=duration_sources,
                    )
                ],
                sources=duration_sources,
            )
        ],
        plans=[
            PlanClaim(
                patient_id="P1",
                effective_start=date(2026, 1, 19),
                effective_end=None,
                minimum_days=1,
                minimum_minutes=45,
                eligible_services=["individual"],
                week_start="Monday",
                patient_present_required=True,
                note="Synthetic plan.",
                quotes=[plan_source.quote],
                sources=[plan_source],
            )
        ],
        assessments=[],
        observations=[],
    )


def answer(
    record: PatientRecord,
    operation: QueryOperation = "durations",
    *,
    budget: int = 10_000,
    unprocessed: list[str] | None = None,
    start: date = date(2026, 1, 19),
    end: date = date(2026, 2, 1),
    metrics: list[QueryMetric] | None = None,
    selected_dates: list[date] | None = None,
) -> AnswerBundle:
    snapshot = ClinicalSnapshot(
        snapshot_id=1,
        patients=[record],
        pending_documents=unprocessed or [],
    )
    question = f"Synthetic {operation} query."
    task = QueryTask(
        operation=operation,
        patient=None if operation == "cohort" else record.patient_id,
        patient_ids=[record.patient_id],
        start=start,
        end=end,
        metrics=metrics or [],
        selected_dates=selected_dates or [],
    )
    plan = QueryPlan(question=question, snapshot_id=1, tasks=[task])
    return answer_question(question, snapshot, budget, plan=plan)


def test_conflicting_duration_requests_scoped_correction_and_preserves_values() -> None:
    result = answer(synthetic_patient())
    need = next(value for value in result.evidence_needs if value.field == "duration")
    assert need.patient_id == "P1"
    assert need.encounter_id == "E115"
    assert need.service_dates == [date(2026, 1, 26)]
    assert "40 or 50" in need.reason
    assert "identifying which earlier assertion it replaces" in need.next_step
    assert "2026-01-26" in need.next_step
    assert {value.document_id for value in need.sources} == {"D40", "D50"}
    assert result.metrics[0].minutes.values == [40, 50]
    assert "Additional evidence needed:" in result.text
    assert result.task_answers[0].evidence_needs == result.evidence_needs


def test_settled_count_does_not_request_unneeded_duration_documentation() -> None:
    result = answer(synthetic_patient(), "counts")
    assert result.metrics[0].session_count.exact == 1
    assert not result.evidence_needs


def test_excluded_event_does_not_request_unknown_contact_duration() -> None:
    record = synthetic_patient()
    record.encounters[0].attendance = "no_show"
    record.encounters[0].patient_present = False
    record.encounters[0].alternatives = [
        ContactAlternative(
            minutes=None,
            intervals=[],
            sources=record.encounters[0].sources,
        )
    ]
    result = answer(record)
    assert result.metrics[0].minutes.exact == 0
    assert not result.evidence_needs


def test_missing_duration_requests_actual_intervals_and_breaks() -> None:
    record = synthetic_patient()
    record.encounters[0].alternatives = [
        ContactAlternative(
            minutes=None,
            intervals=[],
            sources=record.encounters[0].sources,
        )
    ]
    result = answer(record)
    assert result.metrics[0].minutes.exact is None
    assert [need.field for need in result.evidence_needs] == ["duration"]
    assert (
        "actual patient-contact intervals and any break log" in result.evidence_needs[0].next_step
    )


def test_missing_attendance_and_presence_request_patient_specific_evidence() -> None:
    record = synthetic_patient()
    record.encounters[0].attendance = "unknown"
    record.encounters[0].patient_present = None
    result = answer(record, "counts")
    needs = {value.field: value for value in result.evidence_needs}
    assert set(needs) == {"attendance", "patient_present"}
    assert "patient-specific attendance" in needs["attendance"].next_step
    assert "scheduled slot alone does not establish presence" in needs["patient_present"].next_step
    assert result.metrics[0].session_count.values == [0, 1]


def test_analysis_budget_requests_computation_without_clinical_document() -> None:
    result = answer(synthetic_patient(), budget=1)
    assert len(result.evidence_needs) == 1
    need = result.evidence_needs[0]
    assert need.action == "increase_analysis_budget"
    assert need.needed_documentation is None
    assert need.encounter_id is None
    assert "replay this query" in need.next_step


def test_unprocessed_sources_request_processing_without_patient_attribution() -> None:
    result = answer(synthetic_patient(), "counts", unprocessed=["pending.txt"])
    assert len(result.evidence_needs) == 1
    need = result.evidence_needs[0]
    assert need.action == "complete_processing"
    assert need.patient_id is None
    assert need.patient_ids == ["P1"]
    assert need.document_ids == ["pending.txt"]
    assert need.needed_documentation is None
    assert "before requesting new records" in need.next_step


def test_unlinked_identity_requests_event_identifiers() -> None:
    record = synthetic_patient()
    record.encounters[0].decisions.append(
        Decision(
            field="identity",
            status="missing_evidence",
            reason="Two descriptions lack common event identifiers.",
            sources=record.encounters[0].sources,
        )
    )
    result = answer(record, "counts")
    assert result.metrics[0].analysis_status == "analysis_incomplete"
    need = next(value for value in result.evidence_needs if value.field == "encounter_identity")
    assert need.encounter_id == "E115"
    assert "actual event identifiers" in need.next_step


def test_missing_plan_and_midweek_policy_request_effective_rules() -> None:
    record = synthetic_patient()
    record.plans = []
    missing = answer(record, "weekly")
    assert {value.field for value in missing.evidence_needs} >= {"effective_plan", "weekly_goal"}
    assert all(
        "signed treatment plan" in value.next_step
        for value in missing.evidence_needs
        if value.category == "plan"
    )
    record = synthetic_patient()
    revised = record.plans[0].model_copy(
        update={
            "effective_start": date(2026, 1, 28),
            "minimum_minutes": 60,
        }
    )
    record.plans.append(revised)
    mixed = answer(record, "weekly")
    need = next(
        value
        for value in mixed.evidence_needs
        if value.reason == "conflicting_or_midweek_plan_policy_unspecified"
    )
    assert need.start == date(2026, 1, 26)
    assert need.end == date(2026, 2, 1)
    assert "do not infer prorating" in need.next_step


def test_conflicting_plan_eligibility_requests_authoritative_plan_for_count() -> None:
    record = synthetic_patient()
    record.plans.append(record.plans[0].model_copy(update={"eligible_services": ["group"]}))
    result = answer(record, "counts")
    assert result.metrics[0].session_count.values == [0, 1]
    assert [value.field for value in result.evidence_needs] == ["effective_plan"]
    assert "different therapy-inclusion rules" in result.evidence_needs[0].reason


def test_partial_week_requests_query_expansion_without_new_document() -> None:
    result = answer(synthetic_patient(), "weekly", start=date(2026, 1, 19), end=date(2026, 1, 20))
    assert [value.action for value in result.evidence_needs] == ["expand_review_range"]
    assert result.evidence_needs[0].needed_documentation is None


def test_day_and_timeline_do_not_request_unasked_weekly_coverage() -> None:
    for operation in ("day", "timeline"):
        result = answer(
            synthetic_patient(),
            operation,
            start=date(2026, 1, 26),
            end=date(2026, 1, 26),
            metrics=["sessions"],
            selected_dates=[date(2026, 1, 26)] if operation == "day" else [],
        )
        assert result.metrics[0].session_count.exact == 1
        assert not result.evidence_needs


def test_goal_and_comparison_tasks_request_duration_even_without_display_metric() -> None:
    for operation in ("weekly", "cohort", "plan_change"):
        record = synthetic_patient()
        if operation == "plan_change":
            record.plans.append(
                record.plans[0].model_copy(
                    update={
                        "effective_start": date(2026, 1, 26),
                        "minimum_minutes": 60,
                    }
                )
            )
        result = answer(record, operation, metrics=["sessions"])
        need = next(value for value in result.evidence_needs if value.field == "duration")
        assert need.encounter_id == "E115"
        assert "40 or 50" in need.reason


def test_same_assessment_requests_identified_original_form_for_disputed_fields() -> None:
    record = synthetic_patient()
    reference = source("FORM", "Original form F1 has conflicting score and completion annotations.")
    record.assessments = [
        AssessmentClaim(
            patient_id="P1",
            completed_date=date(2026, 1, 20),
            instrument="PHQ-9",
            score=10,
            form_id="F1",
            item_nine=0,
            is_copy=False,
            score_alternatives=[10, 12],
            item_nine_alternatives=[0, 1],
            completed_date_alternatives=[date(2026, 1, 20), date(2026, 1, 21)],
            quotes=[reference.quote],
            sources=[reference],
        )
    ]
    result = answer(record, "symptoms")
    assert {value.field for value in result.evidence_needs} == {
        "score",
        "item_nine",
        "completed_date",
    }
    assert all(value.assessment_id == "F1" for value in result.evidence_needs)
    assert all(
        "original completed PHQ-9 form F1" in value.next_step for value in result.evidence_needs
    )
    assert all(value.sources == [reference] for value in result.evidence_needs)
    assert len(result.assessments) == 1


def test_possible_cohort_member_has_patient_scoped_duration_followup() -> None:
    result = answer(synthetic_patient(), "cohort")
    assert result.cohort_results[0].membership == "possible"
    need = next(value for value in result.evidence_needs if value.field == "duration")
    assert need.patient_id == "P1"
    assert need.encounter_id == "E115"
    assert "40 or 50" in need.reason


def test_symptom_course_preserves_attribution_chronology_and_contact_reason() -> None:
    record = synthetic_patient()
    entries: list[tuple[int, str, str]] = [
        (26, "patient_report", "Sleep improved, but difficulty returning to work persisted."),
        (20, "patient_report", "The patient reported poor sleep."),
        (26, "clinician_observation", "The clinician observed more sustained engagement."),
        (26, "collateral_report", "A family member reported continued withdrawal at home."),
        (26, "reason_for_contact", "An additional contact addressed a reported work stressor."),
    ]
    for index, (day, kind, text) in enumerate(entries):
        reference = source(f"O{index}", text)
        record.observations.append(
            Observation.model_validate(
                {
                    "patient_id": "P1",
                    "observed_date": date(2026, 1, day),
                    "kind": kind,
                    "text": text,
                    "quotes": [text],
                    "sources": [reference],
                }
            )
        )
    result = answer(record, "symptoms")
    assert result.text.index("poor sleep") < result.text.index("Sleep improved")
    for heading in (
        "Patient reports:",
        "Clinician observations:",
        "Collateral reports:",
        "Documented reasons for additional contact:",
    ):
        assert heading in result.text
    assert all(text in result.text for _, _, text in entries)
    assert "do not by themselves establish recovery" in result.text
    assert not result.evidence_needs
