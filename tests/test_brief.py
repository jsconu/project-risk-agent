from project_risk_agent.brief import management_brief
from project_risk_agent.models import Evidence, Finding, FindingType, RiskCategory


def test_brief_contains_evidence_and_actions():
    finding = Finding(
        id="f1",
        type=FindingType.RISK,
        category=RiskCategory.SCHEDULE,
        title="Potential schedule concern",
        description="The dependency date moved.",
        confidence=0.82,
        evidence=[Evidence(signal_id="s1", excerpt="Delivery moved to Friday")],
        recommended_actions=["Confirm the dependency date."],
    )
    brief = management_brief([finding])
    assert "Potential schedule concern" in brief
    assert "s1" in brief
    assert "Confirm the dependency date." in brief
