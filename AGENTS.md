# Project Language

All authored project content must be in English. This includes documentation,
source code identifiers, comments, docstrings, configuration descriptions, tests,
CLI messages, logs, generated reports, and answers to evaluation questions.

Preserve supplied source records as evidence. Do not translate or rewrite them
to enforce this convention.

Conversation with the user may use the user's preferred language.

# Code and Writing

- Helper function names must not start with an underscore.
- Use explicit types. Do not use `Any` or untyped containers.
- Comments, when needed, explain why a decision exists.
- Validate evidence and data contracts where correctness requires it. Avoid
  speculative fallback branches or checks that do not serve actual behavior.
- Keep README and documentation concise. State behavior, commands, results,
  and material limitations.
