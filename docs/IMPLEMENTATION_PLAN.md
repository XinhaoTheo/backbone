# Clinical Review Prototype Implementation Plan

All seven stages are implemented. See the commit history and README for execution
and verification instructions.

Implement a minimal, complete prototype in seven functional commits. Each commit
should add an executable capability and relevant verification. Commit 5 completes
the question-to-answer path; commit 6 completes update and reuse behavior; commit
7 prepares the submission and measured results.

The repository's initial documentation and data import precedes these seven
implementation commits. All authored content and commit messages must be in
English.

| Commit | Scope | Acceptance criteria |
| --- | --- | --- |
| 1 `chore: bootstrap project and persist documents` | Python project, CLI, configuration, SQLite schema, immutable sources, content hashes, and source locators. | Import supplied files; preserve data after restart; repeated input does not duplicate document content records. |
| 2 `feat: extract source-linked evidence with caching` | Model extraction interface, structured claims, source validation, extraction versions, and caching. | Extract identities, encounters, attendance, intervals, plans, assessments, and document relationships; locate supporting passages; reuse unchanged extraction. |
| 3 `feat: reconcile clinical records and publish revisions` | Patient and event linking, event deduplication, scoped corrections, unresolved alternatives, plans and assessments, and coherent revision publication. | Old copies do not revoke corrections; multiple notes do not create extra sessions; conflicting final durations remain unresolved and reviewable. |
| 4 `feat: calculate therapy metrics and plan compliance` | Session and day counts, eligible contact minutes, weekly aggregates, effective plan rules, and uncertainty propagation. | Exclude breaks and disconnects correctly; show contributions and exclusions; evaluate goals as met, not met, or indeterminate. |
| 5 `feat: answer patient and cohort questions with evidence` | Validated query plans, development answers, symptom timelines, consecutive under-target weeks, plan comparisons, and English answer rendering. | Answer all five development questions; support changed patient, date, and query parameters; reuse the saved abstraction for related questions. |
| 6 `feat: support incremental updates and reproducible queries` | New-document processing, affected-patient updates, cache invalidation, query snapshots, retries, and visible failure states. | Historical corrections update affected results; queries work after restart; results do not mix revisions; duplicate retries preserve clinical results. |
| 7 `chore: add benchmarks and submission artifacts` | End-to-end verification, performance measurements, abstraction and answer export, execution logs, README, and submission materials. | Follow setup instructions in a clean environment; produce complete artifacts; distinguish measurements from scaling estimates. |

## Complete prototype acceptance criteria

- Answer every supplied development question with specific sources and
  reproducible calculations.
- Support the stated collection-wide and plan-change analysis operations.
- Handle duplicate inputs, restart, related new questions, and additional records.
- Preserve unresolved conflicts and missing information instead of silently
  selecting values or assigning zero.
- Return a consistent published snapshot and retain the evidence and decisions
  needed to audit the answer.
- Provide measured benchmarks, execution logs, abstraction export, and runnable
  setup instructions.

## Verification throughout implementation

Add checks alongside each capability. Use the supplied evidence cases to verify
corrections, retransmissions, event identity, duration conflicts, reconnections,
and copied symptom assessments. Use additional small text fixtures for multiple
patients, plan changes, and related uncertainty across weeks. Expected test
results may be specified in tests; production code must derive patient facts and
answers from the input records.

The final commit verifies the complete workflow and packages its outputs.

## Initial implementation boundary

Use a modular single-process Python application, SQLite, and a CLI. Preserve
clear extraction, persistence, and workflow interfaces for later expansion.
Prioritize the complete evidence-to-answer workflow within the hiring challenge's
two-to-five-hour scope.
