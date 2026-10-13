from datetime import date

import pytest

from backbone.calculation import (
    WeekWitness,
    calculate,
    cohort,
    compare_plans,
    consecutive_window,
)
from backbone.models import (
    Attendance,
    ContactAlternative,
    Decision,
    Encounter,
    PatientRecord,
    PlanClaim,
    ServiceType,
    SourceRef,
)

START = date(2026, 1, 5)
END = date(2026, 1, 18)


def source(identifier: str) -> SourceRef:
    return SourceRef(
        content_hash=identifier, document_id=identifier, filename=f"{identifier}.txt",
        start_line=1, end_line=2, quote="Synthetic evidence for calculation tests.",
    )


def plan(
    minimum_days: int = 1, minimum_minutes: int = 100,
    effective_start: date = START,
) -> PlanClaim:
    return PlanClaim(
        patient_id="P1", effective_start=effective_start, effective_end=None,
        minimum_days=minimum_days, minimum_minutes=minimum_minutes,
        eligible_services=["individual", "group", "family"], week_start="Monday",
        patient_present_required=True, note="Synthetic plan.", quotes=[], sources=[source("plan")],
    )


def encounter(
    identifier: str, day: date, minutes: list[int | None],
    service: ServiceType = "individual", attendance: Attendance = "attended",
    present: bool | None = True, choices: list[dict[str, str]] | None = None,
) -> Encounter:
    options = choices if choices is not None else [{} for value in minutes]
    return Encounter(
        encounter_id=identifier, patient_id="P1", service_date=day, service_type=service,
        attendance=attendance, patient_present=present,
        alternatives=[ContactAlternative(
            minutes=value, intervals=[], sources=[source(identifier)], choices=option,
        ) for value, option in zip(minutes, options, strict=True)],
        decisions=[], sources=[source(identifier)],
    )


def patient(
    encounters: list[Encounter], plans: list[PlanClaim] | None = None,
    episode_end: date = END, identifier: str = "P1",
) -> PatientRecord:
    return PatientRecord(
        patient_id=identifier, name="Synthetic patient", organization="Test organization",
        episode_start=START, episode_end=episode_end, encounters=encounters,
        plans=[plan()] if plans is None else plans, assessments=[], observations=[],
    )


def test_counts_days_eligibility_and_sources_are_distinct() -> None:
    record = patient([
        encounter("group", START, [60], service="group"),
        encounter("individual", START, [45]),
        encounter("medication", START, [20], service="medication"),
        encounter("absent", date(2026, 1, 6), [60], attendance="no_show"),
    ], episode_end=date(2026, 1, 11))
    result = calculate(record, START, date(2026, 1, 11))
    assert result.session_count.exact == 2
    assert result.distinct_days.exact == 1
    assert result.session_counts["group"].exact == 1
    assert result.session_counts["medication"].exact == 0
    assert result.minutes.exact == 105
    assert result.weeks[0].decision == "met"
    assert {item.encounter_id for item in result.exclusions} == {"medication", "absent"}
    assert result.contributions[0].sources[0].document_id == "group"


def test_missing_duration_is_not_zero_and_retains_lower_bound() -> None:
    record = patient([
        encounter("a", START, [40]),
        encounter("b", date(2026, 1, 6), [40]),
        encounter("c", date(2026, 1, 7), [None]),
    ], plans=[plan(minimum_days=3)], episode_end=date(2026, 1, 11))
    result = calculate(record, START, date(2026, 1, 11))
    assert result.minutes.exact is None
    assert result.minutes.values == []
    assert result.minutes.lower_bound == 80
    assert result.minutes.upper_bound is None
    assert result.minutes.status == "missing_evidence"
    assert result.weeks[0].decision == "indeterminate"


def test_known_lower_bound_can_prove_goal_despite_missing_duration() -> None:
    record = patient([
        encounter("a", START, [110]), encounter("b", START, [None]),
    ], episode_end=date(2026, 1, 11))
    result = calculate(record, START, date(2026, 1, 11))
    assert result.minutes.status == "missing_evidence"
    assert result.weeks[0].decision == "met"


def test_correlated_alternatives_do_not_create_impossible_cohort_membership() -> None:
    record = patient([
        encounter("first", START, [50, 150], choices=[{"revision": "A"}, {"revision": "B"}]),
        encounter("second", date(2026, 1, 12), [150, 50],
                  choices=[{"revision": "A"}, {"revision": "B"}]),
    ])
    result = calculate(record, START, END)
    assert result.scenario_count == 2
    assert result.minutes.exact == 200
    assert [week.decision for week in result.weeks] == ["indeterminate", "indeterminate"]
    assert cohort([record], START, END)[0].membership == "excluded"


def test_cohort_reports_confirmed_possible_and_excluded_patients() -> None:
    confirmed = patient([
        encounter("one", START, [50]), encounter("two", date(2026, 1, 12), [50]),
    ], identifier="confirmed")
    possible = patient([
        encounter("one", START, [50, 150]),
        encounter("two", date(2026, 1, 12), [50, 150]),
    ], identifier="possible")
    excluded = patient([
        encounter("one", START, [150]), encounter("two", date(2026, 1, 12), [150]),
    ], identifier="excluded")
    results = cohort([confirmed, possible, excluded], START, END)
    assert [result.membership for result in results] == ["confirmed", "possible", "excluded"]
    assert [week.minutes for week in results[1].witness] == [50, 50]
    assert all(week.decision == "not_met" for week in results[1].witness)


def test_unknown_duration_does_not_invent_cohort_witness() -> None:
    record = patient([
        encounter("one", START, [50]), encounter("two", date(2026, 1, 12), [None]),
    ])
    result = cohort([record], START, END)[0]
    assert result.membership == "analysis_incomplete"
    assert result.reason == "missing_evidence_or_unspecified_plan_policy"
    assert result.witness == []


def test_one_week_cohort_uses_requested_count() -> None:
    confirmed = patient([encounter("one", START, [50])], identifier="confirmed")
    possible = patient([encounter("one", START, [50, 150])], identifier="possible")
    excluded = patient([encounter("one", START, [150])], identifier="excluded")
    results = cohort(
        [confirmed, possible, excluded], START, date(2026, 1, 11), consecutive_weeks=1,
    )
    assert [result.membership for result in results] == ["confirmed", "possible", "excluded"]
    assert [len(result.witness) for result in results] == [1, 1, 0]
    assert results[0].witness[0].minutes == 50


def test_three_week_cohort_retains_complete_witness() -> None:
    third_week = date(2026, 1, 19)
    end = date(2026, 1, 25)
    confirmed = patient([
        encounter("one", START, [50]),
        encounter("two", date(2026, 1, 12), [50]),
        encounter("three", third_week, [50]),
    ], episode_end=end, identifier="confirmed")
    possible = patient([
        encounter("one", START, [50, 150]),
        encounter("two", date(2026, 1, 12), [50]),
        encounter("three", third_week, [50]),
    ], episode_end=end, identifier="possible")
    results = cohort([confirmed, possible], START, end, consecutive_weeks=3)
    assert [result.membership for result in results] == ["confirmed", "possible"]
    for result in results:
        assert len(result.witness) == 3
        assert [week.minutes for week in result.witness] == [50, 50, 50]
        assert [week.encounter_ids for week in result.witness] == [["one"], ["two"], ["three"]]
        assert all(week.decision == "not_met" for week in result.witness)


def test_three_week_cohort_does_not_stitch_disagreeing_scenarios() -> None:
    end = date(2026, 1, 25)
    record = patient([
        encounter("one", START, [50, 150], choices=[{"revision": "A"}, {"revision": "B"}]),
        encounter("two", date(2026, 1, 12), [50]),
        encounter("three", date(2026, 1, 19), [150, 50],
                  choices=[{"revision": "A"}, {"revision": "B"}]),
    ], episode_end=end)
    assert cohort([record], START, end)[0].membership == "confirmed"
    result = cohort([record], START, end, consecutive_weeks=3)[0]
    assert result.membership == "excluded"
    assert result.witness == []


def test_three_week_missing_duration_remains_unresolved() -> None:
    end = date(2026, 1, 25)
    record = patient([
        encounter("one", START, [50]),
        encounter("two", date(2026, 1, 12), [None]),
        encounter("three", date(2026, 1, 19), [50]),
    ], episode_end=end)
    result = cohort([record], START, end, consecutive_weeks=3)[0]
    assert result.membership == "analysis_incomplete"
    assert result.reason == "missing_evidence_or_unspecified_plan_policy"
    assert result.witness == []


def test_requested_week_count_longer_than_episode_is_excluded() -> None:
    record = patient([
        encounter("one", START, [50]), encounter("two", date(2026, 1, 12), [50]),
    ])
    assert cohort([record], START, END, consecutive_weeks=3)[0].membership == "excluded"


@pytest.mark.parametrize("count", [0, -1])
def test_consecutive_week_count_must_be_positive(count: int) -> None:
    with pytest.raises(ValueError, match="Consecutive week count must be positive"):
        cohort([], START, END, consecutive_weeks=count)
    with pytest.raises(ValueError, match="Consecutive week count must be positive"):
        consecutive_window([], count)


def test_consecutive_window_rejects_calendar_gaps() -> None:
    weeks = [WeekWitness(
        week_start=day, distinct_days=1, minutes=50, known_minutes=50,
        decision="not_met", encounter_ids=[],
    ) for day in [START, date(2026, 1, 12), date(2026, 1, 26)]]
    assert consecutive_window(weeks, 3) == []
    assert len(consecutive_window(weeks, 2)) == 2


def test_unknown_attendance_exposes_uncertain_counts() -> None:
    record = patient([
        encounter("one", START, [50], attendance="unknown"),
    ], episode_end=date(2026, 1, 11))
    result = calculate(record, START, date(2026, 1, 11))
    assert result.session_count.exact is None
    assert result.session_count.lower_bound == 0
    assert result.session_count.upper_bound == 1
    assert result.session_count.status == "missing_evidence"
    assert result.contributions[0].inclusion == "uncertain"


def test_omitted_alternative_attendance_uses_established_complementary_attestation() -> None:
    event = encounter("one", START, [50])
    event.alternatives[0].attendance = "unknown"
    record = patient([event], plans=[plan(minimum_minutes=30)], episode_end=date(2026, 1, 11))
    result = calculate(record, START, date(2026, 1, 11))
    assert result.session_count.exact == 1
    assert result.minutes.exact == 50
    assert result.weeks[0].decision == "met"


def test_explicit_absence_alternative_is_not_overridden_by_canonical_attendance() -> None:
    event = encounter("one", START, [50, 0])
    event.alternatives[0].attendance = "attended"
    event.alternatives[1].attendance = "no_show"
    event.alternatives[1].patient_present = False
    record = patient([event], plans=[plan(minimum_minutes=30)], episode_end=date(2026, 1, 11))
    result = calculate(record, START, date(2026, 1, 11))
    assert result.session_count.values == [0, 1]
    assert result.minutes.values == [0, 50]
    assert result.weeks[0].decision == "indeterminate"


def test_initial_plan_start_is_not_a_change_when_review_begins_before_episode() -> None:
    record = patient([encounter("one", START, [110])])
    comparison = compare_plans(record, date(2026, 1, 1), END)
    assert comparison.change_date is None
    assert comparison.candidate_change_dates == []
    assert comparison.before is None and comparison.after is None
    explicit = compare_plans(record, date(2026, 1, 1), END, change_date=START)
    assert explicit.before is None and explicit.after is None
    assert "not a documented change" in explicit.reason


def test_known_prior_plan_establishes_change_at_episode_start() -> None:
    prior = plan(effective_start=date(2026, 1, 1))
    revised = plan(minimum_minutes=150, effective_start=START)
    record = patient([encounter("one", START, [110])], plans=[prior, revised])
    comparison = compare_plans(record, date(2026, 1, 1), END)
    assert comparison.change_date == START
    assert comparison.before is not None and comparison.after is not None
    assert comparison.before.end == date(2026, 1, 4)


def test_changed_plan_uses_effective_week_and_explicit_comparison_windows() -> None:
    change = date(2026, 1, 12)
    record = patient([
        encounter("one", START, [110]), encounter("two", change, [110]),
    ], plans=[plan(), plan(minimum_days=2, minimum_minutes=150, effective_start=change)])
    result = calculate(record, START, END)
    assert [week.decision for week in result.weeks] == ["met", "not_met"]
    comparison = compare_plans(record, START, END)
    assert comparison.change_date == change
    assert comparison.before is not None and comparison.before.end == date(2026, 1, 11)
    assert comparison.after is not None and comparison.after.start == change
    assert comparison.after.minutes.exact == 110


def test_midweek_plan_transition_remains_indeterminate() -> None:
    record = patient([encounter("one", START, [200])], plans=[
        plan(), plan(minimum_days=2, minimum_minutes=150, effective_start=date(2026, 1, 8)),
    ], episode_end=date(2026, 1, 11))
    week = calculate(record, START, date(2026, 1, 11)).weeks[0]
    assert week.goal is None
    assert week.decision == "indeterminate"
    assert week.goal_reason == "conflicting_or_midweek_plan_policy_unspecified"


def test_partial_review_does_not_prorate_or_claim_missing_days_failed() -> None:
    record = patient([encounter("one", START, [50])])
    week = calculate(record, START, date(2026, 1, 9)).weeks[0]
    assert week.goal is not None and week.goal.minimum_minutes == 100
    assert week.partial_week and not week.complete_episode_coverage
    assert week.decision == "indeterminate"
    record.episode_end = date(2026, 1, 9)
    complete = calculate(record, START, date(2026, 1, 9)).weeks[0]
    assert complete.partial_week and complete.complete_episode_coverage
    assert complete.decision == "not_met"


def test_budget_cap_is_distinct_from_evidence_uncertainty() -> None:
    record = patient([
        encounter("one", START, [50, 150]),
        encounter("two", date(2026, 1, 12), [50, 150]),
    ])
    result = calculate(record, START, END, scenario_budget=1)
    assert result.analysis_status == "analysis_incomplete"
    assert result.reason == "scenario_budget_exceeded"
    assert result.minutes.status == "analysis_incomplete"
    classification = cohort([record], START, END, scenario_budget=1)[0]
    assert classification.membership == "analysis_incomplete"
    assert classification.reason == "scenario_budget_exceeded"
    assert classification.witness == []


def test_narrow_query_preserves_constraints_from_other_dates() -> None:
    record = patient([
        encounter("first", START, [50, 150], choices=[{"revision": "A"}, {"revision": "B"}]),
        encounter("constraint", date(2026, 1, 12), [150], choices=[{"revision": "A"}]),
    ])
    result = calculate(record, START, date(2026, 1, 11))
    assert result.minutes.exact == 50
    assert result.session_count.exact == 1
    assert result.scenario_count == 1
    assert [item.encounter_id for item in result.contributions] == ["first"]
    assert result.contributions[0].minutes == [50]
    assert result.contributions[0].choices == [{"revision": "A"}]
    assert [item.document_id for item in result.constraint_sources] == ["constraint"]


def test_cohort_does_not_treat_weeks_outside_episode_as_unknown_failures() -> None:
    record = patient([encounter("one", START, [150])], episode_end=date(2026, 1, 11))
    result = cohort([record], START, date(2026, 2, 1))[0]
    assert result.membership == "excluded"


def test_event_date_alternatives_cross_weeks_without_creating_two_contacts() -> None:
    contact = encounter("disputed", date(2026, 1, 11), [60, 60])
    contact.alternatives[0].service_date = date(2026, 1, 11)
    contact.alternatives[1].service_date = date(2026, 1, 12)
    record = patient([contact])
    result = calculate(record, START, END)
    assert result.session_count.exact == 1
    assert result.distinct_days.exact == 1
    assert result.minutes.exact == 60
    assert [week.session_count.values for week in result.weeks] == [[0, 1], [0, 1]]
    assert result.contributions[0].service_dates == [date(2026, 1, 11), date(2026, 1, 12)]
    narrow = calculate(record, date(2026, 1, 12), END)
    assert narrow.session_count.values == [0, 1]
    assert narrow.minutes.values == [0, 60]
    assert narrow.contributions[0].inclusion == "uncertain"


def test_service_interpretations_evaluate_eligibility_before_counting() -> None:
    contact = encounter("disputed", START, [60, 60], service="collateral", present=False)
    contact.alternatives[0].service_type = "collateral"
    contact.alternatives[0].patient_present = False
    contact.alternatives[1].service_type = "individual"
    contact.alternatives[1].patient_present = True
    result = calculate(patient([contact]), START, END)
    assert result.session_count.values == [0, 1]
    assert result.session_counts["individual"].values == [0, 1]
    assert result.session_counts["collateral"].exact == 0
    assert result.contributions[0].inclusion == "uncertain"
    eligibility = {
        item.service_type: item.eligible for item in result.contributions[0].interpretations
    }
    assert eligibility == {
        "collateral": False, "individual": True,
    }


def test_date_interpretation_selects_the_plan_effective_on_that_date() -> None:
    contact = encounter("disputed", date(2026, 1, 11), [60, 60])
    contact.alternatives[0].service_date = date(2026, 1, 11)
    contact.alternatives[1].service_date = date(2026, 1, 12)
    revised = plan(effective_start=date(2026, 1, 12))
    revised.eligible_services = ["family"]
    record = patient([contact], plans=[plan(), revised])
    result = calculate(record, START, END)
    assert result.session_count.values == [0, 1]
    assert result.minutes.values == [0, 60]
    assert result.weeks[1].session_count.exact == 0


def test_attendance_and_presence_interpretations_remain_coupled() -> None:
    contact = encounter("disputed", START, [60, 60], attendance="no_show", present=False)
    contact.alternatives[0].attendance = "no_show"
    contact.alternatives[0].patient_present = False
    contact.alternatives[1].attendance = "attended"
    contact.alternatives[1].patient_present = True
    result = calculate(patient([contact]), START, END)
    assert result.session_count.values == [0, 1]
    assert result.minutes.values == [0, 60]
    interpretations = result.contributions[0].interpretations
    assert [(item.attendance, item.patient_present, item.eligible) for item in interpretations] == [
        ("no_show", False, False), ("attended", True, True),
    ]


def test_unlinked_identity_descriptions_do_not_produce_confident_counts() -> None:
    first = encounter("unlinked-first", START, [60])
    second = encounter("unlinked-second", START, [60])
    first.decisions = [Decision(
        field="identity", status="missing_evidence",
        reason="No stable identifier links these descriptions.", sources=first.sources,
    )]
    record = patient([first, second])
    result = calculate(record, START, END)
    assert result.analysis_status == "analysis_incomplete"
    assert result.reason == "unresolved_encounter_identity"
    assert result.session_count.exact is None
    assert result.session_count.lower_bound == 0
    assert result.minutes.exact is None
    assert cohort([record], START, END)[0].membership == "analysis_incomplete"
