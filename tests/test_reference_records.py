from datetime import date
from pathlib import Path

from pydantic import BaseModel, TypeAdapter

from backbone.calculation import calculate
from backbone.extraction import evidence_claims
from backbone.ingestion import read_document
from backbone.models import ClinicalSnapshot, ExtractionResult
from backbone.query import answer_question
from backbone.reconciliation import reconcile

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_EXTRACTIONS = PROJECT_ROOT / "artifacts" / "extractions.jsonl"
REVIEW_START = date(2026, 1, 5)
REVIEW_END = date(2026, 1, 30)


class DevelopmentQuestion(BaseModel):
    id: str
    question: str


def reference_results() -> list[ExtractionResult]:
    results = [
        ExtractionResult.model_validate_json(line)
        for line in REFERENCE_EXTRACTIONS.read_text(encoding="utf-8").splitlines()
    ]
    assert len(results) == 31, "The replay fixture must contain all 31 supplied documents."
    return results


def reference_snapshot(results: list[ExtractionResult]) -> ClinicalSnapshot:
    return ClinicalSnapshot(
        snapshot_id=1,
        patients=reconcile([result.evidence for result in results]),
    )


def development_questions() -> list[DevelopmentQuestion]:
    adapter: TypeAdapter[list[DevelopmentQuestion]] = TypeAdapter(list[DevelopmentQuestion])
    return adapter.validate_json((PROJECT_ROOT / "questions.json").read_text(encoding="utf-8"))


def test_reference_evidence_has_verbatim_source_locations() -> None:
    for result in reference_results():
        assert result.evidence.patients
        for claim in evidence_claims(result.evidence):
            assert claim.sources, "Every replayed claim needs source-backed evidence."
            for source in claim.sources:
                document = read_document(PROJECT_ROOT / "documents" / source.filename)
                assert source.content_hash == document.content_hash
                assert source.document_id == document.document_id
                lines = document.text.splitlines(keepends=True)
                assert 1 <= source.start_line <= source.end_line <= len(lines)
                assert source.quote in "".join(lines[source.start_line - 1 : source.end_line])


def test_reference_pipeline_answers_all_development_questions() -> None:
    snapshot = reference_snapshot(reference_results())
    assert len(snapshot.patients) == 1
    questions = development_questions()
    assert len(questions) == 5
    answers = {question.id: answer_question(question.question, snapshot) for question in questions}
    for answer in answers.values():
        assert answer.snapshot_id == snapshot.snapshot_id
        assert answer.coverage_status == "available_records"
        assert answer.sources
        assert answer.text

    counts = answers["DEV-01"].metrics[0]
    assert counts.session_count.exact == 12
    assert counts.distinct_days.exact == 11
    assert {
        service: counts.session_counts[service].exact
        for service in ["individual", "group", "family"]
    } == {"individual": 5, "group": 5, "family": 2}

    durations = answers["DEV-02"].metrics[0]
    assert durations.minutes.values == [585, 595]
    assert durations.minutes.exact is None
    assert durations.minutes.lower_bound == 585
    assert durations.minutes.upper_bound == 595
    assert [week.minutes.values for week in durations.weeks] == [[140], [120], [180], [145, 155]]

    weekly = answers["DEV-03"].metrics[0].weeks
    assert [week.distinct_days.exact for week in weekly] == [3, 2, 3, 3]
    assert [week.decision for week in weekly] == ["not_met", "not_met", "met", "indeterminate"]
    for week in weekly:
        assert week.goal is not None
        assert week.goal.minimum_days == 3
        assert week.goal.minimum_minutes == 150

    reconstructed = {metrics.start: metrics for metrics in answers["DEV-04"].metrics}
    assert set(reconstructed) == {date(2026, 1, 19), date(2026, 1, 21)}
    assert reconstructed[date(2026, 1, 19)].session_count.exact == 2
    assert reconstructed[date(2026, 1, 19)].minutes.exact == 90
    assert reconstructed[date(2026, 1, 21)].session_count.exact == 1
    assert reconstructed[date(2026, 1, 21)].minutes.exact == 45

    symptoms = answers["DEV-05"]
    assert [assessment.completed_date for assessment in symptoms.assessments] == [
        date(2026, 1, 5),
        date(2026, 1, 16),
        date(2026, 1, 30),
    ]
    assert [assessment.score for assessment in symptoms.assessments] == [18, 14, 10]
    assert any(
        observation.observed_date == date(2026, 1, 19) and observation.kind == "reason_for_contact"
        for observation in symptoms.observations
    )


def test_reference_duplicate_inputs_do_not_change_clinical_results() -> None:
    evidences = [result.evidence for result in reference_results()]
    original = reconcile(evidences)
    repeated = reconcile(evidences + evidences)
    assert len(original) == len(repeated) == 1
    assert (
        calculate(original[0], REVIEW_START, REVIEW_END).model_dump()
        == calculate(repeated[0], REVIEW_START, REVIEW_END).model_dump()
    )
    assert [assessment.model_dump() for assessment in original[0].assessments] == [
        assessment.model_dump() for assessment in repeated[0].assessments
    ]


def test_exported_abstraction_preserves_records_without_delivered_contacts() -> None:
    snapshot = ClinicalSnapshot.model_validate_json(
        (PROJECT_ROOT / "artifacts" / "abstraction.json").read_bytes()
    )
    records = {record.source.document_id: record for record in snapshot.non_contact_records}
    assert {"BH-D001", "BH-D013", "BH-D014"}.issubset(records)
    answer = answer_question(development_questions()[0].question, snapshot)
    assert all(identifier in answer.text for identifier in ("BH-D001", "BH-D013", "BH-D014"))
    assert answer.metrics[0].session_count.exact == 12
    for record in records.values():
        source = record.source
        text = (PROJECT_ROOT / "documents" / source.filename).read_text(encoding="utf-8")
        assert source.quote in text
        assert source.quote in "\n".join(text.splitlines()[source.start_line - 1 : source.end_line])
