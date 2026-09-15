from __future__ import annotations

from dataclasses import dataclass

from project_risk_agent.delta import FindingDelta, compare_findings
from project_risk_agent.models import Finding, ProjectSignal
from project_risk_agent.prioritizer import prioritize
from project_risk_agent.providers import ModelProvider
from project_risk_agent.state import ProjectSnapshot, ProjectStateStore


@dataclass
class AnalysisResult:
    findings: list[Finding]
    signals_analyzed: int
    delta: FindingDelta | None = None

    @property
    def management_attention(self) -> list[Finding]:
        """Return findings requiring the most immediate human attention."""
        return prioritize(self.findings)

    @property
    def changed_findings(self):
        """Return continuing findings whose material attributes changed."""
        return self.delta.changed if self.delta else []


class RiskAnalysisService:
    def __init__(self, provider: ModelProvider) -> None:
        self.provider = provider

    def analyze(self, signals: list[ProjectSignal]) -> AnalysisResult:
        findings = self.provider.analyze(signals)
        return AnalysisResult(findings=findings, signals_analyzed=len(signals))

    def analyze_with_state(
        self,
        signals: list[ProjectSignal],
        store: ProjectStateStore,
    ) -> AnalysisResult:
        """Analyze current signals, compare with prior intelligence, and persist state."""
        previous = store.load()
        result = self.analyze(signals)
        prior_findings = previous.findings if previous else []
        result.delta = compare_findings(prior_findings, result.findings)
        store.save(ProjectSnapshot(signals=signals, findings=result.findings))
        return result
