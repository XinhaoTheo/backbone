from __future__ import annotations

import hashlib
from collections import defaultdict
from datetime import date
from typing import Literal

from backbone.models import (
    AssessmentClaim,
    Attendance,
    ContactAlternative,
    ContactClaim,
    Decision,
    DocumentEvidence,
    Encounter,
    Observation,
    PatientIdentity,
    PatientRecord,
    PlanClaim,
    SourceRef,
    TimeInterval,
)


def merge_sources(groups: list[list[SourceRef]]) -> list[SourceRef]:
    references = {source.model_dump_json(): source for group in groups for source in group}
    return sorted(
        references.values(),
        key=lambda source: (source.document_id, source.start_line, source.quote),
    )


def clock_minutes(clock: str) -> int:
    hour, minute = clock.split(":")
    return int(hour) * 60 + int(minute)


def merge_intervals(intervals: list[TimeInterval]) -> list[tuple[int, int]]:
    merged: list[tuple[int, int]] = []
    for start, end in sorted(
        (clock_minutes(item.start), clock_minutes(item.end)) for item in intervals
    ):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    return merged


def intersect_intervals(
    presence: list[TimeInterval], activity: list[TimeInterval]
) -> list[TimeInterval]:
    return [
        TimeInterval(
            start=f"{start // 60:02d}:{start % 60:02d}", end=f"{end // 60:02d}:{end % 60:02d}"
        )
        for left_start, left_end in merge_intervals(presence)
        for right_start, right_end in merge_intervals(activity)
        if (start := max(left_start, right_start)) < (end := min(left_end, right_end))
    ]


def delivered_minutes(intervals: list[TimeInterval], breaks: list[TimeInterval]) -> int:
    return sum(end - start for start, end in merge_intervals(intervals)) - sum(
        max(0, min(end, break_end) - max(start, break_start))
        for start, end in merge_intervals(intervals)
        for break_start, break_end in merge_intervals(breaks)
    )


def patient_key(identity: PatientIdentity) -> str:
    return f"{identity.organization.strip().casefold()}::{identity.patient_id}"


def encounter_key(claim: ContactClaim) -> str:
    if claim.encounter_id is not None:
        return claim.encounter_id
    if claim.appointment_id is not None:
        return f"appointment:{claim.appointment_id}"
    fingerprint = hashlib.sha256(claim.model_dump_json().encode()).hexdigest()[:16]
    return f"unlinked:{fingerprint}"


def attested_claims(claims: list[ContactClaim]) -> list[ContactClaim]:
    return [claim for claim in claims if claim.record_status not in ("draft", "correction")]


def resolve_attendance(claims: list[ContactClaim]) -> tuple[Attendance, Decision]:
    usable = [
        claim
        for claim in attested_claims(claims)
        if claim.interval_kind != "scheduled"
        or claim.attendance in ("no_show", "cancelled")
        or claim.record_status == "final"
    ]
    updates = [claim for claim in claims if "attendance" in claim.correction_fields]
    statuses = {claim.attendance for claim in updates or usable if claim.attendance != "unknown"}
    sources = merge_sources([claim.sources for claim in claims])
    if len(statuses) == 1:
        return next(iter(statuses)), Decision(
            field="attendance",
            status="established",
            reason="Patient-specific disposition establishes attendance; drafts add no visit.",
            sources=sources,
        )
    if len(statuses) > 1:
        return "unknown", Decision(
            field="attendance",
            status="conflicting_evidence",
            reason="Attendance assertions disagree without a resolving correction.",
            sources=sources,
        )
    return "unknown", Decision(
        field="attendance",
        status="missing_evidence",
        reason="Actual attendance is not established.",
        sources=sources,
    )


def patch_contact(claim: ContactClaim, correction: ContactClaim) -> ContactClaim:
    changed = claim.model_copy(deep=True)
    if "intervals" in correction.correction_fields:
        changed.intervals = correction.intervals
        changed.stated_minutes = None
    if "arrival" in correction.correction_fields and changed.intervals and correction.intervals:
        changed.intervals[0] = TimeInterval(
            start=correction.intervals[0].start, end=changed.intervals[0].end
        )
        changed.stated_minutes = None
    if "departure" in correction.correction_fields and changed.intervals and correction.intervals:
        changed.intervals[-1] = TimeInterval(
            start=changed.intervals[-1].start, end=correction.intervals[-1].end
        )
        changed.stated_minutes = None
    if "duration" in correction.correction_fields:
        changed.stated_minutes = correction.stated_minutes
        if "intervals" not in correction.correction_fields:
            changed.intervals = []
    changed.sources = merge_sources([changed.sources, correction.sources])
    return changed


def corrected_claims(claims: list[ContactClaim]) -> tuple[list[ContactClaim], list[Decision]]:
    ordinary = attested_claims(claims)
    corrections = [claim for claim in claims if claim.record_status == "correction"]
    groups: dict[tuple[date, str, tuple[str, ...]], list[ContactClaim]] = defaultdict(list)
    for correction in corrections:
        scope = tuple(
            sorted(field for field in correction.correction_fields if field != "attendance")
        )
        if scope:
            groups[(correction.service_date, correction.interval_kind, scope)].append(correction)
    variants = ordinary or corrections
    decisions: list[Decision] = []
    for (service_date, kind, fields), updates in groups.items():
        following: list[ContactClaim] = []
        for claim in variants:
            if claim.service_date == service_date and claim.interval_kind == kind:
                following.extend(patch_contact(claim, update) for update in updates)
            else:
                following.append(claim)
        variants = following
        decisions.extend(
            Decision(
                field=field,
                status="established" if len(updates) == 1 else "conflicting_evidence",
                reason="Apply the scoped correction to matching fields, not receipt order.",
                sources=merge_sources([update.sources for update in updates]),
            )
            for field in fields
        )
    return variants, decisions


def duration_alternatives(
    claims: list[ContactClaim], identifier: str
) -> tuple[list[ContactAlternative], list[Decision]]:
    variants, decisions = corrected_claims(claims)
    ordinary = attested_claims(claims)
    alternatives: dict[
        tuple[date, str, Attendance, bool | None, int | None], ContactAlternative
    ] = {}
    timed = [
        claim
        for claim in variants
        if claim.interval_kind in ("patient_contact", "patient_presence")
        or claim.attendance in ("no_show", "cancelled")
    ]
    if not timed:
        timed = variants or claims
    for claim in timed:
        activities = [
            item
            for item in ordinary
            if item.service_date == claim.service_date and item.interval_kind == "group_activity"
        ]
        breaks = [
            interval
            for item in ordinary
            if item.service_date == claim.service_date
            for interval in item.breaks
        ]
        intervals = claim.intervals
        if claim.interval_kind == "patient_presence" and activities:
            intervals = intersect_intervals(
                intervals, [interval for item in activities for interval in item.intervals]
            )
        if claim.attendance in ("no_show", "cancelled"):
            values: list[int | None] = [0]
            intervals = []
        elif claim.interval_kind in ("patient_contact", "patient_presence"):
            minutes = delivered_minutes(intervals, breaks) if intervals else claim.stated_minutes
            values = [minutes]
            if (
                claim.interval_kind == "patient_contact"
                and claim.stated_minutes is not None
                and claim.stated_minutes != minutes
            ):
                values.append(claim.stated_minutes)
        else:
            values = [None]
            intervals = []
        for value in values:
            key = (
                claim.service_date,
                claim.service_type,
                claim.attendance,
                claim.patient_present,
                value,
            )
            refs = merge_sources(
                [
                    claim.sources,
                    *[item.sources for item in activities],
                    *[
                        item.sources
                        for item in ordinary
                        if item.breaks and item.service_date == claim.service_date
                    ],
                ]
            )
            if key in alternatives:
                refs = merge_sources([alternatives[key].sources, refs])
            alternatives[key] = ContactAlternative(
                minutes=value,
                intervals=intervals,
                sources=refs,
                service_date=claim.service_date,
                service_type=claim.service_type,
                attendance=claim.attendance,
                patient_present=claim.patient_present,
            )
    result = sorted(
        alternatives.values(),
        key=lambda option: (
            str(option.service_date),
            str(option.service_type),
            -1 if option.minutes is None else option.minutes,
        ),
    )
    if len(result) > 1:
        for option in result:
            option.choices = {
                f"event:{identifier}": (
                    f"{option.service_date}:{option.service_type}:{option.attendance}:"
                    f"{option.patient_present}:{option.minutes}"
                )
            }
    minutes_set = {option.minutes for option in result}
    status: Literal["missing_evidence", "conflicting_evidence", "established"] = (
        "missing_evidence"
        if None in minutes_set
        else "conflicting_evidence"
        if len(minutes_set) > 1
        else "established"
    )
    decisions.append(
        Decision(
            field="duration",
            status=status,
            reason="Intersect attendance with activity and remove breaks for each interpretation.",
            sources=merge_sources([option.sources for option in result]),
        )
    )
    return result, decisions


def reconcile_encounter(identifier: str, claims: list[ContactClaim]) -> Encounter:
    anchor = claims[0]
    attendance, attendance_decision = resolve_attendance(claims)
    usable = attested_claims(claims)
    types = {claim.service_type for claim in usable if claim.service_type != "other"}
    service = next(iter(types)) if len(types) == 1 else anchor.service_type
    presence = {claim.patient_present for claim in usable if claim.patient_present is not None}
    patient_present = next(iter(presence)) if len(presence) == 1 else None
    alternatives, decisions = duration_alternatives(claims, f"{anchor.patient_id}:{identifier}")
    if attendance in ("no_show", "cancelled"):
        patient_present = False
        for option in alternatives:
            option.attendance = attendance
            option.patient_present = False
            option.minutes = 0
    for field, values in (
        ("service_type", types),
        ("service_date", {str(claim.service_date) for claim in usable}),
    ):
        if len(values) > 1:
            decisions.append(
                Decision(
                    field=field,
                    status="conflicting_evidence",
                    reason="Source interpretations disagree on this field.",
                    sources=merge_sources([claim.sources for claim in usable]),
                )
            )
    return Encounter(
        encounter_id=identifier,
        patient_id=anchor.patient_id,
        service_date=min(claim.service_date for claim in claims),
        service_type=service,
        attendance=attendance,
        patient_present=patient_present,
        alternatives=alternatives,
        decisions=[attendance_decision, *decisions],
        sources=merge_sources([claim.sources for claim in claims]),
    )


def reconcile_plans(plans: list[PlanClaim]) -> list[PlanClaim]:
    grouped: dict[str, PlanClaim] = {}
    for plan in plans:
        key = plan.model_dump_json(exclude={"quotes", "sources", "note"})
        if key in grouped:
            grouped[key].sources = merge_sources([grouped[key].sources, plan.sources])
            grouped[key].quotes = sorted(set([*grouped[key].quotes, *plan.quotes]))
        else:
            grouped[key] = plan.model_copy(deep=True)
    return sorted(grouped.values(), key=lambda plan: plan.effective_start)


def reconcile_assessments(assessments: list[AssessmentClaim]) -> list[AssessmentClaim]:
    grouped: dict[tuple[str, str, date], AssessmentClaim] = {}
    for assessment in sorted(assessments, key=lambda item: item.is_copy):
        identifier = assessment.form_id
        if identifier is None and assessment.is_copy:
            candidates = [
                key
                for key in grouped
                if key[0] == assessment.instrument.casefold()
                and key[2] == assessment.completed_date
            ]
            if len(candidates) == 1:
                identifier = candidates[0][1]
        if identifier is None:
            identifier = hashlib.sha256(assessment.model_dump_json().encode()).hexdigest()[:16]
        key = (assessment.instrument.casefold(), identifier, assessment.completed_date)
        if key not in grouped:
            grouped[key] = assessment.model_copy(deep=True)
            grouped[key].score_alternatives = [assessment.score]
            grouped[key].item_nine_alternatives = (
                [] if assessment.item_nine is None else [assessment.item_nine]
            )
        else:
            existing = grouped[key]
            existing.sources = merge_sources([existing.sources, assessment.sources])
            existing.quotes = sorted(set([*existing.quotes, *assessment.quotes]))
            existing.score_alternatives = sorted(
                set([*existing.score_alternatives, assessment.score])
            )
            if assessment.item_nine is not None:
                existing.item_nine_alternatives = sorted(
                    set([*existing.item_nine_alternatives, assessment.item_nine])
                )
                existing.item_nine = existing.item_nine_alternatives[0]
    return sorted(
        grouped.values(),
        key=lambda assessment: (assessment.completed_date, assessment.instrument, assessment.score),
    )


def reconcile_observations(observations: list[Observation]) -> list[Observation]:
    grouped: dict[str, Observation] = {}
    for observation in observations:
        key = observation.model_dump_json(exclude={"quotes", "sources"})
        if key in grouped:
            grouped[key].sources = merge_sources([grouped[key].sources, observation.sources])
            grouped[key].quotes = sorted(set([*grouped[key].quotes, *observation.quotes]))
        else:
            grouped[key] = observation.model_copy(deep=True)
    return sorted(grouped.values(), key=lambda observation: observation.observed_date)


def reconcile(evidences: list[DocumentEvidence]) -> list[PatientRecord]:
    identities: dict[str, list[PatientIdentity]] = defaultdict(list)
    contacts: dict[str, list[ContactClaim]] = defaultdict(list)
    plans: dict[str, list[PlanClaim]] = defaultdict(list)
    assessments: dict[str, list[AssessmentClaim]] = defaultdict(list)
    observations: dict[str, list[Observation]] = defaultdict(list)
    for evidence in evidences:
        keys = {patient.patient_id: patient_key(patient) for patient in evidence.patients}
        for patient in evidence.patients:
            identities[keys[patient.patient_id]].append(patient)
        for contact in evidence.contacts:
            key = keys[contact.patient_id]
            contacts[key].append(contact.model_copy(update={"patient_id": key}, deep=True))
        for plan in evidence.plans:
            key = keys[plan.patient_id]
            plans[key].append(plan.model_copy(update={"patient_id": key}, deep=True))
        for assessment in evidence.assessments:
            key = keys[assessment.patient_id]
            assessments[key].append(assessment.model_copy(update={"patient_id": key}, deep=True))
        for observation in evidence.observations:
            key = keys[observation.patient_id]
            observations[key].append(observation.model_copy(update={"patient_id": key}, deep=True))
    records: list[PatientRecord] = []
    for key, patient_identities in sorted(identities.items()):
        contact_groups: dict[str, list[ContactClaim]] = defaultdict(list)
        appointment_ids: dict[str, set[str]] = defaultdict(set)
        for claim in contacts[key]:
            if claim.appointment_id is not None and claim.encounter_id is not None:
                appointment_ids[claim.appointment_id].add(claim.encounter_id)
        for claim in contacts[key]:
            if (
                claim.encounter_id is None
                and claim.appointment_id is not None
                and len(appointment_ids[claim.appointment_id]) == 1
            ):
                claim = claim.model_copy(
                    update={"encounter_id": next(iter(appointment_ids[claim.appointment_id]))}
                )
            contact_groups[encounter_key(claim)].append(claim)
        encounters = [
            reconcile_encounter(identifier, grouped)
            for identifier, grouped in sorted(contact_groups.items())
        ]
        anonymous: dict[tuple[date, str], list[Encounter]] = defaultdict(list)
        for encounter in encounters:
            if encounter.encounter_id.startswith("unlinked:"):
                anonymous[(encounter.service_date, encounter.service_type)].append(encounter)
        for ambiguous in anonymous.values():
            if len(ambiguous) > 1:
                for encounter in ambiguous:
                    encounter.decisions.append(
                        Decision(
                            field="identity",
                            status="missing_evidence",
                            reason="Same-day descriptions do not establish distinct contacts.",
                            sources=merge_sources([item.sources for item in ambiguous]),
                        )
                    )
        starts = [
            patient.episode_start
            for patient in patient_identities
            if patient.episode_start is not None
        ]
        ends = [
            patient.episode_end for patient in patient_identities if patient.episode_end is not None
        ]
        records.append(
            PatientRecord(
                patient_id=key,
                name=patient_identities[0].name,
                organization=patient_identities[0].organization,
                episode_start=min(starts) if starts else None,
                episode_end=max(ends) if ends else None,
                encounters=sorted(
                    encounters,
                    key=lambda encounter: (encounter.service_date, encounter.encounter_id),
                ),
                plans=reconcile_plans(plans[key]),
                assessments=reconcile_assessments(assessments[key]),
                observations=reconcile_observations(observations[key]),
            )
        )
    return records
