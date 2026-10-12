from datetime import date

import pytest

from backbone.models import (
    AssessmentClaim,
    ClinicalSnapshot,
    ContactAlternative,
    Decision,
    Encounter,
    Observation,
    PatientRecord,
    PlanClaim,
    SourceRef,
)
from backbone.query import QueryPlanningError, answer_question, plan_question, render_sources
from backbone.reconciliation import reconcile_assessments


def patient(name: str = "Casey", identifier: str = "P1") -> PatientRecord:
    return PatientRecord(
        patient_id=identifier,
        name=name,
        organization="Test clinic",
        episode_start=date(2027, 2, 1),
        episode_end=date(2027, 2, 28),
        encounters=[],
        plans=[],
        assessments=[],
        observations=[],
    )


def snapshot() -> ClinicalSnapshot:
    return ClinicalSnapshot(snapshot_id=7, patients=[patient()])


def evidence(identifier: str, quote: str) -> SourceRef:
    return SourceRef(
        content_hash=identifier,
        document_id=identifier,
        filename=f"{identifier}.txt",
        start_line=4,
        end_line=4,
        quote=quote,
    )


def clinical_patient() -> PatientRecord:
    record = patient()
    plan_source = evidence("PLAN", "The weekly goal is one therapy day and 30 minutes.")
    record.plans = [
        PlanClaim(
            patient_id="P1",
            effective_start=date(2027, 2, 1),
            effective_end=None,
            minimum_days=1,
            minimum_minutes=30,
            eligible_services=["individual", "group"],
            week_start="Monday",
            patient_present_required=True,
            note="Patient-present therapy.",
            quotes=[plan_source.quote],
            sources=[plan_source],
        )
    ]
    disputed_sources = [
        evidence("D40", "Full patient contact was 40 minutes."),
        evidence("D50", "Full patient contact was 50 minutes."),
    ]
    record.encounters = [
        Encounter(
            encounter_id="E9",
            patient_id="P1",
            service_date=date(2027, 2, 9),
            service_type="individual",
            attendance="attended",
            patient_present=True,
            alternatives=[
                ContactAlternative(
                    minutes=minutes,
                    intervals=[],
                    sources=[source],
                    choices={"duration:E9": str(minutes)},
                )
                for minutes, source in zip([40, 50], disputed_sources, strict=True)
            ],
            decisions=[
                Decision(
                    field="duration",
                    status="conflicting_evidence",
                    reason="Two final notes disagree on the full contact duration.",
                    sources=disputed_sources,
                )
            ],
            sources=disputed_sources,
        )
    ]
    for day_number, minutes in [(10, 60), (11, 30)]:
        source = evidence(f"D{day_number}", f"Patient attended {minutes} minutes of group therapy.")
        record.encounters.append(
            Encounter(
                encounter_id=f"E{day_number}",
                patient_id="P1",
                service_date=date(2027, 2, day_number),
                service_type="group",
                attendance="attended",
                patient_present=True,
                alternatives=[ContactAlternative(minutes=minutes, intervals=[], sources=[source])],
                decisions=[],
                sources=[source],
            )
        )
    for day_number, score in [(1, 18.0), (8, 15.0), (20, 12.0)]:
        source = evidence(f"Q{day_number}", f"Questionnaire completed with score {score:g}.")
        record.assessments.append(
            AssessmentClaim(
                patient_id="P1",
                completed_date=date(2027, 2, day_number),
                instrument="PHQ-9",
                score=score,
                form_id=f"F{day_number}",
                item_nine=0.0,
                is_copy=False,
                quotes=[source.quote],
                sources=[source],
            )
        )
    contact_source = evidence(
        "REASON", "An additional contact addressed a reported work-related stressor."
    )
    record.observations.append(
        Observation(
            patient_id="P1",
            observed_date=date(2027, 2, 9),
            kind="reason_for_contact",
            text="An additional contact addressed a reported work-related stressor.",
            quotes=[contact_source.quote],
            sources=[contact_source],
        )
    )
    return record


def test_new_patient_and_iso_range_are_not_development_question_specific() -> None:
    plan = plan_question(
        "How many therapy sessions did Casey attend from 2027-02-03 to 2027-02-17?",
        snapshot(),
    )
    assert plan.operation == "counts"
    assert plan.patient == "P1"
    assert plan.start == date(2027, 2, 3)
    assert plan.end == date(2027, 2, 17)


def test_discrete_dates_exclude_intervening_day() -> None:
    plan = plan_question("Reconstruct Casey's care on February 9 and February 11.", snapshot())
    assert plan.operation == "day"
    assert plan.selected_dates == [date(2027, 2, 9), date(2027, 2, 11)]


def test_omitted_range_uses_documented_episode() -> None:
    plan = plan_question("Did each week's therapy meet Casey's treatment goal?", snapshot())
    assert plan.operation == "weekly"
    assert plan.start == date(2027, 2, 1)
    assert plan.end == date(2027, 2, 28)


def test_english_range_with_explicit_year() -> None:
    plan = plan_question("For February 3–17, 2027, count Casey's sessions.", snapshot())
    assert plan.operation == "counts"
    assert plan.start == date(2027, 2, 3)
    assert plan.end == date(2027, 2, 17)
    assert plan.selected_dates == []


def test_cohort_scope_does_not_select_first_patient() -> None:
    cohort_snapshot = ClinicalSnapshot(snapshot_id=7, patients=[patient(), patient("Morgan", "P2")])
    plan = plan_question(
        "Which patients had two consecutive weeks below their treatment requirements?",
        cohort_snapshot,
    )
    assert plan.operation == "cohort"
    assert plan.patient is None


def test_ambiguous_and_unsupported_questions_are_rejected() -> None:
    with pytest.raises(QueryPlanningError, match="Unsupported"):
        plan_question("What medication should Casey take?", snapshot())
    with pytest.raises(QueryPlanningError, match="separately"):
        plan_question("Compare Casey's symptoms and weekly treatment goals.", snapshot())
    with pytest.raises(QueryPlanningError, match="not present"):
        plan_question("How many sessions did Taylor attend?", snapshot())
    with pytest.raises(QueryPlanningError, match="ratios"):
        plan_question("What percentage of Casey's therapy sessions were individual?", snapshot())
    with pytest.raises(QueryPlanningError, match="Unsupported"):
        plan_question("Why did Casey miss therapy sessions?", snapshot())


def test_missing_patient_is_not_silently_selected_in_multi_patient_snapshot() -> None:
    cohort_snapshot = ClinicalSnapshot(snapshot_id=7, patients=[patient(), patient("Morgan", "P2")])
    with pytest.raises(QueryPlanningError, match="Name a patient"):
        plan_question("How many therapy minutes were delivered?", cohort_snapshot)


def test_source_rendering_retains_precise_original_passage_and_deduplicates() -> None:
    source = SourceRef(
        content_hash="content",
        document_id="D1",
        filename="note.txt",
        start_line=12,
        end_line=13,
        quote="Actual contact: 09:00-09:30.\nPatient present.",
    )
    rendered = render_sources([source, source])
    assert rendered.count("D1,") == 1
    assert "lines 12-13" in rendered
    assert "Actual contact: 09:00-09:30. Patient present." in rendered


def test_answer_preserves_discrete_duration_alternatives_and_reconciliation_evidence() -> None:
    bundle = answer_question(
        "How many therapy minutes did Casey receive?",
        ClinicalSnapshot(snapshot_id=8, patients=[clinical_patient()]),
    )
    assert bundle.snapshot_id == 8
    assert bundle.metrics[0].session_count.exact == 3
    assert bundle.metrics[0].minutes.values == [130, 140]
    assert "130 or 140" in bundle.text
    assert "Two final notes disagree" in bundle.text
    assert {source.document_id for source in bundle.sources} >= {"D40", "D50", "PLAN"}
    assert bundle.uncertainty


def test_day_answer_does_not_include_care_between_named_dates() -> None:
    bundle = answer_question(
        "Reconstruct Casey's care on February 9 and February 11.",
        ClinicalSnapshot(snapshot_id=8, patients=[clinical_patient()]),
    )
    assert [result.start for result in bundle.metrics] == [date(2027, 2, 9), date(2027, 2, 11)]
    assert [result.session_count.exact for result in bundle.metrics] == [1, 1]
    assert "E10" not in bundle.text


def test_symptom_episode_scope_is_not_narrowed_to_additional_contact_date() -> None:
    bundle = answer_question(
        "Summarize Casey's symptom course during the episode and the reason for "
        "the additional contact on February 9.",
        ClinicalSnapshot(snapshot_id=8, patients=[clinical_patient()]),
    )
    assert len(bundle.assessments) == 3
    assert bundle.plan.start == date(2027, 2, 1)
    assert "18 on 2027-02-01 to 12 on 2027-02-20" in bundle.text
    assert "reported work-related stressor" in bundle.text


def test_failed_processing_does_not_establish_negative_weekly_or_cohort_conclusion() -> None:
    incomplete = ClinicalSnapshot(
        snapshot_id=8, patients=[clinical_patient()], failed_documents=["unprocessed.txt"]
    )
    weekly = answer_question("Did each week meet Casey's therapy goal?", incomplete)
    assert all(week.decision != "not_met" for week in weekly.metrics[0].weeks)
    assert weekly.coverage_status == "failed_source_processing"
    assert "unprocessed.txt" in weekly.text
    cohort_bundle = answer_question(
        "Which patients had two consecutive weeks below their therapy requirements?", incomplete
    )
    assert cohort_bundle.cohort_results[0].membership == "analysis_incomplete"


def test_analysis_budget_exhaustion_is_reported_as_execution_limitation() -> None:
    bundle = answer_question(
        "How many therapy minutes did Casey receive?",
        ClinicalSnapshot(snapshot_id=8, patients=[clinical_patient()]),
        scenario_budget=1,
    )
    assert bundle.metrics[0].analysis_status == "analysis_incomplete"
    assert "scenario_budget_exceeded" in bundle.text


def test_discrete_dates_can_share_a_written_year() -> None:
    plan = plan_question("Reconstruct Casey's care on February 9 and 11, 2028.", snapshot())
    assert plan.selected_dates == [date(2028, 2, 9), date(2028, 2, 11)]


def test_repeated_month_names_can_share_trailing_year() -> None:
    plan = plan_question("Reconstruct care on February 9 and February 11, 2028.", snapshot())
    assert plan.selected_dates == [date(2028, 2, 9), date(2028, 2, 11)]


def test_mixed_date_notation_preserves_requested_range_order() -> None:
    plan = plan_question("Count Casey's sessions from February 3, 2027 to 2027-02-17.", snapshot())
    assert plan.start == date(2027, 2, 3)
    assert plan.end == date(2027, 2, 17)


def test_reversed_requested_range_is_rejected() -> None:
    with pytest.raises(QueryPlanningError, match="start follows"):
        plan_question("Count Casey's sessions from 2027-02-17 to 2027-02-03.", snapshot())


def test_first_name_is_resolved_from_documented_full_name() -> None:
    full_name = ClinicalSnapshot(snapshot_id=8, patients=[patient("Casey Morgan", "P1")])
    plan = plan_question("How many therapy sessions did Casey attend?", full_name)
    assert plan.patient == "P1"


def test_full_name_disambiguates_shared_first_name() -> None:
    shared = ClinicalSnapshot(
        snapshot_id=8, patients=[patient("Casey Morgan", "P1"), patient("Casey Taylor", "P2")]
    )
    assert plan_question("Count Casey Taylor's sessions.", shared).patient == "P2"
    with pytest.raises(QueryPlanningError, match="one named patient"):
        plan_question("Count Casey's sessions.", shared)


def test_plan_comparison_keeps_explicit_window_and_documented_change_boundary() -> None:
    record = clinical_patient()
    change_source = evidence(
        "CHANGE", "Effective February 15: two therapy days and 90 minutes weekly."
    )
    record.plans.append(
        record.plans[0].model_copy(
            update={
                "effective_start": date(2027, 2, 15),
                "minimum_days": 2,
                "minimum_minutes": 90,
                "quotes": [change_source.quote],
                "sources": [change_source],
            }
        )
    )
    bundle = answer_question(
        "Compare Casey's care before and after the plan change from 2027-02-03 to 2027-02-20.",
        ClinicalSnapshot(snapshot_id=8, patients=[record]),
    )
    comparison = bundle.plan_comparison
    assert comparison is not None
    assert comparison.change_date == date(2027, 2, 15)
    assert comparison.before is not None and comparison.after is not None
    assert (comparison.before.start, comparison.before.end) == (date(2027, 2, 3), date(2027, 2, 14))
    assert (comparison.after.start, comparison.after.end) == (date(2027, 2, 15), date(2027, 2, 20))
    assert "CHANGE" in {source.document_id for source in bundle.sources}


def test_same_assessment_form_conflicts_render_once_without_selecting_anchor_score() -> None:
    record = clinical_patient()
    original = record.assessments[0]
    copy_source = evidence("COPIED_FORM", "Form F1 score: 20; item nine: 1.")
    conflicting_copy = original.model_copy(
        update={
            "score": 20.0,
            "item_nine": 1.0,
            "is_copy": True,
            "quotes": [copy_source.quote],
            "sources": [copy_source],
        }
    )
    record.assessments = reconcile_assessments([original, conflicting_copy])
    bundle = answer_question(
        "Summarize Casey's documented symptom assessments during the episode.",
        ClinicalSnapshot(snapshot_id=8, patients=[record]),
    )
    assert len(bundle.assessments) == 1
    assert "1 distinct symptom assessment" in bundle.text
    assert "18 or 20 (disputed)" in bundle.text
    assert "0 or 1 (disputed)" in bundle.text
    assert any("score alternatives" in message for message in bundle.uncertainty)
    assert any("item-nine alternatives" in message for message in bundle.uncertainty)
    assert "COPIED_FORM" in {source.document_id for source in bundle.sources}


def test_disputed_endpoint_score_does_not_render_single_net_change() -> None:
    record = clinical_patient()
    record.assessments[0].score_alternatives = [18.0, 20.0]
    bundle = answer_question(
        "Summarize Casey's symptom course during the episode.",
        ClinicalSnapshot(snapshot_id=8, patients=[record]),
    )
    assert "A single numerical change is not established" in bundle.text
    assert "numerical change -6" not in bundle.text


def test_ledger_keeps_coupled_date_and_service_interpretations_together() -> None:
    record = clinical_patient()
    record.encounters = [record.encounters[0]]
    record.encounters[0].alternatives[1].service_date = date(2027, 2, 10)
    record.encounters[0].alternatives[1].service_type = "group"
    bundle = answer_question(
        "How many therapy minutes did Casey receive?",
        ClinicalSnapshot(snapshot_id=8, patients=[record]),
    )
    row = bundle.metrics[0].contributions[0]
    assert row.service_dates == [date(2027, 2, 9), date(2027, 2, 10)]
    assert row.service_types == ["group", "individual"]
    assert "2027-02-09, individual" in bundle.text
    assert "2027-02-10, group" in bundle.text
    assert "alternatives for the same encounter" in bundle.text
