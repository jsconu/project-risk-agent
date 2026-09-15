# Connectors

Connectors isolate provider-specific retrieval and authentication from the risk engine.

## Contract

Implement `ProjectConnector` and provide:

- `authenticate()` — validate credentials/scopes
- `get_projects()` — enumerate accessible projects
- `get_signals(project_id)` — retrieve project-relevant source data
- `normalize(source_data)` — convert provider objects into `ProjectSignal`

A connector may intentionally remain read-only. The risk agent does not need write permissions to identify risks or decisions.

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

## Current adapters

| Source | Status |
|---|---|
| Jira Cloud | Read connector |
| Slack | Read connector |
| Generic webhook/file | Available |
| Monday.com | Template |
| Smartsheet | Template |
| Microsoft Teams | Template |
| Gmail | Template |
| Outlook | Template |
| Meeting transcripts | Template |

### Slack notes

The Slack adapter uses the official Conversations API and a Slack app token supplied through `SLACK_BOT_TOKEN`. `conversations.list` uses the app's granted read scopes, while message history requires the relevant `*:history` scopes. Slack's current documentation also notes tighter history rate limits for many non-Marketplace distributed apps, so the connector intentionally limits a history request to 15 messages and leaves broader synchronization to a host application with appropriate rate-limit handling.

For a production multi-workspace product, use Slack's OAuth installation flow rather than asking users to paste long-lived tokens into an application. Keep tokens in the host application's secret store.

## Security expectations

Use the provider's official API and supported OAuth/token mechanism. Request only the scopes required for the connector. Never store credentials in source control.

Meeting support begins with transcript ingestion rather than live recording. This keeps the core project focused on analysis and avoids making audio capture a prerequisite.

## Adding a connector

1. Create a module under `src/project_risk_agent/connectors/`.
2. Implement `ProjectConnector` where the provider maps cleanly to the generic contract.
3. Normalize provider records into `ProjectSignal`.
4. Add synthetic fixture data.
5. Add normalization tests.
6. Document required credentials/scopes and privacy implications.
7. Run the full test suite and lint checks.

A connector PR should not require changes to the reasoning engine unless a new generic signal capability is genuinely necessary.
