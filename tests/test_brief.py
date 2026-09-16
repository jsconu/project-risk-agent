from project_risk_agent.brief import management_brief
from project_risk_agent.decisions import DecisionRequest
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


def test_brief_includes_decision_queue_and_readiness():
    brief = management_brief(
        [],
        [
            DecisionRequest(
                signal_id="s2",
                description="Choose the rollout approach.",
                readiness="missing_owner_and_deadline",
            )
        ],
    )

    assert "# Project Risk Brief" in brief
    assert "Decision queue" in brief
    assert "missing owner and deadline" in brief
