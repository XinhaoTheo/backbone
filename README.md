# Backbone Clinical Review

A Python CLI that extracts source-linked claims, reconciles encounters, and
calculates therapy counts, minutes, weekly goals, cohorts, plan comparisons, and
symptom timelines. SQLite retains immutable sources, extraction caches, and
published patient revisions. Questions use saved evidence without model calls.

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
uv run backbone ask "How many therapy minutes did Rowan receive on January 21, 2026?"
uv run backbone ask "Which patients had two consecutive weeks below their treatment requirements?"
uv run backbone export questions.json --output artifacts
uv run backbone benchmark artifacts/benchmark_questions.json --repeats 10
```

Process a new file or directory with the same `process` command. Unchanged files
reuse the extraction cache; updates rebuild affected patients. An extraction
failure preserves the published revision and reports incomplete source coverage.
Retry the same input to reuse successful extractions.

Use `ask --snapshot N` to select a published version. `rebuild` recomputes the
abstraction from saved claims without API calls. `--db PATH` precedes the
subcommand and selects a separate database.

To reproduce the submitted answers without an API key or database:

```sh
uv run backbone replay artifacts/abstraction.json questions.json --output .backbone/replay
```

The offline planner accepts the supported question families, patient names or
IDs, ISO or English dates, and explicit before/after change dates. Unsupported
or ambiguous requests return an error. Cohort and plan-change behavior also has
synthetic multi-patient tests.

## Evidence and uncertainty

Content hashes deduplicate identical files. Document IDs and exact quotation
line ranges identify sources. Encounter/appointment IDs link complementary
records; unresolved identity stays explicit. Scoped corrections affect only
their named fields, and later copies do not undo them.

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
| [abstraction.json](artifacts/abstraction.json) | Published patient records and source coverage. |
| [extractions.jsonl](artifacts/extractions.jsonl) | Validated model claims before reconciliation. |
| [execution.jsonl](artifacts/execution.jsonl) | Processing and query execution logs. |
| [benchmark.json](artifacts/benchmark.json) / [performance.json](artifacts/performance.json) | Measured timings, sizes, token usage, and labeled cost estimates. |

## Measurements and model

The final 31-record extraction used `gpt-4.1` (returned snapshot
`gpt-4.1-2025-04-14`), Responses structured outputs, temperature 0,
12,000 maximum output tokens, and four workers. Each failed local validation
gets one retry with its specific error. Exact quotation locations are attached
by code, outside the model schema.

Initial ingestion and extraction took 28.638 seconds and used 117,058 input and
22,716 output tokens. Cached reconciliation/publication took 0.136 seconds.
These are separate measured stages. The final run's standard uncached token
estimate is $0.416 at [$2 input / $8 output per million tokens](https://developers.openai.com/api/docs/models/gpt-4.1).
Actual billing and prompt-cache discounts were not captured; development probes
are additional. Offline query latency and abstraction size are in the benchmark.

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

## Scale

The first expected cold-processing bottleneck at one million documents is model
token volume and rate limits in `workflow.extract_documents`. Use bounded queue
workers, persistent jobs, batch requests, and incremental source discovery.
Current ingestion and futures are held in memory; they need streaming batches.

Queries currently load patient JSON and cached source contexts through
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
and replay behavior. All authored project content is English.
