# Connector Contribution Starter Kit

Connectors turn external project information into the common `ProjectSignal` schema. The reasoning layer should not need to know whether a signal came from Jira, chat, email, a meeting transcript, or a custom system.

## Contract

Implement `ProjectConnector` from `src/project_risk_agent/connectors/base.py`:

```python
from project_risk_agent.connectors.base import ProjectConnector
from project_risk_agent.models import ProjectSignal


class ExampleConnector(ProjectConnector):
    name = "example"

    def authenticate(self) -> None:
        # Validate credentials or establish the client session.
        ...

    def get_projects(self) -> list[dict]:
        ...

    def get_signals(self, project_id: str) -> list[ProjectSignal]:
        ...

    def normalize(self, source_data: dict) -> ProjectSignal:
        ...
```

## Required normalization

Every normalized signal should preserve:

- a stable `id` when the source provides one
- `source` and `source_type`
- a timestamp when available
- project identity when available
- author identity when available and appropriate
- the original human-readable content
- useful source metadata
- provenance identifying the connector

Do not put connector-specific assumptions into the analysis engine.

## Security checklist

Before opening a pull request:

- Use the source system's official API.
- Use OAuth or scoped credentials where supported.
- Request read-only permissions unless a write capability is explicitly required.
- Never hard-code tokens, secrets, or customer data.
- Document required environment variables and scopes.
- Preserve source IDs and timestamps for auditability.
- Avoid logging message bodies or credentials by default.
- Add synthetic tests for normalization and pagination/error handling.

## Pull request checklist

1. Add the connector under `src/project_risk_agent/connectors/`.
2. Export it from `connectors/__init__.py` when appropriate.
3. Add unit tests using synthetic payloads only.
4. Update `docs/connectors.md` with setup and permissions.
5. Add an entry to the connector table in the README when the adapter is usable.
6. Explain any API limits, pagination behavior, and known source-specific caveats.
