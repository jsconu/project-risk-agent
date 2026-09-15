from project_risk_agent.models import Finding, FindingType, RiskCategory
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
