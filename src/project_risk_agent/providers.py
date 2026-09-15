from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from pydantic import TypeAdapter, ValidationError

from project_risk_agent.models import Finding, ProjectSignal


class ModelProvider(Protocol):
    """Provider boundary for optional model-backed semantic reasoning."""

    def analyze(self, signals: list[ProjectSignal]) -> list[Finding]:
        ...


@dataclass
class DeterministicProvider:
    """No-key provider useful for local development, tests, and demos."""

    reasoner: object

    def analyze(self, signals: list[ProjectSignal]) -> list[Finding]:
        return self.reasoner.analyze(signals)


class StructuredModelProvider(Protocol):
    """Minimal boundary for an external model that can return structured JSON."""

    def complete_json(self, *, system: str, user: str) -> object:
        ...


_FINDING_LIST = TypeAdapter(list[Finding])


def parse_model_findings(payload: object) -> list[Finding]:
    """Validate model output before it enters the application domain."""
    candidate = payload["findings"] if isinstance(payload, dict) and "findings" in payload else payload
    try:
        return _FINDING_LIST.validate_python(candidate)
    except ValidationError as exc:
        raise ValueError("Model output does not match the Finding schema") from exc


def build_reasoning_prompt(signals: list[ProjectSignal]) -> str:
    """Create a vendor-neutral prompt while preserving signal provenance."""
    lines = [
        "Analyze these project signals for management-relevant risks, issues, dependencies, and decisions.",
        "Do not invent evidence. Distinguish observed evidence from inference.",
        "Every finding must cite one or more provided signal IDs as evidence.",
        "Return structured findings using the project's Finding schema.",
        "Signals:",
    ]
    for signal in signals:
        lines.append(f"[{signal.id}] ({signal.source_type}) {signal.content}")
    return "\n".join(lines)
