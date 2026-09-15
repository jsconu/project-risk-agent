from datetime import UTC, datetime

from project_risk_agent.analysis import SignalReasoner
from project_risk_agent.models import ProjectSignal, RiskCategory


def signal(content: str, signal_id: str) -> ProjectSignal:
    return ProjectSignal(
        id=signal_id,
        source="test",
        source_type="text",
        timestamp=datetime.now(UTC),
        content=content,
    )


def test_conflicting_schedule_status_is_surfaced():
    findings = SignalReasoner().analyze([
        signal("The launch is on track for September 30.", "s1"),
        signal("The launch date moved from September 30 to October 7.", "s2"),
    ])
    schedule = next(f for f in findings if f.category == RiskCategory.SCHEDULE)
    assert schedule.confidence >= 0.84
    assert {e.signal_id for e in schedule.evidence} == {"s1", "s2"}
    assert "conflicting" in schedule.description.lower()
