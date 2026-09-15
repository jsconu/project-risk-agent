from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from project_risk_agent.connectors.base import ProjectConnector
from project_risk_agent.models import ProjectSignal


class FileConnector(ProjectConnector):
    """Ingest local text or JSON files for development and evaluation."""

    name = "file"

    def authenticate(self) -> None:
        return None

    def get_projects(self) -> list[dict[str, Any]]:
        return [{"id": "local", "name": "Local project"}]

    def get_signals(self, project_id: str) -> list[ProjectSignal]:
        return []

    def normalize(self, source_data: Any) -> ProjectSignal:
        if isinstance(source_data, str):
            content = source_data
            metadata: dict[str, object] = {}
        else:
            content = str(source_data.get("content", ""))
            metadata = dict(source_data.get("metadata", {}))

        return ProjectSignal(
            id=f"file-{abs(hash(content))}",
            source="file",
            source_type="document",
            timestamp=datetime.now(UTC),
            project_id=metadata.pop("project_id", None),
            author=metadata.pop("author", None),
            content=content,
            metadata=metadata,
            provenance={"connector": self.name},
        )

    def load(self, path: str | Path) -> list[ProjectSignal]:
        file_path = Path(path)
        if file_path.suffix.lower() == ".json":
            data = json.loads(file_path.read_text(encoding="utf-8"))
            items = data if isinstance(data, list) else [data]
        else:
            items = [file_path.read_text(encoding="utf-8")]
        return [self.normalize(item) for item in items]
