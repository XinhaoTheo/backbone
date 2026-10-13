from dataclasses import dataclass, field
from datetime import date

import pytest
from pydantic import ValidationError

from backbone.models import (
    ClinicalSnapshot,
    ContactAlternative,
    Encounter,
    ModelUsage,
    PatientRecord,
    PlanClaim,
    QueryOperation,
    QueryPlan,
    QueryTask,
)
from backbone.planning import (
    IntentResult,
    PatientScope,
    PlanningContext,
    QueryIntent,
    QueryPlanningError,
    TaskIntent,
    TimeIntent,
    plan_question,
    validate_plan,
)


@dataclass
class FakePlanner:
    result: IntentResult
    questions: list[str] = field(default_factory=list)
    contexts: list[PlanningContext] = field(default_factory=list)

    def interpret(self, question: str, context: PlanningContext) -> IntentResult:
        self.questions.append(question)
        self.contexts.append(context)
        return self.result


def patient(
    name: str = "Casey Morgan",
    identifier: str = "P1",
    organization: str = "Test clinic",
    start: date = date(2027, 2, 1),
) -> PatientRecord:
    return PatientRecord(
        patient_id=identifier,
        name=name,
        organization=organization,
        episode_start=start,
        episode_end=date(2027, 2, 28),
        encounters=[],
        plans=[],
        assessments=[],
        observations=[],
    )


def snapshot(*patients: PatientRecord) -> ClinicalSnapshot:
    return ClinicalSnapshot(snapshot_id=9, patients=list(patients) or [patient()])


def planner_for(*tasks: TaskIntent) -> FakePlanner:
    return FakePlanner(
        IntentResult(
            intent=QueryIntent(status="ready", message="", tasks=list(tasks)),
            model="test-planner",
            model_calls=1,
            usage=ModelUsage(input_tokens=100, output_tokens=30),
            elapsed_seconds=0.25,
        )
    )


def documented_plan(start: date) -> PlanClaim:
    return PlanClaim(
        patient_id="P1",
        effective_start=start,
        effective_end=None,
        minimum_days=2,
        minimum_minutes=90,
        eligible_services=["individual"],
        week_start="Monday",
        patient_present_required=True,
        note="Patient-present therapy.",
        quotes=["Two therapy days and 90 minutes weekly."],
    )


def encounter(identifier: str, *dates: date) -> Encounter:
    return Encounter(
        encounter_id=identifier,
        patient_id="P1",
        service_date=dates[0],
        service_type="individual",
        attendance="attended",
        patient_present=True,
        alternatives=[
            ContactAlternative(service_date=day, minutes=30, intervals=[], sources=[])
            for day in dates
        ],
        decisions=[],
        sources=[],
    )


def test_model_intent_resolves_calendar_range_and_retains_planning_metadata() -> None:
    engine = planner_for(
        TaskIntent(
            operation="durations",
            patients=PatientScope(references=["Casey"]),
            time=TimeIntent(kind="range", start=date(2027, 2, 1), end=date(2027, 2, 28)),
            metrics=["minutes"],
        )
    )
    question = "Give me Casey's total contact time through the end of February."
    plan = plan_question(question, snapshot(), planner=engine)
    assert plan.question == question
    assert plan.snapshot_id == 9
    assert plan.tasks[0].patient == "P1"
    assert (plan.tasks[0].start, plan.tasks[0].end) == (date(2027, 2, 1), date(2027, 2, 28))
    assert plan.tasks[0].metrics == ["minutes"]
    assert plan.planner_model == "test-planner"
    assert plan.planner_model_calls == 1
    assert plan.planner_usage.input_tokens == 100
    assert plan.planner_elapsed_seconds == 0.25
    assert engine.questions == [question]
    assert len(engine.contexts) == 1
    assert engine.contexts[0].patients[0].episode_start == date(2027, 2, 1)


def test_relative_first_two_weeks_use_documented_episode_start() -> None:
    engine = planner_for(
        TaskIntent(
            operation="counts",
            time=TimeIntent(kind="relative", anchor="episode_start", length=2, length_unit="weeks"),
        )
    )
    plan = plan_question("Count treatment in the first two weeks.", snapshot(), planner=engine)
    assert (plan.tasks[0].start, plan.tasks[0].end) == (date(2027, 2, 1), date(2027, 2, 14))


def test_relative_calendar_week_is_resolved_by_date_arithmetic() -> None:
    engine = planner_for(
        TaskIntent(
            operation="timeline",
            time=TimeIntent(
                kind="relative",
                anchor="episode_start",
                offset=1,
                offset_unit="weeks",
                length=1,
                length_unit="weeks",
                align_to_calendar_week=True,
            ),
        )
    )
    plan = plan_question(
        "Show the calendar week after intake.",
        snapshot(patient(start=date(2027, 2, 3))),
        planner=engine,
    )
    assert (plan.tasks[0].start, plan.tasks[0].end) == (date(2027, 2, 8), date(2027, 2, 14))


def test_explicit_dates_remain_discrete_for_non_day_operations() -> None:
    engine = planner_for(
        TaskIntent(
            operation="durations",
            time=TimeIntent(kind="dates", dates=[date(2027, 2, 11), date(2027, 2, 9)]),
        )
    )
    plan = plan_question("Total only Tuesday and Thursday.", snapshot(), planner=engine)
    assert plan.tasks[0].selected_dates == [date(2027, 2, 9), date(2027, 2, 11)]
    assert (plan.tasks[0].start, plan.tasks[0].end) == (date(2027, 2, 9), date(2027, 2, 11))


def test_three_week_cohort_condition_is_retained_and_scope_is_explicit() -> None:
    engine = planner_for(
        TaskIntent(operation="cohort", patients=PatientScope(kind="all"), consecutive_weeks=3)
    )
    plan = plan_question(
        "Which patients missed their targets for three consecutive weeks?",
        snapshot(patient(), patient("Alex Taylor", "P2")),
        planner=engine,
    )
    assert plan.tasks[0].patient is None
    assert plan.tasks[0].patient_ids == ["P1", "P2"]
    assert plan.tasks[0].consecutive_weeks == 3


def test_multiple_patients_and_operations_expand_into_linked_tasks() -> None:
    scope = PatientScope(references=["Casey Morgan", "Alex Taylor"])
    engine = planner_for(
        TaskIntent(operation="counts", patients=scope, metrics=["sessions"]),
        TaskIntent(operation="symptoms", patients=scope),
    )
    plan = plan_question(
        "Compare attendance and symptoms for Casey and Alex.",
        snapshot(patient(), patient("Alex Taylor", "P2")),
        planner=engine,
    )
    assert [(task.operation, task.patient) for task in plan.tasks] == [
        ("counts", "P1"),
        ("counts", "P2"),
        ("symptoms", "P1"),
        ("symptoms", "P2"),
    ]


def test_organization_scope_filters_documented_catalog() -> None:
    engine = planner_for(
        TaskIntent(
            operation="cohort",
            patients=PatientScope(kind="organization", organization="Test clinic"),
        )
    )
    plan = plan_question(
        "Review patients at this clinic.",
        snapshot(patient(), patient("Alex Taylor", "P2", "Another clinic")),
        planner=engine,
    )
    assert plan.tasks[0].patient_ids == ["P1"]


def test_unknown_patient_never_defaults_to_the_only_patient() -> None:
    engine = planner_for(
        TaskIntent(operation="counts", patients=PatientScope(references=["Taylor"]))
    )
    with pytest.raises(QueryPlanningError, match="not present"):
        plan_question("Count Taylor's sessions.", snapshot(), planner=engine)


def test_shared_name_requires_disambiguation_but_full_name_resolves() -> None:
    shared = snapshot(patient(), patient("Casey Taylor", "P2"))
    ambiguous = planner_for(
        TaskIntent(operation="counts", patients=PatientScope(references=["Casey"]))
    )
    with pytest.raises(QueryPlanningError, match="ambiguous"):
        plan_question("Count Casey's sessions.", shared, planner=ambiguous)
    explicit = planner_for(
        TaskIntent(operation="counts", patients=PatientScope(references=["Casey Taylor"]))
    )
    assert (
        plan_question("Count Casey Taylor's sessions.", shared, planner=explicit).tasks[0].patient
        == "P2"
    )


def test_missing_patient_in_population_does_not_select_first_patient() -> None:
    engine = planner_for(TaskIntent(operation="counts"))
    with pytest.raises(QueryPlanningError, match="Name the patient"):
        plan_question(
            "How much therapy was provided?",
            snapshot(patient(), patient("Alex Taylor", "P2")),
            planner=engine,
        )


def test_source_patient_identifier_alias_resolves_canonical_identifier() -> None:
    engine = planner_for(TaskIntent(operation="counts", patients=PatientScope(references=["MRN8"])))
    plan = plan_question(
        "Count MRN8's sessions.", snapshot(patient(identifier="clinic::MRN8")), planner=engine
    )
    assert plan.tasks[0].patient == "clinic::MRN8"


@pytest.mark.parametrize("status", ["clarification_required", "unsupported"])
def test_unexecutable_model_intent_is_reported_without_fallback(
    status: str,
) -> None:
    intent = QueryIntent.model_validate(
        {"status": status, "message": "Specify the desired metric.", "tasks": []}
    )
    engine = FakePlanner(IntentResult(intent=intent))
    with pytest.raises(QueryPlanningError, match="Specify the desired metric"):
        plan_question("Review everything.", snapshot(), planner=engine)


def test_previous_plan_supplies_patient_and_date_context() -> None:
    previous = QueryPlan(
        question="Count Casey's sessions.",
        snapshot_id=9,
        tasks=[
            QueryTask(
                operation="counts",
                patient="P1",
                patient_ids=["P1"],
                start=date(2027, 2, 3),
                end=date(2027, 2, 17),
            )
        ],
    )
    engine = planner_for(
        TaskIntent(
            operation="durations",
            patients=PatientScope(kind="context"),
            time=TimeIntent(kind="context"),
        )
    )
    plan = plan_question(
        "And the minutes for that patient and period?", snapshot(), planner=engine, context=previous
    )
    assert plan.tasks[0].patient == "P1"
    assert (plan.tasks[0].start, plan.tasks[0].end) == (date(2027, 2, 3), date(2027, 2, 17))
    assert engine.contexts[0].previous_plan == previous


@pytest.mark.parametrize("reference", ["patient", "time"])
def test_context_reference_without_previous_plan_requires_clarification(reference: str) -> None:
    engine = planner_for(
        TaskIntent(
            operation="counts",
            patients=PatientScope(kind="context") if reference == "patient" else PatientScope(),
            time=TimeIntent(kind="context") if reference == "time" else TimeIntent(),
        )
    )
    with pytest.raises(QueryPlanningError, match="no previous query context"):
        plan_question("Use the same one as before.", snapshot(), planner=engine)


def test_plan_change_anchor_is_taken_from_documented_plan() -> None:
    record = patient()
    record.plans = [documented_plan(date(2027, 2, 1)), documented_plan(date(2027, 2, 15))]
    engine = planner_for(
        TaskIntent(operation="durations", time=TimeIntent(kind="relative", anchor="plan_change")),
        TaskIntent(operation="plan_change"),
    )
    plan = plan_question(
        "Compare before and after the revised plan.", snapshot(record), planner=engine
    )
    assert (plan.tasks[0].start, plan.tasks[0].end) == (date(2027, 2, 15), date(2027, 2, 28))
    assert plan.tasks[1].change_date == date(2027, 2, 15)


def test_multiple_plan_changes_require_an_explicit_documented_boundary() -> None:
    record = patient()
    record.plans = [documented_plan(date(2027, 2, day)) for day in (1, 8, 15)]
    engine = planner_for(TaskIntent(operation="plan_change"))
    with pytest.raises(QueryPlanningError, match="Specify which"):
        plan_question("Compare before and after the change.", snapshot(record), planner=engine)
    selected = planner_for(TaskIntent(operation="plan_change", change_date=date(2027, 2, 15)))
    assert plan_question("Compare the latest change.", snapshot(record), planner=selected).tasks[
        0
    ].change_date == date(2027, 2, 15)
    invented = planner_for(TaskIntent(operation="plan_change", change_date=date(2027, 2, 10)))
    with pytest.raises(QueryPlanningError, match="No documented plan change"):
        plan_question("Compare the change.", snapshot(record), planner=invented)


@pytest.mark.parametrize(
    "time, message",
    [
        (TimeIntent(kind="range"), "no resolved boundary"),
        (TimeIntent(kind="relative"), "documented anchor"),
        (TimeIntent(kind="relative", anchor="first_encounter"), "missing or disputed"),
        (TimeIntent(kind="relative", anchor="episode_start", length=0), "positive"),
        (TimeIntent(kind="range", start=date(2027, 2, 17), end=date(2027, 2, 3)), "start follows"),
    ],
)
def test_unresolved_or_invalid_model_dates_do_not_become_episode_scope(
    time: TimeIntent,
    message: str,
) -> None:
    engine = planner_for(TaskIntent(operation="counts", time=time))
    with pytest.raises(QueryPlanningError, match=message):
        plan_question("Count sessions in the requested period.", snapshot(), planner=engine)


def test_saved_plan_replay_requires_original_question_and_snapshot() -> None:
    question = "Count sessions."
    view = snapshot()
    plan = QueryPlan(
        question=question,
        snapshot_id=view.snapshot_id,
        tasks=[
            QueryTask(
                operation="counts",
                patient="P1",
                patient_ids=["P1"],
                start=date(2027, 2, 1),
                end=date(2027, 2, 28),
            )
        ],
    )
    restored = QueryPlan.model_validate_json(plan.model_dump_json())
    validate_plan(restored, question, view)
    with pytest.raises(QueryPlanningError, match="question and snapshot"):
        validate_plan(restored, "Count different sessions.", view)
    with pytest.raises(QueryPlanningError, match="question and snapshot"):
        validate_plan(restored, question, view.model_copy(update={"snapshot_id": 10}))


def test_saved_plan_cannot_reference_nonexistent_patient() -> None:
    plan = QueryPlan(
        question="Count sessions.",
        snapshot_id=9,
        tasks=[
            QueryTask(
                operation="counts",
                patient="missing",
                patient_ids=["missing"],
                start=date(2027, 2, 1),
                end=date(2027, 2, 28),
            )
        ],
    )
    with pytest.raises(QueryPlanningError, match="patients present"):
        validate_plan(plan, plan.question, snapshot())


def test_disputed_first_encounter_date_cannot_anchor_relative_query() -> None:
    record = patient()
    record.encounters = [encounter("E1", date(2027, 2, 4), date(2027, 2, 7))]
    engine = planner_for(
        TaskIntent(
            operation="counts",
            time=TimeIntent(kind="relative", anchor="first_encounter", length=7),
        )
    )
    with pytest.raises(QueryPlanningError, match="missing or disputed"):
        plan_question(
            "Count the first week after the initial encounter.", snapshot(record), planner=engine
        )
    assert engine.contexts[0].patients[0].first_encounter is None


def test_earlier_stable_encounter_establishes_anchor_despite_later_date_conflict() -> None:
    record = patient()
    record.encounters = [
        encounter("EARLY", date(2027, 2, 3)),
        encounter("LATER", date(2027, 2, 4), date(2027, 2, 7)),
    ]
    engine = planner_for(
        TaskIntent(
            operation="counts",
            time=TimeIntent(kind="relative", anchor="first_encounter", length=7),
        )
    )
    plan = plan_question("Count the first week of contacts.", snapshot(record), planner=engine)
    assert engine.contexts[0].patients[0].first_encounter == date(2027, 2, 3)
    assert (plan.tasks[0].start, plan.tasks[0].end) == (date(2027, 2, 3), date(2027, 2, 9))


def test_undated_unrelated_patient_does_not_block_named_patients_fixed_range() -> None:
    undated = patient("Alex Taylor", "P2")
    undated.episode_start = None
    undated.episode_end = None
    engine = planner_for(
        TaskIntent(
            operation="counts",
            patients=PatientScope(references=["P1"]),
            time=TimeIntent(kind="range", start=date(2027, 2, 3), end=date(2027, 2, 17)),
        )
    )
    plan = plan_question(
        "Count Casey's sessions in this period.", snapshot(patient(), undated), planner=engine
    )
    assert plan.tasks[0].patient == "P1"
    assert (plan.tasks[0].start, plan.tasks[0].end) == (date(2027, 2, 3), date(2027, 2, 17))
    assert engine.contexts[0].patients[1].review_start is None
    assert engine.contexts[0].patients[1].episode_start is None


def test_missing_documented_episode_start_does_not_use_observed_date_as_relative_anchor() -> None:
    record = patient()
    record.episode_start = None
    record.encounters = [encounter("E1", date(2027, 2, 4))]
    engine = planner_for(
        TaskIntent(
            operation="counts",
            time=TimeIntent(kind="relative", anchor="episode_start", length=7),
        )
    )
    with pytest.raises(QueryPlanningError, match="No documented episode start"):
        plan_question("Count the first week of the episode.", snapshot(record), planner=engine)
    assert engine.contexts[0].patients[0].review_start == date(2027, 2, 4)
    assert engine.contexts[0].patients[0].episode_start is None


def test_multi_patient_context_requires_a_selected_prior_patient() -> None:
    previous = QueryPlan(
        question="Compare Casey and Alex.",
        snapshot_id=9,
        tasks=[
            QueryTask(
                operation="counts",
                patient=identifier,
                patient_ids=[identifier],
                start=date(2027, 2, 1),
                end=date(2027, 2, 28),
            )
            for identifier in ("P1", "P2")
        ],
    )
    view = snapshot(patient(), patient("Alex Taylor", "P2"))
    ambiguous = planner_for(
        TaskIntent(operation="durations", patients=PatientScope(kind="context"))
    )
    with pytest.raises(QueryPlanningError, match="multiple patients"):
        plan_question("Show that patient's minutes.", view, planner=ambiguous, context=previous)
    explicit = planner_for(
        TaskIntent(operation="durations", patients=PatientScope(kind="context", references=["P2"]))
    )
    plan = plan_question("Show Alex's minutes.", view, planner=explicit, context=previous)
    assert plan.tasks[0].patient == "P2"
    assert plan.tasks[0].patient_ids == ["P2"]


@pytest.mark.parametrize("identifiers", [[], ["P2"], ["P1", "P2"]])
def test_saved_individual_task_patient_ids_must_exactly_match_patient(
    identifiers: list[str],
) -> None:
    plan = QueryPlan(
        question="Count Casey's sessions.",
        snapshot_id=9,
        tasks=[
            QueryTask(
                operation="counts",
                patient="P1",
                patient_ids=identifiers,
                start=date(2027, 2, 1),
                end=date(2027, 2, 28),
            )
        ],
    )
    with pytest.raises(QueryPlanningError, match="must match its individual patient"):
        validate_plan(plan, plan.question, snapshot(patient(), patient("Alex Taylor", "P2")))


@pytest.mark.parametrize("operation", ["weekly", "cohort", "plan_change"])
def test_saved_continuous_operation_cannot_silently_ignore_selected_dates(
    operation: QueryOperation,
) -> None:
    plan = QueryPlan(
        question="Review the selected dates.",
        snapshot_id=9,
        tasks=[
            QueryTask(
                operation=operation,
                patient="P1",
                patient_ids=["P1"],
                start=date(2027, 2, 1),
                end=date(2027, 2, 28),
                selected_dates=[date(2027, 2, 3), date(2027, 2, 17)],
            )
        ],
    )
    with pytest.raises(QueryPlanningError, match="continuous date range"):
        validate_plan(plan, plan.question, snapshot())


@pytest.mark.parametrize(
    "time",
    [
        TimeIntent(kind="range", start=date(2027, 2, 3), end=date(2027, 2, 17)),
        TimeIntent(kind="dates", dates=[date(2027, 2, 3), date(2027, 2, 17)]),
    ],
)
def test_explicit_dates_do_not_require_documented_episode_or_encounters(time: TimeIntent) -> None:
    record = patient()
    record.episode_start = None
    record.episode_end = None
    engine = planner_for(TaskIntent(operation="durations", time=time))
    plan = plan_question("Review the dates I specified.", snapshot(record), planner=engine)
    assert (plan.tasks[0].start, plan.tasks[0].end) == (date(2027, 2, 3), date(2027, 2, 17))
    assert plan.tasks[0].selected_dates == time.dates
    assert engine.contexts[0].patients[0].review_start is None


def test_previous_fixed_range_can_be_reused_without_documented_episode_dates() -> None:
    record = patient()
    record.episode_start = None
    record.episode_end = None
    previous = QueryPlan(
        question="Count the specified dates.",
        snapshot_id=9,
        tasks=[
            QueryTask(
                operation="counts",
                patient="P1",
                patient_ids=["P1"],
                start=date(2027, 2, 3),
                end=date(2027, 2, 17),
            )
        ],
    )
    engine = planner_for(
        TaskIntent(
            operation="durations",
            patients=PatientScope(kind="context"),
            time=TimeIntent(kind="context"),
        )
    )
    plan = plan_question(
        "And the minutes in that same period?", snapshot(record), planner=engine, context=previous
    )
    assert (plan.tasks[0].start, plan.tasks[0].end) == (date(2027, 2, 3), date(2027, 2, 17))


def test_finite_plan_change_relative_range_does_not_require_episode_dates() -> None:
    record = patient()
    record.episode_start = None
    record.episode_end = None
    record.plans = [documented_plan(date(2027, 2, 1)), documented_plan(date(2027, 2, 15))]
    engine = planner_for(
        TaskIntent(
            operation="durations",
            time=TimeIntent(kind="relative", anchor="plan_change", length=1, length_unit="weeks"),
        )
    )
    plan = plan_question(
        "Show the first seven days under the revised plan.", snapshot(record), planner=engine
    )
    assert (plan.tasks[0].start, plan.tasks[0].end) == (date(2027, 2, 15), date(2027, 2, 21))


@pytest.mark.parametrize("field, value", [("custom_threshold", 120), ("service_filter", ["group"])])
def test_saved_task_rejects_unimplemented_conditions_instead_of_ignoring_them(
    field: str,
    value: object,
) -> None:
    task = QueryTask(
        operation="counts",
        patient="P1",
        patient_ids=["P1"],
        start=date(2027, 2, 1),
        end=date(2027, 2, 28),
    )
    payload: dict[str, object] = {**task.model_dump(), field: value}
    with pytest.raises(ValidationError, match=field):
        QueryTask.model_validate(payload)


@pytest.mark.parametrize("field, value", [("custom_threshold", 120), ("service_filter", ["group"])])
def test_saved_plan_rejects_unimplemented_conditions_instead_of_ignoring_them(
    field: str,
    value: object,
) -> None:
    plan = QueryPlan(
        question="Count therapy sessions.",
        snapshot_id=9,
        tasks=[
            QueryTask(
                operation="counts",
                patient="P1",
                patient_ids=["P1"],
                start=date(2027, 2, 1),
                end=date(2027, 2, 28),
            )
        ],
    )
    payload: dict[str, object] = {**plan.model_dump(), field: value}
    with pytest.raises(ValidationError, match=field):
        QueryPlan.model_validate(payload)


@pytest.mark.parametrize("missing_start", [True, False])
def test_open_range_only_requires_the_boundary_that_was_omitted(missing_start: bool) -> None:
    record = patient()
    if missing_start:
        record.episode_start = None
        time = TimeIntent(kind="range", start=date(2027, 2, 3))
        expected = (date(2027, 2, 3), date(2027, 2, 28))
    else:
        record.episode_end = None
        time = TimeIntent(kind="range", end=date(2027, 2, 17))
        expected = (date(2027, 2, 1), date(2027, 2, 17))
    plan = plan_question(
        "Use the explicit boundary and the available episode boundary.",
        snapshot(record),
        planner=planner_for(TaskIntent(operation="counts", time=time)),
    )
    assert (plan.tasks[0].start, plan.tasks[0].end) == expected


def test_since_plan_change_only_requires_the_documented_episode_end() -> None:
    record = patient()
    record.episode_start = None
    record.plans = [documented_plan(date(2027, 2, 1)), documented_plan(date(2027, 2, 15))]
    plan = plan_question(
        "Count sessions since the plan changed.",
        snapshot(record),
        planner=planner_for(
            TaskIntent(
                operation="counts",
                time=TimeIntent(kind="relative", anchor="plan_change"),
            )
        ),
    )
    assert (plan.tasks[0].start, plan.tasks[0].end) == (date(2027, 2, 15), date(2027, 2, 28))
