from __future__ import annotations

from datetime import date
from importlib.resources import files
from typing import Literal

import httpx2
import pytest
from openai import OpenAI
from pydantic import BaseModel

from backbone.models import (
    ClinicalSnapshot,
    Observation,
    PatientRecord,
    QueryPlan,
    QueryTask,
    SourceRef,
)
from backbone.planning import (
    IntentResult,
    OpenAIQueryPlanner,
    PatientScope,
    PlanningContext,
    QueryIntent,
    QueryPlanningError,
    TaskIntent,
    TimeIntent,
    plan_question,
    planning_context,
)


class FormatRequest(BaseModel):
    type: str
    name: str
    strict: bool


class TextRequest(BaseModel):
    format: FormatRequest


class PlanningRequest(BaseModel):
    model: str
    instructions: str
    input: str
    max_output_tokens: int
    store: bool
    text: TextRequest


@pytest.fixture
def snapshot() -> ClinicalSnapshot:
    confidential: str = "Confidential clinical passage not needed for query planning."
    source: SourceRef = SourceRef(
        content_hash="private-source-hash",
        document_id="PRIVATE-D001",
        filename="private-visit.txt",
        start_line=8,
        end_line=8,
        quote=confidential,
    )
    patient: PatientRecord = PatientRecord(
        patient_id="Test clinic::P1",
        name="Casey Morgan",
        organization="Test clinic",
        episode_start=date(2027, 2, 1),
        episode_end=date(2027, 2, 28),
        encounters=[],
        plans=[],
        assessments=[],
        observations=[
            Observation(
                patient_id="P1",
                observed_date=date(2027, 2, 1),
                kind="patient_report",
                text=confidential,
                quotes=[confidential],
                sources=[source],
            )
        ],
    )
    return ClinicalSnapshot(snapshot_id=7, patients=[patient])


@pytest.fixture
def intent() -> QueryIntent:
    return QueryIntent(
        status="ready",
        message="",
        tasks=[
            TaskIntent(
                operation="durations",
                patients=PatientScope(references=["Test clinic::P1"]),
                time=TimeIntent(
                    kind="relative", anchor="episode_start", length=2, length_unit="weeks"
                ),
                metrics=["minutes"],
            )
        ],
    )


def mock_client(
    intent: QueryIntent,
    *,
    output: Literal["text", "refusal", "empty"] = "text",
    status: Literal["completed", "incomplete"] = "completed",
    include_usage: bool = True,
    api_status: int = 200,
    intent_json: str | None = None,
) -> tuple[OpenAI, list[PlanningRequest]]:
    requests: list[PlanningRequest] = []

    def respond(request: httpx2.Request) -> httpx2.Response:
        requests.append(PlanningRequest.model_validate_json(request.content))
        if api_status != 200:
            return httpx2.Response(
                api_status,
                json={
                    "error": {
                        "message": "Planning service unavailable.",
                        "type": "server_error",
                        "code": "server_error",
                    }
                },
            )
        content: dict[str, object] = (
            {"type": "refusal", "refusal": "Unable to plan this request."}
            if output == "refusal"
            else {
                "type": "output_text",
                "text": intent.model_dump_json() if intent_json is None else intent_json,
                "annotations": [],
            }
        )
        payload: dict[str, object] = {
            "id": "resp_planning_test",
            "object": "response",
            "created_at": 0,
            "model": "planner-model-snapshot",
            "status": status,
            "output": []
            if output == "empty"
            else [
                {
                    "id": "msg_planning_test",
                    "type": "message",
                    "role": "assistant",
                    "status": "completed",
                    "content": [content],
                }
            ],
        }
        if status == "incomplete":
            payload["incomplete_details"] = {"reason": "max_output_tokens"}
        if include_usage:
            payload["usage"] = {
                "input_tokens": 120,
                "output_tokens": 45,
                "total_tokens": 165,
                "input_tokens_details": {"cached_tokens": 0, "cache_write_tokens": 0},
                "output_tokens_details": {"reasoning_tokens": 0},
            }
        return httpx2.Response(200, json=payload)

    client: OpenAI = OpenAI(
        api_key="test-key",
        http_client=httpx2.Client(transport=httpx2.MockTransport(respond)),
        max_retries=0,
    )
    return client, requests


def test_sdk_parses_query_intent_and_sends_only_planning_catalog(
    snapshot: ClinicalSnapshot, intent: QueryIntent
) -> None:
    question: str = "Give me Casey's contact time during the first two treatment weeks."
    context: PlanningContext = planning_context(snapshot)
    client: OpenAI
    requests: list[PlanningRequest]
    client, requests = mock_client(intent)
    with client:
        result: IntentResult = OpenAIQueryPlanner(model="planner-model", client=client).interpret(
            question, context
        )
    assert len(requests) == 1
    request: PlanningRequest = requests[0]
    assert request.model == "planner-model"
    assert request.instructions == files("backbone").joinpath("query_prompt.txt").read_text("utf-8")
    assert request.input == (
        f"Snapshot catalog:\n{context.model_dump_json()}\n\nQuestion:\n{question}"
    )
    assert "Casey Morgan" in request.input
    assert "Test clinic::P1" in request.input
    assert "2027-02-28" in request.input
    assert "Confidential clinical passage" not in request.input
    assert "PRIVATE-D001" not in request.input
    assert "private-source-hash" not in request.input
    assert request.text.format.type == "json_schema"
    assert request.text.format.name == "QueryIntent"
    assert request.text.format.strict
    assert request.max_output_tokens == 5000
    assert request.store is False
    assert result.intent == intent
    assert result.model == "planner-model-snapshot"
    assert result.usage.input_tokens == 120
    assert result.usage.output_tokens == 45
    assert result.model_calls == 1
    assert result.elapsed_seconds >= 0


def test_sdk_plan_resolves_relative_dates_and_compound_tasks_in_one_call(
    snapshot: ClinicalSnapshot, intent: QueryIntent
) -> None:
    intent.tasks.append(
        TaskIntent(
            operation="symptoms",
            patients=PatientScope(references=["Test clinic::P1"]),
            time=TimeIntent(kind="episode"),
        )
    )
    question: str = "Show the first two weeks' contact time and symptoms across treatment."
    client: OpenAI
    requests: list[PlanningRequest]
    client, requests = mock_client(intent)
    with client:
        plan: QueryPlan = plan_question(
            question, snapshot, planner=OpenAIQueryPlanner(client=client)
        )
    assert len(requests) == 1
    assert [task.operation for task in plan.tasks] == ["durations", "symptoms"]
    assert (plan.tasks[0].start, plan.tasks[0].end) == (date(2027, 2, 1), date(2027, 2, 14))
    assert (plan.tasks[1].start, plan.tasks[1].end) == (date(2027, 2, 1), date(2027, 2, 28))
    assert all(task.patient == "Test clinic::P1" for task in plan.tasks)
    assert plan.planner_model == "planner-model-snapshot"
    assert plan.planner_usage.input_tokens == 120
    assert plan.planner_model_calls == 1


def test_sdk_receives_explicit_previous_plan_context(
    snapshot: ClinicalSnapshot, intent: QueryIntent
) -> None:
    previous: QueryPlan = QueryPlan(
        question="Count Casey's sessions.",
        snapshot_id=7,
        tasks=[
            QueryTask(
                operation="counts",
                patient="Test clinic::P1",
                patient_ids=["Test clinic::P1"],
                start=date(2027, 2, 1),
                end=date(2027, 2, 14),
            )
        ],
    )
    intent.tasks[0].patients = PatientScope(kind="context")
    intent.tasks[0].time = TimeIntent(kind="context")
    client: OpenAI
    requests: list[PlanningRequest]
    client, requests = mock_client(intent)
    with client:
        plan: QueryPlan = plan_question(
            "And their minutes in the same period?",
            snapshot,
            planner=OpenAIQueryPlanner(client=client),
            context=previous,
        )
    assert previous.model_dump_json() in requests[0].input
    assert plan.tasks[0].patient == previous.tasks[0].patient
    assert plan.tasks[0].end == previous.tasks[0].end


@pytest.mark.parametrize("output", ["refusal", "empty"])
def test_unparsed_planner_output_fails_without_keyword_fallback(
    snapshot: ClinicalSnapshot,
    intent: QueryIntent,
    output: Literal["refusal", "empty"],
) -> None:
    client: OpenAI
    requests: list[PlanningRequest]
    client, requests = mock_client(intent, output=output)
    with client, pytest.raises(QueryPlanningError, match="completed structured plan") as failure:
        plan_question(
            "How many sessions did Casey attend?",
            snapshot,
            planner=OpenAIQueryPlanner(client=client),
        )
    assert len(requests) == 1
    assert failure.value.model_calls == 1
    assert failure.value.usage is not None
    assert failure.value.usage.input_tokens == 120
    assert failure.value.usage.output_tokens == 45
    assert failure.value.elapsed_seconds >= 0


def test_incomplete_planner_output_fails_without_keyword_fallback(
    snapshot: ClinicalSnapshot, intent: QueryIntent
) -> None:
    client: OpenAI
    requests: list[PlanningRequest]
    client, requests = mock_client(intent, status="incomplete")
    with client, pytest.raises(QueryPlanningError) as failure:
        plan_question(
            "How many sessions did Casey attend?",
            snapshot,
            planner=OpenAIQueryPlanner(client=client),
        )
    assert len(requests) == 1
    assert failure.value.model_calls == 1
    assert failure.value.usage is not None
    assert failure.value.usage.input_tokens == 120
    assert failure.value.usage.output_tokens == 45


def test_missing_planner_usage_is_reported_as_planning_failure(
    snapshot: ClinicalSnapshot, intent: QueryIntent
) -> None:
    client: OpenAI
    requests: list[PlanningRequest]
    client, requests = mock_client(intent, include_usage=False)
    with client, pytest.raises(QueryPlanningError, match="token usage") as failure:
        plan_question(
            "How many sessions did Casey attend?",
            snapshot,
            planner=OpenAIQueryPlanner(client=client),
        )
    assert len(requests) == 1
    assert failure.value.model_calls == 1
    assert failure.value.usage is None


@pytest.mark.parametrize("api_status", [401, 429, 500])
def test_api_failure_does_not_fall_back_to_keyword_planning(
    snapshot: ClinicalSnapshot, intent: QueryIntent, api_status: int
) -> None:
    client: OpenAI
    requests: list[PlanningRequest]
    client, requests = mock_client(intent, api_status=api_status)
    with client, pytest.raises(QueryPlanningError, match="API request failed") as failure:
        plan_question(
            "How many sessions did Casey attend?",
            snapshot,
            planner=OpenAIQueryPlanner(client=client),
        )
    assert len(requests) == 1
    assert failure.value.model_calls == 1
    assert failure.value.usage is None


@pytest.mark.parametrize("status", ["clarification_required", "unsupported"])
def test_model_declined_intent_is_not_replaced_by_keyword_operation(
    snapshot: ClinicalSnapshot,
    intent: QueryIntent,
    status: Literal["clarification_required", "unsupported"],
) -> None:
    intent.status = status
    intent.message = "Specify the exact metric requested."
    intent.tasks = []
    client: OpenAI
    requests: list[PlanningRequest]
    client, requests = mock_client(intent)
    with (
        client,
        pytest.raises(QueryPlanningError, match="Specify the exact metric requested") as failure,
    ):
        plan_question(
            "How many sessions did Casey attend?",
            snapshot,
            planner=OpenAIQueryPlanner(client=client),
        )
    assert len(requests) == 1
    assert failure.value.model_calls == 1
    assert failure.value.usage is not None
    assert failure.value.usage.input_tokens == 120


@pytest.mark.parametrize(
    "intent_json",
    [
        '{"status": "ready", "tasks": [',
        '{"status": "ready", "message": "", "tasks": [{"operation": "invented"}]}',
    ],
    ids=["malformed-json", "invalid-schema"],
)
def test_invalid_structured_output_is_a_planning_failure_without_keyword_fallback(
    snapshot: ClinicalSnapshot, intent: QueryIntent, intent_json: str
) -> None:
    client: OpenAI
    requests: list[PlanningRequest]
    client, requests = mock_client(intent, intent_json=intent_json)
    with client, pytest.raises(QueryPlanningError) as failure:
        plan_question(
            "How many sessions did Casey attend?",
            snapshot,
            planner=OpenAIQueryPlanner(client=client),
        )
    assert len(requests) == 1
    assert failure.value.model_calls == 1


def test_planning_cost_uses_configured_per_million_token_rates(
    snapshot: ClinicalSnapshot, intent: QueryIntent
) -> None:
    client, requests = mock_client(intent)
    with client:
        plan = plan_question(
            "Give me Casey's contact time during the first two treatment weeks.",
            snapshot,
            planner=OpenAIQueryPlanner(
                client=client, input_rate_per_million=0.4, output_rate_per_million=1.6
            ),
        )
    assert len(requests) == 1
    assert plan.planner_usage.input_tokens == 120
    assert plan.planner_usage.output_tokens == 45
    assert plan.planner_usage.cost_usd == pytest.approx(0.00012)


@pytest.mark.parametrize("input_rate,output_rate", [(None, None), (0.4, None), (None, 1.6)])
def test_planning_cost_is_unknown_without_both_token_rates(
    snapshot: ClinicalSnapshot,
    intent: QueryIntent,
    input_rate: float | None,
    output_rate: float | None,
) -> None:
    client, requests = mock_client(intent)
    with client:
        result = OpenAIQueryPlanner(
            client=client,
            input_rate_per_million=input_rate,
            output_rate_per_million=output_rate,
        ).interpret("How many therapy minutes did Casey receive?", planning_context(snapshot))
    assert len(requests) == 1
    assert result.usage.input_tokens == 120
    assert result.usage.output_tokens == 45
    assert result.usage.cost_usd is None


@pytest.mark.parametrize(
    "output,status",
    [("refusal", "completed"), ("empty", "completed"), ("text", "incomplete")],
)
def test_unsuccessful_planning_preserves_estimated_cost_when_usage_is_available(
    snapshot: ClinicalSnapshot,
    intent: QueryIntent,
    output: Literal["text", "refusal", "empty"],
    status: Literal["completed", "incomplete"],
) -> None:
    client, requests = mock_client(intent, output=output, status=status)
    with client, pytest.raises(QueryPlanningError) as failure:
        plan_question(
            "How many therapy minutes did Casey receive?",
            snapshot,
            planner=OpenAIQueryPlanner(
                client=client, input_rate_per_million=0.4, output_rate_per_million=1.6
            ),
        )
    assert len(requests) == 1
    assert failure.value.model_calls == 1
    assert failure.value.usage is not None
    assert failure.value.usage.input_tokens == 120
    assert failure.value.usage.output_tokens == 45
    assert failure.value.usage.cost_usd == pytest.approx(0.00012)


def test_declined_intent_preserves_estimated_cost(
    snapshot: ClinicalSnapshot, intent: QueryIntent
) -> None:
    intent.status = "clarification_required"
    intent.message = "Specify which patient's minutes to query."
    intent.tasks = []
    client, requests = mock_client(intent)
    with client, pytest.raises(QueryPlanningError, match="clarification_required") as failure:
        plan_question(
            "How many therapy minutes?",
            snapshot,
            planner=OpenAIQueryPlanner(
                client=client, input_rate_per_million=0.4, output_rate_per_million=1.6
            ),
        )
    assert len(requests) == 1
    assert failure.value.usage is not None
    assert failure.value.usage.cost_usd == pytest.approx(0.00012)


@pytest.mark.parametrize("input_rate,output_rate", [(-0.4, 1.6), (0.4, -1.6)])
def test_negative_planning_token_rates_are_rejected_before_api_calls(
    intent: QueryIntent, input_rate: float, output_rate: float
) -> None:
    client, requests = mock_client(intent)
    with client, pytest.raises(ValueError, match="Token rates cannot be negative"):
        OpenAIQueryPlanner(
            client=client,
            input_rate_per_million=input_rate,
            output_rate_per_million=output_rate,
        )
    assert requests == []
