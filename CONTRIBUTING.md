# Contributing

Thanks for helping improve Project Risk Agent.

## What we want contributors to improve

The project has four especially useful contribution areas:

1. **Connectors** — normalize information from project, communication, email, or meeting systems.
2. **Reasoning** — improve risk, issue, dependency, and decision detection.
3. **Evaluations** — add realistic project scenarios and measurable expected behavior.
4. **Developer experience** — documentation, examples, tests, tooling, and usability.

## Connector philosophy

A connector should do one job well: authenticate using the provider's supported mechanism, retrieve project information, and normalize it into `ProjectSignal` objects.

Do not put risk-analysis logic inside a connector.

## Reasoning changes

Reasoning changes should preserve evidence. A finding should make it possible to answer:

- What was detected?
- What source supports it?
- What is inference versus direct evidence?
- How confident is the system?
- What decision or action may be required?

When possible, add or update an evaluation case for behavior changes.

## Privacy

Never commit real customer, employer, employee, project, email, chat, meeting, or credential data. Use synthetic examples in tests and documentation.

## Pull requests

Keep changes focused. Explain the behavior that changed and include tests or evaluation cases when appropriate.
