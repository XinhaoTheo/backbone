# Backbone Clinical Review Prototype

Build a clinical review prototype that turns distributed clinical and
administrative records into a persistent, auditable abstraction of delivered
care. Numerical answers will be calculated in code, with source support,
explicit reconciliation decisions, and unresolved evidence retained.

The repository currently contains the supplied problem statement, 31 fictional
clinical records, five development questions, and the proposed requirements,
architecture, and implementation sequence. The runnable prototype is planned.

## Repository contents

| Path | Purpose |
| --- | --- |
| [Problem Statement.docx](Problem%20Statement.docx) | Supplied hiring challenge and submission requirements. |
| [documents](documents/) | Supplied fictional clinical and administrative records. |
| [questions.json](questions.json) | Five development questions about the supplied patient episode. |
| [AGENTS.md](AGENTS.md) | English-language convention for all authored project artifacts. |
| [Design requirements](docs/DESIGN_REQUIREMENTS.md) | Question families, evidence handling, uncertainty, and required behavior. |
| [System architecture](docs/SYSTEM_ARCHITECTURE.md) | Six logical modules, their interactions, persistence, and scaling path. |
| [Implementation plan](docs/IMPLEMENTATION_PLAN.md) | Seven planned implementation commits and acceptance criteria. |

## Intended behavior

- Reconcile multiple records of the same clinical event without duplicate counts.
- Combine attendance, clinical content, corrections, and contact intervals.
- Preserve conflicts and distinguish established conclusions from uncertainty.
- Calculate therapy sessions, distinct days, delivered minutes, and weekly goals.
- Support patient questions, collection-wide conditions, plan comparisons, and
  documented symptom trajectories with precise source references.
- Reuse saved work after restarting and update affected results when new records
  arrive.
- Export inspectable answers and abstraction data, execution logs, and measured
  performance results.

## Proposed implementation

Start with a modular Python application, SQLite, and a command-line interface.
Separate ingestion, evidence extraction, reconciliation, deterministic
calculation, question answering, and workflow measurement. Keep source claims
and reconciliation decisions persistent so new questions reuse the abstraction.

The architecture retains interfaces for worker-based extraction and alternative
storage when measured processing or concurrency needs justify expansion.

## Development conventions

All authored project content is in English. Preserve the supplied records as
evidence. Do not hard-code patient facts or question answers into the
implementation. Add meaningful validation with each implementation increment.

Design preparation used OpenAI Codex assistance. The implementation README will
record model names and settings, coding assistance, measured runtime and available
model cost, a tested design decision, an observed limitation, and the expected
first bottleneck at one million documents.
