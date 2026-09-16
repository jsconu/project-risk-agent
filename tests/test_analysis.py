from datetime import UTC, datetime

from project_risk_agent.analysis import SignalReasoner
from project_risk_agent.models import FindingType, ProjectSignal, RiskCategory


def signal(content: str, signal_id: str) -> ProjectSignal:
    return ProjectSignal(
        id=signal_id,
        source="test",
        source_type="text",
        timestamp=datetime.now(UTC),
        content=content,
    )


def test_dependency_is_classified_separately_from_schedule():
    findings = SignalReasoner().analyze([signal("UAT is waiting for the API delivery.", "s1")])
    assert findings[0].type == FindingType.DEPENDENCY
    assert findings[0].category == RiskCategory.DEPENDENCY


def test_cannot_start_language_is_classified_as_dependency():
    findings = SignalReasoner().analyze([signal("QA cannot start integration testing until the API is available.", "s1")])
    assert findings[0].type == FindingType.DEPENDENCY
    assert findings[0].category == RiskCategory.DEPENDENCY


def test_multiple_signals_are_corroborated_with_all_evidence():
    findings = SignalReasoner().analyze([
        signal("The release is delayed by two days.", "s1"),
        signal("The release is still delayed after today's checkpoint.", "s2"),
    ])
    assert len(findings) == 1
    assert {e.signal_id for e in findings[0].evidence} == {"s1", "s2"}
    assert findings[0].confidence > 0.68


def test_explicit_risk_language_is_not_promoted_to_issue():
    findings = SignalReasoner().analyze([signal("Integration testing is at risk because the API is delayed.", "s1")])
    assert len(findings) == 1
    assert findings[0].type == FindingType.RISK
    assert findings[0].category == RiskCategory.SCHEDULE


def test_currently_blocked_condition_is_an_issue():
    findings = SignalReasoner().analyze([signal("UAT is currently blocked by the unavailable API.", "s1")])
    assert findings[0].type == FindingType.ISSUE


def test_decision_language_creates_decision_finding():
    findings = SignalReasoner().analyze([signal("Leadership approval is needed to choose the revised launch date.", "s1")])
    assert findings[0].type == FindingType.DECISION
    assert findings[0].decision_required is True
