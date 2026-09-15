from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from project_risk_agent.models import Finding, ProjectSignal


@dataclass
class ProjectSnapshot:
    """Persisted project intelligence used to compare the latest run with prior state."""

    signals: list[ProjectSignal]
    findings: list[Finding]


class ProjectStateStore(Protocol):
    def load(self) -> ProjectSnapshot | None:
        """Load the most recent snapshot, if one exists."""

    def save(self, snapshot: ProjectSnapshot) -> None:
        """Persist a new project snapshot."""


class JsonProjectStateStore:
    """Small local state store for demos and single-project deployments."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> ProjectSnapshot | None:
        if not self.path.exists():
            return None
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        return ProjectSnapshot(
            signals=[ProjectSignal.model_validate(item) for item in payload.get("signals", [])],
            findings=[Finding.model_validate(item) for item in payload.get("findings", [])],
        )

    def save(self, snapshot: ProjectSnapshot) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "signals": [signal.model_dump(mode="json") for signal in snapshot.signals],
            "findings": [finding.model_dump(mode="json") for finding in snapshot.findings],
        }
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        temporary.replace(self.path)
