from __future__ import annotations

import re
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from backbone.calculation import (
    CohortResult,
    Contribution,
    IntegerResult,
    PatientMetrics,
    PlanComparison,
    calculate,
    cohort,
    compare_plans,
)
from backbone.models import (
    AssessmentClaim,
    ClinicalSnapshot,
    Observation,
    PatientRecord,
    QueryPlan,
    SourceRef,
)


class QueryPlanningError(ValueError):
    pass


class DateScope(BaseModel):
    start: date
    end: date
    dates: list[date] = Field(default_factory=list)
    explicit: bool = False
    contiguous: bool = False


class AnswerBundle(BaseModel):
    question: str
    plan: QueryPlan
    snapshot_id: int
    text: str
    metrics: list[PatientMetrics] = Field(default_factory=list)
    cohort_results: list[CohortResult] = Field(default_factory=list)
    plan_comparison: PlanComparison | None = None
    assessments: list[AssessmentClaim] = Field(default_factory=list)
    observations: list[Observation] = Field(default_factory=list)
    sources: list[SourceRef] = Field(default_factory=list)
    uncertainty: list[str] = Field(default_factory=list)
    coverage_status: Literal["available_records", "failed_source_processing"]


MONTHS: dict[str, int] = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}


def patient_bounds(patient: PatientRecord) -> tuple[date, date]:
    observed = [encounter.service_date for encounter in patient.encounters]
    observed.extend(assessment.completed_date for assessment in patient.assessments)
    observed.extend(observation.observed_date for observation in patient.observations)
    if not observed and (patient.episode_start is None or patient.episode_end is None):
        raise QueryPlanningError(f"No documented review period is available for {patient.name}.")
    start = patient.episode_start if patient.episode_start is not None else min(observed)
    end = patient.episode_end if patient.episode_end is not None else max(observed)
    if start > end:
        raise QueryPlanningError(f"The documented episode bounds for {patient.name} are invalid.")
    return start, end


def match_patient(question: str, snapshot: ClinicalSnapshot) -> PatientRecord | None:
    matches: list[PatientRecord] = []
    for patient in snapshot.patients:
        identifiers = {patient.name, patient.patient_id}
        if any(
            re.search(rf"(?<!\w){re.escape(identifier)}(?!\w)", question, re.IGNORECASE)
            for identifier in identifiers
            if identifier
        ):
            matches.append(patient)
    if not matches:
        for patient in snapshot.patients:
            name_parts = {part for part in patient.name.split() if len(part) > 1}
            if any(
                re.search(rf"(?<!\w){re.escape(part)}(?!\w)", question, re.IGNORECASE)
                for part in name_parts
            ):
                matches.append(patient)
    if len(matches) > 1:
        raise QueryPlanningError(
            "This query format supports one named patient or the whole cohort."
        )
    return matches[0] if matches else None


def default_scope(patients: list[PatientRecord]) -> DateScope:
    if not patients:
        raise QueryPlanningError(
            "The snapshot has no patients; build the clinical abstraction first."
        )
    bounds = [patient_bounds(patient) for patient in patients]
    return DateScope(start=min(value[0] for value in bounds), end=max(value[1] for value in bounds))


def parse_date_scope(question: str, patients: list[PatientRecord]) -> DateScope:
    defaults = default_scope(patients)
    normalized = question.lower().replace("–", "-").replace("—", "-")
    located_dates: list[tuple[int, date]] = []
    month_names = "|".join(MONTHS)
    date_prefix = rf"(?:\d{{4}}-|(?:{month_names})\s+\d)"
    contiguous = bool(re.search(rf"\b(?:from|between|through|to)\s+{date_prefix}", normalized))
    if re.search(r"\d{4}-\d{2}-\d{2}\s*-\s*\d{4}-\d{2}-\d{2}", normalized):
        contiguous = True
    for match in re.finditer(r"(?<!\d)(\d{4}-\d{2}-\d{2})(?!\d)", normalized):
        try:
            located_dates.append((match.start(), date.fromisoformat(match.group(1))))
        except ValueError as error:
            raise QueryPlanningError(f"Invalid date: {match.group(1)}.") from error
    pattern = (
        rf"\b({month_names})\s+(\d{{1,2}})(?!\d)"
        r"(?:\s*-\s*(\d{1,2})(?!\d))?(?:\s*,?\s*(\d{4})(?!\d))?"
    )
    month_specs: list[tuple[int, int, list[int], int | None]] = []
    for match in re.finditer(pattern, normalized):
        explicit_year = match.group(4)
        month = MONTHS[match.group(1)]
        day_numbers = [int(match.group(2))]
        if match.group(3) is not None:
            day_numbers.append(int(match.group(3)))
            contiguous = True
        else:
            tail = normalized[match.end() :]
            list_match = re.match(r"\s+and\s+(\d{1,2})\b(?:\s*,?\s*(\d{4})(?!\d))?", tail)
            if list_match is not None:
                day_numbers.append(int(list_match.group(1)))
                if list_match.group(2) is not None:
                    explicit_year = list_match.group(2)
        month_specs.append(
            (
                match.start(),
                month,
                day_numbers,
                int(explicit_year) if explicit_year is not None else None,
            )
        )
    provided_years = {value.year for _, value in located_dates}
    provided_years.update(year for _, _, _, year in month_specs if year is not None)
    shared_year = next(iter(provided_years)) if len(provided_years) == 1 else None
    if not provided_years and defaults.start.year == defaults.end.year:
        shared_year = defaults.start.year
    for position, month, day_numbers, explicit_year_number in month_specs:
        year = explicit_year_number if explicit_year_number is not None else shared_year
        if year is None:
            raise QueryPlanningError(
                "Specify a year for each date when the question or review period spans years."
            )
        for offset, day_number in enumerate(day_numbers):
            try:
                located_dates.append((position + offset, date(year, month, day_number)))
            except ValueError as error:
                raise QueryPlanningError(
                    f"Invalid date: {year}-{month:02d}-{day_number:02d}."
                ) from error
    if not located_dates:
        return defaults
    found = [value for _, value in sorted(located_dates, key=lambda value: value[0])]
    if contiguous and found[0] > found[-1]:
        raise QueryPlanningError("The requested review start follows the requested review end.")
    dates = sorted(set(found))
    return DateScope(
        start=min(dates), end=max(dates), dates=dates, explicit=True, contiguous=contiguous
    )


def classify_operation(
    question: str, scope: DateScope
) -> Literal[
    "counts", "durations", "weekly", "day", "timeline", "symptoms", "cohort", "plan_change"
]:
    normalized = question.lower()
    if re.search(
        r"\bpercent(?:age)?\b|\bproportion\b|\baverage\b|\bmean\b|\bmedian\b|\bratio\b", normalized
    ):
        raise QueryPlanningError(
            "This planner does not support ratios, averages, or percent calculations."
        )
    cohort = bool(re.search(r"\bconsecutive\s+(?:calendar\s+)?weeks?\b", normalized))
    plan_change = bool(
        re.search(r"\bbefore\b", normalized)
        and re.search(r"\bafter\b", normalized)
        and re.search(r"\bplan\b|\bchange\b", normalized)
    )
    symptoms = bool(
        re.search(r"\bsymptoms?\b|\bassessments?\b|\bphq[ -]?9\b|\bprogress\b", normalized)
    )
    weekly = bool(re.search(r"\bgoals?\b|\brequirements?\b|\bthresholds?\b|\bmeet\b", normalized))
    durations = bool(re.search(r"\bminutes?\b|\bhours?\b|\bdurations?\b", normalized))
    counts = bool(re.search(r"\bhow many\b|\bcounts?\b|\bnumber of\b", normalized))
    timeline = bool(re.search(r"\breconstruct\b|\btimeline\b|\bwhat happened\b", normalized))
    if symptoms and (cohort or plan_change or weekly):
        raise QueryPlanningError("Ask symptom and treatment-goal questions separately.")
    if cohort:
        return "cohort"
    if plan_change:
        return "plan_change"
    if symptoms:
        return "symptoms"
    if weekly:
        return "weekly"
    dated_contact = bool(re.search(r"\bon\s+(?:\d{4}-|" + "|".join(MONTHS) + r")", normalized))
    if scope.explicit and not scope.contiguous and (timeline or dated_contact):
        return "day"
    if durations:
        return "durations"
    if counts:
        return "counts"
    if timeline:
        return "timeline"
    raise QueryPlanningError(
        "Unsupported question. Ask for session counts, contact minutes, weekly goals, "
        "a dated reconstruction, symptoms, a timeline, consecutive weeks, or a plan comparison."
    )


def plan_question(question: str, snapshot: ClinicalSnapshot) -> QueryPlan:
    if not question.strip():
        raise QueryPlanningError("Question must not be empty.")
    patient = match_patient(question, snapshot)
    if patient is None:
        named = re.search(
            r"\bdid\s+([A-Z][A-Za-z'-]+)\s+(?:attend|receive)|"
            r"\b([A-Z][A-Za-z'-]+)[’']s\b|"
            r"\bfor\s+([A-Z][A-Za-z'-]+)\b",
            question,
        )
        if named is not None:
            name = next(value for value in named.groups() if value is not None)
            if name.lower() not in MONTHS:
                raise QueryPlanningError(f"Patient {name} is not present in this snapshot.")
    selected = [patient] if patient is not None else snapshot.patients
    scope = parse_date_scope(question, selected)
    operation = classify_operation(question, scope)
    if operation != "cohort" and patient is None:
        if len(snapshot.patients) != 1:
            raise QueryPlanningError("Name a patient for an individual-patient question.")
        patient = snapshot.patients[0]
    if (
        operation == "symptoms"
        and not scope.contiguous
        and re.search(r"\b(?:during|throughout)\s+(?:the\s+)?episode\b", question, re.IGNORECASE)
    ):
        scope = default_scope([patient] if patient is not None else selected)
    change_date: date | None = None
    if operation == "plan_change":
        if patient is None:
            raise QueryPlanningError("Name a patient for a plan comparison.")
        all_changes = sorted({plan.effective_start for plan in patient.plans})[1:]
        changes = [value for value in all_changes if scope.start < value <= scope.end]
        requested = [value for value in scope.dates if value in all_changes]
        if not scope.contiguous and len(scope.dates) == 1 and len(requested) == 1:
            change_date = requested[0]
            scope = default_scope([patient])
        elif len(changes) == 1:
            change_date = changes[0]
        elif len(changes) > 1:
            raise QueryPlanningError("Specify which documented plan change to compare.")
    return QueryPlan(
        operation=operation,
        patient=patient.patient_id if patient is not None else None,
        start=scope.start,
        end=scope.end,
        change_date=change_date,
        selected_dates=scope.dates if operation == "day" else [],
    )


def source_key(source: SourceRef) -> tuple[str, int, int, str]:
    return source.content_hash, source.start_line, source.end_line, source.quote


def unique_sources(sources: list[SourceRef]) -> list[SourceRef]:
    unique: dict[tuple[str, int, int, str], SourceRef] = {}
    for source in sources:
        unique[source_key(source)] = source
    return list(unique.values())


def render_sources(sources: list[SourceRef]) -> str:
    if not sources:
        return "No supporting source passages are available."
    lines: list[str] = []
    for index, source in enumerate(unique_sources(sources), start=1):
        quote = source.quote.replace("\n", " ").strip()
        lines.append(
            f"[{index}] {source.document_id}, {source.filename}, "
            f"lines {source.start_line}-{source.end_line}: {quote}"
        )
    return "\n".join(lines)


def source_labels(references: list[SourceRef], catalog: list[SourceRef]) -> str:
    positions = {source_key(source): index for index, source in enumerate(catalog, start=1)}
    return ", ".join(f"[{positions[source_key(source)]}]" for source in unique_sources(references))


def metric_sources(metrics: PatientMetrics) -> list[SourceRef]:
    sources = [
        source for row in metrics.contributions + metrics.exclusions for source in row.sources
    ]
    sources.extend(source for week in metrics.weeks for source in week.sources)
    sources.extend(metrics.constraint_sources)
    return unique_sources(sources)


def display_integer(result: IntegerResult) -> str:
    if result.exact is not None:
        return str(result.exact)
    if result.status == "conflicting_evidence" and result.values:
        return " or ".join(str(value) for value in result.values)
    return f"at least {result.lower_bound}; total unresolved ({result.status})"


def display_hours(result: IntegerResult) -> str:
    if result.exact is not None:
        return f"{result.exact / 60:.3f}"
    if result.status == "conflicting_evidence" and result.values:
        return " or ".join(f"{value / 60:.3f}" for value in result.values)
    return f"at least {result.lower_bound / 60:.3f}; total unresolved"


def table_cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def render_ledger(rows: list[Contribution], catalog: list[SourceRef]) -> list[str]:
    lines = [
        "| Date | Encounter | Service | Included | Contact minutes | Reason | Sources |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in sorted(rows, key=lambda entry: (entry.service_date, entry.encounter_id)):
        minutes = " or ".join(
            str(value) if value is not None else "unknown"
            for value in sorted(set(row.minutes), key=lambda value: (value is None, value or 0))
        )
        if row.inclusion == "excluded":
            minutes = "0 counted"
        dates = " or ".join(str(value) for value in row.service_dates) or str(row.service_date)
        services = " or ".join(row.service_types) or row.service_type
        lines.append(
            f"| {dates} | {table_cell(row.encounter_id)} | {table_cell(services)} | "
            f"{row.inclusion} | {minutes} | {table_cell(row.reason)} | "
            f"{source_labels(row.sources, catalog)} |"
        )
    disputed = [row for row in rows if len(row.interpretations) > 1]
    if disputed:
        lines.extend(
            [
                "",
                "Supported event interpretations below are alternatives for the same encounter, "
                "rather than additional visits. Dates, service types, attendance, and durations "
                "within each interpretation stay together.",
                "",
            ]
        )
    for row in disputed:
        for index, interpretation in enumerate(row.interpretations, start=1):
            minutes = "unknown" if interpretation.minutes is None else str(interpretation.minutes)
            presence = (
                "unknown"
                if interpretation.patient_present is None
                else "yes"
                if interpretation.patient_present
                else "no"
            )
            choices = ", ".join(
                f"{key}={value}" for key, value in sorted(interpretation.choices.items())
            )
            lines.append(
                f"- {row.encounter_id}, alternative {index}: {interpretation.service_date}, "
                f"{interpretation.service_type}, {interpretation.attendance}, "
                f"patient present {presence}, {minutes} minutes; "
                f"eligible {'yes' if interpretation.eligible else 'no'}, "
                f"within review window {'yes' if interpretation.in_review_range else 'no'}; "
                f"choices {choices or 'none'}. {source_labels(interpretation.sources, catalog)}"
            )
    return lines


def render_metrics(metrics: PatientMetrics, catalog: list[SourceRef]) -> list[str]:
    lines = [
        f"Review window: {metrics.start} through {metrics.end}, inclusive.",
        "",
        f"Eligible sessions: **{display_integer(metrics.session_count)}**. "
        f"Distinct therapy days: **{display_integer(metrics.distinct_days)}**. "
        f"Therapy minutes: **{display_integer(metrics.minutes)}** "
        f"(**{display_hours(metrics.minutes)} hours**, rounded to 3 decimals).",
        "",
        "| Service | Eligible sessions |",
        "| --- | --- |",
    ]
    lines.extend(
        f"| {service} | {display_integer(value)} |"
        for service, value in sorted(metrics.session_counts.items())
    )
    lines.extend(
        [
            "",
            "Monday-Sunday weekly calculations use the review-range contributions below. "
            "Thresholds are the documented goals; partial weeks are not silently prorated.",
            "",
            "| Calendar week | Reviewed dates | Days | Minutes | Hours | "
            "Goal | Decision | Sources |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for week in metrics.weeks:
        goal = (
            f"{week.goal.minimum_days} days and {week.goal.minimum_minutes} minutes"
            if week.goal is not None
            else f"unresolved: {week.goal_reason}"
        )
        decision = "cannot be determined" if week.decision == "indeterminate" else week.decision
        lines.append(
            f"| {week.week_start} to {week.week_end} | {week.review_start} to {week.review_end} | "
            f"{display_integer(week.distinct_days)} | {display_integer(week.minutes)} | "
            f"{display_hours(week.minutes)} | {table_cell(goal)} | {decision} | "
            f"{source_labels(week.sources, catalog)} |"
        )
    lines.extend(["", "Calculation ledger:", ""])
    if metrics.analysis_status == "analysis_incomplete":
        lines.extend(
            [
                "The ledger retains source-supported candidate contributions; feasibility analysis "
                f"did not complete ({metrics.reason}). Candidate values are not a proved total.",
                "",
            ]
        )
    if metrics.constraint_sources:
        lines.extend(
            [
                "Related evidence outside the displayed contribution window constrains "
                f"consistent alternatives: {source_labels(metrics.constraint_sources, catalog)}.",
                "",
            ]
        )
    lines.extend(render_ledger(metrics.contributions + metrics.exclusions, catalog))
    return lines


def reconciliation_notes(
    patient: PatientRecord, metrics: list[PatientMetrics], catalog: list[SourceRef]
) -> list[str]:
    included_ids = {
        row.encounter_id for result in metrics for row in result.contributions + result.exclusions
    }
    lines: list[str] = []
    for encounter in patient.encounters:
        if encounter.encounter_id not in included_ids:
            continue
        for decision in encounter.decisions:
            lines.append(
                f"- {encounter.encounter_id}, {decision.field} ({decision.status}): "
                f"{decision.reason} {source_labels(decision.sources, catalog)}"
            )
    return lines


def metric_uncertainty(metrics: PatientMetrics) -> list[str]:
    messages: list[str] = []
    for label, value in (
        ("session count", metrics.session_count),
        ("therapy days", metrics.distinct_days),
        ("therapy minutes", metrics.minutes),
    ):
        if value.status != "established":
            messages.append(f"{metrics.start} to {metrics.end}, {label}: {value.reason}")
    for week in metrics.weeks:
        if week.decision == "indeterminate":
            messages.append(f"Week of {week.week_start}: {week.reason}")
    return messages


def apply_failed_coverage(metrics: PatientMetrics, failed: list[str]) -> PatientMetrics:
    if not failed:
        return metrics
    weeks = [
        week.model_copy(
            update={
                "decision": "indeterminate",
                "reason": "Unprocessed source documents may contain care or plan evidence: "
                + ", ".join(failed),
                "complete_episode_coverage": False,
            }
        )
        if week.decision == "not_met"
        else week
        for week in metrics.weeks
    ]
    return metrics.model_copy(update={"weeks": weeks})


def assessment_scores(assessment: AssessmentClaim) -> list[float]:
    return sorted(set(assessment.score_alternatives or [assessment.score]))


def assessment_item_nine(assessment: AssessmentClaim) -> list[float]:
    if assessment.item_nine_alternatives:
        return sorted(set(assessment.item_nine_alternatives))
    return [] if assessment.item_nine is None else [assessment.item_nine]


def display_assessment_values(values: list[float]) -> str:
    if not values:
        return "not documented"
    rendered = " or ".join(f"{value:g}" for value in values)
    return f"{rendered} (disputed)" if len(values) > 1 else rendered


def render_symptoms(
    assessments: list[AssessmentClaim], observations: list[Observation], catalog: list[SourceRef]
) -> list[str]:
    assessment_word = "assessment" if len(assessments) == 1 else "assessments"
    lines = [
        f"The processed record contains **{len(assessments)} distinct symptom {assessment_word}** "
        "in the requested period. Completion dates identify measurements; later imports "
        "and reviews are provenance rather than additional measurements.",
        "",
        "| Completed | Instrument | Score | Item 9 | Form | Sources |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for assessment in assessments:
        score = display_assessment_values(assessment_scores(assessment))
        item_nine = display_assessment_values(assessment_item_nine(assessment))
        lines.append(
            f"| {assessment.completed_date} | {table_cell(assessment.instrument)} | "
            f"{score} | {item_nine} | {assessment.form_id or 'not documented'} | "
            f"{source_labels(assessment.sources, catalog)} |"
        )
    instruments = sorted({assessment.instrument for assessment in assessments})
    for instrument in instruments:
        measured = [assessment for assessment in assessments if assessment.instrument == instrument]
        if len(measured) > 1:
            first, last = measured[0], measured[-1]
            first_scores = assessment_scores(first)
            last_scores = assessment_scores(last)
            change = (
                f"numerical change {last_scores[0] - first_scores[0]:+g}."
                if len(first_scores) == len(last_scores) == 1
                else "A single numerical change is not established "
                "because endpoint scores disagree."
            )
            lines.extend(
                [
                    "",
                    f"{instrument}: {display_assessment_values(first_scores)} "
                    f"on {first.completed_date} to {display_assessment_values(last_scores)} "
                    f"on {last.completed_date}; {change} "
                    f"{source_labels(first.sources + last.sources, catalog)}",
                ]
            )
    lines.extend(["", "Documented observations and reasons for contact:", ""])
    if not observations:
        lines.append(
            "No supported observations or reasons for contact were extracted for this period."
        )
    for observation in observations:
        lines.append(
            f"- {observation.observed_date}, {observation.kind.replace('_', ' ')}: "
            f"{observation.text} {source_labels(observation.sources, catalog)}"
        )
    lines.extend(
        [
            "",
            "Score changes and the attributed observations above describe the documented course. "
            "They do not by themselves establish recovery, resolution of functional problems, "
            "or a causal effect of treatment. Missing measurements are not inferred.",
        ]
    )
    return lines


def answer_question(
    question: str, snapshot: ClinicalSnapshot, scenario_budget: int = 10_000
) -> AnswerBundle:
    plan = plan_question(question, snapshot)
    if plan.start is None or plan.end is None:
        raise QueryPlanningError("A supported query must have explicit resolved date bounds.")
    patient = next((entry for entry in snapshot.patients if entry.patient_id == plan.patient), None)
    metrics: list[PatientMetrics] = []
    cohort_results: list[CohortResult] = []
    comparison: PlanComparison | None = None
    assessments: list[AssessmentClaim] = []
    observations: list[Observation] = []
    sources: list[SourceRef] = []
    uncertainty: list[str] = []
    lines = [f"Snapshot: {snapshot.snapshot_id}. Question: {question}", ""]
    if plan.operation == "cohort":
        selected = [patient] if patient is not None else snapshot.patients
        cohort_results = cohort(selected, plan.start, plan.end, scenario_budget)
        if snapshot.failed_documents:
            cohort_results = [
                entry.model_copy(
                    update={
                        "membership": "analysis_incomplete",
                        "reason": "Unprocessed sources prevent a current cohort determination.",
                    }
                )
                for entry in cohort_results
            ]
        sources.extend(source for entry in cohort_results for source in entry.sources)
    elif patient is None:
        raise QueryPlanningError("The selected patient is not present in this snapshot.")
    elif plan.operation == "symptoms":
        assessments = sorted(
            [
                value
                for value in patient.assessments
                if plan.start <= value.completed_date <= plan.end
            ],
            key=lambda value: (value.completed_date, value.instrument, value.form_id or ""),
        )
        observations = sorted(
            [
                value
                for value in patient.observations
                if plan.start <= value.observed_date <= plan.end
            ],
            key=lambda value: (value.observed_date, value.kind),
        )
        sources.extend(source for value in assessments for source in value.sources)
        sources.extend(source for value in observations for source in value.sources)
        for assessment in assessments:
            label = assessment.form_id or f"{assessment.instrument} on {assessment.completed_date}"
            if len(assessment_scores(assessment)) > 1:
                uncertainty.append(
                    f"Assessment {label} has unresolved score alternatives: "
                    f"{display_assessment_values(assessment_scores(assessment))}."
                )
            if len(assessment_item_nine(assessment)) > 1:
                uncertainty.append(
                    f"Assessment {label} has unresolved item-nine alternatives: "
                    f"{display_assessment_values(assessment_item_nine(assessment))}."
                )
    elif plan.operation == "plan_change":
        comparison = compare_plans(patient, plan.start, plan.end, plan.change_date, scenario_budget)
        for result in (comparison.before, comparison.after):
            if result is not None:
                metrics.append(apply_failed_coverage(result, snapshot.failed_documents))
        comparison = comparison.model_copy(
            update={
                "before": metrics[0] if comparison.before is not None else None,
                "after": metrics[-1] if comparison.after is not None else None,
            }
        )
        if not metrics:
            uncertainty.append(comparison.reason)
        sources.extend(source for value in patient.plans for source in value.sources)
    else:
        periods = (
            [(value, value) for value in plan.selected_dates]
            if plan.operation == "day"
            else [(plan.start, plan.end)]
        )
        for start, end in periods:
            metrics.append(
                apply_failed_coverage(
                    calculate(patient, start, end, scenario_budget), snapshot.failed_documents
                )
            )
        if plan.operation in ("day", "timeline"):
            observations = sorted(
                [
                    value
                    for value in patient.observations
                    if (
                        value.observed_date in plan.selected_dates
                        if plan.selected_dates
                        else plan.start <= value.observed_date <= plan.end
                    )
                ],
                key=lambda value: (value.observed_date, value.kind),
            )
            sources.extend(source for value in observations for source in value.sources)
    for result in metrics:
        sources.extend(metric_sources(result))
        uncertainty.extend(metric_uncertainty(result))
    if patient is not None:
        relevant_ids = {
            row.encounter_id
            for result in metrics
            for row in result.contributions + result.exclusions
        }
        sources.extend(
            source
            for encounter in patient.encounters
            if encounter.encounter_id in relevant_ids
            for decision in encounter.decisions
            for source in decision.sources
        )
    catalog = unique_sources(sources)
    if plan.operation == "cohort":
        lines.extend(
            [
                f"Review window: {plan.start} through {plan.end}. Membership is evaluated "
                "within consistent interpretations across adjacent calendar weeks.",
                "",
                "| Patient | Membership | Reason | Sources |",
                "| --- | --- | --- | --- |",
            ]
        )
        names = {value.patient_id: value.name for value in snapshot.patients}
        for entry in cohort_results:
            lines.append(
                f"| {table_cell(names[entry.patient_id])} | {entry.membership} | "
                f"{table_cell(entry.reason)} | {source_labels(entry.sources, catalog)} |"
            )
            if entry.membership in ("possible", "analysis_incomplete"):
                uncertainty.append(f"{names[entry.patient_id]}: {entry.reason}")
            for witness in entry.witness:
                lines.extend(
                    [
                        "",
                        f"Witness week {witness.week_start}: {witness.distinct_days} days, "
                        f"{witness.minutes if witness.minutes is not None else 'unknown'} minutes, "
                        f"{witness.decision}; encounters {', '.join(witness.encounter_ids)}.",
                    ]
                )
    elif plan.operation == "symptoms":
        lines.extend(render_symptoms(assessments, observations, catalog))
    else:
        if comparison is not None:
            lines.extend(
                [
                    f"Plan-change date: {comparison.change_date or 'not resolved'}. "
                    f"{comparison.reason}",
                    "",
                ]
            )
        for result in metrics:
            lines.extend(render_metrics(result, catalog))
            lines.append("")
        if patient is not None:
            notes = reconciliation_notes(patient, metrics, catalog)
            if notes:
                lines.extend(["Reconciliation decisions:", "", *notes, ""])
        for observation in observations:
            lines.append(
                f"- {observation.observed_date}, {observation.kind.replace('_', ' ')}: "
                f"{observation.text} {source_labels(observation.sources, catalog)}"
            )
    if snapshot.failed_documents:
        uncertainty.append(
            "Source processing is incomplete: "
            + ", ".join(snapshot.failed_documents)
            + ". Reported totals describe the published processed records; additional care "
            "or plan evidence may be absent."
        )
    uncertainty = list(dict.fromkeys(uncertainty))
    if uncertainty:
        lines.extend(["", "Unresolved conclusions and limitations:", ""])
        lines.extend(f"- {message}" for message in uncertainty)
    lines.extend(["", "Source passages:", "", render_sources(catalog)])
    return AnswerBundle(
        question=question,
        plan=plan,
        snapshot_id=snapshot.snapshot_id,
        text="\n".join(lines),
        metrics=metrics,
        cohort_results=cohort_results,
        plan_comparison=comparison,
        assessments=assessments,
        observations=observations,
        sources=catalog,
        uncertainty=uncertainty,
        coverage_status="failed_source_processing"
        if snapshot.failed_documents
        else "available_records",
    )
