from project_risk_agent.delta import compare_findings
from project_risk_agent.models import Finding, FindingType, RiskCategory


def finding(identifier: str) -> Finding:
    return Finding(
        id=identifier,
        type=FindingType.RISK,
        category=RiskCategory.SCHEDULE,
        title=identifier,
        description=identifier,
        confidence=0.8,
    )


def test_compare_findings_tracks_new_continuing_and_resolved():
    delta = compare_findings([finding("old"), finding("same")], [finding("same"), finding("new")])

    assert [item.id for item in delta.new] == ["new"]
    assert [item.id for item in delta.continuing] == ["same"]
    assert [item.id for item in delta.resolved] == ["old"]
