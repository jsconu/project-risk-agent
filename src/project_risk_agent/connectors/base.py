from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from project_risk_agent.models import ProjectSignal


class ProjectConnector(ABC):
    """Interface implemented by every external project-data connector."""

    name: str

    @abstractmethod
    def authenticate(self) -> None:
        """Validate or establish authentication for the connector."""
        raise NotImplementedError

    @abstractmethod
    def get_projects(self) -> list[dict[str, Any]]:
        """Return projects available to the authenticated user."""
        raise NotImplementedError

    @abstractmethod
    def get_signals(self, project_id: str) -> list[ProjectSignal]:
        """Return normalized signals for a project."""
        raise NotImplementedError

    @abstractmethod
    def normalize(self, source_data: Any) -> ProjectSignal:
        """Convert source-specific data into the common signal model."""
        raise NotImplementedError
