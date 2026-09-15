from __future__ import annotations

import base64
import json
import os
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from project_risk_agent.connectors.base import ProjectConnector
from project_risk_agent.models import ProjectSignal


class JiraConnector(ProjectConnector):
    """Read Jira Cloud projects and issues using the official REST API."""

    name = "jira"

    def __init__(self, base_url: str | None = None, email: str | None = None, api_token: str | None = None, timeout: int = 30) -> None:
        self.base_url = (base_url or os.getenv("JIRA_BASE_URL", "")).rstrip("/")
        self.email = email or os.getenv("JIRA_EMAIL")
        self.api_token = api_token or os.getenv("JIRA_API_TOKEN")
        self.timeout = timeout

    def authenticate(self) -> None:
        if not self.base_url or not self.email or not self.api_token:
            raise ValueError("Set JIRA_BASE_URL, JIRA_EMAIL, and JIRA_API_TOKEN")
        self._request("/rest/api/3/myself")

    def get_projects(self) -> list[dict[str, Any]]:
        self._require_credentials()
        start_at = 0
        projects: list[dict[str, Any]] = []
        while True:
            payload = self._request("/rest/api/3/project/search", params={"startAt": start_at, "maxResults": 50})
            values = payload.get("values", [])
            projects.extend({"id": str(item["id"]), "key": item.get("key"), "name": item.get("name")} for item in values)
            if start_at + len(values) >= payload.get("total", 0) or not values:
                return projects
            start_at += len(values)

    def get_signals(self, project_id: str) -> list[ProjectSignal]:
        self._require_credentials()
        signals: list[ProjectSignal] = []
        next_page_token: str | None = None
        while True:
            params: dict[str, str | int] = {"jql": f'project = "{project_id}" ORDER BY updated DESC', "maxResults": 100, "fields": "summary,status,description,updated,assignee,priority"}
            if next_page_token:
                params["nextPageToken"] = next_page_token
            payload = self._request("/rest/api/3/search/jql", method="POST", json_body=params)
            issues = payload.get("issues", [])
            signals.extend(self.normalize(issue) for issue in issues)
            next_page_token = payload.get("nextPageToken")
            if not next_page_token or not issues:
                return signals

    def normalize(self, source_data: Any) -> ProjectSignal:
        fields = source_data.get("fields", {})
        issue_key = source_data.get("key", source_data.get("id", "unknown"))
        description = _adf_text(fields.get("description"))
        status = (fields.get("status") or {}).get("name", "")
        priority = (fields.get("priority") or {}).get("name", "")
        summary = fields.get("summary", "")
        content = " | ".join(part for part in [summary, status, priority, description] if part)
        return ProjectSignal(id=f"jira-{issue_key}", source="jira", source_type="issue", timestamp=_parse_timestamp(fields.get("updated")), project_id=(fields.get("project") or {}).get("key"), author=(fields.get("assignee") or {}).get("displayName"), content=content, metadata={"issue_key": issue_key, "status": status, "priority": priority}, provenance={"connector": self.name, "resource": f"/browse/{issue_key}"})

    def _require_credentials(self) -> None:
        if not self.base_url or not self.email or not self.api_token:
            raise ValueError("Set JIRA_BASE_URL, JIRA_EMAIL, and JIRA_API_TOKEN")

    def _request(self, path: str, *, method: str = "GET", params: dict[str, str | int] | None = None, json_body: dict[str, Any] | None = None) -> dict[str, Any]:
        self._require_credentials()
        url = f"{self.base_url}{path}"
        if params:
            url += "?" + urlencode(params)
        credentials = base64.b64encode(f"{self.email}:{self.api_token}".encode()).decode()
        body = json.dumps(json_body).encode() if json_body is not None else None
        request = Request(url, data=body, method=method, headers={"Accept": "application/json", "Content-Type": "application/json", "Authorization": f"Basic {credentials}"})
        with urlopen(request, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))


def _adf_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if not isinstance(value, dict):
        return ""
    parts: list[str] = []
    if value.get("type") == "text" and value.get("text"):
        parts.append(str(value["text"]))
    for child in value.get("content", []):
        text = _adf_text(child)
        if text:
            parts.append(text)
    return " ".join(parts)


def _parse_timestamp(value: Any) -> datetime:
    if not value:
        return datetime.now(UTC)
    return datetime.fromisoformat(str(value))
