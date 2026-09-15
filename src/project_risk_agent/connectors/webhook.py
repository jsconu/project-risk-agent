from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from project_risk_agent.connectors.base import ProjectConnector
from project_risk_agent.models import ProjectSignal


class WebhookConnector(ProjectConnector):
    """Normalize generic webhook payloads from systems without a native adapter."""

    name = "webhook"

    def authenticate(self) -> None:
        return None

    def get_projects(self) -> list[dict[str, Any]]:
        return []

    def get_signals(self, project_id: str) -> list[ProjectSignal]:
        return []

    def normalize(self, source_data: dict[str, Any]) -> ProjectSignal:
        content = str(source_data.get("content", source_data.get("text", "")))
        timestamp = source_data.get("timestamp")
        if isinstance(timestamp, str):
            parsed_timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        else:
            parsed_timestamp = datetime.now(timezone.utc)

        return ProjectSignal(
            id=str(source_data.get("id", f"webhook-{abs(hash(content))}")),
            source=str(source_data.get("source", "webhook")),
            source_type=str(source_data.get("source_type", "webhook")),
            timestamp=parsed_timestamp,
            project_id=source_data.get("project_id"),
            author=source_data.get("author"),
            content=content,
            metadata=dict(source_data.get("metadata", {})),
            provenance={"connector": self.name, "payload_type": "generic"},
        )
