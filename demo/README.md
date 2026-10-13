# Synthetic multi-patient demonstration

All records in this directory are synthetic. They are separate from the supplied
records and the five development answers.

```bash
uv run backbone demo --output .backbone/synthetic-demo
uv run backbone --db .backbone/synthetic-demo/review.sqlite3 status
uv run backbone replay .backbone/synthetic-demo/abstraction.json \
  .backbone/synthetic-demo/questions.json \
  --plans .backbone/synthetic-demo/plans.json --output .backbone/synthetic-replay
```

The demo imports 15 source files, validates authored extraction fixtures against
their verbatim quotes, runs reconciliation, publishes a snapshot, and executes
authored saved plans. It makes no API calls. This demonstrates the calculation
and evidence pipeline; it does not measure model extraction or planning accuracy.

| Patient | Expected result |
| --- | --- |
| Casey Demo | 120 and 130 minutes in two complete weeks, below the 150-minute goal; confirmed cohort member. |
| Morgan Demo | Each week has conflicting final notes for the same event: 130 or 170 minutes; possible cohort member. |
| Alex Demo | No consecutive two-week shortfall; excluded cohort member. Documented plan changes on Monday, March 15, 2027. |

Alex's old goal is one treatment day and 100 minutes per week. The new goal is
two days and 150 minutes. The comparison covers two full weeks on each side:

| Period | Sessions | Days | Minutes | Weekly decisions |
| --- | --- | --- | --- | --- |
| March 1-14, 2027 | 2 | 2 | 210 | met, met |
| March 15-28, 2027 | 3 | 3 | 280 | not_met, met |

The output contains a separate SQLite database, copied source files,
`abstraction.json`, `answers.json`, `answers.md`, `plans.json`, `questions.json`,
`extractions.jsonl`, `execution.jsonl`, and `demo-report.json`. Answers contain
source document IDs, verbatim passages, and line locations.

Run the current model planner against only this synthetic database:

```bash
uv run backbone --db .backbone/synthetic-demo/review.sqlite3 answer-file \
  .backbone/synthetic-demo/questions.json --output .backbone/synthetic-live
```

This last command requires `OPENAI_API_KEY` and makes planning API calls. It does
not use the saved demo plans.

[Recorded outputs](artifacts) include a separate live benchmark with three
repeats of each question. [Planner validation](artifacts/planner-validation.json)
checks all nine runs against the expected scopes, cohort membership, plan goals,
and exact source locations.

```bash
uv run backbone --db .backbone/synthetic-demo/review.sqlite3 benchmark-live \
  demo/questions.json --model gpt-4.1-mini --repeats 3 \
  --input-rate-per-million 0.4 --output-rate-per-million 1.6 \
  --output .backbone/synthetic-live-benchmark.json
uv run python -m scripts.validate_demo .backbone/synthetic-live-benchmark.json
```

Regenerate the authored fixtures after editing the demo specification:

```bash
uv run python demo/create_fixtures.py
```
