# Project Risk Agent

An open-source AI agent that turns unstructured project information into evidence-backed risks, issues, dependencies, and management decisions.

## What it does

Project Risk Agent is designed to look across the information that project teams already produce and identify what deserves management attention.

It is intentionally **source-agnostic**. Signals can come from project-management systems, email, chat, meeting transcripts, documents, or other systems.

The agent should:

- identify emerging risks, including risks that are implied rather than explicitly stated
- distinguish risks, issues, dependencies, and decisions
- cite the evidence behind each finding
- preserve source provenance
- assess likelihood, impact, urgency, and confidence
- identify when a management decision is required
- suggest actions without making the decision for the project team

## Design principle

> Don't just summarize what happened. Identify what may require management attention, show the evidence, and make the reasoning inspectable.

## Architecture

```text
Email / Chat / Meetings / PM Tools / Documents
                    |
                    v
             Source Connectors
                    |
                    v
             Project Signals
                    |
                    v
            Risk Intelligence
                 Agent
                    |
        +-----------+-----------+
        |           |           |
       Risks      Issues   Dependencies
                    |
                    v
             Decisions Needed
                    |
                    v
            Evidence-backed
            Management Brief
```

Connectors normalize source-specific data into a common `ProjectSignal` model. The risk engine does not need to know whether a signal originated in Jira, Monday, Smartsheet, Slack, Teams, Gmail, Outlook, or a meeting transcript.

## Initial scope

The first release focuses on a clean, extensible foundation:

1. common signal and finding schemas
2. file/text ingestion for local experimentation
3. evidence and provenance handling
4. risk/issue/dependency/decision classification
5. evaluation cases for project-risk reasoning
6. connector interfaces that can be extended independently

Planned connectors include Jira, Monday.com, Smartsheet, Slack, Microsoft Teams, Gmail, Outlook, and meeting-transcript sources.

Integrations should use official APIs and least-privilege authentication. No connector should require users to surrender credentials to the project itself.

## Example finding

```json
{
  "type": "risk",
  "category": "schedule",
  "title": "Integration testing may slip the launch date",
  "description": "The latest updates indicate the dependency is not yet available and testing has already moved once.",
  "likelihood": "high",
  "impact": "high",
  "confidence": 0.86,
  "evidence": [
    {"signal_id": "signal-104", "quote": "API delivery moved to Friday"},
    {"signal_id": "signal-117", "quote": "Testing cannot start until API is available"}
  ],
  "decision_required": true,
  "recommended_actions": [
    "Confirm the dependency owner and committed delivery date",
    "Evaluate a parallel test path or contingency"
  ]
}
```

## Safety and privacy

Project data can contain sensitive business information. The project therefore follows these principles:

- no telemetry by default
- secrets supplied through environment/configuration, never source code
- least-privilege connector scopes
- provenance for model-derived findings
- explicit distinction between evidence and inference
- configurable retention and redaction
- no autonomous business decisions

See `SECURITY.md` for the security model and threat considerations.

## Contributing

This project is deliberately designed for community improvement. A contributor should be able to add a connector or improve the risk reasoning without understanding the entire codebase.

See `CONTRIBUTING.md` and `docs/connectors.md`.

Evaluations are treated as a first-class part of development. New reasoning behavior should ideally include an evaluation case demonstrating what improved or regressed.

## Project status

Early development. APIs and schemas may change.

## License

Apache-2.0
