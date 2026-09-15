from __future__ import annotations

from typing import Any

from project_risk_agent.connectors.base import ProjectConnector
from project_risk_agent.models import ProjectSignal


class PlannedConnector(ProjectConnector):
    """Base template for provider adapters.

    Provider-specific authentication and retrieval are intentionally left to
    each integration. The important contract is normalization into signals.
    """

    def authenticate(self) -> None:
        raise NotImplementedError("Configure provider authentication in this connector")

    def get_projects(self) -> list[dict[str, Any]]:
        raise NotImplementedError

    def get_signals(self, project_id: str) -> list[ProjectSignal]:
        raise NotImplementedError

    def normalize(self, source_data: Any) -> ProjectSignal:
        raise NotImplementedError


class JiraConnector(PlannedConnector):
    name = "jira"


class MondayConnector(PlannedConnector):
    name = "monday"


class SmartsheetConnector(PlannedConnector):
    name = "smartsheet"


class SlackConnector(PlannedConnector):
    name = "slack"


class TeamsConnector(PlannedConnector):
    name = "teams"


class GmailConnector(PlannedConnector):
    name = "gmail"


class OutlookConnector(PlannedConnector):
    name = "outlook"


class MeetingTranscriptConnector(PlannedConnector):
    name = "meeting_transcript"
