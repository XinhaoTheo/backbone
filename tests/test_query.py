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
    QueryOperation,
    QueryPlan,
    QueryTask,
    SourceRef,
)
from backbone.query import AnswerBundle, answer_question, render_sources
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


def answer_for_operation(
    question: str,
    snapshot: ClinicalSnapshot,
    *,
    operation: QueryOperation,
    start: date = date(2027, 2, 1),
    end: date = date(2027, 2, 28),
    selected_dates: list[date] | None = None,
    change_date: date | None = None,
    scenario_budget: int = 10_000,
) -> AnswerBundle:
    dates = selected_dates if selected_dates is not None else []
    task = QueryTask(
        operation=operation,
        patient=None if operation == "cohort" else "P1",
        patient_ids=[record.patient_id for record in snapshot.patients]
        if operation == "cohort"
        else ["P1"],
        start=min(dates) if dates else start,
        end=max(dates) if dates else end,
        selected_dates=dates,
        change_date=change_date,
    )
    plan = QueryPlan(question=question, snapshot_id=snapshot.snapshot_id, tasks=[task])
    return answer_question(question, snapshot, scenario_budget, plan=plan)


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
    bundle = answer_for_operation(
        "How many therapy minutes did Casey receive?",
        ClinicalSnapshot(snapshot_id=8, patients=[clinical_patient()]),
        operation="durations",
    )
    assert bundle.snapshot_id == 8
    assert bundle.metrics[0].session_count.exact == 3
    assert bundle.metrics[0].minutes.values == [130, 140]
    assert "130 or 140" in bundle.text
    assert "Two final notes disagree" in bundle.text
    assert {source.document_id for source in bundle.sources} >= {"D40", "D50", "PLAN"}
    assert bundle.uncertainty


def test_day_answer_does_not_include_care_between_named_dates() -> None:
    bundle = answer_for_operation(
        "Reconstruct Casey's care on February 9 and February 11.",
        ClinicalSnapshot(snapshot_id=8, patients=[clinical_patient()]),
        operation="day",
        selected_dates=[date(2027, 2, 9), date(2027, 2, 11)],
    )
    assert [result.start for result in bundle.metrics] == [date(2027, 2, 9), date(2027, 2, 11)]
    assert [result.session_count.exact for result in bundle.metrics] == [1, 1]
    assert "E10" not in bundle.text


def test_symptom_episode_scope_is_not_narrowed_to_additional_contact_date() -> None:
    bundle = answer_for_operation(
        "Summarize Casey's symptom course during the episode and the reason for "
        "the additional contact on February 9.",
        ClinicalSnapshot(snapshot_id=8, patients=[clinical_patient()]),
        operation="symptoms",
    )
    assert len(bundle.assessments) == 3
    assert bundle.plan.tasks[0].start == date(2027, 2, 1)
    assert "18 on 2027-02-01 to 12 on 2027-02-20" in bundle.text
    assert "reported work-related stressor" in bundle.text


def test_failed_processing_does_not_establish_negative_weekly_or_cohort_conclusion() -> None:
    incomplete = ClinicalSnapshot(
        snapshot_id=8, patients=[clinical_patient()], failed_documents=["unprocessed.txt"]
    )
    weekly = answer_for_operation(
        "Did each week meet Casey's therapy goal?", incomplete, operation="weekly"
    )
    assert all(week.decision != "not_met" for week in weekly.metrics[0].weeks)
    assert weekly.coverage_status == "failed_source_processing"
    assert "unprocessed.txt" in weekly.text
    cohort_bundle = answer_for_operation(
        "Which patients had two consecutive weeks below their therapy requirements?",
        incomplete,
        operation="cohort",
    )
    assert cohort_bundle.cohort_results[0].membership == "analysis_incomplete"


def test_analysis_budget_exhaustion_is_reported_as_execution_limitation() -> None:
    bundle = answer_for_operation(
        "How many therapy minutes did Casey receive?",
        ClinicalSnapshot(snapshot_id=8, patients=[clinical_patient()]),
        scenario_budget=1,
        operation="durations",
    )
    assert bundle.metrics[0].analysis_status == "analysis_incomplete"
    assert "scenario_budget_exceeded" in bundle.text


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
    bundle = answer_for_operation(
        "Compare Casey's care before and after the plan change from 2027-02-03 to 2027-02-20.",
        ClinicalSnapshot(snapshot_id=8, patients=[record]),
        operation="plan_change",
        start=date(2027, 2, 3),
        end=date(2027, 2, 20),
        change_date=date(2027, 2, 15),
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
    bundle = answer_for_operation(
        "Summarize Casey's documented symptom assessments during the episode.",
        ClinicalSnapshot(snapshot_id=8, patients=[record]),
        operation="symptoms",
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
    bundle = answer_for_operation(
        "Summarize Casey's symptom course during the episode.",
        ClinicalSnapshot(snapshot_id=8, patients=[record]),
        operation="symptoms",
    )
    assert "A single numerical change is not established" in bundle.text
    assert "numerical change -6" not in bundle.text


def test_ledger_keeps_coupled_date_and_service_interpretations_together() -> None:
    record = clinical_patient()
    record.encounters = [record.encounters[0]]
    record.encounters[0].alternatives[1].service_date = date(2027, 2, 10)
    record.encounters[0].alternatives[1].service_type = "group"
    bundle = answer_for_operation(
        "How many therapy minutes did Casey receive?",
        ClinicalSnapshot(snapshot_id=8, patients=[record]),
        operation="durations",
    )
    row = bundle.metrics[0].contributions[0]
    assert row.service_dates == [date(2027, 2, 9), date(2027, 2, 10)]
    assert row.service_types == ["group", "individual"]
    assert "2027-02-09, individual" in bundle.text
    assert "2027-02-10, group" in bundle.text
    assert "alternatives for the same encounter" in bundle.text


def test_pending_source_processing_prevents_negative_weekly_and_cohort_determinations() -> None:
    pending = ClinicalSnapshot(
        snapshot_id=8, patients=[clinical_patient()], pending_documents=["pending.txt"]
    )
    weekly = answer_for_operation(
        "Did each week meet Casey's therapy goal?", pending, operation="weekly"
    )
    assert all(week.decision != "not_met" for week in weekly.metrics[0].weeks)
    assert "pending.txt" in weekly.text
    assert weekly.coverage_status == "failed_source_processing"
    population = answer_for_operation(
        "Which patients had two consecutive weeks below their therapy requirements?",
        pending,
        operation="cohort",
    )
    assert population.cohort_results[0].membership == "analysis_incomplete"


def dated_conflict_patient() -> PatientRecord:
    record = clinical_patient()
    original = record.assessments[0]
    copied_source = evidence("DATED_COPY", "Form F1 completion date: February 22, 2027; score 18.")
    copied = original.model_copy(
        update={
            "completed_date": date(2027, 2, 22),
            "is_copy": True,
            "quotes": [copied_source.quote],
            "sources": [copied_source],
        }
    )
    record.assessments = reconcile_assessments([*record.assessments, copied])
    return record


def test_same_form_date_conflict_does_not_create_measurement_or_established_progress() -> None:
    bundle = answer_for_operation(
        "Summarize Casey's symptom course during the episode.",
        ClinicalSnapshot(snapshot_id=8, patients=[dated_conflict_patient()]),
        operation="symptoms",
    )
    assert len(bundle.assessments) == 3
    assert "2027-02-01 or 2027-02-22 (disputed)" in bundle.text
    assert (
        "conflicting completion dates prevent an established chronological sequence" in bundle.text
    )
    assert "numerical change -6" not in bundle.text
    assert any("conflicting completion dates" in message for message in bundle.uncertainty)


@pytest.mark.parametrize("operation", ["symptom assessments", "clinical timeline"])
def test_assessment_scope_includes_noncanonical_date_and_qualifies_membership(
    operation: str,
) -> None:
    bundle = answer_for_operation(
        f"Show Casey's {operation} from 2027-02-20 to 2027-02-22.",
        ClinicalSnapshot(snapshot_id=8, patients=[dated_conflict_patient()]),
        operation="symptoms" if operation == "symptom assessments" else "timeline",
        start=date(2027, 2, 20),
        end=date(2027, 2, 22),
    )
    assert {value.form_id for value in bundle.assessments} == {"F1", "F20"}
    assert "disputed period membership" in bundle.text
    assert "possible; completion date disputed" in bundle.text
    assert any("may fall outside" in message for message in bundle.uncertainty)
    assert "DATED_COPY" in {value.document_id for value in bundle.sources}


def test_composite_answer_links_each_patient_operation_to_its_own_results() -> None:
    first = clinical_patient()
    second = clinical_patient().model_copy(deep=True)
    second.patient_id = "P2"
    second.name = "Alex"
    second.encounters = []
    second.observations = []
    for assessment, score in zip(second.assessments, [8.0, 6.0, 4.0], strict=True):
        assessment.patient_id = "P2"
        assessment.score = score
    view = ClinicalSnapshot(snapshot_id=8, patients=[first, second])
    question = "Count Casey's sessions and summarize Alex's symptom course."
    tasks = [
        QueryTask(
            operation="counts",
            patient="P1",
            patient_ids=["P1"],
            start=date(2027, 2, 1),
            end=date(2027, 2, 28),
            metrics=["sessions"],
        ),
        QueryTask(
            operation="symptoms",
            patient="P2",
            patient_ids=["P2"],
            start=date(2027, 2, 1),
            end=date(2027, 2, 28),
        ),
    ]
    plan = QueryPlan(question=question, snapshot_id=view.snapshot_id, tasks=tasks)
    bundle = answer_question(question, view, plan=plan)
    assert len(bundle.task_answers) == 2
    count_answer, symptom_answer = bundle.task_answers
    assert count_answer.task == tasks[0]
    assert count_answer.metrics[0].patient_id == "P1"
    assert count_answer.metrics[0].session_count.exact == 3
    assert not count_answer.assessments
    assert symptom_answer.task == tasks[1]
    assert not symptom_answer.metrics
    assert [assessment.score for assessment in symptom_answer.assessments] == [8, 6, 4]
    assert all(assessment.patient_id == "P2" for assessment in symptom_answer.assessments)
    assert len(bundle.metrics) == 1
    assert len(bundle.assessments) == 3


def test_discrete_duration_task_excludes_intervening_therapy() -> None:
    view = ClinicalSnapshot(snapshot_id=8, patients=[clinical_patient()])
    question = "Total only the February 9 and February 11 therapy minutes."
    task = QueryTask(
        operation="durations",
        patient="P1",
        patient_ids=["P1"],
        start=date(2027, 2, 9),
        end=date(2027, 2, 11),
        selected_dates=[date(2027, 2, 9), date(2027, 2, 11)],
        metrics=["minutes"],
    )
    bundle = answer_question(
        question, view, plan=QueryPlan(question=question, snapshot_id=8, tasks=[task])
    )
    assert [result.start for result in bundle.metrics] == [date(2027, 2, 9), date(2027, 2, 11)]
    assert [result.minutes.values for result in bundle.metrics] == [[40, 50], [30]]
    assert "E10" not in bundle.text
