from __future__ import annotations

from project_risk_agent.analysis import SignalReasoner
from project_risk_agent.models import Finding, ProjectSignal


class RiskAnalyzer:
    """Public analysis facade for the project risk agent."""

    def __init__(self, reasoner: SignalReasoner | None = None) -> None:
        self.reasoner = reasoner or SignalReasoner()

    def analyze(self, signals: list[ProjectSignal]) -> list[Finding]:
        return self.reasoner.analyze(signals)
