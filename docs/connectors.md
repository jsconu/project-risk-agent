# Connectors

Connectors isolate provider-specific retrieval and authentication from the risk engine.

## Contract

Implement `ProjectConnector` and provide:

- `authenticate()` — validate credentials/scopes
- `get_projects()` — enumerate accessible projects
- `get_signals(project_id)` — retrieve project-relevant source data
- `normalize(source_data)` — convert provider objects into `ProjectSignal`

## Signal requirements

Every normalized signal should retain:

- stable source identifier
- source/provider
- source type
- timestamp
- project identifier when known
- author when available
- content
- useful metadata
- provenance sufficient to trace the original source

## Supported design targets

The architecture accommodates:

| Source | Planned adapter |
|---|---|
| Jira | Yes |
| Monday.com | Yes |
| Smartsheet | Yes |
| Slack | Yes |
| Microsoft Teams | Yes |
| Gmail | Yes |
| Outlook | Yes |
| Meeting transcripts | Yes |
| Generic webhook/file | Yes |

The repository currently includes connector templates; provider-specific API implementations are developed independently.

## Security expectations

Use the provider's official API and supported OAuth/token mechanism. Request only the scopes required for the connector. Never store credentials in source control.

Meeting support begins with transcript ingestion rather than live recording. This keeps the core project focused on analysis and avoids making audio capture a prerequisite.

## Adding a connector

1. Create a module under `src/project_risk_agent/connectors/`.
2. Implement `ProjectConnector`.
3. Normalize provider records into `ProjectSignal`.
4. Add synthetic fixture data.
5. Add normalization tests.
6. Document required credentials/scopes and privacy implications.
7. Run the full test suite and lint checks.

A connector PR should not require changes to the reasoning engine unless a new generic signal capability is genuinely necessary.
