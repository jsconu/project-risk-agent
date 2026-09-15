# Architecture

Project Risk Agent separates **retrieval**, **normalization**, **reasoning**, **prioritization**, and **presentation** so provider integrations and model choices can evolve independently.

```text
                 External systems
       ┌───────────┬───────────┬───────────┐
       │ Jira      │ Slack     │ Files/... │
       └─────┬─────┴─────┬─────┴─────┬─────┘
             │            │           │
             └────────────┴───────────┘
                          │
                    ProjectSignal
                          │
                 ┌────────▼────────┐
                 │ Reasoning       │
                 │ deterministic or│
                 │ model-backed    │
                 └────────┬────────┘
                          │
                       Finding
                          │
                 ┌────────▼────────┐
                 │ Prioritization  │
                 │ + decisions    │
                 └────────┬────────┘
                          │
                  Management brief
```

## Core boundaries

### ProjectSignal

The normalized input contract. A signal keeps its source, timestamp, author, content, metadata, and provenance so findings can be traced back to source evidence.

### Reasoning

The reasoning layer operates on normalized signals. The deterministic implementation is deliberately conservative and evidence-first. The provider boundary allows a model-backed implementation without coupling the rest of the application to a specific model vendor.

### Evidence

Findings should never be detached from the signals that support them. Evidence utilities deduplicate and preserve source IDs. Model output is validated against the domain schema before it is accepted.

### Prioritization

Prioritization is an explicit, transparent calculation based on likelihood, impact, urgency, and confidence. It is a management-attention aid, not an autonomous business decision.

### Connectors

Connectors own provider-specific authentication, pagination, API details, and normalization. They should prefer read-only permissions because risk analysis does not require write access.

## Agentic evolution

The project is intentionally starting with a deterministic reasoning core. Future agentic behavior should add controlled loops around the same contracts rather than replace them with an opaque prompt chain:

1. retrieve new signals
2. compare with prior project state
3. identify changes and contradictions
4. gather supporting evidence
5. generate candidate findings
6. validate evidence and schema
7. prioritize management attention
8. surface decisions for a human
9. retain an auditable result

Autonomous consequential actions are out of scope for the public project.
