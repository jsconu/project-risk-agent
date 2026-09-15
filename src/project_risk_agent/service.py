from __future__ import annotations

from dataclasses import dataclass

from project_risk_agent.models import Finding, ProjectSignal
from project_risk_agent.prioritizer import prioritize
from project_risk_agent.providers import ModelProvider


@dataclass
class AnalysisResult:
    findings: list[Finding]
    signals_analyzed: int

    @property
    def management_attention(self) -> list[Finding]:
        """Return findings requiring the most immediate human attention."""
        return prioritize(self.findings)


class RiskAnalysisService:
    def __init__(self, provider: ModelProvider) -> None:
        self.provider = provider

    def analyze(self, signals: list[ProjectSignal]) -> AnalysisResult:
        findings = self.provider.analyze(signals)
        return AnalysisResult(findings=findings, signals_analyzed=len(signals))
