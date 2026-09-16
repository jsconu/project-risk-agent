from project_risk_agent.dependencies import dependency_items
from project_risk_agent.models import Evidence, Finding, FindingType, RiskCategory


def dependency(description: str) -> Finding:
    return Finding(
        id="dependency-1",
        type=FindingType.DEPENDENCY,
        category=RiskCategory.DEPENDENCY,
        title="Dependency concern",
        description=description,
        confidence=0.8,
        evidence=[Evidence(signal_id="s1", excerpt=description)],
    )


def test_dependencies_report_blocked_status_and_evidence():
    result = dependency_items([dependency("Testing cannot start because the API is blocked.")])

    assert result[0].status == "blocked"
    assert result[0].evidence_signal_ids == ["s1"]


def test_dependencies_distinguish_waiting_and_at_risk():
    waiting = dependency_items([dependency("The team is waiting for the API.")])
    at_risk = dependency_items([dependency("The vendor delivery may slip.")])

    assert waiting[0].status == "waiting"
    assert at_risk[0].status == "at_risk"
