from __future__ import annotations

import os
from datetime import date, timedelta
from importlib.resources import files
from json import JSONDecodeError
from time import perf_counter
from typing import Literal, Protocol

from openai import OpenAI, OpenAIError
from openai.types.responses import ParsedResponse
from pydantic import BaseModel, Field, ValidationError

from backbone.models import (
    ClinicalSnapshot,
    Encounter,
    ModelUsage,
    PatientRecord,
    QueryMetric,
    QueryOperation,
    QueryPlan,
    QueryTask,
)


class QueryPlanningError(ValueError):
    def __init__(
        self,
        message: str,
        *,
        model_calls: int = 0,
        usage: ModelUsage | None = None,
        elapsed_seconds: float = 0.0,
    ) -> None:
        super().__init__(message)
        self.model_calls: int = model_calls
        self.usage: ModelUsage | None = usage
        self.elapsed_seconds: float = elapsed_seconds


class PatientScope(BaseModel):
    kind: Literal["explicit", "all", "organization", "context"] = "explicit"
    references: list[str] = Field(default_factory=list)
    organization: str | None = None


class TimeIntent(BaseModel):
    kind: Literal["episode", "range", "dates", "relative", "context"] = "episode"
    start: date | None = None
    end: date | None = None
    dates: list[date] = Field(default_factory=list)
    anchor: Literal["episode_start", "episode_end", "plan_change", "first_encounter"] | None = None
    anchor_date: date | None = None
    offset: int = 0
    offset_unit: Literal["days", "weeks"] = "days"
    length: int | None = None
    length_unit: Literal["days", "weeks"] = "days"
    align_to_calendar_week: bool = False


class TaskIntent(BaseModel):
    operation: QueryOperation
    patients: PatientScope = Field(default_factory=PatientScope)
    time: TimeIntent = Field(default_factory=TimeIntent)
    metrics: list[QueryMetric] = Field(default_factory=list)
    consecutive_weeks: int = Field(default=2, ge=1)
    change_date: date | None = None


class QueryIntent(BaseModel):
    status: Literal["ready", "clarification_required", "unsupported"]
    message: str
    tasks: list[TaskIntent]


class PatientCatalog(BaseModel):
    patient_id: str
    name: str
    organization: str
    episode_start: date | None
    episode_end: date | None
    review_start: date | None
    review_end: date | None
    plan_change_dates: list[date]
    first_encounter: date | None


class PlanningContext(BaseModel):
    snapshot_id: int
    patients: list[PatientCatalog]
    previous_plan: QueryPlan | None = None


class IntentResult(BaseModel):
    intent: QueryIntent
    model: str | None = None
    usage: ModelUsage = Field(default_factory=ModelUsage)
    elapsed_seconds: float = 0.0
    model_calls: int = 0


class QueryPlanner(Protocol):
    def interpret(self, question: str, context: PlanningContext) -> IntentResult: ...


def encounter_dates(encounter: Encounter) -> set[date]:
    return {
        alternative.service_date or encounter.service_date for alternative in encounter.alternatives
    } or {encounter.service_date}


def first_encounter_date(patient: PatientRecord) -> date | None:
    if not patient.encounters:
        return None
    lower = min(min(encounter_dates(entry)) for entry in patient.encounters)
    upper = min(max(encounter_dates(entry)) for entry in patient.encounters)
    return lower if lower == upper else None


def available_bounds(patient: PatientRecord) -> tuple[date | None, date | None]:
    observed = [value for encounter in patient.encounters for value in encounter_dates(encounter)]
    observed.extend(
        value
        for assessment in patient.assessments
        for value in (assessment.completed_date_alternatives or [assessment.completed_date])
    )
    observed.extend(observation.observed_date for observation in patient.observations)
    start = (
        patient.episode_start if patient.episode_start is not None else min(observed, default=None)
    )
    end = patient.episode_end if patient.episode_end is not None else max(observed, default=None)
    return start, end


def patient_bounds(patient: PatientRecord) -> tuple[date, date]:
    start, end = available_bounds(patient)
    if start is None or end is None:
        raise QueryPlanningError(f"No documented review period is available for {patient.name}.")
    if start > end:
        raise QueryPlanningError(f"The documented episode bounds for {patient.name} are invalid.")
    return start, end


def review_boundary(patients: list[PatientRecord], boundary: Literal["start", "end"]) -> date:
    values: list[date] = []
    for patient in patients:
        value = available_bounds(patient)[0 if boundary == "start" else 1]
        if value is None:
            raise QueryPlanningError(f"No documented review {boundary} for {patient.name}.")
        values.append(value)
    return min(values) if boundary == "start" else max(values)


def plan_changes(patient: PatientRecord) -> list[date]:
    return sorted({plan.effective_start for plan in patient.plans})[1:]


def planning_context(
    snapshot: ClinicalSnapshot,
    context: QueryPlan | None = None,
) -> PlanningContext:
    patients: list[PatientCatalog] = []
    for patient in snapshot.patients:
        start, end = available_bounds(patient)
        patients.append(
            PatientCatalog(
                patient_id=patient.patient_id,
                name=patient.name,
                organization=patient.organization,
                episode_start=patient.episode_start,
                episode_end=patient.episode_end,
                review_start=start,
                review_end=end,
                plan_change_dates=plan_changes(patient),
                first_encounter=first_encounter_date(patient),
            )
        )
    return PlanningContext(
        snapshot_id=snapshot.snapshot_id, patients=patients, previous_plan=context
    )


class OpenAIQueryPlanner:
    def __init__(
        self,
        model: str | None = None,
        *,
        client: OpenAI | None = None,
        input_rate_per_million: float | None = None,
        output_rate_per_million: float | None = None,
    ) -> None:
        self.model: str = model or os.environ.get(
            "OPENAI_QUERY_MODEL", os.environ.get("OPENAI_MODEL", "gpt-4.1")
        )
        try:
            self.client: OpenAI = client if client is not None else OpenAI(timeout=90.0)
        except OpenAIError as error:
            raise QueryPlanningError(
                "Configure OPENAI_API_KEY for query planning, or supply a saved plan."
            ) from error
        self.prompt: str = files("backbone").joinpath("query_prompt.txt").read_text("utf-8")
        self.input_rate_per_million: float | None = input_rate_per_million
        self.output_rate_per_million: float | None = output_rate_per_million
        if any(
            rate is not None and rate < 0
            for rate in (
                input_rate_per_million,
                output_rate_per_million,
            )
        ):
            raise ValueError("Token rates cannot be negative.")

    def interpret(self, question: str, context: PlanningContext) -> IntentResult:
        started = perf_counter()
        try:
            response: ParsedResponse[QueryIntent] = self.client.responses.parse(
                model=self.model,
                instructions=self.prompt,
                input=f"Snapshot catalog:\n{context.model_dump_json()}\n\nQuestion:\n{question}",
                text_format=QueryIntent,
                max_output_tokens=5000,
                store=False,
            )
        except OpenAIError as error:
            raise QueryPlanningError(
                f"Query planning API request failed: {error}",
                model_calls=1,
                elapsed_seconds=perf_counter() - started,
            ) from error
        except (JSONDecodeError, ValidationError) as error:
            raise QueryPlanningError(
                "The query planner returned invalid structured intent.",
                model_calls=1,
                elapsed_seconds=perf_counter() - started,
            ) from error
        usage = (
            ModelUsage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                cost_usd=(
                    response.usage.input_tokens * self.input_rate_per_million
                    + response.usage.output_tokens * self.output_rate_per_million
                )
                / 1_000_000
                if self.input_rate_per_million is not None
                and self.output_rate_per_million is not None
                else None,
            )
            if response.usage
            else None
        )
        if response.status != "completed" or response.output_parsed is None:
            raise QueryPlanningError(
                "The query planner did not return a completed structured plan.",
                model_calls=1,
                usage=usage,
                elapsed_seconds=perf_counter() - started,
            )
        if usage is None:
            raise QueryPlanningError(
                "The query planner did not report token usage.",
                model_calls=1,
                elapsed_seconds=perf_counter() - started,
            )
        return IntentResult(
            intent=response.output_parsed,
            model=response.model,
            usage=usage,
            elapsed_seconds=perf_counter() - started,
            model_calls=1,
        )


def resolve_patients(
    scope: PatientScope,
    snapshot: ClinicalSnapshot,
    context: QueryPlan | None,
) -> list[PatientRecord]:
    if scope.kind == "all":
        selected = snapshot.patients
    elif scope.kind == "organization":
        if scope.organization is None:
            raise QueryPlanningError("Specify the organization to query.")
        selected = [
            entry
            for entry in snapshot.patients
            if entry.organization.casefold() == scope.organization.casefold()
        ]
    else:
        references = scope.references
        if scope.kind == "context":
            if context is None:
                raise QueryPlanningError(
                    "Specify the patient; no previous query context was supplied."
                )
            prior_references = list(
                dict.fromkeys(
                    identifier
                    for task in context.tasks
                    for identifier in (task.patient_ids or ([task.patient] if task.patient else []))
                )
            )
            if references:
                if any(value not in prior_references for value in references):
                    raise QueryPlanningError("The requested patient was not in the previous query.")
            elif len(prior_references) == 1:
                references = prior_references
            else:
                raise QueryPlanningError("The previous query has multiple patients; specify which.")
        if not references:
            if len(snapshot.patients) != 1:
                raise QueryPlanningError("Name the patient or explicitly request the whole cohort.")
            selected = snapshot.patients
        else:
            selected = []
            for reference in references:
                exact = [
                    entry
                    for entry in snapshot.patients
                    if reference.casefold() in {entry.patient_id.casefold(), entry.name.casefold()}
                ]
                matches = exact or [
                    entry
                    for entry in snapshot.patients
                    if reference.casefold()
                    in {
                        entry.patient_id.rsplit("::", 1)[-1].casefold(),
                        *(part.casefold() for part in entry.name.split()),
                    }
                ]
                if not matches:
                    raise QueryPlanningError(
                        f"Patient {reference} is not present in this snapshot."
                    )
                if len(matches) != 1:
                    raise QueryPlanningError(
                        f"Patient reference {reference} is ambiguous; use a full name or ID."
                    )
                if matches[0] not in selected:
                    selected.append(matches[0])
    if not selected:
        raise QueryPlanningError("No patients match the requested scope.")
    return selected


def resolve_change(patient: PatientRecord, requested: date | None) -> date:
    changes = plan_changes(patient)
    if requested is not None:
        if requested not in changes:
            raise QueryPlanningError(
                f"No documented plan change on {requested} for {patient.name}."
            )
        return requested
    if len(changes) != 1:
        raise QueryPlanningError(f"Specify which documented plan change to use for {patient.name}.")
    return changes[0]


def resolve_time(
    intent: TimeIntent,
    patients: list[PatientRecord],
    context: QueryPlan | None,
) -> tuple[date, date, list[date]]:
    dates: list[date] = []
    if intent.kind == "episode":
        bounds = [patient_bounds(patient) for patient in patients]
        start, end = min(value[0] for value in bounds), max(value[1] for value in bounds)
    elif intent.kind == "range":
        if intent.start is None and intent.end is None:
            raise QueryPlanningError("The requested date range has no resolved boundary.")
        start = intent.start if intent.start is not None else review_boundary(patients, "start")
        end = intent.end if intent.end is not None else review_boundary(patients, "end")
    elif intent.kind == "dates":
        dates = sorted(set(intent.dates))
        if not dates:
            raise QueryPlanningError("Specify the dates to query.")
        start, end = dates[0], dates[-1]
    elif intent.kind == "context":
        if context is None:
            raise QueryPlanningError(
                "Specify the date range; no previous query context was supplied."
            )
        windows = {(task.start, task.end, tuple(task.selected_dates)) for task in context.tasks}
        if len(windows) != 1:
            raise QueryPlanningError(
                "The previous query has multiple date ranges; specify which to reuse."
            )
        start, end, previous_dates = next(iter(windows))
        dates = list(previous_dates)
    else:
        if len(patients) != 1:
            raise QueryPlanningError("Resolve relative dates separately for each patient.")
        patient = patients[0]
        if intent.anchor == "episode_start":
            if patient.episode_start is None:
                raise QueryPlanningError(f"No documented episode start for {patient.name}.")
            anchor = patient.episode_start
        elif intent.anchor == "episode_end":
            if patient.episode_end is None:
                raise QueryPlanningError(f"No documented episode end for {patient.name}.")
            anchor = patient.episode_end
        elif intent.anchor == "plan_change":
            anchor = resolve_change(patient, intent.anchor_date)
        elif intent.anchor == "first_encounter":
            first = first_encounter_date(patient)
            if first is None:
                raise QueryPlanningError(
                    f"The first encounter date is missing or disputed for {patient.name}."
                )
            anchor = first
        else:
            raise QueryPlanningError("Specify a documented anchor for the relative date range.")
        if intent.align_to_calendar_week:
            anchor -= timedelta(days=anchor.weekday())
        start = anchor + timedelta(days=intent.offset * (7 if intent.offset_unit == "weeks" else 1))
        if intent.length is None:
            end = review_boundary([patient], "end")
        else:
            if intent.length < 1:
                raise QueryPlanningError("Relative date-range length must be positive.")
            span = intent.length * (7 if intent.length_unit == "weeks" else 1)
            end = start + timedelta(days=span - 1)
    if start > end:
        raise QueryPlanningError("The requested review start follows the requested review end.")
    return start, end, dates


def validate_plan(plan: QueryPlan, question: str, snapshot: ClinicalSnapshot) -> None:
    if plan.question != question or plan.snapshot_id != snapshot.snapshot_id:
        raise QueryPlanningError("The saved plan must match this question and snapshot.")
    known = {patient.patient_id: patient for patient in snapshot.patients}
    for task in plan.tasks:
        identifiers = task.patient_ids if task.operation == "cohort" else [task.patient]
        if not identifiers or any(identifier not in known for identifier in identifiers):
            raise QueryPlanningError(
                "Every query task must reference patients present in this snapshot."
            )
        if task.operation != "cohort" and task.patient_ids != [task.patient]:
            raise QueryPlanningError("Task patient IDs must match its individual patient.")
        if (
            task.operation == "cohort"
            and task.patient is not None
            and task.patient not in task.patient_ids
        ):
            raise QueryPlanningError(
                "The cohort's patient must belong to its selected patient IDs."
            )
        if task.selected_dates and task.operation in ("weekly", "cohort", "plan_change"):
            raise QueryPlanningError("This operation requires a continuous date range.")
        if task.start > task.end:
            raise QueryPlanningError("The requested review start follows the requested review end.")
        if any(not task.start <= value <= task.end for value in task.selected_dates):
            raise QueryPlanningError("Selected dates must be inside the task's date bounds.")
        if task.operation == "day" and not task.selected_dates:
            raise QueryPlanningError("A day query must specify selected dates.")
        if task.operation == "plan_change":
            patient = known[str(task.patient)]
            boundary = resolve_change(patient, task.change_date)
            if not task.start <= boundary <= task.end:
                raise QueryPlanningError("Plan-change date must be within the review range.")


def plan_question(
    question: str,
    snapshot: ClinicalSnapshot,
    *,
    planner: QueryPlanner | None = None,
    context: QueryPlan | None = None,
) -> QueryPlan:
    if not question.strip():
        raise QueryPlanningError("Question must not be empty.")
    if not snapshot.patients:
        raise QueryPlanningError("The snapshot has no patients; process records first.")
    engine = planner if planner is not None else OpenAIQueryPlanner()
    result = engine.interpret(question, planning_context(snapshot, context))
    if result.intent.status != "ready":
        raise QueryPlanningError(
            f"{result.intent.status}: {result.intent.message}",
            model_calls=result.model_calls,
            usage=result.usage,
            elapsed_seconds=result.elapsed_seconds,
        )
    try:
        if not result.intent.tasks:
            raise QueryPlanningError("The query planner returned no tasks.")
        tasks: list[QueryTask] = []
        for intent in result.intent.tasks:
            patients = resolve_patients(intent.patients, snapshot, context)
            groups = (
                [patients]
                if intent.operation == "cohort" and intent.time.kind != "relative"
                else [[patient] for patient in patients]
            )
            for group in groups:
                start, end, dates = resolve_time(intent.time, group, context)
                if dates and intent.operation in ("weekly", "cohort", "plan_change"):
                    raise QueryPlanningError("This operation requires a continuous date range.")
                change_date = (
                    resolve_change(group[0], intent.change_date)
                    if intent.operation == "plan_change"
                    else None
                )
                tasks.append(
                    QueryTask(
                        operation=intent.operation,
                        patient=group[0].patient_id if len(group) == 1 else None,
                        patient_ids=[patient.patient_id for patient in group],
                        start=start,
                        end=end,
                        selected_dates=dates,
                        change_date=change_date,
                        metrics=intent.metrics,
                        consecutive_weeks=intent.consecutive_weeks,
                    )
                )
        plan = QueryPlan(
            question=question,
            snapshot_id=snapshot.snapshot_id,
            tasks=tasks,
            planner_model=result.model,
            planner_usage=result.usage,
            planner_elapsed_seconds=result.elapsed_seconds,
            planner_model_calls=result.model_calls,
        )
        validate_plan(plan, question, snapshot)
    except QueryPlanningError as error:
        raise QueryPlanningError(
            str(error),
            model_calls=result.model_calls,
            usage=result.usage,
            elapsed_seconds=result.elapsed_seconds,
        ) from error
    return plan
