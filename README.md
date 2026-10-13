# Backbone Clinical Review

A Python CLI that extracts source-linked claims, reconciles encounters, and
calculates therapy counts, minutes, weekly goals, cohorts, plan comparisons, and
symptom timelines. SQLite retains immutable sources, extraction caches, and
published patient revisions. One structured LLM call plans each new question;
code calculates answers from saved evidence. Saved plans execute without model calls.

## Run

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```sh
uv sync --frozen
cp .env.example .env
```

Set `OPENAI_API_KEY` in `.env`, then:

```sh
uv run backbone process documents --model gpt-4.1 --workers 4
uv run backbone answer-file questions.json --output artifacts
uv run backbone ask "How many therapy minutes did Rowan receive on January 21, 2026?" \
  --save-plan .backbone/query-plan.json
uv run backbone ask "Which patients had two consecutive weeks below their treatment requirements?"
uv run backbone export questions.json --output artifacts
uv run backbone benchmark artifacts/benchmark_questions.json \
  --plans artifacts/benchmark_plans.json --repeats 10
```

Process a new file or directory with the same `process` command. Unchanged files
reuse the extraction cache; updates rebuild affected patients. An extraction
failure preserves the published revision and reports incomplete source coverage.
Retry the same input to reuse successful extractions.

Use `ask --snapshot N` to select a published version. `rebuild` recomputes the
abstraction from saved claims without API calls. `--db PATH` precedes the
subcommand and selects a separate database.

Browse updates for a stored patient ID, then select a revision or publication time:

```sh
uv run backbone history "harbor grove behavioral health::HG-M042"
uv run backbone patient "harbor grove behavioral health::HG-M042" --snapshot 2
uv run backbone patient "harbor grove behavioral health::HG-M042" \
  --as-of "2026-10-13T17:26:00-04:00"
uv run backbone ask "How many therapy sessions did Rowan attend?" \
  --as-of "2026-10-13T17:26:00-04:00"
```

History lists patient updates and removals with UTC publication timestamps.
`patient` returns the record and both its last update and the selected global
snapshot. An unchanged patient can have an earlier update than the snapshot.
`--as-of` selects the latest published revision at or before the timestamp;
it is independent of treatment dates in the question. Include Z or a UTC offset.
`--snapshot` and `--as-of` are mutually exclusive and also work for batch queries.
Before a patient's first publication, its state is `not_recorded`; a removal
returns `removed` rather than its previous record. These metadata commands do
not call a model. `Store.patient_history()` and `Store.patient_at()` expose the
same lookup in Python.

To reproduce the submitted answers without an API key or database:

```sh
uv run backbone replay artifacts/abstraction.json questions.json \
  --plans artifacts/plans.json --output .backbone/replay
```

`OPENAI_QUERY_MODEL` selects the query model, falling back to `OPENAI_MODEL`.
The planner receives patient IDs, names, organizations, documented date anchors,
and optional previous-plan context; it does not receive clinical passages.
It supports multiple patients/tasks, whole months, relative periods, and a
requested positive count of consecutive below-goal weeks. Code binds patient
references, resolves date arithmetic, validates supported tasks, and executes them.
Ambiguous or unsupported requests return an actionable error.

Use `ask --plan PATH` for one saved plan or `--context PATH` for a previous plan.
Batch commands accept `--plans PATH`; export writes `plans.json`. A saved plan
must match the exact question and snapshot. Replay requires saved plans and
makes no API calls. The submitted plans were migrated from the initial rule-based
run; they are not represented as fresh LLM outputs.

No vector RAG is implemented. Numerical questions require complete scoped event
sets. Symptom answers use saved assessments and attributed observations. Semantic
retrieval can support source enrichment when a new question needs missing fields.
A model-generated plan still needs review: schema validation cannot establish
that the question was interpreted correctly.

## Evidence and uncertainty

Content hashes deduplicate identical files. Document IDs and exact quotation
line ranges identify sources. Encounter/appointment IDs link complementary
records; unresolved identity stays explicit. Scoped corrections affect only
their named fields, and later copies do not undo them. New extractions require
separate source quotes for plan thresholds/effective dates and stated patient
minutes. Numeric checks use the relevant field quote. Legacy caches remain
readable; changed extraction settings use a new cache key.

Code intersects patient attendance with group activity, removes nontherapeutic
breaks and connection gaps, and applies effective participation rules. Conflicting
final records retain discrete, source-linked alternatives. Feasible scenarios
preserve shared choices; exceeding the scenario budget reports incomplete
analysis. Partial weeks and unspecified plan transitions remain qualified.

The supplied records yield 12 eligible sessions on 11 days and 585 or 595
minutes. The last week's plan status remains indeterminate because the January
26 contact has unresolved 40/50-minute alternatives. Production code contains
no patient-specific rules or answers.

## Submission

| File | Contents |
| --- | --- |
| [answers.md](artifacts/answers.md) / [answers.json](artifacts/answers.json) | Five development answers, calculations, exclusions, uncertainty, and source passages. |
| [plans.json](artifacts/plans.json) / [benchmark_plans.json](artifacts/benchmark_plans.json) | Saved query tasks for offline execution. |
| [abstraction.json](artifacts/abstraction.json) | Published patient records and source coverage. |
| [extractions.jsonl](artifacts/extractions.jsonl) | Validated model claims before reconciliation. |
| [execution.jsonl](artifacts/execution.jsonl) | Processing and query execution logs. |
| [query_planning_checks.json](artifacts/query_planning_checks.json) | Synthetic live-API intent and field-grounding checks, including the observed failure and retry. |
| [benchmark.json](artifacts/benchmark.json) / [performance.json](artifacts/performance.json) | Measured timings, sizes, token usage, and labeled cost estimates. |

## Measurements and model

The final 31-record extraction used `gpt-4.1` (returned snapshot
`gpt-4.1-2025-04-14`), Responses structured outputs, temperature 0,
12,000 maximum output tokens, and four workers. Each failed local validation
gets one retry with its specific error. Exact quotation locations are attached
by code, outside the model schema. Query planning uses Responses structured
outputs with 5,000 maximum output tokens; each saved plan records the returned
model, tokens, planning time, and logical model calls. Query sampling uses the
provider default. Costs are null when no rate was configured. The implementation
follows [OpenAI Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs).

Initial ingestion and extraction took 28.638 seconds and used 117,058 input and
22,716 output tokens. Cached reconciliation/publication took 0.136 seconds.
These are separate measured stages. The final run's standard uncached token
estimate is $0.416 at [$2 input / $8 output per million tokens](https://developers.openai.com/api/docs/models/gpt-4.1).
Actual billing and prompt-cache discounts were not captured; development probes
are additional. Saved-plan execution latency and current abstraction size are in the benchmark.
Initial extraction figures above describe the earlier extraction run. Query
planning time, tokens, and model calls are reported separately from execution.

A seven-record comparison found that `gpt-4.1-mini` repeatedly generated a
non-verbatim quotation and misclassified group timing. Clearer field descriptions
and explicit quantity validation fixed several errors; `gpt-4.1` then passed
all seven cases. The final 31-record outputs also pass independent expected-ledger
and duplicate-invariance checks.

Exact quotation validation does not establish semantic correctness. The final
model still labeled an administrative desk export as final and a routine
continuation statement as an added-contact reason. Neither changes the supplied
therapy totals. Next, label claim status, timing scope, and observation attribution
on additional records and compare error rates before changing the schema or model.

OpenAI Codex and collaborating coding agents assisted implementation and review.
No coding-assistant sampling settings were configured in the repository.

Ten synthetic live query-planning checks initially passed nine cases. Average
session duration incorrectly triggered a date clarification; capability-priority
instructions made the targeted retry return unsupported. Two synthetic live
extraction checks passed old/new plan goals and patient-versus-therapist duration.
The check artifact records returned models and token usage. These checks are not
an accuracy estimate on a broader question distribution.

## Scale

The first expected cold-processing bottleneck at one million documents is model
token volume and rate limits in `workflow.extract_documents`. Use bounded queue
workers, persistent jobs, batch requests, and incremental source discovery.
Current ingestion and futures are held in memory; they need streaming batches.

Query planning currently sends the patient catalog to the model; at larger
patient counts, retrieve entity candidates and resolve cohort scopes in the
database before planning. Queries currently load patient JSON and cached source contexts through
`Store.snapshot`; collection-wide queries run scenarios for every selected
patient in memory. Normalize events and
patient-week aggregates, index date/patient filters, and invalidate affected
weeks on publication. SQLite has one writer; move revision publication to a
transactional shared store when concurrent writers are needed. The 31-document,
one-patient benchmark does not measure 500K-document or million-document capacity.
See [architecture](docs/SYSTEM_ARCHITECTURE.md) for the expansion path.

## Verify

```sh
uv run pytest
uv run mypy src tests
uv run ruff check src tests
```

Tests include exact source grounding, the five reference answers, scoped
corrections, duplicates, conflicting times/dates, unknown attendance, coupled
scenarios, cohort membership, plan changes, retries, revisions, and CLI restart
and replay behavior. Planner tests cover compound tasks, relative dates, missing
context, disputed anchors, unsupported requests, SDK failures, and saved-plan
validation. All authored project content is English.
