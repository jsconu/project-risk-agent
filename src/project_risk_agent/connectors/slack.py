from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from project_risk_agent.connectors.base import ProjectConnector
from project_risk_agent.models import ProjectSignal


class SlackConnector(ProjectConnector):
    """Read-only Slack Conversations API connector."""

    name = "slack"
    API_URL = "https://slack.com/api"

    def __init__(self, token: str | None = None, timeout: float = 20.0) -> None:
        self.token = token or os.getenv("SLACK_BOT_TOKEN")
        self.timeout = timeout
        if not self.token:
            raise ValueError("SLACK_BOT_TOKEN is required")

    def authenticate(self) -> bool:
        return bool(self._request("auth.test", {}).get("ok"))

    def get_projects(self) -> list[dict[str, Any]]:
        projects: list[dict[str, Any]] = []
        cursor = ""
        while True:
            params = {"exclude_archived": "true", "limit": "200", "types": "public_channel,private_channel"}
            if cursor:
                params["cursor"] = cursor
            response = self._request("conversations.list", params)
            projects.extend(response.get("channels", []))
            cursor = response.get("response_metadata", {}).get("next_cursor", "")
            if not cursor:
                return projects

    def get_signals(self, project_id: str, limit: int = 15) -> list[ProjectSignal]:
        response = self._request("conversations.history", {"channel": project_id, "limit": min(limit, 15)})
        return [self.normalize(message, project_id) for message in response.get("messages", [])]

    @staticmethod
    def normalize(message: dict[str, Any], project_id: str | None = None) -> ProjectSignal:
        timestamp = message.get("ts", "")
        try:
            observed = datetime.fromtimestamp(float(timestamp), tz=UTC)
        except (TypeError, ValueError, OverflowError):
            observed = datetime.now(UTC)
        message_id = f"slack:{project_id or 'conversation'}:{message.get('ts', 'unknown')}"
        return ProjectSignal(
            id=message_id,
            source="slack",
            source_type="message",
            timestamp=observed,
            project_id=project_id,
            author=message.get("user"),
            content=message.get("text", ""),
            metadata={"thread_ts": message.get("thread_ts"), "subtype": message.get("subtype")},
            provenance={"provider": "slack", "conversation_id": project_id, "message_ts": message.get("ts")},
        )

    def _request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        request = Request(
            f"{self.API_URL}/{method}",
            data=urlencode(params).encode("utf-8"),
            headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=self.timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if not payload.get("ok"):
            raise RuntimeError(f"Slack API error for {method}: {payload.get('error', 'unknown_error')}")
        return payload
