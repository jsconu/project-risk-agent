from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from project_risk_agent.models import Finding, ProjectSignal


class ModelProvider(Protocol):
    """Provider boundary for optional LLM-backed reasoning."""

    def analyze(self, signals: list[ProjectSignal]) -> list[Finding]:
        ...


@dataclass
class DeterministicProvider:
    """No-key provider useful for local development, tests, and demos."""

    reasoner: object

    def analyze(self, signals: list[ProjectSignal]) -> list[Finding]:
        analyze = getattr(self.reasoner, "analyze")
        return analyze(signals)
