from project_risk_agent.models import Finding, FindingType, ProjectSignal, RiskCategory
from project_risk_agent.service import RiskAnalysisService
from project_risk_agent.state import JsonProjectStateStore


class StaticProvider:
    def __init__(self, findings):
        self.findings = findings

    def analyze(self, signals):
        return self.findings


def finding(identifier: str) -> Finding:
    return Finding(
        id=identifier,
        type=FindingType.RISK,
        category=RiskCategory.SCHEDULE,
        title=identifier,
        description=identifier,
        confidence=0.8,
    )


def test_analyze_with_state_persists_and_returns_delta(tmp_path):
    store = JsonProjectStateStore(tmp_path / "state.json")
    signal = ProjectSignal(id="s1", source="test", source_type="text", content="update")

    first = RiskAnalysisService(StaticProvider([finding("a")])).analyze_with_state([signal], store)
    second = RiskAnalysisService(StaticProvider([finding("a"), finding("b")])).analyze_with_state([signal], store)

    assert first.delta is not None
    assert [item.id for item in first.delta.new] == ["a"]
    assert [item.id for item in second.delta.new] == ["b"]
    assert [item.id for item in second.delta.continuing] == ["a"]
