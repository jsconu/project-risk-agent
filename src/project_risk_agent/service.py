from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from project_risk_agent.delta import FindingChange, FindingDelta, compare_findings
from project_risk_agent.decisions import DecisionRequest, extract_decision_requests
from project_risk_agent.freshness import FindingFreshness, freshness_for_findings
from project_risk_agent.models import Finding, ProjectSignal
from project_risk_agent.prioritizer import prioritize
from project_risk_agent.providers import ModelProvider
from project_risk_agent.state import ProjectSnapshot, ProjectStateStore
from project_risk_agent.trajectory import FindingTrajectory, trajectories


@dataclass
class AnalysisResult:
    findings: list[Finding]
    signals_analyzed: int
    signals: list[ProjectSignal] | None = None
    decision_requests: list[DecisionRequest] | None = None
    delta: FindingDelta | None = None
    analyzed_at: datetime | None = None
    freshness: list[FindingFreshness] | None = None

    @property
    def management_attention(self) -> list[Finding]:
        """Return findings requiring the most immediate human attention."""
        return prioritize(self.findings)

    @property
    def changed_findings(self) -> list[FindingChange]:
        """Return continuing findings whose material attributes changed."""
        return self.delta.changed if self.delta else []

    @property
    def trend(self) -> str:
        """Summarize whether management attention is increasing, decreasing, or stable."""
        if not self.delta or not self.delta.changed:
            return "stable"
        increased = sum(change.attention_direction == "increased" for change in self.delta.changed)
        decreased = sum(change.attention_direction == "decreased" for change in self.delta.changed)
        if increased > decreased:
            return "increasing"
        if decreased > increased:
            return "decreasing"
        return "mixed"

    def freshness_for(self, finding_id: str) -> FindingFreshness | None:
        """Look up the evidence freshness for a finding."""
        return next((item for item in self.freshness or [] if item.finding_id == finding_id), None)

    def trajectory_for(self, finding_id: str) -> FindingTrajectory | None:
        """Return the longitudinal trajectory for a finding."""
        return next((item for item in self.trajectories if item.finding_id == finding_id), None)

    @property
    def trajectories(self) -> list[FindingTrajectory]:
        """Classify current findings by longitudinal state and evidence freshness."""
        return trajectories(self.findings, self.delta, self.freshness, self.signals, now=self.analyzed_at)


class RiskAnalysisService:
    def __init__(self, provider: ModelProvider) -> None:
        self.provider = provider

    def analyze(self, signals: list[ProjectSignal]) -> AnalysisResult:
        findings = self.provider.analyze(signals)
        return AnalysisResult(
            findings=findings,
            signals_analyzed=len(signals),
            signals=signals,
            decision_requests=extract_decision_requests(signals),
            analyzed_at=datetime.now(UTC),
            freshness=freshness_for_findings(findings, signals),
        )

    def analyze_with_state(self, signals: list[ProjectSignal], store: ProjectStateStore) -> AnalysisResult:
        """Analyze current signals, compare with prior intelligence, and persist state."""
        previous = store.load()
        result = self.analyze(signals)
        prior_findings = previous.findings if previous else []
        result.delta = compare_findings(prior_findings, result.findings)
        store.save(ProjectSnapshot(signals=signals, findings=result.findings, analyzed_at=result.analyzed_at))
        return result
