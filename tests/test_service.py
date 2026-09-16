from project_risk_agent.models import Finding, FindingType, ProjectSignal, RiskCategory
from project_risk_agent.service import RiskAnalysisService


class StubProvider:
    def analyze(self, signals):
        return [
            Finding(id="low", type=FindingType.RISK, category=RiskCategory.OTHER, title="Low", description="", urgency="low", impact="low", confidence=0.9),
            Finding(id="high", type=FindingType.RISK, category=RiskCategory.OTHER, title="High", description="", urgency="high", impact="high", confidence=0.7),
        ]


def test_management_attention_orders_by_urgency_and_impact():
    result = RiskAnalysisService(StubProvider()).analyze([])
    assert [finding.id for finding in result.management_attention] == ["high", "low"]


def test_service_exposes_decision_queue_separately_from_findings():
    signal = ProjectSignal(
        id="decision-1",
        source="meeting",
        source_type="transcript",
        timestamp="2026-01-01T00:00:00Z",
        content="A decision is needed to choose the rollout approach by Friday.",
    )

    result = RiskAnalysisService(StubProvider()).analyze([signal])

    assert result.decision_requests is not None
    assert result.decision_requests[0].readiness == "missing_owner"
