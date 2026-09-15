from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

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
        analyze = getattr(self.reasoner, "analyze")
        return analyze(signals)


class StructuredModelProvider(Protocol):
    """Minimal boundary for an external model that can return structured JSON."""

    def complete_json(self, *, system: str, user: str) -> object:
        ...


def build_reasoning_prompt(signals: list[ProjectSignal]) -> str:
    """Create a vendor-neutral prompt while preserving signal provenance."""
    lines = [
        "Analyze these project signals for management-relevant risks, issues, dependencies, and decisions.",
        "Do not invent evidence. Distinguish observed evidence from inference.",
        "Return structured findings using the project's Finding schema.",
        "Signals:",
    ]
    for signal in signals:
        lines.append(f"[{signal.id}] ({signal.source_type}) {signal.content}")
    return "\n".join(lines)
