from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from backbone.calculation import (
    CohortResult,
    Contribution,
    IntegerResult,
    PatientMetrics,
    PlanComparison,
    active_plans,
    calculate,
    cohort,
    compare_plans,
)
from backbone.models import (
    AssessmentClaim,
    ClinicalSnapshot,
    Observation,
    PatientRecord,
    QueryMetric,
    QueryPlan,
    QueryTask,
    SourceRef,
)
from backbone.planning import QueryPlanner, QueryPlanningError, plan_question, validate_plan

__all__ = ["AnswerBundle", "QueryPlanningError", "answer_question", "plan_question"]


class EvidenceNeed(BaseModel):
    category: Literal["contact", "plan", "assessment", "processing", "analysis", "review_scope"]
    action: Literal[
        "obtain_documentation",
        "complete_processing",
        "increase_analysis_budget",
        "expand_review_range",
    ]
    patient_id: str | None
    patient_ids: list[str] = Field(default_factory=list)
    encounter_id: str | None = None
    assessment_id: str | None = None
    start: date
    end: date
    service_dates: list[date] = Field(default_factory=list)
    field: str
    reason: str
    needed_documentation: str | None
    next_step: str
    sources: list[SourceRef] = Field(default_factory=list)
    document_ids: list[str] = Field(default_factory=list)


class AnswerData(BaseModel):
    text: str
    metrics: list[PatientMetrics] = Field(default_factory=list)
    cohort_results: list[CohortResult] = Field(default_factory=list)
    plan_comparison: PlanComparison | None = None
    assessments: list[AssessmentClaim] = Field(default_factory=list)
    observations: list[Observation] = Field(default_factory=list)
    sources: list[SourceRef] = Field(default_factory=list)
    uncertainty: list[str] = Field(default_factory=list)
    evidence_needs: list[EvidenceNeed] = Field(default_factory=list)
    coverage_status: Literal["available_records", "failed_source_processing"]


class TaskAnswer(AnswerData):
    task: QueryTask


class AnswerBundle(AnswerData):
    question: str
    plan: QueryPlan
    snapshot_id: int
    task_answers: list[TaskAnswer]


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


def render_metrics(
    metrics: PatientMetrics,
    catalog: list[SourceRef],
    requested: list[QueryMetric],
) -> list[str]:
    enabled = set(requested or ["sessions", "distinct_days", "minutes", "service_mix"])
    summary: list[str] = []
    if "sessions" in enabled:
        summary.append(f"Eligible sessions: **{display_integer(metrics.session_count)}**.")
    if "distinct_days" in enabled:
        summary.append(f"Distinct therapy days: **{display_integer(metrics.distinct_days)}**.")
    if "minutes" in enabled:
        summary.append(
            f"Therapy minutes: **{display_integer(metrics.minutes)}** "
            f"(**{display_hours(metrics.minutes)} hours**, rounded to 3 decimals)."
        )
    lines = [
        f"Review window: {metrics.start} through {metrics.end}, inclusive.",
        "",
        " ".join(summary),
    ]
    if "service_mix" in enabled:
        lines.extend(["", "| Service | Eligible sessions |", "| --- | --- |"])
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


def contact_evidence_need(
    metrics: PatientMetrics,
    row: Contribution,
    field: str,
    reason: str,
    documentation: str,
) -> EvidenceNeed:
    dates = row.service_dates or [row.service_date]
    return EvidenceNeed(
        category="contact",
        action="obtain_documentation",
        patient_id=metrics.patient_id,
        encounter_id=row.encounter_id,
        start=metrics.start,
        end=metrics.end,
        service_dates=dates,
        field=field,
        reason=reason,
        needed_documentation=documentation,
        next_step=documentation,
        sources=unique_sources(row.sources),
    )


def metric_evidence_needs(
    patient: PatientRecord, metrics: PatientMetrics, task: QueryTask
) -> list[EvidenceNeed]:
    needs: list[EvidenceNeed] = []
    if metrics.reason == "scenario_budget_exceeded":
        return [
            EvidenceNeed(
                category="analysis",
                action="increase_analysis_budget",
                patient_id=patient.patient_id,
                start=metrics.start,
                end=metrics.end,
                field="scenario_budget",
                reason="Supported combinations were not fully evaluated "
                "within the analysis budget.",
                needed_documentation=None,
                next_step="Increase the scenario budget and replay this query; "
                "this execution limit does not by itself require another clinical document.",
                sources=metric_sources(metrics),
            )
        ]
    minutes_requested = task.operation in ("weekly", "cohort", "plan_change") or (
        "minutes" in task.metrics or (not task.metrics and task.operation != "counts")
    )
    encounters = {value.encounter_id: value for value in patient.encounters}
    for row in metrics.contributions:
        encounter = encounters[row.encounter_id]
        label = f"patient {patient.patient_id}, encounter {row.encounter_id}, " + " or ".join(
            str(value) for value in row.service_dates or [row.service_date]
        )
        relevant = [value for value in row.interpretations if value.in_review_range]
        if any(
            decision.field == "identity" and decision.status != "established"
            for decision in encounter.decisions
        ):
            needs.append(
                contact_evidence_need(
                    metrics,
                    row,
                    "encounter_identity",
                    "The record does not establish whether these descriptions are one encounter "
                    "or separate encounters.",
                    f"Obtain an encounter or appointment linkage record for {label} that links "
                    "the source descriptions to their actual event identifiers.",
                )
            )
        if row.inclusion == "uncertain":
            attendance = {value.attendance for value in relevant}
            if "unknown" in attendance or len(attendance) > 1:
                needs.append(
                    contact_evidence_need(
                        metrics,
                        row,
                        "attendance",
                        "Actual attendance is missing or differs across supported "
                        "event interpretations.",
                        "Obtain the patient-specific attendance or disposition record, "
                        "or an explicit "
                        f"attendance correction, for {label}.",
                    )
                )
            presence = {value.patient_present for value in relevant}
            requires_presence = any(
                plan.patient_present_required
                for value in relevant
                for plan in active_plans(patient, value.service_date)
            )
            if requires_presence and (None in presence or len(presence) > 1):
                needs.append(
                    contact_evidence_need(
                        metrics,
                        row,
                        "patient_present",
                        "The effective plan requires patient presence, which is not established "
                        "consistently for this encounter.",
                        "Obtain a patient attendance/presence record with actual arrival "
                        "and departure "
                        f"times for {label}; a scheduled slot alone does not establish presence.",
                    )
                )
            if any(key.startswith("plan:") for value in relevant for key in value.choices):
                plan_sources = [
                    reference
                    for value in relevant
                    for effective_plan in active_plans(patient, value.service_date)
                    for reference in effective_plan.sources
                ]
                needs.append(
                    contact_evidence_need(
                        metrics,
                        row,
                        "effective_plan",
                        "Conflicting effective plans give different therapy-inclusion rules.",
                        f"Obtain the authoritative signed treatment plan or an explicit plan "
                        f"correction effective for {label}, establishing eligible services "
                        "and patient-presence requirements.",
                    ).model_copy(
                        update={
                            "category": "plan",
                            "sources": unique_sources(row.sources + plan_sources),
                        }
                    )
                )
        counted = [value for value in relevant if value.eligible]
        durations = {value.minutes for value in counted}
        if minutes_requested and len({value for value in durations if value is not None}) > 1:
            values = " or ".join(
                str(value) for value in sorted(value for value in durations if value is not None)
            )
            needs.append(
                contact_evidence_need(
                    metrics,
                    row,
                    "duration",
                    "Supported records disagree on actual patient-contact duration: "
                    f"{values} minutes.",
                    f"Obtain an explicit duration correction scoped to {label}, identifying which "
                    "earlier assertion it replaces, or the actual patient-contact start/end times "
                    "and break record for that encounter.",
                )
            )
        elif minutes_requested and None in durations:
            needs.append(
                contact_evidence_need(
                    metrics,
                    row,
                    "duration",
                    "An eligible interpretation has no established patient-contact duration.",
                    f"Obtain actual patient-contact intervals and any break log for {label}; "
                    "for group care, document this patient's presence within "
                    "the activity interval.",
                )
            )
        for field, conflicting_values, documentation in (
            (
                "service_date",
                {value.service_date for value in row.interpretations},
                "a dated encounter record or explicit service-date correction",
            ),
            (
                "service_type",
                {value.service_type for value in row.interpretations},
                "a service record or explicit correction identifying the delivered service type",
            ),
        ):
            if len(conflicting_values) > 1:
                needs.append(
                    contact_evidence_need(
                        metrics,
                        row,
                        field,
                        f"Supported event interpretations disagree on {field.replace('_', ' ')}.",
                        f"Obtain {documentation} for {label}, linked to the source assertions.",
                    )
                )
        dates_without_plan = sorted(
            {
                value.service_date
                for value in relevant
                if value.attendance not in ("no_show", "cancelled")
                and not active_plans(patient, value.service_date)
            }
        )
        if dates_without_plan:
            needs.append(
                contact_evidence_need(
                    metrics,
                    row,
                    "effective_plan",
                    "No effective treatment plan establishes which services "
                    "and presence rules apply.",
                    f"Obtain the signed treatment plan effective for {label}, including effective "
                    "dates, eligible services, and patient-presence requirements.",
                )
            )
    if task.operation in ("weekly", "cohort", "plan_change"):
        for week in metrics.weeks:
            if week.goal_reason in (
                "missing_effective_plan",
                "conflicting_or_midweek_plan_policy_unspecified",
            ):
                documentation = (
                    "Obtain the signed treatment plan and effective dates covering this week, "
                    "with its weekly day/minute targets and service eligibility rules."
                    if week.goal_reason == "missing_effective_plan"
                    else "Obtain the authoritative effective plan or a scoped plan correction, "
                    "plus an explicit rule for applying weekly targets when a plan changes "
                    "within the week; do not infer prorating."
                )
                needs.append(
                    EvidenceNeed(
                        category="plan",
                        action="obtain_documentation",
                        patient_id=patient.patient_id,
                        start=week.week_start,
                        end=week.week_end,
                        field="weekly_goal",
                        reason=week.goal_reason,
                        needed_documentation=documentation,
                        next_step=documentation,
                        sources=unique_sources(week.sources),
                    )
                )
            elif week.decision == "indeterminate" and (
                week.review_start > max(week.week_start, patient.episode_start or week.week_start)
                or week.review_end < min(week.week_end, patient.episode_end or week.week_end)
            ):
                needs.append(
                    EvidenceNeed(
                        category="review_scope",
                        action="expand_review_range",
                        patient_id=patient.patient_id,
                        start=week.week_start,
                        end=week.week_end,
                        field="weekly_coverage",
                        reason="The selected dates do not cover the week's full treatment episode.",
                        needed_documentation=None,
                        next_step="Expand the query to the complete episode portion "
                        "of this calendar "
                        "week before concluding that its weekly target was missed.",
                        sources=unique_sources(week.sources),
                    )
                )
    return needs


def assessment_evidence_needs(assessments: list[AssessmentClaim]) -> list[EvidenceNeed]:
    needs: list[EvidenceNeed] = []
    for assessment in assessments:
        dates = assessment_dates(assessment)
        identifier = assessment.form_id or f"{assessment.instrument} on {assessment.completed_date}"
        for field, disputed in (
            ("score", len(assessment_scores(assessment)) > 1),
            ("item_nine", len(assessment_item_nine(assessment)) > 1),
            ("completed_date", len(dates) > 1),
        ):
            if disputed:
                documentation = (
                    f"Obtain the original completed {assessment.instrument} form {identifier} "
                    f"for patient {assessment.patient_id}, or an explicit corrected result linked "
                    f"to that form, establishing its {field.replace('_', ' ')}. "
                    "A later import or review is not a new completed measurement."
                )
                needs.append(
                    EvidenceNeed(
                        category="assessment",
                        action="obtain_documentation",
                        patient_id=assessment.patient_id,
                        assessment_id=identifier,
                        start=min(dates),
                        end=max(dates),
                        service_dates=dates,
                        field=field,
                        reason="The same assessment has conflicting "
                        f"{field.replace('_', ' ')} values.",
                        needed_documentation=documentation,
                        next_step=documentation,
                        sources=unique_sources(assessment.sources),
                    )
                )
    return needs


def unique_evidence_needs(needs: list[EvidenceNeed]) -> list[EvidenceNeed]:
    unique: dict[str, EvidenceNeed] = {}
    for need in needs:
        key = need.model_dump_json(exclude={"sources"})
        previous = unique.get(key)
        unique[key] = (
            need
            if previous is None
            else need.model_copy(
                update={"sources": unique_sources(previous.sources + need.sources)}
            )
        )
    return list(unique.values())


def render_evidence_needs(needs: list[EvidenceNeed], catalog: list[SourceRef]) -> list[str]:
    if not needs:
        return []
    lines = ["", "Additional evidence needed:", ""]
    for need in needs:
        population = need.patient_id or ", ".join(need.patient_ids)
        identifier = need.encounter_id or need.assessment_id
        scope = f"patient {population}" if need.patient_id is not None else f"patients {population}"
        if identifier is not None:
            scope += f", {identifier}"
        scope += f", {need.start} through {need.end}"
        lines.append(
            f"- {scope}, {need.field.replace('_', ' ')}: {need.reason} "
            f"{need.next_step} {source_labels(need.sources, catalog)}".rstrip()
        )
    return lines


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


def assessment_dates(assessment: AssessmentClaim) -> list[date]:
    return sorted(set(assessment.completed_date_alternatives or [assessment.completed_date]))


def assessment_in_scope(
    assessment: AssessmentClaim, start: date, end: date, selected_dates: list[date]
) -> bool:
    return any(
        value in selected_dates if selected_dates else start <= value <= end
        for value in assessment_dates(assessment)
    )


def assessment_certain_in_scope(
    assessment: AssessmentClaim, start: date, end: date, selected_dates: list[date]
) -> bool:
    return all(
        value in selected_dates if selected_dates else start <= value <= end
        for value in assessment_dates(assessment)
    )


def select_assessments(
    patient: PatientRecord, start: date, end: date, selected_dates: list[date]
) -> list[AssessmentClaim]:
    return sorted(
        [
            value
            for value in patient.assessments
            if assessment_in_scope(value, start, end, selected_dates)
        ],
        key=lambda value: (min(assessment_dates(value)), value.instrument, value.form_id or ""),
    )


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
    assessments: list[AssessmentClaim],
    observations: list[Observation],
    catalog: list[SourceRef],
    start: date,
    end: date,
    selected_dates: list[date],
) -> list[str]:
    assessment_word = "assessment" if len(assessments) == 1 else "assessments"
    certain_count = sum(
        assessment_certain_in_scope(value, start, end, selected_dates) for value in assessments
    )
    count_text = (
        f"The processed record contains **{len(assessments)} distinct symptom {assessment_word}** "
        "in the requested period."
        if certain_count == len(assessments)
        else f"The record establishes **{certain_count} distinct symptom assessments** "
        f"in the requested period; **{len(assessments) - certain_count} additional forms** "
        "have disputed period membership."
    )
    lines = [
        count_text + " Completion dates identify measurements; later imports "
        "and reviews are provenance rather than additional measurements.",
        "",
        "| Completed | Instrument | Score | Item 9 | Form | Period membership | Sources |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for assessment in assessments:
        score = display_assessment_values(assessment_scores(assessment))
        item_nine = display_assessment_values(assessment_item_nine(assessment))
        dates = " or ".join(str(value) for value in assessment_dates(assessment))
        if len(assessment_dates(assessment)) > 1:
            dates += " (disputed)"
        membership = (
            "established"
            if assessment_certain_in_scope(assessment, start, end, selected_dates)
            else "possible; completion date disputed"
        )
        lines.append(
            f"| {dates} | {table_cell(assessment.instrument)} | "
            f"{score} | {item_nine} | {assessment.form_id or 'not documented'} | "
            f"{membership} | "
            f"{source_labels(assessment.sources, catalog)} |"
        )
    instruments = sorted({assessment.instrument for assessment in assessments})
    for instrument in instruments:
        measured = [assessment for assessment in assessments if assessment.instrument == instrument]
        if len(measured) > 1:
            if any(len(assessment_dates(value)) > 1 for value in measured):
                lines.extend(
                    [
                        "",
                        f"{instrument}: conflicting completion dates prevent an established "
                        "chronological sequence or a single net-change conclusion.",
                    ]
                )
                continue
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
    lines.extend(["", "Attributed clinical course:", ""])
    if not observations:
        lines.append(
            "No supported observations or reasons for contact were extracted for this period."
        )
    groups: list[tuple[str, str]] = [
        ("patient_report", "Patient reports"),
        ("clinician_observation", "Clinician observations"),
        ("collateral_report", "Collateral reports"),
        ("reason_for_contact", "Documented reasons for additional contact"),
    ]
    for kind, heading in groups:
        entries = sorted(
            [value for value in observations if value.kind == kind],
            key=lambda value: value.observed_date,
        )
        if entries:
            lines.extend([heading + ":", ""])
            for observation in entries:
                lines.append(
                    f"- {observation.observed_date}: {observation.text} "
                    f"{source_labels(observation.sources, catalog)}"
                )
            lines.append("")
    lines.extend(
        [
            "",
            "Score changes and the attributed observations above describe the documented course. "
            "They do not by themselves establish recovery, resolution of functional problems, "
            "or a causal effect of treatment. Missing measurements are not inferred.",
        ]
    )
    return lines


def answer_task(
    question: str, snapshot: ClinicalSnapshot, plan: QueryTask, scenario_budget: int
) -> TaskAnswer:
    patient = next((entry for entry in snapshot.patients if entry.patient_id == plan.patient), None)
    metrics: list[PatientMetrics] = []
    cohort_results: list[CohortResult] = []
    comparison: PlanComparison | None = None
    assessments: list[AssessmentClaim] = []
    observations: list[Observation] = []
    sources: list[SourceRef] = []
    uncertainty: list[str] = []
    evidence_needs: list[EvidenceNeed] = []
    non_contacts = [
        record
        for record in snapshot.non_contact_records
        if patient is not None
        and patient.patient_id in record.patient_ids
        and plan.operation == "counts"
    ]
    sources.extend(record.source for record in non_contacts)
    lines = [f"Snapshot: {snapshot.snapshot_id}. Question: {question}", ""]
    if plan.operation == "cohort":
        selected = [entry for entry in snapshot.patients if entry.patient_id in plan.patient_ids]
        cohort_results = cohort(
            selected, plan.start, plan.end, scenario_budget, plan.consecutive_weeks
        )
        unresolved_ids = {
            entry.patient_id
            for entry in cohort_results
            if entry.membership in ("possible", "analysis_incomplete")
        }
        for cohort_patient in selected:
            if cohort_patient.patient_id in unresolved_ids:
                cohort_metrics = calculate(cohort_patient, plan.start, plan.end, scenario_budget)
                evidence_needs.extend(metric_evidence_needs(cohort_patient, cohort_metrics, plan))
        if snapshot.unprocessed_documents:
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
        assessments = select_assessments(patient, plan.start, plan.end, plan.selected_dates)
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
        sources.extend(source for value in assessments for source in value.sources)
        sources.extend(source for value in observations for source in value.sources)
    elif plan.operation == "plan_change":
        comparison = compare_plans(patient, plan.start, plan.end, plan.change_date, scenario_budget)
        for result in (comparison.before, comparison.after):
            if result is not None:
                metrics.append(apply_failed_coverage(result, snapshot.unprocessed_documents))
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
            if plan.selected_dates
            else [(plan.start, plan.end)]
        )
        for start, end in periods:
            metrics.append(
                apply_failed_coverage(
                    calculate(patient, start, end, scenario_budget), snapshot.unprocessed_documents
                )
            )
        if plan.operation in ("day", "timeline"):
            assessments = select_assessments(patient, plan.start, plan.end, plan.selected_dates)
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
            sources.extend(source for value in assessments for source in value.sources)
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
        if len(assessment_dates(assessment)) > 1:
            uncertainty.append(
                f"Assessment {label} has conflicting completion dates: "
                + " or ".join(str(value) for value in assessment_dates(assessment))
                + ". Exact chronology is not established."
            )
        if not assessment_certain_in_scope(assessment, plan.start, plan.end, plan.selected_dates):
            uncertainty.append(f"Assessment {label} may fall outside the requested period.")
    for result in metrics:
        sources.extend(metric_sources(result))
        uncertainty.extend(metric_uncertainty(result))
        if patient is not None:
            evidence_needs.extend(metric_evidence_needs(patient, result, plan))
    evidence_needs.extend(assessment_evidence_needs(assessments))
    if snapshot.unprocessed_documents:
        evidence_needs.append(
            EvidenceNeed(
                category="processing",
                action="complete_processing",
                patient_id=None,
                patient_ids=plan.patient_ids,
                start=plan.start,
                end=plan.end,
                field="source_processing",
                reason="Listed source documents have not been incorporated "
                "into the published record; "
                "their patient attribution and effect on this query are not yet established.",
                needed_documentation=None,
                next_step="Complete extraction and reconciliation for these existing documents: "
                + ", ".join(snapshot.unprocessed_documents)
                + ". Publish the updated snapshot and rerun the query "
                "before requesting new records.",
                document_ids=snapshot.unprocessed_documents,
            )
        )
    evidence_needs = unique_evidence_needs(evidence_needs)
    sources.extend(source for need in evidence_needs for source in need.sources)
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
        lines.extend(
            render_symptoms(
                assessments, observations, catalog, plan.start, plan.end, plan.selected_dates
            )
        )
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
            lines.extend(render_metrics(result, catalog, plan.metrics))
            lines.append("")
        if patient is not None:
            notes = reconciliation_notes(patient, metrics, catalog)
            if notes:
                lines.extend(["Reconciliation decisions:", "", *notes, ""])
        if assessments:
            lines.extend(
                render_symptoms(
                    assessments, observations, catalog, plan.start, plan.end, plan.selected_dates
                )
            )
        else:
            for observation in observations:
                lines.append(
                    f"- {observation.observed_date}, {observation.kind.replace('_', ' ')}: "
                    f"{observation.text} {source_labels(observation.sources, catalog)}"
                )
    if non_contacts:
        lines.extend(["", "Records with no extracted care contact:", ""])
        for record in non_contacts:
            lines.append(
                f"- {record.source.document_id}: {record.assessment_claims} assessment claims and "
                f"{record.observation_claims} observations; no additional session is counted. "
                "Administrative quantities and measure reviews do not establish "
                "delivered contacts. "
                f"{source_labels([record.source], catalog)}"
            )
    if snapshot.unprocessed_documents:
        uncertainty.append(
            "Source processing is incomplete: "
            + ", ".join(snapshot.unprocessed_documents)
            + ". Reported totals describe the published processed records; additional care "
            "or plan evidence may be absent."
        )
    uncertainty = list(dict.fromkeys(uncertainty))
    if uncertainty:
        lines.extend(["", "Unresolved conclusions and limitations:", ""])
        lines.extend(f"- {message}" for message in uncertainty)
    lines.extend(render_evidence_needs(evidence_needs, catalog))
    lines.extend(["", "Source passages:", "", render_sources(catalog)])
    return TaskAnswer(
        task=plan,
        text="\n".join(lines),
        metrics=metrics,
        cohort_results=cohort_results,
        plan_comparison=comparison,
        assessments=assessments,
        observations=observations,
        sources=catalog,
        uncertainty=uncertainty,
        evidence_needs=evidence_needs,
        coverage_status="failed_source_processing"
        if snapshot.unprocessed_documents
        else "available_records",
    )


def answer_question(
    question: str,
    snapshot: ClinicalSnapshot,
    scenario_budget: int = 10_000,
    *,
    plan: QueryPlan | None = None,
    planner: QueryPlanner | None = None,
    context: QueryPlan | None = None,
) -> AnswerBundle:
    resolved = (
        plan
        if plan is not None
        else plan_question(question, snapshot, planner=planner, context=context)
    )
    validate_plan(resolved, question, snapshot)
    answers = [answer_task(question, snapshot, task, scenario_budget) for task in resolved.tasks]
    names = {patient.patient_id: patient.name for patient in snapshot.patients}
    text = (
        answers[0].text
        if len(answers) == 1
        else "\n\n".join(
            f"Task {index}: {answer.task.operation}; "
            f"patients {', '.join(names[value] for value in answer.task.patient_ids)}.\n\n"
            f"{answer.text}"
            for index, answer in enumerate(answers, start=1)
        )
    )
    return AnswerBundle(
        question=question,
        plan=resolved,
        snapshot_id=snapshot.snapshot_id,
        text=text,
        task_answers=answers,
        metrics=[entry for answer in answers for entry in answer.metrics],
        cohort_results=[entry for answer in answers for entry in answer.cohort_results],
        plan_comparison=answers[0].plan_comparison if len(answers) == 1 else None,
        assessments=[entry for answer in answers for entry in answer.assessments],
        observations=[entry for answer in answers for entry in answer.observations],
        sources=unique_sources([source for answer in answers for source in answer.sources]),
        uncertainty=list(
            dict.fromkeys(message for answer in answers for message in answer.uncertainty)
        ),
        evidence_needs=unique_evidence_needs(
            [entry for answer in answers for entry in answer.evidence_needs]
        ),
        coverage_status="failed_source_processing"
        if snapshot.unprocessed_documents
        else "available_records",
    )
