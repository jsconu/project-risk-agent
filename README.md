# Project Risk Agent

[![Tests](https://github.com/jsconu/project-risk-agent/actions/workflows/test.yml/badge.svg)](https://github.com/jsconu/project-risk-agent/actions/workflows/test.yml)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

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

## Quick start: no terminal needed

Project Risk Agent includes a friendly chat window, so you don't need to write code or use a terminal.

1. **Download the app** for your computer from the [latest release](https://github.com/jsconu/project-risk-agent/releases/latest) (available from version 0.3.0):
   - Windows: `ProjectRiskAgent-Windows.exe`
   - Mac (Apple silicon): `ProjectRiskAgent-macOS.zip`
2. **Open it.** The first time, your computer may warn that the app is from an unrecognized publisher, because it isn't code-signed yet:
   - Windows: click **More info**, then **Run anyway**.
   - Mac: unzip it, right-click (or Control-click) the app, choose **Open**, then **Open** again. If macOS still blocks it, go to System Settings, then Privacy & Security, and choose **Open Anyway**.
3. **A chat opens in your web browser.** Click **Try an example** to see how it works, then paste in your own project updates (status reports, emails, meeting notes) or drag in a file (`.txt`, `.md`, `.csv`, `.json`, `.eml`).

I'll list what may need attention, quote the exact words I based each item on, and answer follow-up questions like "What decisions are needed?" You can download a report to share.

Everything runs on your own computer. Nothing you paste is sent anywhere, and nothing is saved when you close the app. Click **Quit** in the chat (or close the black window on Windows) when you're done. See [docs/chat-app.md](docs/chat-app.md) for details.

If you use Python, you can also run the same chat with `pip install "project-risk-agent[chat]"` and then `project-risk-agent-chat`.

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

## Install

```bash
pip install project-risk-agent
```

The project has a deterministic, no-API-key baseline, so you can run it against your own signals file without a paid model:

```bash
project-risk-agent path/to/signals.json --brief
```

### Try the bundled example (from a clone)

```bash
git clone https://github.com/jsconu/project-risk-agent.git
cd project-risk-agent
pip install -e ".[dev]"
project-risk-agent examples/scenarios/hidden_dependency_risk.json
project-risk-agent examples/scenarios/hidden_dependency_risk.json --brief
```

### Optional OpenAI provider

The deterministic provider remains the default. To use OpenAI's model-backed reasoning, install the optional dependency, set an API key outside the repository, and choose a model explicitly:

```bash
pip install "project-risk-agent[openai]"
export OPENAI_API_KEY="..."
project-risk-agent examples/scenarios/hidden_dependency_risk.json --provider openai --model YOUR_MODEL_ID
```

The provider uses the OpenAI Responses API with structured JSON output, validates every response against the existing `Finding` schema, and rejects evidence citations for signals that were not supplied. The API app also accepts any `ModelProvider` through `create_app(provider=...)`, so deployments can opt in without changing the HTTP contract. See the official [Responses API reference](https://developers.openai.com/api/reference/cli/resources/responses/methods/create) for the current API contract.

To enable longitudinal project intelligence locally, provide a state file:

```bash
project-risk-agent examples/scenarios/hidden_dependency_risk.json --state .project-risk/state.json
```

Run the same command later with updated signals to see material finding changes and whether management attention increased or decreased.

Trajectory output reports `new`, `persistent`, `improving`, `deteriorating`, and `stale` active findings. A finding is `resolved` only with fresh, explicitly linked resolution evidence; simply omitting it in a later run never closes it.

Explicit decision requests are emitted separately in CLI and API output. Each has a readiness status: `ready`, `missing_owner`, `missing_deadline`, or `missing_owner_and_deadline`. This is an accountability aid for human review; it does not make or execute project decisions.

Dependency findings are also emitted as a separate queue. Their status is `blocked`, `waiting`, or `at_risk`, and each item keeps the IDs of its supporting signals.

For the HTTP API:

```bash
pip install "project-risk-agent[api]"
uvicorn project_risk_agent.api:app --reload
```

The API exposes `GET /health`, `POST /analyze`, and `POST /brief`. `/analyze` returns structured findings; `/brief` also returns a concise Markdown management brief. Both use the same core service as the CLI.

### Try the demo UI

With the API running, serve the static demo from the repository root:

```bash
python -m http.server 8001 --directory demo
```

Open `http://127.0.0.1:8001` and click **Analyze**. The page uses only synthetic sample data and calls the local API. The API explicitly allows requests from the two localhost origins used by this demo.

## Persistent project intelligence

The service can retain a local snapshot and compare the next analysis with the previous one. This creates the foundation for an agent that understands **change over time**, rather than repeatedly summarizing the current state from scratch.

```python
from project_risk_agent.state import JsonProjectStateStore

store = JsonProjectStateStore(".project-risk/state.json")
result = service.analyze_with_state(signals, store)

print("New:", [f.title for f in result.delta.new])
print("Resolved:", [f.title for f in result.delta.resolved])
print("Changed:", [c.attention_direction for c in result.changed_findings])
```

Continuing findings are compared for material changes in severity, urgency, confidence, ownership, decision state, and recommended actions. The delta reports whether management attention increased or decreased. See `docs/state.md` for the persistence model and privacy considerations.

## Evaluation

Synthetic evaluations are a first-class development artifact:

```bash
python evaluations/run.py
```

The current suite includes ten scenarios spanning explicit and inferred risks, active issues, dependencies, decisions, resource pressure, scope changes, quality regressions, vendor uncertainty, and false-positive controls. See `docs/evaluations.md`.

## Jira Cloud

A working Jira Cloud read connector is included for local/personal integrations. Set:

```bash
export JIRA_BASE_URL="https://your-domain.atlassian.net"
export JIRA_EMAIL="you@example.com"
export JIRA_API_TOKEN="..."
```

Then use `JiraConnector` to list projects and normalize Jira issues into `ProjectSignal` objects. For a hosted multi-user application, the connector should be extended to Atlassian OAuth 2.0 rather than collecting individual API tokens.

## Initial scope

The current foundation includes:

1. common signal and finding schemas
2. file/text ingestion for local experimentation
3. evidence and provenance handling
4. risk/issue/dependency/decision classification
5. cross-signal and temporal schedule reasoning
6. transparent finding prioritization
7. structured decision-request extraction
8. executable synthetic evaluation cases
9. a provider abstraction for deterministic or model-backed reasoning
10. a minimal FastAPI surface with analysis and management-brief endpoints
11. persistent local project state and finding-delta detection
12. longitudinal change detection for continuing findings
13. a working Jira Cloud read connector
14. a working Slack read connector
15. connector templates for additional providers
16. a lightweight local demo UI
17. an optional OpenAI Responses API provider with schema and evidence validation
18. a decision queue that surfaces missing ownership and deadlines
19. a dependency queue with evidence-linked delivery status

Planned production connectors include Monday.com, Smartsheet, Microsoft Teams, Gmail, Outlook, and meeting-transcript sources.

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
    {"signal_id": "signal-104", "excerpt": "API delivery moved to Friday"},
    {"signal_id": "signal-117", "excerpt": "Testing cannot start until API is available"}
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

See `CONTRIBUTING.md`, `docs/connectors.md`, `docs/connector-template.md`, and
`docs/releasing.md` for the release process. Participation is governed by our
[Code of Conduct](CODE_OF_CONDUCT.md).

Evaluations are treated as a first-class part of development. New reasoning behavior should ideally include an evaluation case demonstrating what improved or regressed.

## Project status

Early development. APIs and schemas may change. Jira and Slack are the first external connectors implemented end-to-end; other provider directories currently contain architectural adapters/templates rather than claimed production integrations.

## License

Apache-2.0
