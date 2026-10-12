from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Literal

from pydantic import BaseModel, Field

from backbone.models import ContactAlternative, Encounter, PatientRecord, PlanClaim, SourceRef

ResultStatus = Literal[
    "established", "conflicting_evidence", "missing_evidence", "analysis_incomplete"
]
WeeklyDecision = Literal["met", "not_met", "indeterminate"]


class IntegerResult(BaseModel):
    values: list[int]
    exact: int | None
    lower_bound: int
    upper_bound: int | None
    status: ResultStatus
    reason: str


class ContactInterpretation(BaseModel):
    service_date: date
    service_type: str
    attendance: str
    patient_present: bool | None
    minutes: int | None
    eligible: bool
    in_review_range: bool
    choices: dict[str, str]
    sources: list[SourceRef]


class Contribution(BaseModel):
    encounter_id: str
    service_date: date
    service_type: str
    inclusion: Literal["included", "excluded", "uncertain"]
    reason: str
    minutes: list[int | None]
    choices: list[dict[str, str]]
    sources: list[SourceRef]
    service_dates: list[date] = Field(default_factory=list)
    service_types: list[str] = Field(default_factory=list)
    interpretations: list[ContactInterpretation] = Field(default_factory=list)


class PlanGoal(BaseModel):
    minimum_days: int
    minimum_minutes: int
    eligible_services: list[str]
    patient_present_required: bool
    sources: list[SourceRef]


class WeekMetrics(BaseModel):
    week_start: date
    week_end: date
    review_start: date
    review_end: date
    partial_week: bool
    complete_episode_coverage: bool
    goal: PlanGoal | None
    goal_reason: str
    session_count: IntegerResult
    distinct_days: IntegerResult
    minutes: IntegerResult
    decision: WeeklyDecision
    reason: str
    sources: list[SourceRef]


class PatientMetrics(BaseModel):
    patient_id: str
    start: date
    end: date
    session_counts: dict[str, IntegerResult]
    session_count: IntegerResult
    distinct_days: IntegerResult
    minutes: IntegerResult
    weeks: list[WeekMetrics]
    contributions: list[Contribution]
    exclusions: list[Contribution]
    constraint_sources: list[SourceRef] = Field(default_factory=list)
    scenario_count: int
    analysis_status: Literal["complete", "analysis_incomplete"]
    reason: str


class WeekWitness(BaseModel):
    week_start: date
    distinct_days: int
    minutes: int | None
    known_minutes: int
    decision: WeeklyDecision
    encounter_ids: list[str]


class CohortResult(BaseModel):
    patient_id: str
    membership: Literal["confirmed", "possible", "excluded", "analysis_incomplete"]
    reason: str
    choices: dict[str, str] = Field(default_factory=dict)
    witness: list[WeekWitness] = Field(default_factory=list)
    sources: list[SourceRef]


class PlanComparison(BaseModel):
    patient_id: str
    change_date: date | None
    candidate_change_dates: list[date]
    before: PatientMetrics | None
    after: PatientMetrics | None
    reason: str


@dataclass
class Option:
    included: bool
    alternative: ContactAlternative | None
    choices: dict[str, str]
    encounter: Encounter


@dataclass
class Candidate:
    encounter: Encounter
    options: list[Option]
    reason: str
    missing_eligibility: bool = False
    identity_uncertain: bool = False


@dataclass
class Selection:
    encounter: Encounter
    alternative: ContactAlternative


@dataclass
class Scenario:
    selections: list[Selection]
    choices: dict[str, str]


@dataclass
class ScenarioSet:
    scenarios: list[Scenario]
    complete: bool
    reason: str


def unique_sources(sources: list[SourceRef]) -> list[SourceRef]:
    return list({source.model_dump_json(): source for source in sources}.values())


def plan_key(plan: PlanClaim) -> str:
    return (
        f"{plan.minimum_days}:{plan.minimum_minutes}:"
        f"{','.join(sorted(plan.eligible_services))}:{plan.patient_present_required}"
    )


def active_plans(patient: PatientRecord, day: date) -> list[PlanClaim]:
    plans = [
        plan for plan in patient.plans
        if plan.effective_start <= day
        and (plan.effective_end is None or day <= plan.effective_end)
    ]
    if not plans:
        return []
    latest = max(plan.effective_start for plan in plans)
    return [plan for plan in plans if plan.effective_start == latest]


def merge_choices(left: dict[str, str], right: dict[str, str]) -> dict[str, str] | None:
    if any(key in left and left[key] != value for key, value in right.items()):
        return None
    return left | right


def effective_encounter(encounter: Encounter, alternative: ContactAlternative) -> Encounter:
    return encounter.model_copy(update={
        "service_date": alternative.service_date or encounter.service_date,
        "service_type": alternative.service_type or encounter.service_type,
        "attendance": alternative.attendance or encounter.attendance,
        "patient_present": (
            alternative.patient_present if alternative.patient_present is not None
            else encounter.patient_present
        ),
    })


def eligibility_variants(
    patient: PatientRecord, encounter: Encounter
) -> list[tuple[bool | None, dict[str, str]]]:
    if encounter.attendance in ("no_show", "cancelled"):
        return [(False, {})]
    plans = active_plans(patient, encounter.service_date)
    if not plans:
        return [(None, {})]
    rules = {plan_key(plan): plan for plan in plans}
    variants: list[tuple[bool | None, dict[str, str]]] = []
    for key, plan in rules.items():
        choices = {f"plan:{plan.effective_start.isoformat()}": key} if len(rules) > 1 else {}
        eligible: bool | None = encounter.service_type in plan.eligible_services
        if eligible and plan.patient_present_required:
            eligible = encounter.patient_present
        if eligible is not False and encounter.attendance == "unknown":
            eligible = None
        variants.append((eligible, choices))
    return variants


def candidate(patient: PatientRecord, encounter: Encounter) -> Candidate:
    options: list[Option] = []
    alternatives = encounter.alternatives or [ContactAlternative(
        minutes=None, intervals=[], sources=encounter.sources
    )]
    missing = False
    for index, alternative in enumerate(alternatives):
        if alternative.minutes is not None and alternative.minutes < 0:
            raise ValueError(f"Negative duration for {encounter.encounter_id}.")
        effective = effective_encounter(encounter, alternative)
        event_choices = alternative.choices.copy()
        if len(alternatives) > 1 and any(
            value is not None for value in (
                alternative.service_date, alternative.service_type,
                alternative.attendance, alternative.patient_present,
            )
        ):
            event_choices[f"event:{encounter.encounter_id}"] = str(index)
        for eligible, choices in eligibility_variants(patient, effective):
            missing = missing or eligible is None
            combined = merge_choices(choices, event_choices)
            if combined is None:
                continue
            eligibility_key = f"eligibility:{encounter.encounter_id}"
            if eligible is not True:
                excluded_choices = (
                    combined | {eligibility_key: "excluded"} if eligible is None else combined
                )
                options.append(Option(False, alternative, excluded_choices, effective))
            if eligible is not False:
                included_choices = (
                    combined | {eligibility_key: "included"} if eligible is None else combined
                )
                options.append(Option(True, alternative, included_choices, effective))
    if options and all(option.included for option in options):
        reason = "Eligible attended patient therapy under the effective plan."
    elif options and all(not option.included for option in options):
        reason = "Every event interpretation is absent or excluded by the effective plan."
    else:
        reason = "Coupled event evidence leaves therapy inclusion unresolved."
    identity_uncertain = any(
        decision.field == "identity" and decision.status == "missing_evidence"
        for decision in encounter.decisions
    )
    if identity_uncertain:
        reason = "Unlinked descriptions may refer to the same encounter."
    return Candidate(encounter, options, reason, missing, identity_uncertain)


def enumerate_scenarios(candidates: list[Candidate], budget: int) -> ScenarioSet:
    if budget < 1:
        raise ValueError("scenario_budget must be positive.")
    frontier = [Scenario([], {})]
    examined = 0
    for item in candidates:
        following: list[Scenario] = []
        for current in frontier:
            for option in item.options:
                examined += 1
                if examined > budget:
                    return ScenarioSet([], False, "scenario_budget_exceeded")
                choices = merge_choices(current.choices, option.choices)
                if choices is None:
                    continue
                selections = current.selections.copy()
                if option.included and option.alternative is not None:
                    selections.append(Selection(option.encounter, option.alternative))
                following.append(Scenario(selections, choices))
        frontier = following
        if not frontier:
            return ScenarioSet([], False, "inconsistent_alternative_choices")
    return ScenarioSet(frontier, True, "All supported alternative choices evaluated.")


def integer_result(
    values: list[int | None], lower_bound: int, complete: bool, reason: str
) -> IntegerResult:
    known = sorted({value for value in values if value is not None})
    if not complete:
        return IntegerResult(
            values=known, exact=None, lower_bound=lower_bound, upper_bound=None,
            status="analysis_incomplete", reason=reason,
        )
    if any(value is None for value in values):
        return IntegerResult(
            values=known, exact=None, lower_bound=lower_bound, upper_bound=None,
            status="missing_evidence", reason="At least one supported scenario lacks a duration.",
        )
    if not known:
        raise ValueError("A complete scenario set must contain an interpretation.")
    return IntegerResult(
        values=known, exact=known[0] if len(known) == 1 else None,
        lower_bound=min(known), upper_bound=max(known),
        status="established" if len(known) == 1 else "conflicting_evidence",
        reason=("Identical across supported interpretations." if len(known) == 1
                else "Values are discrete alternatives from consistent source interpretations."),
    )


def selected(scenario: Scenario, start: date, end: date) -> list[Selection]:
    return [item for item in scenario.selections if start <= item.encounter.service_date <= end]


def scenario_minutes(selections: list[Selection]) -> tuple[int | None, int]:
    # Missing durations contribute no proven lower bound but remain unknown in the total.
    known = sum(item.alternative.minutes or 0 for item in selections)
    total = None if any(item.alternative.minutes is None for item in selections) else known
    return total, known


def option_in_range(option: Option, start: date, end: date, service: str | None = None) -> bool:
    return start <= option.encounter.service_date <= end and (
        service is None or option.encounter.service_type == service
    )


def candidate_in_range(item: Candidate, start: date, end: date) -> bool:
    if not item.options:
        dates = [alternative.service_date or item.encounter.service_date
                 for alternative in item.encounter.alternatives] or [item.encounter.service_date]
        return any(start <= day <= end for day in dates)
    return any(option_in_range(option, start, end) for option in item.options)


def guaranteed_selections(
    candidates: list[Candidate], start: date, end: date, service: str | None
) -> list[Candidate]:
    return [item for item in candidates if item.options and not item.identity_uncertain and all(
        option.included and option_in_range(option, start, end, service) for option in item.options
    )]


def summarize(
    candidates: list[Candidate], scenarios: ScenarioSet, start: date, end: date,
    service_type: str | None = None,
) -> tuple[IntegerResult, IntegerResult, IntegerResult]:
    relevant = [item for item in candidates if any(
        option_in_range(option, start, end, service_type) for option in item.options
    )]
    guaranteed = guaranteed_selections(relevant, start, end, service_type)
    guaranteed_minutes = sum(min(
        option.alternative.minutes or 0 for option in item.options
        if option.alternative is not None
    ) for item in guaranteed)
    counts: list[int | None] = []
    days: list[int | None] = []
    minutes: list[int | None] = []
    known_minutes: list[int] = []
    for scenario in scenarios.scenarios:
        entries = [entry for entry in selected(scenario, start, end)
                   if service_type is None or entry.encounter.service_type == service_type]
        counts.append(len(entries))
        days.append(len({entry.encounter.service_date for entry in entries}))
        total, known = scenario_minutes(entries)
        minutes.append(total)
        known_minutes.append(known)
    fixed_dates = {
        next(iter(dates)) for item in guaranteed
        if len(dates := {option.encounter.service_date for option in item.options}) == 1
    }
    day_lower_bound = max(len(fixed_dates), int(bool(guaranteed)))
    if scenarios.reason == "unresolved_encounter_identity":
        guaranteed, guaranteed_minutes, day_lower_bound = [], 0, 0
    results = (
        integer_result(counts, len(guaranteed), scenarios.complete, scenarios.reason),
        integer_result(days, day_lower_bound,
                       scenarios.complete, scenarios.reason),
        integer_result(minutes, min(known_minutes) if known_minutes else guaranteed_minutes,
                       scenarios.complete, scenarios.reason),
    )
    if any(item.missing_eligibility for item in relevant):
        for result in results:
            if result.status == "conflicting_evidence":
                result.status = "missing_evidence"
                result.reason = (
                    "Attendance, required patient presence, or plan eligibility is missing."
                )
    return results


def monday(day: date) -> date:
    return day - timedelta(days=day.weekday())


def goal_for_week(
    patient: PatientRecord, week_start: date, week_end: date
) -> tuple[PlanGoal | None, str]:
    first = max(week_start, patient.episode_start or week_start)
    last = min(week_end, patient.episode_end or week_end)
    plans: list[PlanClaim] = []
    day = first
    while day <= last:
        active = active_plans(patient, day)
        if not active:
            return None, "missing_effective_plan"
        plans.extend(active)
        day += timedelta(days=1)
    rules = {plan_key(plan): plan for plan in plans}
    if not rules:
        return None, "week_outside_episode"
    if len(rules) > 1:
        return None, "conflicting_or_midweek_plan_policy_unspecified"
    plan = next(iter(rules.values()))
    if plan.minimum_days < 0 or plan.minimum_minutes < 0:
        raise ValueError("Treatment-plan thresholds cannot be negative.")
    return PlanGoal(
        minimum_days=plan.minimum_days, minimum_minutes=plan.minimum_minutes,
        eligible_services=list(plan.eligible_services),
        patient_present_required=plan.patient_present_required,
        sources=unique_sources([source for item in plans for source in item.sources]),
    ), "Full documented thresholds; no prorating."


def weekly_decision(
    entries: list[Selection], goal: PlanGoal | None, complete_coverage: bool
) -> WeeklyDecision:
    if goal is None:
        return "indeterminate"
    days = len({entry.encounter.service_date for entry in entries})
    total, known = scenario_minutes(entries)
    if days >= goal.minimum_days and known >= goal.minimum_minutes:
        return "met"
    if not complete_coverage:
        return "indeterminate"
    if days < goal.minimum_days or (total is not None and total < goal.minimum_minutes):
        return "not_met"
    return "indeterminate"


def week_metrics(
    patient: PatientRecord, candidates: list[Candidate], scenarios: ScenarioSet,
    week_start: date, start: date, end: date,
) -> WeekMetrics:
    week_end = week_start + timedelta(days=6)
    first, last = max(start, week_start), min(end, week_end)
    episode_first = max(week_start, patient.episode_start or week_start)
    episode_last = min(week_end, patient.episode_end or week_end)
    coverage = first <= episode_first and last >= episode_last
    goal, goal_reason = goal_for_week(patient, week_start, week_end)
    counts, days, minutes = summarize(candidates, scenarios, first, last)
    decisions = {
        weekly_decision(selected(scenario, first, last), goal, coverage)
        for scenario in scenarios.scenarios
    }
    decision: WeeklyDecision = "indeterminate"
    if scenarios.complete and len(decisions) == 1:
        decision = next(iter(decisions))
    sources = [source for item in candidates if candidate_in_range(item, first, last)
               for source in item.encounter.sources]
    sources.extend(source for plan in patient.plans
                   if plan.effective_start <= week_end
                   and (plan.effective_end is None or plan.effective_end >= week_start)
                   for source in plan.sources)
    reason = (
        scenarios.reason if not scenarios.complete else
        goal_reason if goal is None else
        "Review-range totals meet every required threshold in every supported interpretation."
        if decision == "met" else
        "Every supported interpretation fails at least one required threshold."
        if decision == "not_met" else
        "Supported interpretations disagree, duration is missing, or week coverage is incomplete."
    )
    return WeekMetrics(
        week_start=week_start, week_end=week_end, review_start=first, review_end=last,
        partial_week=first != week_start or last != week_end,
        complete_episode_coverage=coverage, goal=goal, goal_reason=goal_reason,
        session_count=counts, distinct_days=days, minutes=minutes,
        decision=decision, reason=reason, sources=unique_sources(sources),
    )


def prepare(
    patient: PatientRecord, start: date, end: date, scenario_budget: int
) -> tuple[list[Candidate], ScenarioSet]:
    if start > end:
        raise ValueError("Review start must not follow review end.")
    encounters = patient.encounters
    if len({entry.encounter_id for entry in encounters}) != len(encounters):
        raise ValueError("Encounter identities must be unique within a patient abstraction.")
    all_candidates = [candidate(patient, entry) for entry in encounters]
    candidates = [item for item in all_candidates if candidate_in_range(item, start, end)]
    remaining = [item for item in all_candidates if not candidate_in_range(item, start, end)]
    # A source interpretation outside the window can constrain a shared revision inside it.
    while remaining:
        keys = {key for item in candidates for option in item.options for key in option.choices}
        connected = [item for item in remaining if any(
            key in keys for option in item.options for key in option.choices
        )]
        if not connected:
            break
        candidates.extend(connected)
        identifiers = {item.encounter.encounter_id for item in connected}
        remaining = [item for item in remaining if item.encounter.encounter_id not in identifiers]
    if any(item.identity_uncertain for item in candidates):
        return candidates, ScenarioSet([], False, "unresolved_encounter_identity")
    return candidates, enumerate_scenarios(candidates, scenario_budget)


def calculate(
    patient: PatientRecord, start: date, end: date, scenario_budget: int = 10_000
) -> PatientMetrics:
    candidates, scenarios = prepare(patient, start, end, scenario_budget)
    counts, days, minutes = summarize(candidates, scenarios, start, end)
    relevant = [item for item in candidates if candidate_in_range(item, start, end)]
    services = sorted({option.encounter.service_type for item in relevant for option in item.options
                       if option_in_range(option, start, end)})
    service_counts: dict[str, IntegerResult] = {
        service: summarize(candidates, scenarios, start, end, service)[0] for service in services
    }
    weeks: list[WeekMetrics] = []
    week = monday(start)
    while week <= end:
        weeks.append(week_metrics(patient, candidates, scenarios, week, start, end))
        week += timedelta(days=7)
    contributions: list[Contribution] = []
    exclusions: list[Contribution] = []
    for item in relevant:
        entries = [next((entry for entry in scenario.selections
                         if entry.encounter.encounter_id == item.encounter.encounter_id), None)
                   for scenario in scenarios.scenarios]
        feasible_options = [option for option in item.options if not scenarios.complete or any(
            merge_choices(scenario.choices, option.choices) is not None
            and (
                entry is None if not option.included else
                entry is not None and entry.alternative is option.alternative
            )
            for scenario, entry in zip(scenarios.scenarios, entries, strict=True)
        )]
        included = (
            {entry is not None and start <= entry.encounter.service_date <= end
             for entry in entries} if scenarios.complete
            else {option.included and option_in_range(option, start, end)
                  for option in item.options}
        )
        inclusion: Literal["included", "excluded", "uncertain"] = (
            "included" if included == {True} else "excluded" if included == {False}
            else "uncertain"
        )
        if item.identity_uncertain:
            inclusion = "uncertain"
        minutes_values = (
            [entry.alternative.minutes for entry in entries
             if entry is not None and start <= entry.encounter.service_date <= end]
            if scenarios.complete else [option.alternative.minutes for option in item.options
                                        if option.alternative is not None and option.included
                                        and option_in_range(option, start, end)]
        )
        option_keys = {key for option in item.options for key in option.choices}
        choices_values = (
            [{key: value for key, value in scenario.choices.items() if key in option_keys}
             for scenario in scenarios.scenarios] if scenarios.complete
            else [option.choices for option in item.options]
        )
        unique_choices: list[dict[str, str]] = []
        for choice in choices_values:
            if choice not in unique_choices:
                unique_choices.append(choice)
        contribution = Contribution(
            encounter_id=item.encounter.encounter_id, service_date=item.encounter.service_date,
            service_type=item.encounter.service_type, inclusion=inclusion, reason=item.reason,
            minutes=sorted(set(minutes_values), key=lambda value: (value is None, value or 0)),
            choices=unique_choices, sources=item.encounter.sources,
            service_dates=sorted({option.encounter.service_date for option in feasible_options}),
            service_types=sorted({option.encounter.service_type for option in feasible_options}),
            interpretations=[ContactInterpretation(
                service_date=option.encounter.service_date,
                service_type=option.encounter.service_type,
                attendance=option.encounter.attendance,
                patient_present=option.encounter.patient_present,
                minutes=option.alternative.minutes if option.alternative is not None else None,
                eligible=option.included, in_review_range=option_in_range(option, start, end),
                choices=option.choices,
                sources=option.alternative.sources if option.alternative is not None else [],
            ) for option in feasible_options],
        )
        (exclusions if inclusion == "excluded" else contributions).append(contribution)
    return PatientMetrics(
        patient_id=patient.patient_id, start=start, end=end, session_counts=service_counts,
        session_count=counts, distinct_days=days, minutes=minutes, weeks=weeks,
        contributions=contributions, exclusions=exclusions,
        constraint_sources=unique_sources([
            source for item in candidates if not candidate_in_range(item, start, end)
            for source in item.encounter.sources
        ]),
        scenario_count=len(scenarios.scenarios),
        analysis_status="complete" if scenarios.complete else "analysis_incomplete",
        reason=scenarios.reason,
    )


def consecutive_pair(
    weeks: list[WeekWitness], possible: bool = False
) -> list[WeekWitness]:
    for left, right in zip(weeks, weeks[1:]):
        if right.week_start - left.week_start != timedelta(days=7):
            continue
        decisions = (left.decision, right.decision)
        if (all(decision != "met" for decision in decisions) if possible
                else all(decision == "not_met" for decision in decisions)):
            return [left, right]
    return []


def cohort(
    patients: list[PatientRecord], start: date, end: date, scenario_budget: int = 10_000
) -> list[CohortResult]:
    results: list[CohortResult] = []
    for patient in patients:
        candidates, scenarios = prepare(patient, start, end, scenario_budget)
        metrics = calculate(patient, start, end, scenario_budget)
        definite: list[tuple[Scenario, list[WeekWitness]]] = []
        unresolved = False
        for scenario in scenarios.scenarios:
            witnesses: list[WeekWitness] = []
            for week in metrics.weeks:
                if week.goal_reason == "week_outside_episode":
                    continue
                entries = selected(scenario, week.review_start, week.review_end)
                minutes, known = scenario_minutes(entries)
                witnesses.append(WeekWitness(
                    week_start=week.week_start,
                    distinct_days=len({entry.encounter.service_date for entry in entries}),
                    minutes=minutes, known_minutes=known,
                    decision=weekly_decision(entries, week.goal, week.complete_episode_coverage),
                    encounter_ids=[entry.encounter.encounter_id for entry in entries],
                ))
            pair = consecutive_pair(witnesses)
            if pair:
                definite.append((scenario, pair))
            elif consecutive_pair(witnesses, possible=True):
                unresolved = True
        membership: Literal["confirmed", "possible", "excluded", "analysis_incomplete"]
        if not scenarios.complete:
            membership, reason = "analysis_incomplete", scenarios.reason
        elif definite and len(definite) == len(scenarios.scenarios):
            membership = "confirmed"
            reason = "Every consistent interpretation has two below-goal weeks."
        elif definite:
            membership = "possible"
            reason = "A consistent source interpretation establishes a pair."
        elif unresolved:
            membership = "analysis_incomplete"
            reason = "missing_evidence_or_unspecified_plan_policy"
        else:
            membership = "excluded"
            reason = "No consistent interpretation has two below-goal weeks."
        scenario, witness = definite[0] if definite else (Scenario([], {}), [])
        results.append(CohortResult(
            patient_id=patient.patient_id, membership=membership, reason=reason,
            choices=scenario.choices, witness=witness,
            sources=unique_sources(
                [source for week in metrics.weeks for source in week.sources]
                + metrics.constraint_sources
            ),
        ))
    return results


def compare_plans(
    patient: PatientRecord, start: date, end: date, change_date: date | None = None,
    scenario_budget: int = 10_000,
) -> PlanComparison:
    if start > end:
        raise ValueError("Review start must not follow review end.")
    changes = sorted({plan.effective_start for plan in patient.plans
                      if start < plan.effective_start <= end})
    if change_date is None and len(changes) != 1:
        return PlanComparison(
            patient_id=patient.patient_id, change_date=None, candidate_change_dates=changes,
            before=None, after=None,
            reason="Specify a change date when zero or multiple changes exist.",
        )
    boundary = change_date if change_date is not None else changes[0]
    if not start <= boundary <= end:
        raise ValueError("Plan-change date must be within the review range.")
    before = (
        calculate(patient, start, boundary - timedelta(days=1), scenario_budget)
        if start < boundary else None
    )
    return PlanComparison(
        patient_id=patient.patient_id, change_date=boundary, candidate_change_dates=changes,
        before=before, after=calculate(patient, boundary, end, scenario_budget),
        reason="Compare explicit windows and service mix; window lengths may differ. "
               "Separate period alternatives must not be combined as independent scenarios.",
    )
